# Security Review

Use for a defensive review of changes in the user's code. Inputs: repository and diff scope, assets, actor/tenant model, permission policy, allowed local checks and intended deployment.

1. Draw trust boundaries and trace each relevant action from transport authentication to object authorization and the upstream credential. Establish which state is tenant-scoped. Treat tool arguments and returned content as untrusted.
2. Inspect the affected implementation and defensive tests for missing authorization, data leaks, secrets in storage/logs/output, excessive privilege, retention and unsafe failure behavior. Use only approved read-only checks and authorized owned fixtures. Do not use live customer accounts or external probes.
3. Separate confirmed defects from open questions. Give a precise code location, broken invariant, affected roles or assets, impact, confidence, and a scoped remediation and regression assertion. Redact secret values from every artifact.
4. If asked to remediate, patch the narrow control and verify denial and legitimate behavior locally. If an access boundary cannot be verified, state exactly what was out of scope or missing.

**Output:** `severity | confidence | code location | invariant | affected scope | remediation | evidence`, plus unreviewed areas.

**Example:** Verify filtering an invoice by ID still enforces tenant ownership after a repository refactor, using two fixture tenants.

**MCP branch:** Check protected resource/token scope, separation of upstream credentials, cache/cursor/job scoping, approval binding and replay handling. Review tool descriptions and upstream data handling without treating either as policy enforcement.
