# Release Readiness

Use for a go/no-go on an exact candidate, never to execute a release. Inputs: candidate digest, environments, relevant policy and approvals, CI/runtime evidence, rollout runbook and migration or recovery plan.

1. Identify the candidate, required gates per environment, change order, data/schema impact, and owners. Verify the evidence was collected against that candidate and the intended environment.
2. Check build, CI and actual runtime smoke evidence, configuration, dependencies, provisioning and required approvals. Grade missing or stale evidence separately from a known failure.
3. Confirm staged rollout, measurable abort criteria, ownership, rollback/forward recovery, and after-release checks. Distinguish code rollback from data reversal. Do not create tags, publish, deploy, roll back or apply migrations.
4. Return `ready` only when all mandatory gates pass; `blocked` for a confirmed required failure; `not verified` for remaining required evidence gaps without known failure. Preserve the scope and next owner even on success.

**Output:** `candidate | target | verdict | required gate → evidence ID and outcome | abort metrics | recovery owner | next decision`.

**Example:** A candidate runs on staging, but its data migration is irreversible and a restore has not been rehearsed. Mark the related gate not verified, not ready.

**MCP branch:** Combine the contract diff, exact client matrix, authorization/isolation results and approved staging write evidence as applicable. Run the suite's evidence gate for the exact target and profile. Never substitute a fixture pass for a staging or selected-client gate.
