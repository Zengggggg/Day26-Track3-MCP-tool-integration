import pytest

fastmcp = pytest.importorskip("fastmcp")

from fastmcp import Client

from implementation.init_db import create_database
from implementation.mcp_server import DB_PATH, build_auth_provider, mcp


@pytest.fixture(autouse=True)
def reset_database():
    create_database(DB_PATH)


@pytest.mark.asyncio
async def test_fastmcp_tool_and_resource_discovery():
    async with Client(mcp) as client:
        tools = await client.list_tools()
        resources = await client.list_resources()
        templates = await client.list_resource_templates()

    assert {tool.name for tool in tools} == {"search", "insert", "aggregate"}
    assert "schema://database" in {str(resource.uri) for resource in resources}
    assert "schema://table/{table_name}" in {
        str(template.uriTemplate) for template in templates
    }


@pytest.mark.asyncio
async def test_fastmcp_valid_and_invalid_tool_calls():
    async with Client(mcp) as client:
        valid = await client.call_tool(
            "aggregate",
            {"table": "students", "metric": "count", "group_by": "cohort"},
        )
        invalid = await client.call_tool("search", {"table": "missing_table"})

    assert valid.data["ok"] is True
    assert len(valid.data["rows"]) == 2
    assert valid.data["annotations"]["grouped"] is True
    assert invalid.data["ok"] is False
    assert "unknown table" in invalid.data["error"]


def test_auth_provider_is_disabled_without_token(monkeypatch):
    monkeypatch.delenv("MCP_AUTH_TOKEN", raising=False)

    assert build_auth_provider() is None


def test_auth_provider_is_enabled_with_token(monkeypatch):
    monkeypatch.setenv("MCP_AUTH_TOKEN", "sqlite-lab-secret")

    auth = build_auth_provider()

    assert auth is not None
