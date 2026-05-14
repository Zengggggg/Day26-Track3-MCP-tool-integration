$ErrorActionPreference = "Stop"
$Python = (Get-Command python).Source
$Server = Join-Path $PSScriptRoot "mcp_server.py"
npx -y @modelcontextprotocol/inspector $Python $Server

