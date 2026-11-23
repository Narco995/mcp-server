"""Verify the actual synthetic MCP process with the installed, pinned SDK."""

import asyncio
import json
import sys
from importlib.metadata import version
from pathlib import Path
from tempfile import TemporaryFile

from jsonschema import validate
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def smoke():
    assert version("mcp") == "1.30.0", "run with the fixture lockfile"
    server = Path(__file__).with_name("server.py").resolve()
    params = StdioServerParameters(command=sys.executable, args=[str(server)], env={})
    received_exceptions = []

    async def message_handler(message):
        if isinstance(message, Exception):
            received_exceptions.append(message)

    with TemporaryFile(mode="w+", encoding="utf-8") as stderr:
        async with (
            asyncio.timeout(30),
            stdio_client(params, errlog=stderr) as (incoming, outgoing),
            ClientSession(
                incoming, outgoing, message_handler=message_handler
            ) as session,
        ):
            started = await session.initialize()
            assert started.protocolVersion == "2025-11-25", started.protocolVersion
            listed = await session.list_tools()
            tools = {tool.name: tool for tool in listed.tools}
            assert set(tools) == {"search_catalog", "get_catalog_item"}, set(tools)

            async def call(name, arguments):
                result = await session.call_tool(name, arguments)
                assert not result.isError, result.content
                assert tools[name].outputSchema is not None
                validate(result.structuredContent, tools[name].outputSchema)
                return result.structuredContent

            first = await call("search_catalog", {"query": "Pen", "limit": 2})
            assert [item["id"] for item in first["items"]] == ["pen-01", "pen-02"]
            assert first == await call("search_catalog", {"query": "Pen", "limit": 2})
            cursor = first["next_cursor"]
            assert cursor
            second = await call(
                "search_catalog", {"query": "Pen", "limit": 2, "cursor": cursor}
            )
            assert [item["id"] for item in second["items"]] == ["pen-03"] and second[
                "next_cursor"
            ] is None
            exact = await call("get_catalog_item", {"item_id": "pen-01"})
            assert exact == first["items"][0]

            wrong_cursor = await session.call_tool(
                "search_catalog", {"query": "notebook", "cursor": cursor}
            )
            absent = await session.call_tool("get_catalog_item", {"item_id": "absent"})
            bad_limit = await session.call_tool(
                "search_catalog", {"query": "Pen", "limit": 999}
            )
            assert (
                wrong_cursor.isError
                and "INVALID_CURSOR" in wrong_cursor.content[0].text
            )
            assert absent.isError and "NOT_FOUND" in absent.content[0].text
            assert bad_limit.isError
        stderr.seek(0)
        diagnostics = stderr.read()
        assert not received_exceptions, received_exceptions
        assert "Traceback" not in diagnostics, diagnostics
    print(
        json.dumps(
            {
                "status": "passed",
                "sdk": version("mcp"),
                "client": "Python ClientSession",
                "revision": started.protocolVersion,
                "tools": sorted(tools),
                "checked": [
                    "stdio framing",
                    "discovery",
                    "structured schema",
                    "stable pagination",
                    "exact lookup",
                    "cursor binding",
                    "not found",
                    "bounds",
                ],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    asyncio.run(smoke())
