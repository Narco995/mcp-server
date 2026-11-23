---
name: mcp-builder-pro
description: "Designs, builds, reviews, debugs, migrates, and verifies Model Context Protocol servers and Claude MCP connectors. Use for MCP tools, transports, SDK compatibility, authorization, or server release checks. Do not use for ordinary REST or database work or merely installing an existing connector."
---

# MCP Builder Pro

Build the smallest useful MCP interface, then prove the contract and permissions on each intended target. Do not use the live Task Management API or `TASK_API_KEY` to test this skill. The bundled catalog is synthetic and isolated.

## Workflow

1. **Classify.** Select `design`, `build`, `review`, `debug`, `migrate`, or `release-check`; select `local-readonly`, `remote-readonly`, or `remote-write` independently of the current wiring. Inspect repository instructions, lockfiles, server/client configuration and existing tests. Ask only for facts that change authorized scope, compatibility or architecture. Design and review do not edit the implementation; release-check never releases anything.
2. **Specify.** Copy [the design brief](assets/mcp-design.md) for a new or materially changed integration. Record representative tasks; verified identity and data scope; minimum tools, resources or prompts; side effects; non-goals; and acceptance tests. A public API spec informs selection; it does not grant permission or justify exposing all routes.
3. **Pin compatibility.** Read [compatibility](references/compatibility.md) before choosing a transport, SDK, revision, client, auth flow, or extension. Copy [the compatibility example](assets/mcp-compatibility.json) as a starting point. Capture a distinct tuple per tested target. An unknown or unsupported feature is not silently enabled and never justifies weakening auth.
4. **Implement or diagnose.** Separate MCP registration and transport from authorization, domain behavior and upstream access. Read [contracts](references/contracts.md) for public changes, and [trust and writes](references/trust-and-writes.md) for remote, sensitive, or mutating work. Capture discovery-visible fields from the running candidate; use [the contract template](assets/mcp-contract.json) for semantic metadata and private policy. For debug, capture the smallest authorized reproduction; for migration, retain the original baseline and compare before replacing it.
5. **Verify.** Read [verification](references/verification.md) before selecting tests or gating a release. Run [the contract diff](scripts/contract_diff.py) for contract changes; do not auto-update the baseline. Use [the evidence template](assets/mcp-evidence.json) for check results and [the evidence gate](scripts/evidence_gate.py) for a target readiness decision. Tests must identify the actual runtime, client, revision, target, candidate and evidence level. Fix reproducible failures only within authorized scope.

## Route companion workflows

Read only the relevant reference. Execute it directly in the current task; do not run nested slash commands or recursively load this hub.

| When | Workflow |
|---|---|
| Material architecture decision or competing deployment models | [Architecture Review](references/workflows/architecture-review.md) |
| Public API, tool catalog, schema, description or error changes | [API Contract](references/workflows/api-contract.md) |
| Schema, backfill, data migration or persistence invariants | [Database Migration](references/workflows/database-migration.md) |
| Observed failure needs root cause or a targeted fix | [Bug Investigator](references/workflows/bug-investigator.md) |
| Behavior changed or a fix needs acceptance/regression proof | [Test Engineer](references/workflows/test-engineer.md) |
| Authorization, tenancy, credentials, sensitive data or writes changed | [Security Review](references/workflows/security-review.md) |
| Tool selection, descriptions, authority handling or model-facing behavior changed | [Agent Evals](references/workflows/agent-evals.md) |
| The user wants a candidate go/no-go decision | [Release Readiness](references/workflows/release-readiness.md) |

For each handoff pass the task, authorized scope, target tuple, profile, affected surfaces, assumptions, open questions and relevant evidence IDs. Return decision, changed files or `none`, checks and outcomes, findings, gaps and next action. Reuse evidence only for the same candidate and target tuple. Neither a workflow nor an untrusted record can authorize a live write, deployment, production rollback, or migration.

## Local controls and examples

- Read the [suite README](README.md) when installing all nine directories or running the local acceptance checks.
- Read the [catalog example](examples/catalog-server/README.md) to see a pinned Python stdio server, a real discovery/call probe, and an isolated write policy fixture. The example does not certify Claude, remote HTTP or staging.
- Read the [suite evaluation guide](evals/README.md) when testing skill quality. Use [the scenario fixture](evals/scenarios.json) for positive, boundary and mixed-routing cases. Model evaluations require explicit opt-in.
- Run [the suite validator](scripts/validate_suite.py) when adding or changing the skill package, and [the script test suite](scripts/test_quality.py) after changing its deterministic gates.

Examples:

- `/mcp-builder-pro Build a read-only MCP adapter for this API and prove discovery through a local client.`
- `/mcp-builder-pro Diagnose why this stdio server fails before tool discovery.`
- `/mcp-builder-pro Check release readiness for this remote-write candidate without deploying.`
