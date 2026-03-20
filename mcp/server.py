"""MCP server — exposes agent tools via Model Context Protocol.

Two transports:
  - HTTP/SSE  : FastAPI router at /mcp (for web clients and testing)
  - stdio JSON-RPC: run via `python -m mcp` (for Claude Desktop)
"""
import json
import os
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

router = APIRouter(prefix="/mcp", tags=["mcp"])

_CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")

# ---------------------------------------------------------------------------
# Tool schemas (shared between HTTP and stdio transports)
# ---------------------------------------------------------------------------

TOOL_SCHEMAS = [
    {
        "name": "recommend_dish",
        "description": "Recommend dishes based on taste preferences and dietary restrictions.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string", "description": "Restaurant tenant identifier"},
                "query": {"type": "string", "description": "User's taste preference query"},
                "allergen_stops": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Hard-stop allergens (e.g. ['gluten', 'dairy'])",
                },
                "positive_signals": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Preferred flavour signals",
                },
                "top_n": {"type": "integer", "description": "Number of recommendations", "default": 3},
            },
            "required": ["tenant_id", "query"],
        },
    },
    {
        "name": "get_menu",
        "description": "Get the full structured menu for a restaurant tenant.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string"},
                "available_only": {"type": "boolean", "default": True},
                "category": {"type": "string", "description": "Optional category filter"},
            },
            "required": ["tenant_id"],
        },
    },
    {
        "name": "search_reviews",
        "description": "Semantic search over verified customer reviews.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "tenant_id": {"type": "string"},
                "query": {"type": "string"},
                "top_k": {"type": "integer", "default": 5},
            },
            "required": ["tenant_id", "query"],
        },
    },
]

MCP_MANIFEST = {
    "schema_version": "v1",
    "name": "restaurant-agent",
    "description": "Restaurant dish recommendation and review search",
    "tools": TOOL_SCHEMAS,
}


# ---------------------------------------------------------------------------
# Tool dispatcher (used by both HTTP and stdio transports)
# ---------------------------------------------------------------------------

async def _call_tool(tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    """Execute a named tool and return a JSON-serialisable result dict."""
    tenant_id = tool_input.get("tenant_id", "")
    session_id = "mcp-session"

    if tool_name == "recommend_dish":
        from core.tools.dish_recommender import DishRecommenderInput, DishRecommenderTool
        tool = DishRecommenderTool(chroma_path=_CHROMA_PATH)
        result = await tool(DishRecommenderInput(
            tenant_id=tenant_id,
            session_id=session_id,
            query=tool_input.get("query", ""),
            allergen_stops=tool_input.get("allergen_stops", []),
            positive_signals=tool_input.get("positive_signals", []),
            top_n=tool_input.get("top_n", 3),
        ))
        return result.model_dump()

    if tool_name == "get_menu":
        from core.tools.menu_fetcher import MenuFetcherInput, MenuFetcherTool
        tool = MenuFetcherTool()
        result = await tool(MenuFetcherInput(
            tenant_id=tenant_id,
            session_id=session_id,
            available_only=tool_input.get("available_only", True),
            category=tool_input.get("category"),
        ))
        return result.model_dump()

    if tool_name == "search_reviews":
        from core.tools.review_retrieval import ReviewRetrievalInput, ReviewRetrievalTool
        tool = ReviewRetrievalTool(chroma_path=_CHROMA_PATH)
        result = await tool(ReviewRetrievalInput(
            tenant_id=tenant_id,
            session_id=session_id,
            query=tool_input.get("query", ""),
            top_k=tool_input.get("top_k", 5),
        ))
        return result.model_dump()

    raise ValueError(f"Unknown tool: {tool_name!r}")


# ---------------------------------------------------------------------------
# HTTP/SSE transport — FastAPI routes
# ---------------------------------------------------------------------------

@router.get("")
async def mcp_manifest(request: Request) -> StreamingResponse:
    """MCP server SSE endpoint — streams the tool manifest."""
    async def event_stream():
        yield f"data: {json.dumps(MCP_MANIFEST)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@router.get("/tools")
async def list_tools() -> dict:
    """Return all available MCP tool schemas."""
    return {"tools": TOOL_SCHEMAS}


class ToolCallRequest(BaseModel):
    tool_name: str
    tool_input: dict[str, Any] = {}


@router.post("/call")
async def call_tool(request: ToolCallRequest) -> dict:
    """Execute an MCP tool and return the result."""
    try:
        result = await _call_tool(request.tool_name, request.tool_input)
        return {"success": True, "result": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tool execution failed: {e}")
