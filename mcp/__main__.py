"""
MCP stdio server entry point — runs when `python -m mcp` is executed.

Implements the MCP JSON-RPC 2.0 protocol over stdin/stdout for integration
with Claude Desktop and other MCP clients.

Protocol reference: https://modelcontextprotocol.io/specification
"""
import asyncio
import json
import sys


async def _handle_request(request: dict) -> dict | None:
    """Dispatch a single JSON-RPC request and return the response."""
    method = request.get("method", "")
    req_id = request.get("id")
    params = request.get("params", {})

    def _ok(result):
        return {"jsonrpc": "2.0", "id": req_id, "result": result}

    def _err(code, message):
        return {"jsonrpc": "2.0", "id": req_id, "error": {"code": code, "message": message}}

    # MCP initialise handshake
    if method == "initialize":
        return _ok({
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "restaurant-agent", "version": "0.1.0"},
        })

    if method == "notifications/initialized":
        return None  # notification — no response

    # tools/list
    if method == "tools/list":
        from mcp.server import TOOL_SCHEMAS
        return _ok({"tools": TOOL_SCHEMAS})

    # tools/call
    if method == "tools/call":
        from mcp.server import _call_tool
        tool_name = params.get("name", "")
        tool_input = params.get("arguments", {})
        try:
            result = await _call_tool(tool_name, tool_input)
            return _ok({"content": [{"type": "text", "text": json.dumps(result, default=str)}]})
        except ValueError as e:
            return _err(-32601, str(e))
        except Exception as e:
            return _err(-32603, f"Tool execution error: {e}")

    return _err(-32601, f"Method not found: {method!r}")


async def main():
    """Read JSON-RPC messages from stdin, write responses to stdout."""
    reader = asyncio.StreamReader()
    protocol = asyncio.StreamReaderProtocol(reader)
    await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin)

    write_transport, _ = await asyncio.get_event_loop().connect_write_pipe(
        lambda: asyncio.BaseProtocol(), sys.stdout
    )

    async def write_response(obj: dict):
        line = json.dumps(obj) + "\n"
        write_transport.write(line.encode())

    while True:
        try:
            line = await reader.readline()
            if not line:
                break
            request = json.loads(line.decode().strip())
            response = await _handle_request(request)
            if response is not None:
                await write_response(response)
        except json.JSONDecodeError:
            pass  # skip malformed lines
        except Exception:
            break


if __name__ == "__main__":
    asyncio.run(main())
