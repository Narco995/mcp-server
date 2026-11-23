# Database Migration

Use for schema changes, backfills or altered persistence invariants. Inputs: engine/version, topology, concurrency and size data, schema and migration tooling, backup/restore policy and rollout budgets. Verify database-specific claims; never assume one engine's locking or transaction semantics apply to another.

1. Record current and desired invariants, deployment order, lock and latency budgets, and which mixed application/schema versions must coexist. Choose a reversible expansion, backfill, validation, cutover and contraction when applicable.
2. Plan restartable idempotent batches with checkpoints and bounded contention. Specify validation for counts, uniqueness, integrity and ownership, along with abort, pause and resume conditions. Validate using synthetic or authorized isolated data.
3. Document backward compatibility, backups and restore verification. Split recoverable app/schema changes from irreversible data changes needing forward repair.
4. If explicitly asked to implement, write migration files and test locally. Never connect to or mutate a live database or execute suggested production commands.

**Output:** `phase | code/schema compatibility | expected lock budget | safety check | abort condition | rollback or recovery | owner`.

**Example:** Add a non-null field by introducing it nullable, backfilling in batches, validating coverage, then enforcing the invariant.

**MCP branch:** Check tenant membership and policy joins against both data shapes. Verify deterministic ordering and cursor behavior through a staged switch; expire or version old cursors explicitly if they cannot be honored safely.
