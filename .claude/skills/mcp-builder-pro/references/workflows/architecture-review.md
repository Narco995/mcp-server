# Architecture Review

Use for a material design decision. Inputs: user outcomes, constraints, scale assumptions, security boundaries, operational goals and reversibility requirements.

1. State the exact decision and what it is not deciding. Separate verified constraints from forecasts. Compare viable options including the status quo when feasible.
2. Compare failure isolation, resource/cost drivers, integration complexity, state ownership, privacy, observability and operational toil. Identify likely bottlenecks, not just theoretical capacity.
3. Give the most important uncertain assumptions a cheap measurement or prototype and a threshold that would change the recommendation. Prefer the simplest option meeting the requirements.
4. Record the recommendation, rejected alternatives, tradeoffs, owner, staged implementation, reversal path and conditions to revisit. Do not change code unless asked.

**Output:** `decision / context / options and tradeoffs / assumptions and tests / recommendation / risks / staged plan and reversal triggers`.

**Example:** Compare a Postgres-backed job table with a separate queue; justify the queue only if the latency, retention or throughput measurements require it.

**MCP branch:** Compare stdio versus remote HTTP, identity placement, tool catalog size, target version compatibility and application versus protocol state. Require a real client proof for any feature that materially affects the decision.
