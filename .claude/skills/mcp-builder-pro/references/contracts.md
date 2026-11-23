# Design and compare MCP contracts

Start with representative tasks and their success conditions. Use tools for operations, resources for addressable context and prompts for user-facing templates, only when the target client supports the primitive. Favor a narrow tool surface with bounded output, stable IDs, opaque scoped cursors and a distinction between discovery, lookup and writes. A tool description should tell a model what to use it for, when to choose a neighbor, and how to interpret the result.

For each tool record:

| Discovery or consumer-visible | Private behavior to verify |
|---|---|
| Stable name and description; input/output schemas; error categories; defaults; pagination and ordering | Authorized principal and tenant; scopes and object membership; upstream credentials; side effects; approval, replay and reconciliation |

Collect discovery from a running server and map it into the canonical template; add private-policy facts separately from policy tests. Record the error layer: HTTP/authentication versus protocol error versus tool-level failure. Follow the pinned revision's error and structured-result rules. A compatibility text fallback, if needed, must preserve semantics without duplicating sensitive fields.

Compare reviewed baseline and candidate:

```sh
python3 .claude/skills/mcp-builder-pro/scripts/contract_diff.py baseline.json candidate.json
python3 .claude/skills/mcp-builder-pro/scripts/contract_diff.py baseline.json candidate.json --format json
```

Exit codes: `0` unchanged or supported additive changes, `1` at least one breaking change, `2` manual review required with no known break detected, `3` invalid input. Candidate inputs must accept previously valid requests; candidate outputs must remain consumable by older clients. The comparator supports simple recursive objects, arrays, primitive types, required sets, enums and selected bounds. Unsupported compositions and semantic changes fail to manual review. It is not a general JSON Schema inclusion prover. Never accept a model-facing description change, scope or policy change, or unclear output behavior on wire-schema comparison alone.

Example: an optional `region` filter can be additive when omitted behavior is unchanged and the previous schema explicitly rejected unknown fields. Making that filter mandatory is breaking. Widening tenant scope or steering the model toward the wrong tool is a regression even with identical schemas.
