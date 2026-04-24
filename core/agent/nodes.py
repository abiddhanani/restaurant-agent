"""LangGraph node implementations — domain-agnostic catalog agent."""
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
from core.tools.dish_recommender import RecommenderInput, RecommenderTool
from core.tools.menu_fetcher import CatalogFetcherInput, CatalogFetcherTool
from core.tools.review_retrieval import ReviewRetrievalInput, ReviewRetrievalTool

# A2A client with domain-expert connector registered
_a2a_client = A2AClient()
_a2a_client.register(CuisineExpertConnector())

_DOMAIN_A2A_TIMEOUT = 5.0  # seconds

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "You are a helpful assistant. "
    "You help customers discover products and services they'll love based on the catalog and their preferences. "
    "Be warm, concise, and specific — always ground recommendations in real catalog items. "
    "Use the catalog_fetcher tool whenever the user asks about what's available, specific items, or categories."
)

# --------------------------------------------------------------------------- #
# Anthropic tool definitions
# --------------------------------------------------------------------------- #

TOOLS = [
    {
        "name": "catalog_fetcher",
        "description": (
            "Fetch available catalog items. "
            "Use when the user asks about what's available, specific items, prices, or categories."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "available_only": {
                    "type": "boolean",
                    "description": "Only return currently available items (default: true)",
                },
                "category": {
                    "type": "string",
                    "description": "Optional category filter (e.g. 'Mains', 'Services', 'Plans')",
                },
            },
        },
    },
    {
        "name": "review_retrieval",
        "description": (
            "Retrieve relevant customer review snippets from the vector store. "
            "Use when the user asks about quality, experience, what people say, or specific item feedback."
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
                    "description": "Minimum freshness score 0-1 (default: 0.3)",
                },
            },
            "required": ["query"],
        },
    },
    {
        "name": "get_domain_context",
        "description": (
            "Get background context for a domain, style, or product category. "
            "Use when the user asks about origins, tradition, or cultural context."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "context_type": {
                    "type": "string",
                    "description": "The domain/category to look up (e.g. 'Italian cuisine', 'balayage technique')",
                },
            },
            "required": ["context_type"],
        },
    },
    {
        "name": "recommender",
        "description": (
            "Recommend items by cross-referencing the catalog with the user's preference profile and reviews. "
            "Use when the user asks for recommendations, suggestions, or what they should choose. "
            "Always respects hard-stop constraints — safe to call even with restrictions."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "User's preference description (e.g. 'spicy food, no gluten')",
                },
                "hard_stops": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Hard-stop constraints (e.g. ['gluten', 'dairy'])",
                },
                "positive_signals": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Positive preference signals (e.g. ['spicy', 'umami'])",
                },
                "negative_signals": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Negative preference signals (e.g. ['cilantro', 'sweet'])",
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

_recommender = RecommenderTool()
_catalog_fetcher = CatalogFetcherTool()
_review_retrieval = ReviewRetrievalTool()


async def _execute_tool(name: str, tool_input: dict[str, Any], state: AgentState) -> str:
    """Dispatch a tool call and return the result as a JSON string."""
    # Layer 2: tool-execution guardrail (hard-stop checker + catalog grounding)
    profile = state.customer_profile
    hard_stops = profile.hard_stops if profile else []
    guardrail_result = await _guardrail_pipeline.check_tool_execution(
        tool_name=name,
        tool_input=tool_input,
        hard_stops=hard_stops,
        catalog_item_names=[],  # populated per-tool below when item_name is known
    )
    if not guardrail_result.passed:
        return json.dumps({"error": guardrail_result.reason, "blocked": True})

    if name == "catalog_fetcher":
        result = await _catalog_fetcher(
            CatalogFetcherInput(
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
    if name == "recommender":
        profile = state.customer_profile
        result = await _recommender(
            RecommenderInput(
                tenant_id=state.tenant_id,
                session_id=state.session_id,
                query=tool_input.get("query", ""),
                hard_stops=tool_input.get("hard_stops", profile.hard_stops if profile else []),
                positive_signals=tool_input.get("positive_signals", profile.positive_signals if profile else []),
                negative_signals=tool_input.get("negative_signals", profile.negative_signals if profile else []),
                top_n=tool_input.get("top_n", 3),
            )
        )
        return json.dumps(result.model_dump(), default=str)
    if name == "get_domain_context":
        context_type = tool_input.get("context_type", "unknown")
        try:
            response = await asyncio.wait_for(
                _a2a_client.dispatch(
                    agent_id="cuisine-expert-v1",
                    capability="get_cuisine_info",
                    payload={"cuisine_type": context_type},
                ),
                timeout=_DOMAIN_A2A_TIMEOUT,
            )
            if response.success:
                return json.dumps(response.data, default=str)
        except (asyncio.TimeoutError, Exception):
            pass
        return json.dumps({"context_type": context_type, "info": "Context info unavailable"})
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

@_observe(name="llm_node")
async def llm_node(state: AgentState) -> dict:
    """Call the LLM (with tools) and execute any tool calls before returning."""
    try:
        from langfuse.decorators import langfuse_context
        langfuse_context.update_current_observation(
            session_id=state.session_id,
            metadata={"tenant_id": state.tenant_id, "model": os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")},
        )
    except Exception:
        pass

    client = AsyncAnthropic()
    model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514")

    # Layer 1: input guardrail — check the latest user message
    latest_user_msg = next(
        (m.content for m in reversed(state.messages) if m.role == "user"), ""
    )
    guardrail_result = await _guardrail_pipeline.check_input(latest_user_msg, state.tenant_id)
    if not guardrail_result.passed:
        return {"messages": [Message(role="assistant", content=guardrail_result.reason or "I can only help with questions about our products and services.")]}

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
            reply_text = next(
                (b.text for b in response.content if hasattr(b, "text")), ""
            )
            logger.debug("LLM reply for session=%s: %s", state.session_id, reply_text[:80])

            # Layer 3: output guardrail
            output_result = await _guardrail_pipeline.check_output(
                response=reply_text,
                retrieved_docs=[],
                catalog_item_names=[],
            )
            if not output_result.passed:
                safe_reply = "I'm sorry, I can only provide information about our catalog and services."
                return {"messages": [Message(role="assistant", content=safe_reply)]}

            return {"messages": [Message(role="assistant", content=reply_text)]}

        if response.stop_reason == "tool_use":
            api_messages.append({"role": "assistant", "content": response.content})

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

            api_messages.append({"role": "user", "content": tool_results})
            continue

        # Unexpected stop_reason — extract whatever text is available.
        reply_text = next(
            (b.text for b in response.content if hasattr(b, "text")), str(response.content)
        )
        return {"messages": [Message(role="assistant", content=reply_text)]}
