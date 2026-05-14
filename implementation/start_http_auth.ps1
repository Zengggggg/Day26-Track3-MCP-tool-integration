$ErrorActionPreference = "Stop"
$env:MCP_TRANSPORT = "http"
$env:MCP_HOST = "127.0.0.1"
$env:MCP_PORT = "3001"
$env:MCP_AUTH_TOKEN = "sqlite-lab-secret"
$Python = Join-Path (Split-Path $PSScriptRoot -Parent) ".venv\Scripts\python.exe"
& $Python (Join-Path $PSScriptRoot "mcp_server.py")

