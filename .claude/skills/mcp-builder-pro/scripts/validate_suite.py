#!/usr/bin/env python3
"""Check the Claude Code skill suite, its local links and evaluation fixture coverage."""

import argparse
import json
import re
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory

HUB = "mcp-builder-pro"
COMPANIONS = (
    "test-engineer",
    "bug-investigator",
    "release-readiness",
    "security-review",
    "api-contract",
    "database-migration",
    "architecture-review",
    "agent-evals",
)
LINK = re.compile(r"(?<!!)\]\(([^ )]+)\)")
FRONTMATTER = re.compile(r"\A---\r?\n(.*?)\r?\n---\r?\n", re.DOTALL)


def validate(root, standard=False):
    paths = [root / name / "SKILL.md" for name in (HUB, *COMPANIONS)]
    hub = root / HUB
    projections = {}
    for path in paths:
        body = path.read_text(encoding="utf-8")
        match = FRONTMATTER.match(body)
        if not match:
            raise ValueError(f"{path}: missing or malformed frontmatter")
        meta = {}
        for line in match[1].splitlines():
            key, sep, value = line.partition(": ")
            if not sep or key in meta:
                raise ValueError(f"{path}: ambiguous metadata")
            meta[key] = value
        name = path.parent.name
        expected = (
            {"name", "description"}
            if name == HUB
            else {"name", "description", "disable-model-invocation"}
        )
        description = json.loads(meta.get("description", "null"))
        if (
            set(meta) != expected
            or meta["name"] != name
            or not isinstance(description, str)
            or not description.strip()
            or len(description) > 1024
        ):
            raise ValueError(f"{path}: name, description or frontmatter fields invalid")
        if name == HUB:
            if len(body.splitlines()) >= 200:
                raise ValueError(f"{path}: hub must stay under 200 lines")
        else:
            target = f"../{HUB}/references/workflows/{name}.md"
            if meta["disable-model-invocation"] != "true" or (
                f"${{CLAUDE_SKILL_DIR}}/{target}" not in body
                or not (path.parent / target).is_file()
            ):
                raise ValueError(
                    f"{path}: invalid manual mode or unresolved canonical workflow"
                )
        projections[name] = body.replace("\ndisable-model-invocation: true\n", "\n", 1)
    checked_links = 0
    for path in sorted(
        {
            *paths,
            hub / "README.md",
            *hub.glob("references/**/*.md"),
            *hub.glob("assets/*.md"),
            *hub.glob("evals/*.md"),
            *hub.glob("examples/*/README.md"),
        }
    ):
        for ref in LINK.findall(path.read_text(encoding="utf-8")):
            if ref.startswith(("https://", "http://", "mailto:", "#")):
                continue
            dest = (path.parent / ref.split("#", 1)[0]).resolve()
            if not dest.is_relative_to(root) or not dest.exists():
                raise ValueError(f"{path}: missing or out-of-suite reference {ref}")
            checked_links += 1
    scenarios = json.loads((hub / "evals/scenarios.json").read_text(encoding="utf-8"))
    if scenarios.get("schemaVersion") != 1 or set(scenarios["companions"]) != set(
        COMPANIONS
    ):
        raise ValueError("scenario inventory does not cover all companions")
    for name, cases in scenarios["companions"].items():
        if any(
            not cases.get(kind, "").startswith(f"/{name} ")
            for kind in ("positive", "boundary")
        ) or not cases.get("assertions"):
            raise ValueError(f"missing direct/boundary scenario or assertions: {name}")
    hub_cases = scenarios["hub"]
    names = set(COMPANIONS)
    if (
        len({case["id"] for case in hub_cases}) != len(hub_cases)
        or not any(not case["activate"] for case in hub_cases)
        or sum(
            bool(case["activate"] and case["required"] and case["excluded"])
            for case in hub_cases
        )
        < 2
    ):
        raise ValueError(
            "hub evals must include a negative and at least two selective routes"
        )
    for case in hub_cases:
        required, excluded = set(case["required"]), set(case["excluded"])
        if (
            not (required | excluded) <= names
            or required & excluded
            or (not case["activate"] and required)
        ):
            raise ValueError(f"impossible hub fixture: {case['id']}")

    if standard:
        executable = shutil.which("agentskills")
        if executable is None:
            raise ValueError("--standard requires `agentskills` on PATH")
        with TemporaryDirectory() as tmp:
            for name, body in projections.items():
                projection = Path(tmp) / name
                projection.mkdir()
                (projection / "SKILL.md").write_text(body, encoding="utf-8")
                subprocess.run([executable, "validate", str(projection)], check=True)
    return len(paths), checked_links, len(hub_cases) + 2 * len(COMPANIONS)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--standard",
        action="store_true",
        help="also validate portable frontmatter projections",
    )
    args = parser.parse_args()
    try:
        skills, links, cases = validate(
            Path(__file__).resolve().parents[2], args.standard
        )
    except (
        OSError,
        ValueError,
        KeyError,
        TypeError,
        subprocess.CalledProcessError,
    ) as exc:
        print(f"Invalid suite: {exc}")
        return 1
    print(
        f"Valid Claude Code suite: {skills} skill entries, {links} local links, {cases} scenario cases."
    )
    if args.standard:
        print(
            "Portable projections omit the Claude Code-only disable-model-invocation field."
        )
    print(
        "Static validation only; model activation and direct invocations not assessed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
