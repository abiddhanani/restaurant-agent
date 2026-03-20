"""Chat endpoint — main entry point for widget conversations."""
import logging
from typing import Optional

from fastapi import APIRouter, Request
from pydantic import BaseModel

from core.agent.graph import agent_graph
from core.models.session import Message
from sessions.manager import SessionManager

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["chat"])

# In-memory session store — Phase 0 (Redis in Phase 1+).
_session_manager = SessionManager()


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

    # Get or create session.
    if body.session_id:
        session = await _session_manager.get_session(body.session_id)
        if session is None:
            session = await _session_manager.create_session(tenant_id)
    else:
        session = await _session_manager.create_session(tenant_id)

    # Add user message.
    user_message = Message(role="user", content=body.message)
    session.messages.append(user_message)

    # Build initial state for this turn.
    initial_state = {
        "session_id": session.session_id,
        "tenant_id": tenant_id,
        "messages": session.messages,
        "current_input": body.message,
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
