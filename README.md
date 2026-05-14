# SQLite FastMCP Database Server Lab

This repository implements a FastMCP database server for the lab rubric. It exposes a SQLite database through `search`, `insert`, and `aggregate`, publishes schema resources, and includes bonus support for HTTP/SSE authentication, PostgreSQL adapter selection, and richer output metadata.

## Setup

Use Python 3.12 or newer.

```powershell
py -3.12 -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
cp .env.example .env
python implementation\init_db.py
```

The `.env` file controls transport, auth, and database backend. Defaults use local stdio and SQLite:

```env
MCP_TRANSPORT=stdio
MCP_HOST=127.0.0.1
MCP_PORT=3001
MCP_AUTH_TOKEN=
DATABASE_URL=
POSTGRES_SCHEMA=public
```

Run tests:

```powershell
python -m pytest -q
```

Run the repeatable MCP verification:

```powershell
python implementation\verify_server.py
```

Expected verification includes tool discovery for `search`, `insert`, `aggregate`, resource discovery for `schema://database`, resource template discovery for `schema://table/{table_name}`, valid tool calls, and an invalid-table validation error.

## Default Stdio Server

The default transport is stdio and uses SQLite at `implementation/lab.db`.

```powershell
python implementation\mcp_server.py
```

Inspector command:

```powershell
npx -y @modelcontextprotocol/inspector python implementation\mcp_server.py
```

## Tools

### `search`

Search rows with filters, selected columns, ordering, and pagination.

```json
{
  "table": "students",
  "filters": [{"column": "cohort", "op": "=", "value": "A1"}],
  "columns": ["id", "name", "cohort", "score"],
  "order_by": "score",
  "descending": true,
  "limit": 3
}
```

The response includes the original fields plus richer metadata:

```json
{
  "ok": true,
  "table": "students",
  "count": 3,
  "pagination": {
    "limit": 3,
    "offset": 0,
    "returned": 3,
    "has_more": false,
    "next_offset": null
  },
  "annotations": {
    "backend": "SQLiteAdapter",
    "selected_columns": 4,
    "filter_count": 1,
    "ordered_by": "score",
    "order_direction": "desc"
  }
}
```

### `insert`

Insert one row after validating the table and columns.

```json
{
  "table": "students",
  "values": {
    "name": "Minh Ho",
    "cohort": "C3",
    "email": "minh.ho@example.edu",
    "score": 81.0
  }
}
```

### `aggregate`

Run `count`, `avg`, `sum`, `min`, or `max`.

```json
{
  "table": "students",
  "metric": "avg",
  "column": "score",
  "group_by": "cohort"
}
```

## Resources

- `schema://database`: full schema snapshot
- `schema://table/{table_name}`: one table schema, for example `schema://table/students`

## Validation And Safety

The tools reject unknown tables, unknown columns, unsupported operators, invalid aggregate requests, empty inserts, invalid identifiers, and invalid pagination. SQL values use bound parameters. Table and column identifiers are checked against database schema metadata before being quoted into SQL.

## Bonus: HTTP/SSE Authentication

Stdio remains unauthenticated for local MCP clients. Authentication is enabled for HTTP/SSE by setting `MCP_AUTH_TOKEN`.

Run authenticated HTTP by editing `.env`:

```env
MCP_TRANSPORT=http
MCP_HOST=127.0.0.1
MCP_PORT=3001
MCP_AUTH_TOKEN=sqlite-lab-secret
```

Then run:

```powershell
.\implementation\start_http_auth.ps1
```

This script sets:

```text
MCP_TRANSPORT=http
MCP_HOST=127.0.0.1
MCP_PORT=3001
MCP_AUTH_TOKEN=sqlite-lab-secret
```

Manual equivalent without editing `.env`:

```powershell
$env:MCP_TRANSPORT = "http"
$env:MCP_HOST = "127.0.0.1"
$env:MCP_PORT = "3001"
$env:MCP_AUTH_TOKEN = "sqlite-lab-secret"
python implementation\mcp_server.py
```

Connect with a client that sends:

```text
Authorization: Bearer sqlite-lab-secret
```

With FastMCP client code, pass `auth="sqlite-lab-secret"` when connecting to the HTTP endpoint. Without the bearer token, protected HTTP/SSE requests should be rejected.

For SSE instead of streamable HTTP:

```powershell
$env:MCP_TRANSPORT = "sse"
$env:MCP_AUTH_TOKEN = "sqlite-lab-secret"
python implementation\mcp_server.py
```

## Bonus: PostgreSQL Backend

SQLite is the default. PostgreSQL is selected when `DATABASE_URL` starts with `postgresql://` or `postgres://`. Put this in `.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/sqlite_lab
POSTGRES_SCHEMA=public
```

Or set it manually:

```powershell
$env:DATABASE_URL = "postgresql://user:password@localhost:5432/sqlite_lab"
python implementation\verify_server.py
```

The MCP tool surface is unchanged. PostgreSQL must contain tables compatible with the lab dataset, such as `students`, `courses`, and `enrollments`. The default tests do not require a live PostgreSQL server.

Optional schema selection:

```powershell
$env:POSTGRES_SCHEMA = "public"
```

## Client Config Examples

Claude Code `.mcp.json`:

```json
{
  "mcpServers": {
    "sqlite-lab": {
      "type": "stdio",
      "command": "D:\\AI_IN_ACTION\\LAB\\Asg26\\Day26-Track3-MCP-tool-integration\\.venv\\Scripts\\python.exe",
      "args": [
        "D:\\AI_IN_ACTION\\LAB\\Asg26\\Day26-Track3-MCP-tool-integration\\implementation\\mcp_server.py"
      ],
      "env": {}
    }
  }
}
```

Codex `~/.codex/config.toml`:

```toml
[mcp_servers.sqlite_lab]
command = "D:\\AI_IN_ACTION\\LAB\\Asg26\\Day26-Track3-MCP-tool-integration\\.venv\\Scripts\\python.exe"
args = ["D:\\AI_IN_ACTION\\LAB\\Asg26\\Day26-Track3-MCP-tool-integration\\implementation\\mcp_server.py"]
```

Gemini CLI:

```powershell
gemini mcp add sqlite-lab D:\AI_IN_ACTION\LAB\Asg26\Day26-Track3-MCP-tool-integration\.venv\Scripts\python.exe D:\AI_IN_ACTION\LAB\Asg26\Day26-Track3-MCP-tool-integration\implementation\mcp_server.py --description "SQLite lab FastMCP server" --timeout 10000
gemini mcp list
```

## Demo Checklist

1. Run `python implementation\verify_server.py`.
2. Show `search`, `insert`, and `aggregate`.
3. Read `schema://database` and `schema://table/students`.
4. Show invalid `search` with `{"table": "missing_table"}`.
5. Show `pagination` and `annotations` in a `search` result.
6. Start `.\implementation\start_http_auth.ps1` and explain Bearer token auth for HTTP/SSE.
7. Mention PostgreSQL backend selection through `DATABASE_URL`.
