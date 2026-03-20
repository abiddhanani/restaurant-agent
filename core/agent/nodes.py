"""LangGraph node implementations for the restaurant agent."""
import logging
import os

from anthropic import AsyncAnthropic

from core.agent.state import AgentState
from core.models.session import Message

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a helpful restaurant assistant. "
    "You help customers discover dishes they'll love based on the menu and their taste. "
    "Be warm, concise, and specific — always ground recommendations in real menu items. "
    "If you don't know what's on the menu yet, invite the customer to ask about specific dishes or dietary needs."
)

try:
    from langfuse.decorators import observe as _observe
except ImportError:  # pragma: no cover
    def _observe(func=None, **_):  # type: ignore[misc]
        return func if func is not None else (lambda f: f)


@_observe()
async def llm_node(state: AgentState) -> dict:
    """Call the LLM with the current message history and return the assistant reply."""
    client = AsyncAnthropic()
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    messages = [{"role": m.role, "content": m.content} for m in state.messages]

    response = await client.messages.create(
        model=model,
        max_tokens=1024,
        system=SYSTEM_PROMPT,
        messages=messages,
    )

    reply_text = response.content[0].text
    logger.debug("LLM reply for session=%s: %s", state.session_id, reply_text[:80])

    return {"messages": [Message(role="assistant", content=reply_text)]}
