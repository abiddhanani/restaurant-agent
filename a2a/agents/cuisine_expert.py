"""Connector for the CuisineExpert external agent."""
import os
import httpx
from a2a.client import AgentConnector, AgentRequest, AgentResponse
from typing import Any


class CuisineExpertConnector(AgentConnector):
    """
    Connects to the CuisineExpert agent service.
    Provides: dish origin stories, cultural context, ingredient deep-dives.
    Runs as a separate Docker service on CUISINE_EXPERT_AGENT_URL.
    """
    agent_id = "cuisine-expert-v1"

    def __init__(self) -> None:
        """Load agent URL from environment."""
        self.base_url = os.getenv("CUISINE_EXPERT_AGENT_URL", "http://localhost:8002")

    async def call(self, capability: str, payload: dict[str, Any]) -> AgentResponse:
        """POST a capability request to the CuisineExpert agent."""
        request = AgentRequest(
            capability=capability,
            payload=payload,
            calling_agent_id="restaurant-agent-v1",
        )
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{self.base_url}/a2a/invoke",
                    json=request.model_dump(),
                )
                response.raise_for_status()
                return AgentResponse(**response.json())
        except httpx.HTTPError as e:
            return AgentResponse(
                success=False,
                error=f"CuisineExpert agent unavailable: {str(e)}",
            )
