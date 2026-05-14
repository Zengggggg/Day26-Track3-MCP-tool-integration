from __future__ import annotations

import asyncio
import json
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _print_json(title, payload):
    print("\n{}".format(title))
    print(json.dumps(payload, indent=2, sort_keys=True, default=str))


async def main() -> None:
    try:
        from fastmcp import Client
    except ImportError:
        raise SystemExit(
            "fastmcp is not installed. Run: python -m pip install -r requirements.txt"
        )

    from implementation.init_db import create_database
    from implementation.mcp_server import DB_PATH, mcp

    create_database(DB_PATH)

    async with Client(mcp) as client:
        tools = await client.list_tools()
        resources = await client.list_resources()
        templates = await client.list_resource_templates()

        tool_names = [tool.name for tool in tools]
        resource_uris = [str(resource.uri) for resource in resources]
        template_uris = [str(template.uriTemplate) for template in templates]

        _print_json("DISCOVERY", {
            "tools": tool_names,
            "resources": resource_uris,
            "resource_templates": template_uris,
        })

        search_result = await client.call_tool(
            "search",
            {
                "table": "students",
                "filters": [{"column": "cohort", "op": "=", "value": "A1"}],
                "columns": ["id", "name", "cohort", "score"],
                "order_by": "score",
                "descending": True,
                "limit": 3,
            },
        )
        _print_json("SEARCH cohort A1", search_result.data)

        unique_email = "minh.ho+{}@example.edu".format(uuid.uuid4().hex[:8])
        insert_result = await client.call_tool(
            "insert",
            {
                "table": "students",
                "values": {
                    "name": "Minh Ho",
                    "cohort": "C3",
                    "email": unique_email,
                    "score": 81.0,
                },
            },
        )
        _print_json("INSERT student", insert_result.data)

        aggregate_result = await client.call_tool(
            "aggregate",
            {
                "table": "students",
                "metric": "avg",
                "column": "score",
                "group_by": "cohort",
            },
        )
        _print_json("AGGREGATE avg score by cohort", aggregate_result.data)

        invalid_result = await client.call_tool("search", {"table": "missing_table"})
        _print_json("INVALID search", invalid_result.data)

        schema = await client.read_resource("schema://database")
        table_schema = await client.read_resource("schema://table/students")
        _print_json("SCHEMA resource count", {"schema_contents": len(schema)})
        _print_json("TABLE schema resource count", {"schema_contents": len(table_schema)})

    required = {"search", "insert", "aggregate"}
    if set(tool_names) != required:
        raise SystemExit("unexpected tools: {}".format(tool_names))
    if "schema://database" not in resource_uris:
        raise SystemExit("schema://database resource was not discovered")
    if "schema://table/{table_name}" not in template_uris:
        raise SystemExit("schema://table/{table_name} template was not discovered")

    print("\nVerification passed.")


if __name__ == "__main__":
    asyncio.run(main())
