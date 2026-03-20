"""A2A inbound server — makes this agent callable by other agents."""
import os
from typing import Any

from fastapi import APIRouter

from a2a.agent_card import AgentCard, build_agent_card
from a2a.client import AgentRequest, AgentResponse

router = APIRouter(prefix="/a2a", tags=["a2a"])
well_known_router = APIRouter(tags=["well-known"])

_AGENT_ID = "restaurant-agent-v1"


def _endpoint_url() -> str:
    return os.getenv("PUBLIC_ENDPOINT_URL", "http://localhost:8000")


# --------------------------------------------------------------------------- #
# Agent Card endpoints
# --------------------------------------------------------------------------- #

@router.get("/agent-card", response_model=AgentCard)
async def get_agent_card() -> AgentCard:
    """Serve this agent's capability manifest to other agents."""
    return build_agent_card(_endpoint_url())


@well_known_router.get("/.well-known/agent-card", response_model=AgentCard)
async def well_known_agent_card() -> AgentCard:
    """Well-known URL for agent card discovery (A2A spec)."""
    return build_agent_card(_endpoint_url())


# --------------------------------------------------------------------------- #
# Capability stubs — full implementations added in RA-12/RA-13
# --------------------------------------------------------------------------- #

def _stub_recommend_dish(payload: dict[str, Any]) -> AgentResponse:
    return AgentResponse(
        success=True,
        data={
            "recommendations": [],
            "confidence": 0.0,
            "note": "stub — full implementation in RA-13",
        },
        responding_agent_id=_AGENT_ID,
        correlation_id=None,
    )


def _stub_search_reviews(payload: dict[str, Any]) -> AgentResponse:
    return AgentResponse(
        success=True,
        data={
            "snippets": [],
            "note": "stub — full implementation in RA-12",
        },
        responding_agent_id=_AGENT_ID,
        correlation_id=None,
    )


_CAPABILITY_HANDLERS = {
    "recommend_dish": _stub_recommend_dish,
    "search_reviews": _stub_search_reviews,
}


@router.post("/invoke", response_model=AgentResponse)
async def invoke_capability(request: AgentRequest) -> AgentResponse:
    """Receive and route capability invocations from external agents."""
    handler = _CAPABILITY_HANDLERS.get(request.capability)
    if handler is None:
        return AgentResponse(
            success=False,
            error=f"Unknown capability: {request.capability!r}",
            responding_agent_id=_AGENT_ID,
            correlation_id=request.correlation_id,
        )
    response = handler(request.payload)
    response.correlation_id = request.correlation_id
    return response
