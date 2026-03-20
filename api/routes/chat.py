"""Chat endpoint — main entry point for widget conversations."""
import logging
from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

from core.agent.graph import agent_graph
from core.models.preference import UserTasteProfile
from core.models.session import Message  # used in type annotations
from core.preferences.profile import PreferenceExtractor
from sessions.manager import SessionManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])

# Module-level singletons — Phase 0 in-memory.
_session_manager = SessionManager()
_preference_extractor = PreferenceExtractor()


class ChatRequest(BaseModel):
    """Incoming chat message from widget."""
    session_id: Optional[str] = None  # None = start new session
    message: str


class ChatResponse(BaseModel):
    """Response back to widget."""
    session_id: str
    response: str
    suggestions: list[str] = []


@router.post("", response_model=ChatResponse)
async def chat(
    body: ChatRequest,
    request: Request,
) -> ChatResponse:
    """Main chat endpoint. Tenant resolved from X-Tenant-ID header via middleware."""
    tenant_id: str = request.state.tenant_id

    # Get or create session (enforces tenant isolation).
    session = await _session_manager.get_or_create(tenant_id, body.session_id)

    # Update taste profile from user message.
    current_profile = session.taste_profile or UserTasteProfile(
        session_id=session.session_id, tenant_id=tenant_id
    )
    updated_profile = await _preference_extractor.update_from_message(
        current_profile, body.message, role="user"
    )
    session.taste_profile = updated_profile

    # Add user message.
    await _session_manager.add_message(session.session_id, "user", body.message)

    # Build initial state for this turn.
    initial_state = {
        "session_id": session.session_id,
        "tenant_id": tenant_id,
        "messages": session.messages,
        "current_input": body.message,
        "taste_profile": updated_profile,
        "input_passed_guardrails": True,
        "output_passed_guardrails": True,
    }

    # Run agent graph.
    result = await agent_graph.ainvoke(initial_state)

    # Extract assistant reply from updated messages.
    updated_messages: list[Message] = result["messages"]
    assistant_message = next(
        (m for m in reversed(updated_messages) if m.role == "assistant"), None
    )
    reply_text = assistant_message.content if assistant_message else ""

    # Persist updated session.
    session.messages = updated_messages
    await _session_manager.update_session(session)

    return ChatResponse(
        session_id=session.session_id,
        response=reply_text,
    )
