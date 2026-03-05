"""LangGraph agent state definition."""
from typing import Any, Optional, Annotated
from pydantic import BaseModel
from core.models.preference import UserTasteProfile
from core.models.session import Message
import operator


class AgentState(BaseModel):
    """
    Complete agent state passed between LangGraph nodes.
    Immutable pattern — nodes return updated copies.
    """
    # Identity
    session_id: str
    tenant_id: str

    # Conversation
    messages: Annotated[list[Message], operator.add] = []
    current_input: str = ""

    # Preferences — evolves through conversation
    taste_profile: Optional[UserTasteProfile] = None

    # Tool results
    last_tool_results: dict[str, Any] = {}

    # Guardrail state
    input_passed_guardrails: bool = False
    output_passed_guardrails: bool = False

    # A2A
    external_agent_responses: dict[str, Any] = {}

    # Control flow
    should_call_external_agent: bool = False
    external_agent_name: Optional[str] = None
    is_complete: bool = False
    error: Optional[str] = None
