# Trust, authority, and writes

## Establish the boundary

Draw principal → client → MCP transport → action/object policy → upstream. For each crossing record what is authenticated, who selects the target, which identity reaches the next system and where sensitive data may persist. Treat tool arguments, configuration obtained from untrusted sources, and upstream text as data, not authorization. Avoid generic shell, HTTP, SQL or filesystem escape hatches. Constrain destinations, operations, payload size, concurrency and deadlines.

For protected remote HTTP, verify revision-specific OAuth discovery, resource/audience binding and scope behavior ([MCP authorization](https://modelcontextprotocol.io/specification/2026-07-28/basic/authorization)). Reject credentials not issued for this resource; never pass inbound MCP tokens upstream. Acquire upstream credentials under a separate policy. Derive user and tenant identity from verified credentials, perform object-level authorization on every operation and partition caches, cursors, handles and jobs by tenant and authority. Use redacted correlation IDs; keep credentials and private payloads out of URLs, output, logs and fixtures.

## Consequential writes

1. Preview a canonical proposed mutation. Display its exact target, fields and expected effect.
2. Get genuine user authorization where required. Bind a short-lived approval to the verified principal, tenant, operation, candidate state/precondition and canonical payload digest. A model-supplied boolean is not approval.
3. Recheck policy and state at commit. Atomically reserve the actor/tenant/action-scoped idempotency key or use an upstream primitive with equivalent guarantees. Reject the same key with a different payload. Scope recovery/status lookup to the same principal.
4. Record an explicit `committed`, `not_committed`, or `unknown` outcome. Reconcile unknown outcomes before retrying. If no authoritative reconciliation exists, stop and report the risk instead of claiming exactly-once semantics.

Test wrong actor, tenant and payload, expired approval, authorization revocation, concurrent duplicates and ambiguous timeouts in controlled fixtures. Require authorized staging evidence separately if releasing a write-capable target. Never perform live writes or use production credentials as a verification shortcut.
