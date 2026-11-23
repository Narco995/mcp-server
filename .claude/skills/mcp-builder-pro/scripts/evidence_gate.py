#!/usr/bin/env python3
"""Check current, target-bound MCP evidence and issue a non-deploying verdict."""

import argparse
import hashlib
import json
import math
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

LOCAL = {
    "skill-package": "fixture",
    "contract": "fixture",
    "server-smoke": "local-runtime",
    "stdio-framing": "local-runtime",
    "read-and-input-policy": "local-runtime",
}
REMOTE = {
    "skill-package": "fixture",
    "contract": "fixture",
    "compatibility": "documentation",
    "http-policy": "staging",
    "auth-and-isolation": "staging",
    "selected-client": "real-client",
    "rollout-recovery-plan": "documentation",
}
REQUIRED = {
    "local-readonly": LOCAL,
    "remote-readonly": REMOTE,
    "remote-write": {
        **REMOTE,
        "write-authorization-and-approval": "staging",
        "concurrent-idempotency": "fixture",
        "unknown-outcome-reconciliation": "fixture",
        "staging-write-flow": "staging",
    },
}
TARGET_TEXT = {
    "id",
    "client",
    "clientVersion",
    "revision",
    "sdk",
    "sdkVersion",
    "runtime",
    "transport",
    "auth",
}
DIGEST = re.compile(r"^[0-9a-f]{64}$")
CANDIDATE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")


def target_fingerprint(target):
    value = json.dumps(
        target, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def validate(ledger):
    if (
        not isinstance(ledger, dict)
        or type(ledger.get("schemaVersion")) is not int
        or ledger["schemaVersion"] != 1
    ):
        raise ValueError("expected evidence ledger schemaVersion 1")
    target = ledger.get("target")
    if (
        not isinstance(target, dict)
        or set(target) != TARGET_TEXT | {"extensions"}
        or any(
            not isinstance(target[key], str) or not target[key].strip()
            for key in TARGET_TEXT
        )
    ):
        raise ValueError("target tuple is incomplete or invalid")
    extensions = target["extensions"]
    if (
        not isinstance(extensions, list)
        or any(not isinstance(x, str) or not x for x in extensions)
        or extensions != sorted(set(extensions))
    ):
        raise ValueError("target.extensions must be sorted, unique strings")
    candidate = ledger.get("candidate")
    profile = ledger.get("profile")
    if not isinstance(candidate, str) or not CANDIDATE.fullmatch(candidate):
        raise ValueError("candidate must be a commit or digest in hexadecimal")
    if not isinstance(profile, str) or profile not in REQUIRED:
        raise ValueError("unknown profile")
    checks = ledger.get("checks")
    if not isinstance(checks, list):
        raise TypeError("checks must be an array")
    seen = set()
    for check in checks:
        check_id = check.get("id") if isinstance(check, dict) else None
        if not isinstance(check_id, str) or not check_id or check_id in seen:
            raise ValueError("each check must have a unique, nonempty id")
        if check.get("outcome") not in ("passed", "failed", "skipped", "not-run"):
            raise ValueError(f"{check_id}: invalid outcome")
        seen.add(check_id)


def verify_artifact(check, root):
    artifact = check.get("artifact")
    digest = check.get("sha256")
    if (
        not isinstance(artifact, str)
        or not artifact
        or not isinstance(digest, str)
        or not DIGEST.fullmatch(digest)
    ):
        return False
    relative = Path(artifact)
    if relative.is_absolute() or ".." in relative.parts:
        return False
    try:
        path = (root / relative).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            return False
        with path.open("rb") as stream:
            return hashlib.file_digest(stream, "sha256").hexdigest() == digest
    except (OSError, RuntimeError, ValueError):
        return False


def assess(
    ledger, root, candidate, target_id, target_digest, profile, now, max_age_hours
):
    validate(ledger)
    fingerprint = target_fingerprint(ledger["target"])
    if (
        ledger["candidate"],
        ledger["target"]["id"],
        fingerprint,
        ledger["profile"],
    ) != (
        candidate,
        target_id,
        target_digest,
        profile,
    ):
        return {
            "verdict": "not verified",
            "reason": "ledger does not match requested candidate, target and profile",
            "checks": [],
        }, 2
    root = root.resolve()
    by_id = {check["id"]: check for check in ledger["checks"]}
    results = []
    for check_id, kind in sorted(REQUIRED[profile].items()):
        check = by_id.get(check_id)
        state = "not verified"
        if check is None:
            reason = "missing required check"
        elif (
            check.get("candidate") != candidate
            or check.get("targetFingerprint") != fingerprint
        ):
            reason = "candidate or target fingerprint mismatch"
        elif check.get("kind") != kind:
            reason = f"requires {kind} evidence"
        elif check["outcome"] in ("skipped", "not-run"):
            reason = check["outcome"]
        elif not isinstance(check.get("command"), str) or not check["command"].strip():
            reason = "missing command or procedure"
        else:
            try:
                timestamp = datetime.fromisoformat(check.get("recordedAt", ""))
                fresh = (
                    timestamp.tzinfo is not None
                    and now - timedelta(hours=max_age_hours) <= timestamp <= now
                )
            except (ValueError, TypeError):
                fresh = False
            if not fresh:
                reason = "stale, future or invalid timestamp"
            elif not verify_artifact(check, root):
                reason = "missing or unverifiable artifact"
            else:
                state = check["outcome"]
                reason = "current evidence matches target and candidate"
        results.append({"id": check_id, "state": state, "reason": reason})
    states = {item["state"] for item in results}
    verdict, code = (
        ("blocked", 1)
        if "failed" in states
        else (("not verified", 2) if "not verified" in states else ("ready", 0))
    )
    return {
        "verdict": verdict,
        "target": target_id,
        "candidate": candidate,
        "profile": profile,
        "targetFingerprint": fingerprint,
        "checks": results,
    }, code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ledger", type=Path)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--target", required=True)
    parser.add_argument(
        "--target-fingerprint",
        required=True,
        help="SHA-256 of the approved exact target tuple",
    )
    parser.add_argument("--profile", choices=REQUIRED, required=True)
    parser.add_argument("--max-age-hours", type=float, default=72)
    args = parser.parse_args()
    try:
        if (
            not CANDIDATE.fullmatch(args.candidate)
            or not args.target.strip()
            or not DIGEST.fullmatch(args.target_fingerprint)
            or not (
                math.isfinite(args.max_age_hours) and 0 < args.max_age_hours <= 87600
            )
        ):
            raise ValueError("invalid candidate, target or max-age-hours")
        result, code = assess(
            json.loads(args.ledger.read_text()),
            args.ledger.parent,
            args.candidate,
            args.target,
            args.target_fingerprint,
            args.profile,
            datetime.now(UTC),
            args.max_age_hours,
        )
    except (ValueError, TypeError, OSError) as exc:
        result, code = {"verdict": "invalid", "error": str(exc)}, 3
    print(json.dumps(result, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
