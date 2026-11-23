# Synthetic catalog MCP fixture

Two read-only stdio tools, with in-memory sample data only. No Task Management API, credentials or live mutations. The cursor is opaque, position- and query-bound for this fixed dataset; it is not an authorization token. A real service must bind cursor semantics to verified identity/tenant and data lifetime as applicable.

From this directory, use the checked-in `uv.lock` with Python 3.12 (or another supported Python 3.11–3.14 runtime):

```sh
uv run --locked --python 3.12 smoke.py
uv run --locked --python 3.12 python -m unittest -v test_write_policy.py
```

The first command spawns a real server process, initializes an SDK client, lists its tools and exercises search, exact lookup, pagination, invalid arguments and tool errors. The second command verifies defensive write-policy behavior in an in-memory fake; no write is registered as an MCP tool. These tests are not Claude Code, remote HTTP, live upstream, or staging certification.

For a local MCP client, run the equivalent of `uv --directory /absolute/path/to/catalog-server run --locked --python 3.12 server.py` as its stdio subprocess. Never log arbitrary diagnostic output to stdout. After dependencies are installed, `uv run --offline --locked` can run these fixtures with no network.
