"""Agent Card manifest — machine-readable capability declaration for A2A."""
from pydantic import BaseModel
from typing import Optional


class AgentCapability(BaseModel):
    """Single declared capability of an agent."""
    name: str
    description: str
    input_schema: dict
    output_schema: dict
    requires_tenant_context: bool = False


class AgentCard(BaseModel):
    """
    Agent Card manifest — declares what this agent can do.
    Consumed by other agents to discover and call our capabilities.
    Aligned with emerging A2A protocol standards.
    Served at: GET /a2a/agent-card
    """
    agent_id: str
    name: str
    description: str
    version: str
    capabilities: list[AgentCapability]
    endpoint_url: str
    auth_required: bool = True
    supported_protocols: list[str] = ["a2a/v1", "mcp"]
    contact_email: Optional[str] = None


def build_agent_card(endpoint_url: str) -> AgentCard:
    """Build the agent card for this restaurant agent."""
    return AgentCard(
        agent_id="restaurant-agent-v1",
        name="Restaurant Discovery Agent",
        description=(
            "Recommends dishes, retrieves verified reviews, and manages "
            "user taste preferences for restaurant customers."
        ),
        version="0.1.0",
        endpoint_url=endpoint_url,
        capabilities=[
            AgentCapability(
                name="recommend_dish",
                description="Recommend dishes based on taste preferences and reviews.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "taste_preferences": {"type": "array", "items": {"type": "string"}},
                        "dietary_restrictions": {"type": "array", "items": {"type": "string"}},
                        "top_k": {"type": "integer", "default": 3},
                    },
                    "required": ["taste_preferences"],
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "recommendations": {"type": "array"},
                        "confidence": {"type": "number"},
                    },
                },
                requires_tenant_context=True,
            ),
            AgentCapability(
                name="search_reviews",
                description="Semantic search over verified restaurant reviews.",
                input_schema={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string"},
                        "top_k": {"type": "integer", "default": 5},
                    },
                    "required": ["query"],
                },
                output_schema={
                    "type": "object",
                    "properties": {"snippets": {"type": "array"}},
                },
                requires_tenant_context=True,
            ),
        ],
    )
