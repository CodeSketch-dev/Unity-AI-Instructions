"""Stdio MCP server (JSON-RPC 2.0, newline delimited) for Claude Code and Codex. Standard library only."""
from __future__ import annotations

import json
import sys
from typing import Any

from app.mcp import blender, guide, jobs, models  # noqa: F401  (importing registers the tools)
from app.mcp.registry import TOOLS

SERVER = {"name": "meshy-ai-studio", "version": "3.0"}
INSTRUCTIONS = ("Drives the Meshy AI Studio desktop app (keep MeshyAIStudio.exe running: the owner solves CAPTCHAs there), headless "
                "Blender and a Unity file hand-off. Call workflow_guide first.")


def tools_list() -> list[dict]:
    return [{"name": t.name, "description": t.description, "inputSchema": t.schema} for t in TOOLS.values()]


def call_tool(name: str, arguments: dict) -> Any:
    if name not in TOOLS:
        raise ValueError(f"unknown tool: {name}")
    return TOOLS[name].handler(arguments or {})


def handle(request: dict) -> dict | None:
    request_id, method = request.get("id"), request.get("method")
    params = request.get("params") or {}
    if request_id is None:
        return None  # notifications (initialized, cancelled...) need no reply
    if method == "initialize":
        result = {"protocolVersion": params.get("protocolVersion", "2024-11-05"), "capabilities": {"tools": {}},
                  "serverInfo": SERVER, "instructions": INSTRUCTIONS}
    elif method == "tools/list":
        result = {"tools": tools_list()}
    elif method == "tools/call":
        try:
            data = call_tool(params.get("name"), params.get("arguments") or {})
            result = {"content": [{"type": "text", "text": json.dumps(data, ensure_ascii=False)}]}
        except Exception as error:
            result = {"isError": True, "content": [{"type": "text", "text": f"{type(error).__name__}: {error}"}]}
    elif method == "ping":
        result = {}
    else:
        return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": f"method not found: {method}"}}
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def main() -> None:
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            reply = handle(json.loads(line))
        except Exception as error:
            reply = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": str(error)}}
        if reply is not None:
            print(json.dumps(reply, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
