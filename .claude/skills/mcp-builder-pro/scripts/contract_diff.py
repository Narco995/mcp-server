#!/usr/bin/env python3
"""Conservative, deterministic semantic comparison of version-1 contracts."""

import argparse
import json
from pathlib import Path

PRIMITIVES = {"array", "boolean", "integer", "null", "number", "object", "string"}
BOUNDS = ("minimum", "maximum", "minLength", "maxLength", "minItems", "maxItems")
SCHEMA_KEYS = {
    "type",
    "properties",
    "required",
    "additionalProperties",
    "items",
    "enum",
    "default",
    "description",
    "title",
    "examples",
    *BOUNDS,
}
KINDS = {"tools": "name", "resources": "uri", "prompts": "name"}


def canonical(value):
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def index_contract(document):
    if (
        not isinstance(document, dict)
        or type(document.get("schemaVersion")) is not int
        or document["schemaVersion"] != 1
        or set(document) != {"schemaVersion", *KINDS}
    ):
        raise ValueError(
            "expected schemaVersion 1 plus tools, resources and prompts arrays"
        )
    result = {}
    for kind, key in KINDS.items():
        entries = document[kind]
        if not isinstance(entries, list):
            raise TypeError(f"{kind} must be an array")
        by_name = result[kind] = {}
        for entry in entries:
            name = entry.get(key) if isinstance(entry, dict) else None
            if not isinstance(name, str) or not name.strip() or name in by_name:
                raise ValueError(f"{kind} requires a unique nonempty {key}")
            if kind == "tools":
                if entry.get("action") not in ("read", "write"):
                    raise ValueError(f"{name}: action must be read or write")
                scopes = entry.get("requiredScopes")
                if (
                    not isinstance(scopes, list)
                    or any(not isinstance(x, str) or not x for x in scopes)
                    or len(set(scopes)) != len(scopes)
                ):
                    raise ValueError(
                        f"{name}: requiredScopes must contain unique scope strings"
                    )
                if not isinstance(entry.get("description"), str):
                    raise ValueError(f"{name}: description must be a string")
                if not isinstance(entry.get("inputSchema"), dict):
                    raise ValueError(f"{name}: inputSchema must be an object")
                if "outputSchema" in entry and not isinstance(
                    entry["outputSchema"], dict
                ):
                    raise ValueError(
                        f"{name}: outputSchema, if present, must be an object"
                    )
                if not isinstance(entry.get("semantics"), dict):
                    raise ValueError(f"{name}: semantics must be an object")
            by_name[name] = entry
    return result


def simple(schema):
    if not isinstance(schema, dict) or set(schema) - SCHEMA_KEYS:
        return False
    kind = schema.get("type")
    if "type" in schema and (not isinstance(kind, str) or kind not in PRIMITIVES):
        return False
    if (
        any(key in schema for key in ("properties", "required", "additionalProperties"))
        and kind != "object"
    ):
        return False
    if "items" in schema and (kind != "array" or not isinstance(schema["items"], dict)):
        return False
    if (
        "additionalProperties" in schema
        and type(schema["additionalProperties"]) is not bool
    ):
        return False
    props = schema.get("properties", {})
    req = schema.get("required", [])
    enum = schema.get("enum", None)
    if not isinstance(props, dict) or any(
        not isinstance(v, dict) for v in props.values()
    ):
        return False
    if (
        not isinstance(req, list)
        or any(not isinstance(x, str) for x in req)
        or not set(req) <= set(props)
    ):
        return False
    if "enum" in schema and (not isinstance(enum, list) or not enum):
        return False
    for key in set(schema) & set(BOUNDS):
        value = schema[key]
        if key in ("minimum", "maximum"):
            if kind not in ("integer", "number") or type(value) not in (int, float):
                return False
        elif (
            type(value) is not int
            or value < 0
            or kind != ("array" if key.endswith("Items") else "string")
        ):
            return False
    return not any(
        low in schema and high in schema and schema[low] > schema[high]
        for low, high in (
            ("minimum", "maximum"),
            ("minItems", "maxItems"),
            ("minLength", "maxLength"),
        )
    )


def possible_types(schema):
    kind = schema.get("type")
    if kind is None:
        return PRIMITIVES
    return {"number", "integer"} if kind == "number" else {kind}


