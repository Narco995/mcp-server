# Agent Evals

Use for agent/tool behavior changes or skill quality evaluation. Inputs: pinned model/settings if available, baseline and candidate instructions or catalogs, held-out fixtures, assertions, run budget and permission to invoke online models if needed.

1. Define a representative task distribution, held-out cases and strict invariants. Compare baseline and candidate with identical configuration, inputs and tool states. Use synthetic data and preserve fixture versions and model/settings.
2. Grade activation, correct tool/arguments, completion, unnecessary calls, respect for authority and honest status reports. Use deterministic checks first. Separate subjective judgments, judge rationale and confidence.
3. Run a bounded repeated comparison only with opt-in for external/model calls. Track trial counts and variability; label small or noisy effects inconclusive. If unavailable, deliver fixtures and mark model runs not-run.
4. Treat unauthorized actions, cross-tenant access, credential disclosure and fabricated verification as hard failures. Never average them away. Return representative redacted traces and concrete next changes.

**Output:** `scenario | baseline / candidate count | deterministic pass | judgment | hard failure | trace | next action` and a release recommendation separate from statistical claims.

**Example:** Compare two support-agent prompts on held-out policy questions with known answers and unclear cases where the right behavior is to escalate.

**MCP branch:** Include look-alike tools, read versus write selection, missing client capability, stale approval, ambiguous write result, upstream untrusted text, and unrelated work that must not trigger MCP Builder.
