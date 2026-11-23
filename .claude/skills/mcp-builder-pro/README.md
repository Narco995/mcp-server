# MCP Builder Pro skill suite

Keep the hub and all eight sibling directories together under the repository's `.claude/skills/`. The hub is the MCP-specific entry point; companions are explicitly invoked and share the hub's canonical workflow references without copying them. See [Claude Code project skills](https://code.claude.com/docs/en/skills).

| Example | Entry point |
|---|---|
| `/mcp-builder-pro Build a read-only MCP adapter, then prove discovery and one tool call.` | [MCP Builder Pro](SKILL.md) |
| `/test-engineer Prove this fix with a reproducible regression test.` | [Test Engineer](../test-engineer/SKILL.md) |
| `/bug-investigator Why does the local subprocess fail at startup?` | [Bug Investigator](../bug-investigator/SKILL.md) |
| `/release-readiness Assess this candidate without releasing it.` | [Release Readiness](../release-readiness/SKILL.md) |
| `/security-review Review the authorization and tenant checks in this diff.` | [Security Review](../security-review/SKILL.md) |
| `/api-contract Can existing clients still use this changed filter?` | [API Contract](../api-contract/SKILL.md) |
| `/database-migration Plan a resumable backfill without running it live.` | [Database Migration](../database-migration/SKILL.md) |
| `/architecture-review Compare stdio and remote HTTP against these constraints.` | [Architecture Review](../architecture-review/SKILL.md) |
| `/agent-evals Design offline tests for selection between these two tools.` | [Agent Evals](../agent-evals/SKILL.md) |

## Verify locally

From the repository root:

```sh
suite=.claude/skills/mcp-builder-pro
python3 "$suite/scripts/validate_suite.py"
python3 "$suite/scripts/test_quality.py" -v
uv --directory "$suite/examples/catalog-server" run --locked --python 3.12 smoke.py
uv --directory "$suite/examples/catalog-server" run --locked --python 3.12 python -m unittest -v test_write_policy.py
```

After installing the locked dependencies, `uv run --offline --locked` can run the catalog tests without network access. To additionally check portable frontmatter with `agentskills`, pass `--standard` to the suite validator. It removes only the Claude-specific invocation flag in temporary projections and verifies that flag on the actual wrappers separately.

These checks cover the suite, a synthetic local MCP process, and a fake write policy. They do not call the repository's live Task Management API, validate the target in Claude Code, certify remote HTTP, or deploy it. Use the [scenario guide](evals/README.md) for opt-in model evaluation.
