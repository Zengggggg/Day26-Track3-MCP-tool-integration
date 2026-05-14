from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

ROOT_DIR = Path(__file__).resolve().parents[1]
try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None

if load_dotenv is not None:
    load_dotenv(ROOT_DIR / ".env")

try:
    from .db import ValidationError, create_adapter
    from .init_db import create_database
except ImportError:
    from db import ValidationError, create_adapter
    from init_db import create_database


DB_PATH = Path(__file__).with_name("lab.db")
if not os.getenv("DATABASE_URL") and not DB_PATH.exists():
    create_database(DB_PATH)


def build_auth_provider():
    token = os.getenv("MCP_AUTH_TOKEN")
    if not token:
        return None

    try:
        from fastmcp.server.auth.providers.jwt import StaticTokenVerifier
    except ImportError as error:
        raise RuntimeError("FastMCP auth provider is unavailable") from error

    return StaticTokenVerifier(
        tokens={
            token: {
                "client_id": "sqlite-lab-demo",
                "scopes": ["mcp:read", "mcp:write"],
            }
        }
    )


def create_mcp_server() -> FastMCP:
    auth = build_auth_provider()
    kwargs = {"auth": auth} if auth is not None else {}
    return FastMCP("SQLite Lab MCP Server", **kwargs)


adapter = create_adapter(DB_PATH)
mcp = create_mcp_server()


def _validation_error(error: ValidationError) -> Dict[str, Any]:
    return {"ok": False, "error": str(error), "error_type": "validation_error"}


@mcp.tool(name="search")
def search(
    table: str,
    filters: Optional[List[Dict[str, Any]]] = None,
    columns: Optional[List[str]] = None,
    limit: int = 20,
    offset: int = 0,
    order_by: Optional[str] = None,
    descending: bool = False,
) -> Dict[str, Any]:
    """Search rows with validated filters, ordering, and pagination."""
    try:
        result = adapter.search(
            table=table,
            filters=filters,
            columns=columns,
            limit=limit,
            offset=offset,
            order_by=order_by,
            descending=descending,
        )
        return {"ok": True, **result}
    except ValidationError as error:
        return _validation_error(error)


@mcp.tool(name="insert")
def insert(table: str, values: Dict[str, Any]) -> Dict[str, Any]:
    """Insert one row after validating the table and column names."""
    try:
        result = adapter.insert(table=table, values=values)
        return {"ok": True, **result}
    except ValidationError as error:
        return _validation_error(error)


@mcp.tool(name="aggregate")
def aggregate(
    table: str,
    metric: str,
    column: Optional[str] = None,
    filters: Optional[List[Dict[str, Any]]] = None,
    group_by: Optional[str] = None,
) -> Dict[str, Any]:
    """Run count, avg, sum, min, or max with optional filters and grouping."""
    try:
        result = adapter.aggregate(
            table=table,
            metric=metric,
            column=column,
            filters=filters,
            group_by=group_by,
        )
        return {"ok": True, **result}
    except ValidationError as error:
        return _validation_error(error)


@mcp.resource("schema://database", mime_type="application/json")
def database_schema() -> Dict[str, Any]:
    """Read the full database schema."""
    return adapter.get_database_schema()


@mcp.resource("schema://table/{table_name}", mime_type="application/json")
def table_schema(table_name: str) -> Dict[str, Any]:
    """Read the schema for one table."""
    try:
        return {"table": table_name, "columns": adapter.get_table_schema(table_name)}
    except ValidationError as error:
        return _validation_error(error)


if __name__ == "__main__":
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport not in {"stdio", "http", "sse", "streamable-http"}:
        raise SystemExit(
            "MCP_TRANSPORT must be one of: stdio, http, sse, streamable-http"
        )

    if transport == "stdio":
        mcp.run()
    else:
        mcp.run(
            transport=transport,
            host=os.getenv("MCP_HOST", "127.0.0.1"),
            port=int(os.getenv("MCP_PORT", "3001")),
        )
