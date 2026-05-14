# Demo Notes

Use this sequence for the required short demo video or screenshots.

## 1. Start From A Clean Database

```powershell
.\.venv\Scripts\python.exe implementation\init_db.py
```

If `.env` does not exist yet:

```powershell
Copy-Item .env.example .env
```

Expected output:

```text
D:\AI_IN_ACTION\LAB\Asg26\Day26-Track3-MCP-tool-integration\implementation\lab.db
```

## 2. Run Automated Verification

```powershell
.\.venv\Scripts\python.exe implementation\verify_server.py
```

Verified in this workspace:

```text
DISCOVERY
tools: search, insert, aggregate
resources: schema://database
resource_templates: schema://table/{table_name}

SEARCH cohort A1
returns Emma Vo, An Nguyen, and Binh Tran ordered by score

INSERT student
returns inserted Minh Ho payload with generated id

AGGREGATE avg score by cohort
returns average scores grouped by A1, B2, and C3

INVALID search
returns ok=false with unknown table validation_error

SEARCH output bonus
shows pagination.has_more / next_offset and annotations.backend

Verification passed.
```

## 3. Optional Inspector Demo

```powershell
.\implementation\start_inspector.ps1
```

Show:

- the three tools are discoverable
- `schema://database` is readable
- `schema://table/students` is readable
- one valid call for each tool
- one invalid call with a clear validation error
- pagination and annotations in a `search` response

## 4. Bonus HTTP Auth Demo

Set `.env` for HTTP auth:

```env
MCP_TRANSPORT=http
MCP_HOST=127.0.0.1
MCP_PORT=3001
MCP_AUTH_TOKEN=sqlite-lab-secret
```

Start the protected HTTP server:

```powershell
.\implementation\start_http_auth.ps1
```

The demo token is:

```text
sqlite-lab-secret
```

Explain that HTTP/SSE clients must send:

```text
Authorization: Bearer sqlite-lab-secret
```

Without that bearer token, protected HTTP/SSE MCP requests are rejected. Stdio is intentionally left unauthenticated for local MCP clients and Inspector demos.

## 5. Bonus PostgreSQL Demo Note

PostgreSQL uses the same MCP tool names and JSON payloads. Select it in `.env`:

```env
DATABASE_URL=postgresql://user:password@localhost:5432/sqlite_lab
POSTGRES_SCHEMA=public
```

Or from PowerShell:

```powershell
$env:DATABASE_URL = "postgresql://user:password@localhost:5432/sqlite_lab"
.\.venv\Scripts\python.exe implementation\mcp_server.py
```

The PostgreSQL database must already contain compatible `students`, `courses`, and `enrollments` tables.
