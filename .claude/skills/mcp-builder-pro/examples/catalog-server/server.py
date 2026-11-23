"""A read-only, synthetic stdio MCP server. No upstream or credentials."""

from base64 import urlsafe_b64decode, urlsafe_b64encode
from binascii import Error as InvalidBase64
from hashlib import sha256
from typing import Annotated

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from pydantic import BaseModel, Field


class Item(BaseModel):
    id: str
    label: str
    category: str


class SearchPage(BaseModel):
    items: list[Item]
    next_cursor: str | None


ITEMS = (
    Item(id="pen-01", label="Blue pen", category="Stationery"),
    Item(id="pen-02", label="Green pen", category="Stationery"),
    Item(id="pen-03", label="Red pen", category="Stationery"),
    Item(id="pad-04", label="Pocket notebook", category="Stationery"),
)
BY_ID = {item.id: item for item in ITEMS}
server = FastMCP("synthetic-catalog")


def encode_cursor(index: int, query: str) -> str:
    marker = sha256(query.encode("utf-8")).hexdigest()[:16]
    return urlsafe_b64encode(f"{index}:{marker}".encode("ascii")).decode("ascii")


def decode_cursor(cursor: str | None, query: str, total: int) -> int:
    if cursor is None:
        return 0
    try:
        index = int(urlsafe_b64decode(cursor).decode("ascii").split(":")[0])
        if 0 < index < total and encode_cursor(index, query) == cursor:
            return index
    except (ValueError, OverflowError, InvalidBase64):
        pass
    raise ToolError("INVALID_CURSOR: restart search without a cursor")


@server.tool()
def search_catalog(
    query: Annotated[str, Field(min_length=1, max_length=100)],
    limit: Annotated[int, Field(ge=1, le=3)] = 2,
    cursor: Annotated[str, Field(max_length=120)] | None = None,
) -> SearchPage:
    """Find synthetic catalog items by free-text query; use exact lookup for known IDs."""
    normalized = query.strip().casefold()
    if not normalized:
        raise ToolError("INVALID_QUERY: enter free text")
    matching = sorted(
        (
            item
            for item in ITEMS
            if normalized in f"{item.label} {item.category}".casefold()
        ),
        key=lambda item: item.id,
    )
    start = decode_cursor(cursor, normalized, len(matching))
    end = start + limit
    return SearchPage(
        items=matching[start:end],
        next_cursor=encode_cursor(end, normalized) if end < len(matching) else None,
    )


@server.tool()
def get_catalog_item(
    item_id: Annotated[str, Field(min_length=1, max_length=32)],
) -> Item:
    """Look up one synthetic catalog item by exact ID; use search_catalog for free text."""
    if item_id not in BY_ID:
        raise ToolError("NOT_FOUND: no catalog item has that ID")
    return BY_ID[item_id]


if __name__ == "__main__":
    server.run(transport="stdio")
