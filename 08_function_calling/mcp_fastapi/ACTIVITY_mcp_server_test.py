# ACTIVITY_mcp_server_test.py
# Stage 3: Test the filter_rows MCP tool with tools/call
# Pairs with ACTIVITY_mcp_server.md and server.py
# Tim Fraser (activity extension)

# This script mirrors testme.py: handshake, list tools, then call a tool.
# It focuses on calling filter_rows directly via mcp_request("tools/call", ...).
#
# Start the server before running (from mcp_fastapi/):
#   uvicorn server:app --port 8000 --reload
#   or from repo root: python 08_function_calling/mcp_fastapi/runme.py

# 0. SETUP ###################################
print("# 0. SETUP ###################################")

print("Note: Run this script from the mcp_fastapi/ folder (or set MCP_SERVER_URL).")

## 0.1 Import libraries #################################
import json
import os

import requests  # pip install requests
from dotenv import load_dotenv

## 0.2 Environment variables #################################
load_dotenv()

# Local default; override with MCP_SERVER_URL or use deployed Connect URL + CONNECT_API_KEY.
SERVER = os.environ.get("MCP_SERVER_URL", "http://127.0.0.1:8000/mcp")


def mcp_request(method, params=None, id=1):
    # One JSON-RPC round-trip to the MCP server (same pattern as testme.py).
    body = {"jsonrpc": "2.0", "id": id, "method": method, "params": params or {}}
    headers = {}
    key = os.getenv("CONNECT_API_KEY")
    if key:
        headers["Authorization"] = f"Key {key}"
    resp = requests.post(SERVER, json=body, headers=headers)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data:
        raise RuntimeError(data["error"])
    return data.get("result")


# 1. HANDSHAKE — initialize ##############################
print("# 1. HANDSHAKE — initialize ##############################")

init = mcp_request(
    "initialize",
    {
        "protocolVersion": "2025-03-26",
        "clientInfo": {"name": "py-activity-filter-test", "version": "0.1.0"},
        "capabilities": {},
    },
)

print(f"Server: {init['serverInfo']['name']} v {init['serverInfo']['version']}")

# 2. DISCOVER TOOLS — tools/list #########################
print("# 2. DISCOVER TOOLS — tools/list #########################")

tools = mcp_request("tools/list")
print("Available tools:")
for t in tools["tools"]:
    print(f"  - {t['name']}: {t['description']}")

# 3. CALL filter_rows — tools/call ############################
print("# 3. CALL filter_rows — tools/call ############################")

# Example: iris rows where Species is setosa (string equality).
result = mcp_request(
    "tools/call",
    {
        "name": "filter_rows",
        "arguments": {
            "dataset_name": "iris",
            "column": "Species",
            "operator": "==",
            "value": "setosa",
        },
    },
)

text = result["content"][0]["text"]
rows = json.loads(text)
print(f"filter_rows returned {len(rows)} rows (expected 50 for setosa).")
print(text[:800] + ("..." if len(text) > 800 else ""))

# Second call: numeric filter on mtcars (mpg > 21).
result2 = mcp_request(
    "tools/call",
    {
        "name": "filter_rows",
        "arguments": {
            "dataset_name": "mtcars",
            "column": "mpg",
            "operator": ">",
            "value": 21,
        },
    },
    id=2,
)

text2 = result2["content"][0]["text"]
rows2 = json.loads(text2)
print(f"\nmtcars mpg > 21: {len(rows2)} rows.")
print(text2[:800] + ("..." if len(text2) > 800 else ""))
