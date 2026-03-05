"""A2A inbound server — makes this agent callable by other agents."""
from fastapi import APIRouter, HTTPException
from a2a.client import AgentRequest, AgentResponse
from a2a.agent_card import build_agent_card, AgentCard
import os

router = APIRouter(prefix="/a2a", tags=["a2a"])


@router.get("/agent-card", response_model=AgentCard)
async def get_agent_card() -> AgentCard:
    """Serve this agent's capability manifest to other agents."""
    endpoint_url = os.getenv("PUBLIC_ENDPOINT_URL", "http://localhost:8000")
    return build_agent_card(endpoint_url)


@router.post("/invoke", response_model=AgentResponse)
async def invoke_capability(request: AgentRequest) -> AgentResponse:
    """
    Receive and handle capability invocations from external agents.
    Implemented Week 5 — routes to appropriate internal handler per capability.
    """
    # TODO Week 5: implement capability routing
    # recommend_dish → DishRecommenderTool
    # search_reviews → ReviewRetrievalTool
    raise HTTPException(status_code=501, detail="A2A invoke not yet implemented")
