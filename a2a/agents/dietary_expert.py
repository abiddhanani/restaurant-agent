"""Connector for the DietaryExpert external agent."""
import os
import httpx
from a2a.client import AgentConnector, AgentRequest, AgentResponse
from typing import Any


class DietaryExpertConnector(AgentConnector):
    """
    Connects to the DietaryExpert agent service.
    Provides: deep allergen analysis, nutritional info, complex dietary needs.
    Runs as a separate Docker service on DIETARY_EXPERT_AGENT_URL.
    """
    agent_id = "dietary-expert-v1"

    def __init__(self) -> None:
        """Load agent URL from environment."""
        self.base_url = os.getenv("DIETARY_EXPERT_AGENT_URL", "http://localhost:8003")

    async def call(self, capability: str, payload: dict[str, Any]) -> AgentResponse:
        """POST a capability request to the DietaryExpert agent."""
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
                error=f"DietaryExpert agent unavailable: {str(e)}",
            )
