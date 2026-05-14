#!/usr/bin/env sh
set -eu
PYTHON_BIN="${PYTHON_BIN:-python}"
SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
npx -y @modelcontextprotocol/inspector "$PYTHON_BIN" "$SCRIPT_DIR/mcp_server.py"
