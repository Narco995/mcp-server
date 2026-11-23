# Revision, SDK, client, and transport

Build a matrix per exact client and version, revision, SDK/runtime, transport, auth and enabled extension set. Record a versioned documentation URL, observed handshake/discovery, or explicit gap for every material claim: `documented`, `tested`, `unknown`, or `unsupported`. A fixture is not a production client. Never infer that an SDK supports a revision just because its release is recent.

| Use | Default | Verify |
|---|---|---|
| Local subprocess | stdio, protocol on stdout, diagnostics on stderr | Executable path, working directory, environment, discovery and call |
| New remote deployment | Streamable HTTP | Host URL, TLS, origin checks, selected revision's HTTP headers and response handling, protected resource authorization |
| Existing legacy target | Keep a compatibility endpoint only if an identified client needs it | Isolate from the modern path; test both independently and document a sunset |

## Revision checks

- **2025-11-25:** Test `initialize`, selected revision and capability negotiation, then `notifications/initialized`. For HTTP use the selected revision's subsequent request headers and verify session behavior only if your SDK uses it ([lifecycle](https://modelcontextprotocol.io/specification/2025-11-25/basic/lifecycle)).
- **2026-07-28:** Verify revision metadata, stateless request handling, and discovery if the client uses it. For HTTP confirm the chosen endpoint's method and names match request headers and that it implements the revision's response and streaming rules. Do not transport assumptions about `initialize`, session IDs or legacy SSE endpoints into the newer branch ([specification](https://modelcontextprotocol.io/specification/2026-07-28), [Streamable HTTP](https://modelcontextprotocol.io/specification/2026-07-28/basic/transports/streamable-http)).
- **Extensions:** Enable only when both ends document support and the workflow needs it. Make unsupported optional functionality explicit. Do not make destructive actions appear supported by falling back to a generic tool.

## Pinned stdio recipes

**Python:** The bundled fixture pins `mcp==1.30.0`. See its [server and smoke-test instructions](../examples/catalog-server/README.md). It uses `mcp.server.fastmcp.FastMCP`, `mcp.ClientSession`, and `mcp.client.stdio.stdio_client`. For a different Python SDK major use its own SDK documentation and rerun the wire check.

**TypeScript, SDK v1:** With `@modelcontextprotocol/sdk@1.26.0` and `zod@3.25.76`, set the project to ESM, lock dependencies, and start with this deliberately small tool. This is not a recipe for the split-package v2 SDK. See [the SDK's tagged source](https://github.com/modelcontextprotocol/typescript-sdk/tree/v1.26.0) and [the package release](https://www.npmjs.com/package/@modelcontextprotocol/sdk/v/1.26.0).

```typescript
import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { z } from "zod";

const server = new McpServer({ name: "catalog", version: "0.1.0" });
server.registerTool(
  "get_catalog_item",
  { description: "Look up an item by exact ID", inputSchema: { id: z.string() } },
  async ({ id }) => ({ content: [{ type: "text", text: `Fixture item ${id}` }] }),
);
await server.connect(new StdioServerTransport());
```

For Claude configuration verify the actual client variant and version. Use a pinned local command for stdio; use the verified MCP endpoint for HTTP. Do not include credentials in committed client configuration ([Claude Code MCP docs](https://code.claude.com/docs/en/mcp.md)). Before replacing a production target, run baseline and candidate probes and preserve a way for clients to select the last compatible release.
