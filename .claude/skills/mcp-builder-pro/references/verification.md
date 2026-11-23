# Verification, evidence, and release

Use deterministic unit/policy tests, actual MCP process probes, owned upstream fixtures and opt-in model behavior evaluations as separate evidence levels. Start with the smallest check that can falsify the claim. Test protocol startup/discovery/call, valid outputs, errors and permission cases, not just successful process exit. The catalog client is a real MCP SDK client, not Claude or a staging provider.

For a failing MCP probe, separate executable launch, stdout framing, transport URL and TLS, revision/lifecycle, authentication, discovery/schema, handler policy and upstream behavior. Record safe commands, exact environment and pinned versions; redact headers and payloads. Capture only synthetic or authorized sanitized traces. Normalize times and request IDs. For retry/cancellation/fault fixtures, use a fake clock where practical and preserve the failing seed.

Use the evidence ledger with this CLI:

```sh
python3 .claude/skills/mcp-builder-pro/scripts/evidence_gate.py evidence.json \
  --candidate "$CANDIDATE" --target "$TARGET_ID" \
  --target-fingerprint "$APPROVED_TARGET_SHA256" --profile remote-write
```

The verifier binds evidence to one candidate and a fingerprint of the exact target tuple. Artifacts must be relative to the ledger directory, readable, and match their reported SHA-256. The default freshness window is 72 hours, configurable with `--max-age-hours`. Exit `0` is `ready`, `1` is `blocked` (a required check failed), `2` is `not verified` (missing, invalid, stale or insufficient evidence), and `3` is malformed invocation or ledger. A passing result verifies these evidence rules, not the accuracy of claims inside a forged artifact. Require maintained access control and review around production CI evidence.

Each check has `id`, `outcome`, `kind`, `candidate`, `targetFingerprint`, `command`, `recordedAt` (UTC ISO 8601), `artifact` (relative path), and `sha256`. Use the gate's `REQUIRED` map for check IDs and evidence kinds, and `target_fingerprint(target)` to compute the fingerprint of the exact approved tuple, independently of the submitted ledger. Pin the full Git commit or SHA-256 digest, sort extensions, and never include credentials in `command` or its output.

For remote releases additionally record owner, measured error/latency budgets, rollout stages, abort thresholds, reversible versus irreversible state changes, and post-rollout validation. Run a selected-client check in the actual client. Real staging and release are separate actions requiring their own authority.
