"""Integration tests for ReviewRetrievalTool + agent tool-use loop (RA-12)."""
import json
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import chromadb
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sentence_transformers import SentenceTransformer
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

import api.middleware.tenant as tenant_middleware_module
import core.agent.nodes as nodes_module
from api.main import app
from core.models.tenant import TenantConfig
from core.tools.review_retrieval import ReviewRetrievalInput, ReviewRetrievalTool

TENANT_ID = "review_test_tenant"
HEADERS = {"X-Tenant-ID": TENANT_ID}

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
_test_engine = create_async_engine(TEST_DB_URL, echo=False)
_TestSessionLocal = async_sessionmaker(_test_engine, class_=AsyncSession, expire_on_commit=False)

_MODEL = SentenceTransformer("all-MiniLM-L6-v2")

SAMPLE_REVIEWS = [
    "The pasta carbonara is absolutely divine. Rich, creamy, and perfectly al dente.",
    "Great service and warm atmosphere. Staff were very attentive and friendly.",
    "The tiramisu was the highlight of my evening. Light and full of espresso flavour.",
    "Lamb shank melted off the bone. Outstanding slow-cooked depth of flavour.",
    "Excellent wine list. The sommelier's recommendations were spot on.",
]


@pytest.fixture(scope="module")
def chroma_path(tmp_path_factory):
    path = tmp_path_factory.mktemp("chroma_review_tool")
    client = chromadb.PersistentClient(path=str(path))
    collection = client.get_or_create_collection(f"reviews_{TENANT_ID}")

    ids, embeddings, documents, metadatas = [], [], [], []
    for idx, text in enumerate(SAMPLE_REVIEWS):
        chunk_id = f"rev_{idx}_chunk_0"
        emb = _MODEL.encode(text).tolist()
        ids.append(chunk_id)
        embeddings.append(emb)
        documents.append(text)
        metadatas.append({
            "freshness_score": 0.9,
            "rating": 5,
            "source_review_id": f"rev_{idx}",
            "tenant_id": TENANT_ID,
            "chunk_index": 0,
        })

    collection.upsert(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
    return str(path)


@pytest.fixture(scope="module")
def tool(chroma_path):
    return ReviewRetrievalTool(chroma_path=chroma_path)


# --------------------------------------------------------------------------- #
# ReviewRetrievalTool unit-style tests
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_tool_returns_snippets(tool):
    result = await tool(ReviewRetrievalInput(
        tenant_id=TENANT_ID, session_id="s1", query="pasta carbonara"
    ))
    assert result.success
    assert len(result.snippets) > 0


@pytest.mark.asyncio
async def test_top_k_limits_results(tool):
    result = await tool(ReviewRetrievalInput(
        tenant_id=TENANT_ID, session_id="s1", query="food quality", top_k=2
    ))
    assert result.success
    assert len(result.snippets) <= 2


@pytest.mark.asyncio
async def test_snippet_fields_populated(tool):
    result = await tool(ReviewRetrievalInput(
        tenant_id=TENANT_ID, session_id="s1", query="dessert tiramisu"
    ))
    assert result.success
    snippet = result.snippets[0]
    assert snippet.text
    assert snippet.source == "google_places"
    assert 0.0 <= snippet.rating <= 5.0
    assert 0.0 <= snippet.freshness_score <= 1.0
    assert 0.0 <= snippet.relevance_score <= 1.0


@pytest.mark.asyncio
async def test_min_freshness_filters_low_freshness(chroma_path, tmp_path):
    """Chunks with freshness_score below min_freshness_score are excluded."""
    # Add a stale review to a separate path to avoid polluting shared fixture
    stale_path = tmp_path / "stale_chroma"
    client = chromadb.PersistentClient(path=str(stale_path))
    tenant = "stale_tenant"
    col = client.get_or_create_collection(f"reviews_{tenant}")
    emb = _MODEL.encode("stale old review text").tolist()
    col.upsert(
        ids=["stale_chunk"],
        embeddings=[emb],
        documents=["stale old review text"],
        metadatas=[{"freshness_score": 0.05, "rating": 3, "source_review_id": "r0", "tenant_id": tenant, "chunk_index": 0}],
    )

    stale_tool = ReviewRetrievalTool(chroma_path=str(stale_path))
    result = await stale_tool(ReviewRetrievalInput(
        tenant_id=tenant, session_id="s1", query="old review", min_freshness_score=0.5
    ))
    assert result.success
    assert result.snippets == []


@pytest.mark.asyncio
async def test_unknown_tenant_returns_empty(tool):
    result = await tool(ReviewRetrievalInput(
        tenant_id="ghost_tenant_xyz", session_id="s1", query="anything"
    ))
    assert result.success
    assert result.snippets == []


@pytest.mark.asyncio
async def test_relevance_scores_between_0_and_1(tool):
    result = await tool(ReviewRetrievalInput(
        tenant_id=TENANT_ID, session_id="s1", query="wine service"
    ))
    assert result.success
    for snippet in result.snippets:
        assert 0.0 <= snippet.relevance_score <= 1.0


# --------------------------------------------------------------------------- #
# Agent tool-use loop integration tests
# --------------------------------------------------------------------------- #

def _make_tool_use_response(tool_use_id: str, tool_name: str, tool_input: dict):
    block = MagicMock()
    block.type = "tool_use"
    block.id = tool_use_id
    block.name = tool_name
    block.input = tool_input
    resp = MagicMock()
    resp.stop_reason = "tool_use"
    resp.content = [block]
    return resp


def _make_text_response(text: str):
    block = MagicMock()
    block.type = "text"
    block.text = text
    resp = MagicMock()
    resp.stop_reason = "end_turn"
    resp.content = [block]
    return resp


@pytest_asyncio.fixture
async def db_with_tenant(monkeypatch):
    """Set up in-memory DB with tenant row for agent HTTP tests."""
    @asynccontextmanager
    async def _patched():
        async with _TestSessionLocal() as s:
            yield s

    monkeypatch.setattr(tenant_middleware_module, "get_session", _patched)

    async with _test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with _TestSessionLocal() as s:
        s.add(TenantConfig(tenant_id=TENANT_ID, restaurant_name="Review Test", api_key="sk-x", is_active=True))
        await s.commit()

    yield

    async with _test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_agent_calls_review_tool_when_asked(client, db_with_tenant, monkeypatch, chroma_path):
    """Agent should call review_retrieval when user asks about quality/reviews."""
    monkeypatch.setattr(nodes_module, "_review_retrieval", ReviewRetrievalTool(chroma_path=chroma_path))

    call_count = 0

    async def fake_create(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _make_tool_use_response("tid1", "review_retrieval", {"query": "food quality"})
        return _make_text_response("Customers love the pasta and desserts!")

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(side_effect=fake_create)
    monkeypatch.setattr(nodes_module, "AsyncAnthropic", lambda: mock_client)

    resp = await client.post(
        "/chat",
        json={"message": "What do customers say about the food?"},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    assert call_count == 2


@pytest.mark.asyncio
async def test_agent_tool_loop_sends_review_results_to_llm(client, db_with_tenant, monkeypatch, chroma_path):
    """Tool results from review_retrieval must be passed back to LLM as tool_result."""
    monkeypatch.setattr(nodes_module, "_review_retrieval", ReviewRetrievalTool(chroma_path=chroma_path))

    received_messages: list = []

    async def fake_create(**kwargs):
        received_messages.append(kwargs.get("messages", []))
        if len(received_messages) == 1:
            return _make_tool_use_response("tid1", "review_retrieval", {"query": "best dish"})
        return _make_text_response("Based on reviews, the pasta is highly rated!")

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(side_effect=fake_create)
    monkeypatch.setattr(nodes_module, "AsyncAnthropic", lambda: mock_client)

    await client.post("/chat", json={"message": "What's the best dish?"}, headers=HEADERS)

    second_call_messages = received_messages[1]
    last_msg = second_call_messages[-1]
    assert last_msg["role"] == "user"
    assert isinstance(last_msg["content"], list)
    assert any(
        isinstance(b, dict) and b.get("type") == "tool_result"
        for b in last_msg["content"]
    )
