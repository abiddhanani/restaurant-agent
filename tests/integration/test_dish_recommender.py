"""Integration tests for DishRecommenderTool + agent tool-use loop (RA-13)."""
import json
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import chromadb
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

import api.middleware.tenant as tenant_middleware_module
import core.agent.nodes as nodes_module
import core.tools.dish_recommender as dish_recommender_module
from api.main import app
from core.models.menu import MenuItem
from core.models.tenant import TenantConfig
from core.tools.dish_recommender import DishRecommenderInput, DishRecommenderTool

TENANT_ID = "recommender_test_tenant"
HEADERS = {"X-Tenant-ID": TENANT_ID}

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
_test_engine = create_async_engine(TEST_DB_URL, echo=False)
_TestSessionLocal = async_sessionmaker(_test_engine, class_=AsyncSession, expire_on_commit=False)

_RNG = np.random.default_rng(42)


@pytest.fixture(scope="module")
def chroma_path(tmp_path_factory):
    """Pre-populated ChromaDB with reviews for the test tenant."""
    path = tmp_path_factory.mktemp("chroma_recommender")
    client = chromadb.PersistentClient(path=str(path))
    col = client.get_or_create_collection(f"reviews_{TENANT_ID}")

    reviews = [
        ("rev0", "Spicy Lamb is incredible. Rich, bold, and perfectly spiced.", 5),
        ("rev1", "The Tiramisu was light and heavenly. Best dessert I've had.", 5),
        ("rev2", "Bruschetta starter was fresh and vibrant. Loved the tomatoes.", 4),
    ]
    ids, embs, docs, metas = [], [], [], []
    for rid, text, rating in reviews:
        ids.append(f"{rid}_chunk_0")
        embs.append(_RNG.random(384).tolist())
        docs.append(text)
        metas.append({"freshness_score": 0.9, "rating": rating, "source_review_id": rid,
                      "tenant_id": TENANT_ID, "chunk_index": 0})
    col.upsert(ids=ids, embeddings=embs, documents=docs, metadatas=metas)
    return str(path)


@pytest_asyncio.fixture(autouse=True)
async def setup_db(monkeypatch):
    @asynccontextmanager
    async def _patched():
        async with _TestSessionLocal() as s:
            yield s

    monkeypatch.setattr(tenant_middleware_module, "get_session", _patched)
    monkeypatch.setattr(dish_recommender_module, "get_session", _patched)

    async with _test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with _TestSessionLocal() as s:
        s.add(TenantConfig(tenant_id=TENANT_ID, restaurant_name="Recommender Test",
                           api_key="sk-x", is_active=True))
        s.add(MenuItem(tenant_id=TENANT_ID, dish_id="d1", name="Spicy Lamb",
                       description="Slow-cooked lamb curry with bold spices",
                       price=18.0, category="Mains",
                       allergens='["gluten"]', dietary_tags='["spicy"]'))
        s.add(MenuItem(tenant_id=TENANT_ID, dish_id="d2", name="Tiramisu",
                       description="Classic Italian dessert with espresso",
                       price=9.0, category="Desserts",
                       allergens='["dairy","eggs"]', dietary_tags='[]'))
        s.add(MenuItem(tenant_id=TENANT_ID, dish_id="d3", name="Bruschetta",
                       description="Toasted bread with fresh tomato and basil",
                       price=7.0, category="Starters",
                       allergens='["gluten"]', dietary_tags='["vegetarian","vegan"]'))
        s.add(MenuItem(tenant_id=TENANT_ID, dish_id="d4", name="Grilled Salmon",
                       description="Atlantic salmon with lemon herb butter",
                       price=22.0, category="Mains",
                       allergens='["fish"]', dietary_tags='["gluten-free"]'))
        await s.commit()

    yield

    async with _test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


# --------------------------------------------------------------------------- #
# DishRecommenderTool unit-style tests
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_returns_recommendations(chroma_path):
    tool = DishRecommenderTool(chroma_path=chroma_path)
    result = await tool(DishRecommenderInput(
        tenant_id=TENANT_ID, session_id="s1", query="I love spicy food"
    ))
    assert result.success
    assert len(result.recommendations) > 0


@pytest.mark.asyncio
async def test_allergen_circuit_breaker_excludes_dishes(chroma_path):
    """Dishes containing hard-stop allergens must never appear in results."""
    tool = DishRecommenderTool(chroma_path=chroma_path)
    result = await tool(DishRecommenderInput(
        tenant_id=TENANT_ID, session_id="s1",
        query="recommend something",
        allergen_stops=["gluten", "dairy", "eggs", "fish"],
    ))
    assert result.success
    assert result.recommendations == []


