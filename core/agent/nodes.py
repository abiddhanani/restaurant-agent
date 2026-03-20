"""LangGraph node implementations for the restaurant agent."""
import json
import logging
import os
from typing import Any

from anthropic import AsyncAnthropic

from core.agent.state import AgentState
from core.models.session import Message
from core.tools.menu_fetcher import MenuFetcherInput, MenuFetcherTool
from core.tools.review_retrieval import ReviewRetrievalInput, ReviewRetrievalTool

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a helpful restaurant assistant. "
    "You help customers discover dishes they'll love based on the menu and their taste. "
    "Be warm, concise, and specific — always ground recommendations in real menu items. "
    "Use the menu_fetcher tool whenever the user asks about the menu, dishes, or availability."
)

# --------------------------------------------------------------------------- #
# Anthropic tool definitions
# --------------------------------------------------------------------------- #

TOOLS = [
    {
        "name": "menu_fetcher",
        "description": (
            "Fetch available menu items for the restaurant. "
            "Use when the user asks about the menu, what's available, specific dishes, or categories."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "available_only": {
                    "type": "boolean",
                    "description": "Only return currently available dishes (default: true)",
                },
                "category": {
                    "type": "string",
                    "description": "Optional dish category filter (e.g. 'Mains', 'Starters', 'Desserts')",
                },
            },
        },
    },
    {
        "name": "review_retrieval",
        "description": (
            "Retrieve relevant customer review snippets from the vector store. "
            "Use when the user asks about quality, experience, what people say, or specific dish feedback."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Semantic search query (e.g. 'best pasta dish', 'service quality')",
                },
                "top_k": {
                    "type": "integer",
                    "description": "Number of review snippets to retrieve (default: 5)",
                },
                "min_freshness_score": {
                    "type": "number",
                    "description": "Minimum freshness score 0-1 (default: 0.3 — filters very old reviews)",
                },
            },
            "required": ["query"],
        },
    },
]

# --------------------------------------------------------------------------- #
# Tool executor
# --------------------------------------------------------------------------- #

_menu_fetcher = MenuFetcherTool()
_review_retrieval = ReviewRetrievalTool()


async def _execute_tool(name: str, tool_input: dict[str, Any], state: AgentState) -> str:
    """Dispatch a tool call and return the result as a JSON string."""
    if name == "menu_fetcher":
        result = await _menu_fetcher(
            MenuFetcherInput(
                tenant_id=state.tenant_id,
                session_id=state.session_id,
                available_only=tool_input.get("available_only", True),
                category=tool_input.get("category"),
            )
        )
        return json.dumps(result.model_dump(), default=str)
    if name == "review_retrieval":
        result = await _review_retrieval(
            ReviewRetrievalInput(
                tenant_id=state.tenant_id,
                session_id=state.session_id,
                query=tool_input["query"],
                top_k=tool_input.get("top_k", 5),
                min_freshness_score=tool_input.get("min_freshness_score", 0.3),
            )
        )
        return json.dumps(result.model_dump(), default=str)
    return json.dumps({"error": f"Unknown tool: {name!r}"})


# --------------------------------------------------------------------------- #
# Langfuse tracing (optional)
# --------------------------------------------------------------------------- #

try:
    from langfuse.decorators import observe as _observe
except ImportError:  # pragma: no cover
    def _observe(func=None, **_):  # type: ignore[misc]
        return func if func is not None else (lambda f: f)


# --------------------------------------------------------------------------- #
# LLM node — agentic tool-use loop
# --------------------------------------------------------------------------- #

@_observe()
async def llm_node(state: AgentState) -> dict:
    """Call the LLM (with tools) and execute any tool calls before returning."""
    client = AsyncAnthropic()
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    # Build Anthropic API message list (raw format supports tool_use blocks).
    api_messages: list[dict] = [
        {"role": m.role, "content": m.content} for m in state.messages
    ]

    # Agentic loop — continue until the model stops requesting tool calls.
    while True:
        response = await client.messages.create(
            model=model,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=api_messages,
            tools=TOOLS,
        )

        if response.stop_reason == "end_turn":
            # Extract text from first text block.
            reply_text = next(
                (b.text for b in response.content if hasattr(b, "text")), ""
            )
            logger.debug("LLM reply for session=%s: %s", state.session_id, reply_text[:80])
            return {"messages": [Message(role="assistant", content=reply_text)]}

        if response.stop_reason == "tool_use":
            # Append assistant's tool-use turn to the running conversation.
            api_messages.append({"role": "assistant", "content": response.content})

            # Execute each requested tool in parallel (sequential for Phase 0).
            tool_results = []
            for block in response.content:
                if block.type == "tool_use":
                    result_str = await _execute_tool(block.name, block.input, state)
                    tool_results.append(
                        {
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result_str,
                        }
                    )

            # Feed results back as a user turn and loop.
            api_messages.append({"role": "user", "content": tool_results})
            continue

        # Unexpected stop_reason — extract whatever text is available.
        reply_text = next(
            (b.text for b in response.content if hasattr(b, "text")), str(response.content)
        )
        return {"messages": [Message(role="assistant", content=reply_text)]}
