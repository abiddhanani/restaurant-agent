"""LangGraph node implementations for the restaurant agent."""
import asyncio
import json
import logging
import os
from typing import Any

from anthropic import AsyncAnthropic

from a2a.agents.cuisine_expert import CuisineExpertConnector
from a2a.client import A2AClient
from core.agent.state import AgentState
from core.guardrails.pipeline import GuardrailPipeline
from core.models.session import Message

_guardrail_pipeline = GuardrailPipeline()
from core.tools.dish_recommender import DishRecommenderInput, DishRecommenderTool
from core.tools.menu_fetcher import MenuFetcherInput, MenuFetcherTool
from core.tools.review_retrieval import ReviewRetrievalInput, ReviewRetrievalTool

# A2A client with cuisine-expert connector registered
_a2a_client = A2AClient()
_a2a_client.register(CuisineExpertConnector())

_CUISINE_A2A_TIMEOUT = 5.0  # seconds

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
    {
        "name": "get_cuisine_info",
        "description": (
            "Get cultural background, history, and key ingredients for a cuisine type. "
            "Use when the user asks about the origins, tradition, or cultural context of a cuisine."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cuisine_type": {
                    "type": "string",
                    "description": "The cuisine to look up (e.g. 'Italian', 'Indian', 'Japanese')",
                },
            },
            "required": ["cuisine_type"],
        },
    },
    {
        "name": "dish_recommender",
        "description": (
            "Recommend dishes by cross-referencing the menu with the user's taste profile and reviews. "
            "Use when the user asks for recommendations, suggestions, or what they should order. "
            "Always respects allergen hard stops — safe to call even with dietary restrictions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "User's preference description (e.g. 'spicy food, no gluten')",
                },
                "allergen_stops": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Hard-stop allergens (e.g. ['gluten', 'dairy'])",
                },
                "positive_signals": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Positive taste signals (e.g. ['spicy', 'umami'])",
                },
                "negative_signals": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Negative taste signals (e.g. ['cilantro', 'sweet'])",
                },
                "top_n": {
                    "type": "integer",
                    "description": "Number of recommendations to return (default: 3)",
                },
            },
            "required": ["query"],
        },
    },
]

# --------------------------------------------------------------------------- #
# Tool executor
# --------------------------------------------------------------------------- #

_dish_recommender = DishRecommenderTool()
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
    if name == "dish_recommender":
        profile = state.taste_profile
        result = await _dish_recommender(
            DishRecommenderInput(
                tenant_id=state.tenant_id,
                session_id=state.session_id,
                query=tool_input.get("query", ""),
                allergen_stops=tool_input.get("allergen_stops", profile.dietary_hard_stops if profile else []),
                positive_signals=tool_input.get("positive_signals", profile.positive_signals if profile else []),
                negative_signals=tool_input.get("negative_signals", profile.negative_signals if profile else []),
                top_n=tool_input.get("top_n", 3),
            )
        )
        return json.dumps(result.model_dump(), default=str)
    if name == "get_cuisine_info":
        cuisine_type = tool_input.get("cuisine_type", "unknown")
        try:
            response = await asyncio.wait_for(
                _a2a_client.dispatch(
                    agent_id="cuisine-expert-v1",
                    capability="get_cuisine_info",
                    payload={"cuisine_type": cuisine_type},
                ),
                timeout=_CUISINE_A2A_TIMEOUT,
            )
            if response.success:
                return json.dumps(response.data, default=str)
        except (asyncio.TimeoutError, Exception):
            pass
        return json.dumps({"cuisine_type": cuisine_type, "info": "Cuisine info unavailable"})
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

    # Layer 1: input guardrail — check the latest user message
    latest_user_msg = next(
        (m.content for m in reversed(state.messages) if m.role == "user"), ""
    )
    guardrail_result = await _guardrail_pipeline.check_input(latest_user_msg, state.tenant_id)
    if not guardrail_result.passed:
        return {"messages": [Message(role="assistant", content=guardrail_result.reason or "I can only help with food and restaurant questions.")]}

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
