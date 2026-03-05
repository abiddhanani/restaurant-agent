"""A2A outbound client — calls external agents."""
from abc import ABC, abstractmethod
from typing import Any, Optional
import httpx
from pydantic import BaseModel


class AgentRequest(BaseModel):
    """Standard A2A request envelope."""
    capability: str
    payload: dict[str, Any]
    calling_agent_id: str = "restaurant-agent-v1"
    correlation_id: Optional[str] = None


class AgentResponse(BaseModel):
    """Standard A2A response envelope."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    responding_agent_id: str = ""
    correlation_id: Optional[str] = None


class AgentConnector(ABC):
    """Base class for all external agent connectors."""
    agent_id: str
    base_url: str

    @abstractmethod
    async def call(self, capability: str, payload: dict[str, Any]) -> AgentResponse:
        """Call a capability on the external agent."""
        ...

    async def fetch_agent_card(self) -> dict[str, Any]:
        """Fetch and cache the remote agent's Agent Card."""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/a2a/agent-card")
            response.raise_for_status()
            return response.json()


class A2AClient:
    """
    Registry and dispatcher for external agent connections.
    Add connectors via register(). Call via dispatch().
    """

    def __init__(self) -> None:
        """Initialise empty connector registry."""
        self._connectors: dict[str, AgentConnector] = {}

    def register(self, connector: AgentConnector) -> None:
        """Register an external agent connector."""
        self._connectors[connector.agent_id] = connector

    async def dispatch(
        self,
        agent_id: str,
        capability: str,
        payload: dict[str, Any],
    ) -> AgentResponse:
        """Dispatch a capability call to a registered external agent."""
        connector = self._connectors.get(agent_id)
        if not connector:
            return AgentResponse(
                success=False,
                error=f"No connector registered for agent_id: {agent_id}",
            )
        return await connector.call(capability, payload)
