# Test Engineer

Use when expected behavior needs proof, a bug fix needs regression evidence, or a suite has a coverage gap. Inputs: acceptance criteria, changed surfaces, supported environments, and permitted test targets. Do not infer authority to test live writes.

1. Map criteria and invariants to named checks. Choose the cheapest layer that detects the failure: unit, policy, integration, contract, runtime, or client. Include controls for positive, boundary, negative and concurrency cases where relevant.
2. For a bug fix, verify the regression fails for the expected reason on a clean baseline before running it on the fix. Use a disposable worktree if necessary; do not reset the user's changes. If the old state or dependencies cannot run, mark baseline unavailable.
3. Use owned fixtures, fake clocks, and reproducible seeds. Record raw first results and any reruns separately. A flaky pass does not erase the first failure. Test public behavior rather than internal call order unless that order is the invariant.
4. Run exact targeted and adjacent checks, then report with candidate and runtime. Stop on missing permissions, destructive test configuration, or unknown endpoints; replace with local fixtures or report the gap.

**Output:** `criterion | check ID | layer | baseline | candidate | command/evidence | remaining gap`.

**Example:** A password reset link is single use. Use a fake clock and synthetic users to prove two concurrent redemptions cannot both succeed.

**MCP branch:** Test the actual process through discovery and call, validate the declared output and error layer, and check selected-client evidence separately from shared-SDK testing. Use fixture tenants to prove denial, not only a successful read.