def compare_schema(old, new, path, output, emit):
    if canonical(old) == canonical(new):
        return
    if not simple(old) or not simple(new):
        emit("manual-review", path, "unsupported schema structure changed")
        return
    for field in ("description", "title", "default", "examples"):
        if canonical(old.get(field)) != canonical(new.get(field)) or (field in old) != (
            field in new
        ):
            emit("manual-review", f"{path}.{field}", "annotation or default changed")

    def inclusion(left, right, name, detail):
        accepts, supplies = (left, right) if output else (right, left)
        if not supplies <= accepts:
            emit("breaking", f"{path}.{name}", detail)
        elif left != right:
            emit(
                "additive",
                f"{path}.{name}",
                "constraint changed in the compatible direction",
            )

    def boolean_constraint(left, right, name):
        inclusion(
            {False, True} if left else {False},
            {False, True} if right else {False},
            name,
            "previously valid shape is no longer compatible",
        )

    inclusion(
        possible_types(old), possible_types(new), "type", "incompatible type change"
    )
    if "enum" in old or "enum" in new:
        before = {canonical(v) for v in old["enum"]} if "enum" in old else None
        after = {canonical(v) for v in new["enum"]} if "enum" in new else None
        supplies, accepts = (after, before) if output else (before, after)
        if accepts is not None and (supplies is None or not supplies <= accepts):
            emit("breaking", f"{path}.enum", "incompatible enum change")
        elif before != after:
            emit("additive", f"{path}.enum", "enum changed in the compatible direction")
    for bound in BOUNDS:
        is_min = bound.startswith("min")
        unbounded = -float("inf") if is_min else float("inf")
        a, b = old.get(bound, unbounded), new.get(bound, unbounded)
        if a != b:
            tighter = b > a if is_min else b < a
            kind = "breaking" if tighter != output else "additive"
            emit(kind, f"{path}.{bound}", "bound changed")
    if old.get("type") == new.get("type") == "object":
        props_a, props_b = old.get("properties", {}), new.get("properties", {})
        required_a, required_b = (
            set(old.get("required", [])),
            set(new.get("required", [])),
        )
        additional_a, additional_b = (
            old.get("additionalProperties", True),
            new.get("additionalProperties", True),
        )
        boolean_constraint(additional_a, additional_b, "additionalProperties")
        added_req, removed_req = required_b - required_a, required_a - required_b
        for prop in sorted(added_req | removed_req):
            broken = (prop in removed_req) if output else (prop in added_req)
            emit(
                "breaking" if broken else "additive",
                f"{path}.required.{prop}",
                "requiredness changed",
            )
        for prop in sorted(props_a.keys() | props_b.keys()):
            qualified = f"{path}.properties.{prop}"
            if prop in props_a and prop in props_b:
                compare_schema(props_a[prop], props_b[prop], qualified, output, emit)
            elif prop not in props_b:
                broken = output or not additional_b
                emit(
                    "breaking" if broken else "manual-review",
                    qualified,
                    "declared property removed",
                )
            else:
                # A new output field cannot be returned to a client that rejected it.
                # A new input field can restrict values an older open schema accepted.
                if output and not additional_a:
                    emit(
                        "breaking",
                        qualified,
                        "new output property not accepted by previous schema",
                    )
                elif not output and additional_a:
                    compare_schema({}, props_b[prop], qualified, False, emit)
                    emit(
                        "manual-review",
                        qualified,
                        "new declared property on previously open inputs",
                    )
                else:
                    emit("additive", qualified, "property added")
    elif old.get("type") == new.get("type") == "array":
        compare_schema(
            old.get("items", {}), new.get("items", {}), f"{path}.items", output, emit
        )
    elif any(
        k in old or k in new
        for k in ("properties", "required", "items", "additionalProperties")
    ):
        emit("manual-review", path, "container shape changed with its type")


def compare(old, new):
    a, b = index_contract(old), index_contract(new)
    findings = []

    def add(level, path, detail):
        findings.append({"classification": level, "path": path, "detail": detail})

    for kind, key in KINDS.items():
        before, after = a[kind], b[kind]
        for name in sorted(before.keys() | after.keys()):
            path = f"{kind}/{name}"
            if name not in after:
                add("breaking", path, "entry removed or renamed")
                continue
            if name not in before:
                mutating = after[name].get("action") == "write"
                add(
                    "manual-review" if mutating else "additive",
                    path,
                    "new write requires policy review" if mutating else "entry added",
                )
                continue
            original, candidate = before[name], after[name]
            for field in sorted((original.keys() | candidate.keys()) - {key}):
                left, right = original.get(field), candidate.get(field)
                if canonical(left) == canonical(right) and (field in original) == (
                    field in candidate
                ):
                    continue
                attr = f"{path}.{field}"
                if kind == "tools" and field in ("inputSchema", "outputSchema"):
                    if right is None:
                        add(
                            "breaking",
                            attr,
                            "previously declared output schema removed",
                        )
                    elif left is None:
                        add(
                            "manual-review",
                            attr,
                            "output schema added; verify existing consumers",
                        )
                    else:
                        compare_schema(left, right, attr, field == "outputSchema", add)
                elif kind == "tools" and field == "action" and right == "write":
                    add("breaking", attr, "read operation became mutating")
                elif (
                    kind == "tools"
                    and field == "requiredScopes"
                    and set(left) == set(right)
                ):
                    continue
                else:
                    add(
                        "manual-review",
                        attr,
                        "consumer-visible behavior or private policy changed",
                    )
    return sorted(findings, key=lambda f: (f["path"], f["classification"], f["detail"]))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("baseline", type=Path)
    parser.add_argument("candidate", type=Path)
    parser.add_argument("--format", choices=("text", "json"), default="text")
    args = parser.parse_args()
    try:
        results = compare(
            json.loads(args.baseline.read_text()),
            json.loads(args.candidate.read_text()),
        )
    except (OSError, TypeError, ValueError) as exc:
        print(
            json.dumps({"status": "invalid", "error": str(exc)})
            if args.format == "json"
            else f"invalid: {exc}"
        )
        return 3
    levels = {result["classification"] for result in results}
    status, code = next(
        (
            (level, code)
            for level, code in (("breaking", 1), ("manual-review", 2), ("additive", 0))
            if level in levels
        ),
        ("unchanged", 0),
    )
    if args.format == "json":
        print(json.dumps({"status": status, "findings": results}, indent=2))
    else:
        print(status)
        for item in results:
            print(f"{item['classification']}: {item['path']}: {item['detail']}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
