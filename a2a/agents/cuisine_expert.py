"""CuisineExpert agent — stub server + outbound connector."""
import os
import httpx
from a2a.client import AgentConnector, AgentRequest, AgentResponse
from typing import Any

# ---------------------------------------------------------------------------
# Stub server (runs on port 8002; Phase 0 returns hard-coded cuisine facts)
# ---------------------------------------------------------------------------

_CUISINE_FACTS: dict[str, dict[str, str]] = {
    "italian": {
        "origin": "Italy",
        "history": "Italian cuisine evolved over centuries, shaped by ancient Rome, the Renaissance, and regional diversity across the peninsula.",
        "key_ingredients": "olive oil, tomatoes, pasta, Parmigiano-Reggiano, fresh herbs",
    },
    "indian": {
        "origin": "Indian subcontinent",
        "history": "Indian cuisine spans thousands of years, influenced by Mughal, Persian, and colonial histories, resulting in incredible regional diversity.",
        "key_ingredients": "turmeric, cumin, coriander, garam masala, ghee, lentils",
    },
    "japanese": {
        "origin": "Japan",
        "history": "Japanese cuisine emphasises seasonal ingredients and presentation, shaped by Buddhist dietary restrictions and centuries of isolation.",
        "key_ingredients": "soy sauce, miso, dashi, rice, fresh seafood, sake",
    },
    "mexican": {
        "origin": "Mexico",
        "history": "Mexican cuisine blends indigenous Mesoamerican cooking with Spanish colonial influences, earning UNESCO Intangible Cultural Heritage status.",
        "key_ingredients": "chillies, corn, beans, avocado, epazote, chocolate",
    },
    "thai": {
        "origin": "Thailand",
        "history": "Thai cuisine balances five flavours — sweet, sour, salty, bitter, and spicy — drawing on Chinese, Indian, and Malay influences.",
        "key_ingredients": "lemongrass, galangal, kaffir lime, fish sauce, coconut milk, Thai basil",
    },
}

_DEFAULT_FACT = {
    "origin": "Various",
    "history": "A rich culinary tradition shaped by local ingredients, culture, and history.",
    "key_ingredients": "Fresh seasonal ingredients prepared with care.",
}


class CuisineExpertAgent:
    """
    Stub implementation of the CuisineExpert agent.
    Phase 0: returns hard-coded facts — no LLM call required.
    """

    agent_id = "cuisine-expert-v1"

    def get_cuisine_info(self, cuisine_type: str) -> dict[str, Any]:
        """Return stub cuisine facts for the given cuisine type."""
        key = cuisine_type.lower().strip()
        fact = _CUISINE_FACTS.get(key, _DEFAULT_FACT)
        return {
            "cuisine_type": cuisine_type,
            **fact,
            "source": "cuisine-expert-stub-v1",
        }

    def handle(self, capability: str, payload: dict[str, Any]) -> AgentResponse:
        """Dispatch an A2A capability request."""
        if capability == "get_cuisine_info":
            cuisine_type = payload.get("cuisine_type", "unknown")
            data = self.get_cuisine_info(cuisine_type)
            return AgentResponse(
                success=True,
                data=data,
                responding_agent_id=self.agent_id,
            )
        return AgentResponse(
            success=False,
            error=f"Unknown capability: {capability!r}",
            responding_agent_id=self.agent_id,
        )


# Singleton for use in the FastAPI route
_cuisine_expert_agent = CuisineExpertAgent()


def get_cuisine_expert_response(request: AgentRequest) -> AgentResponse:
    """Entry point for the cuisine-expert FastAPI endpoint."""
    response = _cuisine_expert_agent.handle(request.capability, request.payload)
    response.correlation_id = request.correlation_id
    return response


# ---------------------------------------------------------------------------
# Outbound connector (used by the restaurant agent to call the cuisine service)
# ---------------------------------------------------------------------------


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