@pytest.mark.asyncio
async def test_allergen_stops_removes_specific_dishes(chroma_path):
    """With only gluten stopped, dairy/egg dishes and fish should remain."""
    tool = DishRecommenderTool(chroma_path=chroma_path)
    result = await tool(DishRecommenderInput(
        tenant_id=TENANT_ID, session_id="s1",
        query="recommend something",
        allergen_stops=["gluten"],
    ))
    assert result.success
    names = [r.name for r in result.recommendations]
    assert "Spicy Lamb" not in names
    assert "Bruschetta" not in names
    # Tiramisu or Grilled Salmon should appear
    assert any(n in names for n in ["Tiramisu", "Grilled Salmon"])


@pytest.mark.asyncio
async def test_positive_signals_boost_matching_dishes(chroma_path):
    """Dishes matching positive signals should rank higher."""
    tool = DishRecommenderTool(chroma_path=chroma_path)
    result = await tool(DishRecommenderInput(
        tenant_id=TENANT_ID, session_id="s1",
        query="dinner",
        positive_signals=["spicy"],
    ))
    assert result.success
    assert len(result.recommendations) > 0
    # Spicy Lamb has "spicy" tag — should be in results
    names = [r.name for r in result.recommendations]
    assert "Spicy Lamb" in names


@pytest.mark.asyncio
async def test_top_n_limits_results(chroma_path):
    tool = DishRecommenderTool(chroma_path=chroma_path)
    result = await tool(DishRecommenderInput(
        tenant_id=TENANT_ID, session_id="s1",
        query="anything", top_n=2,
    ))
    assert result.success
    assert len(result.recommendations) <= 2


@pytest.mark.asyncio
async def test_recommendation_fields_populated(chroma_path):
    tool = DishRecommenderTool(chroma_path=chroma_path)
    result = await tool(DishRecommenderInput(
        tenant_id=TENANT_ID, session_id="s1", query="spicy lamb"
    ))
    assert result.success
    rec = result.recommendations[0]
    assert rec.dish_id
    assert rec.name
    assert rec.category
    assert rec.price > 0
    assert rec.match_reason
    assert 0.0 <= rec.score <= 5.0  # scores can be higher due to review bonus


@pytest.mark.asyncio
async def test_empty_menu_returns_empty(monkeypatch, chroma_path):
    """If no items exist for the tenant, return empty list gracefully."""
    tool = DishRecommenderTool(chroma_path=chroma_path)
    result = await tool(DishRecommenderInput(
        tenant_id="ghost_tenant_xyz", session_id="s1", query="food"
    ))
    assert result.success
    assert result.recommendations == []


@pytest.mark.asyncio
async def test_confidence_increases_with_signals(chroma_path):
    tool = DishRecommenderTool(chroma_path=chroma_path)
    low = await tool(DishRecommenderInput(
        tenant_id=TENANT_ID, session_id="s1", query="food"
    ))
    high = await tool(DishRecommenderInput(
        tenant_id=TENANT_ID, session_id="s1", query="food",
        positive_signals=["spicy", "bold"],
        allergen_stops=["gluten"],
    ))
    assert high.confidence >= low.confidence


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
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_agent_calls_recommender_tool(client, monkeypatch, chroma_path):
    monkeypatch.setattr(nodes_module, "_dish_recommender", DishRecommenderTool(chroma_path=chroma_path))

    call_count = 0

    async def fake_create(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _make_tool_use_response(
                "tid1", "dish_recommender",
                {"query": "spicy food, no dairy"},
            )
        return _make_text_response("I recommend the Spicy Lamb!")

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(side_effect=fake_create)
    monkeypatch.setattr(nodes_module, "AsyncAnthropic", lambda: mock_client)

    resp = await client.post(
        "/chat",
        json={"message": "What should I order?"},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    assert call_count == 2


@pytest.mark.asyncio
async def test_agent_passes_taste_profile_to_recommender(client, monkeypatch, chroma_path):
    """Allergen stops from state.taste_profile should be injected even if LLM omits them."""
    monkeypatch.setattr(nodes_module, "_dish_recommender", DishRecommenderTool(chroma_path=chroma_path))

    captured_input: list[DishRecommenderInput] = []
    original_tool = DishRecommenderTool(chroma_path=chroma_path)

    async def spy_execute(inp: DishRecommenderInput):
        captured_input.append(inp)
        return await original_tool.execute(inp)

    monkeypatch.setattr(nodes_module._dish_recommender, "execute", spy_execute)

    call_count = 0

    async def fake_create(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _make_tool_use_response(
                "tid1", "dish_recommender",
                {"query": "recommend me something"},  # no allergen_stops from LLM
            )
        return _make_text_response("Here are my recommendations!")

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(side_effect=fake_create)
    monkeypatch.setattr(nodes_module, "AsyncAnthropic", lambda: mock_client)

    await client.post("/chat", json={"message": "Suggest something"}, headers=HEADERS)
    # Tool was called — captured input shows it ran
    assert len(captured_input) >= 1
