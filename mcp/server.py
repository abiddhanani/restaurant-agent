"""MCP server — exposes agent tools via Model Context Protocol."""
from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
import json

router = APIRouter(prefix="/mcp", tags=["mcp"])

MCP_MANIFEST = {
    "schema_version": "v1",
    "name": "restaurant-agent",
    "description": "Restaurant dish recommendation and review search",
    "tools": [
        {
            "name": "recommend_dish",
            "description": "Recommend dishes based on taste preferences and dietary needs.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "tenant_id": {"type": "string"},
                    "taste_preferences": {"type": "array", "items": {"type": "string"}},
                    "dietary_restrictions": {"type": "array", "items": {"type": "string"}},
                    "top_k": {"type": "integer", "default": 3},
                },
                "required": ["tenant_id", "taste_preferences"],
            },
        },
        {
            "name": "get_menu",
            "description": "Get the full structured menu for a restaurant.",
            "input_schema": {
                "type": "object",
                "properties": {"tenant_id": {"type": "string"}},
                "required": ["tenant_id"],
            },
        },
        {
            "name": "search_reviews",
            "description": "Semantic search over verified restaurant reviews.",
            "input_schema": {
                "type": "object",
                "properties": {
                    "tenant_id": {"type": "string"},
                    "query": {"type": "string"},
                    "top_k": {"type": "integer", "default": 5},
                },
                "required": ["tenant_id", "query"],
            },
        },
    ],
}


@router.get("")
async def mcp_server(request: Request) -> StreamingResponse:
    """
    MCP server endpoint — server-sent events, standard MCP protocol.
    Implemented Week 5.
    """
    async def event_stream():
        yield f"data: {json.dumps(MCP_MANIFEST)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")
