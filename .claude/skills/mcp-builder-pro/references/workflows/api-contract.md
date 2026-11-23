# API Contract

Use for a new API interface, public behavior change or consumer compatibility review. Inputs: consumer workflows, baseline and candidate contracts, pinned schema dialect, examples and any authorization requirements.

1. Map only the operations users need. Specify schema, defaults, ordering, pagination/cursor semantics, errors, side effects, and identity/authorization. Clearly mark what is contractual and what is implementation detail.
2. Capture current discovery or representative responses when available and reconcile drift between running behavior and documentation. Keep private policy facts separate from published fields.
3. Compare in both directions: a new server must accept prior valid requests and outputs must remain consumable by prior clients. Review dependencies among fields, descriptions, scopes, defaults and retries. Send uncertain schema relations to manual review.
4. Report each change and affected clients, then propose migration/deprecation for incompatible behavior. Do not silently bless new baselines or version guarantees.

**Output:** `operation | baseline | candidate | classification | consumer impact | migration | proof`.

**Example:** An optional address field becomes required on an existing endpoint. Keep the prior version available or give consumers a migration before enforcing it.

**MCP branch:** Use the suite contract comparator for stable names, schemas and private metadata. Separate wire changes from a new model tendency to choose a tool incorrectly; route those changes to Agent Evals.
