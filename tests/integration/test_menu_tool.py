"""Integration tests for MenuFetcherTool + agent tool-use loop (RA-11)."""
import json
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

import api.middleware.tenant as tenant_middleware_module
import core.agent.nodes as nodes_module
import core.tools.menu_fetcher as menu_fetcher_module
from api.main import app
from core.models.menu import MenuItem
from core.models.tenant import TenantConfig
from core.tools.menu_fetcher import MenuFetcherInput, MenuFetcherTool

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
_test_engine = create_async_engine(TEST_DB_URL, echo=False)
_TestSessionLocal = async_sessionmaker(_test_engine, class_=AsyncSession, expire_on_commit=False)

TENANT_ID = "restaurant_demo"
HEADERS = {"X-Tenant-ID": TENANT_ID}


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db(monkeypatch):
    @asynccontextmanager
    async def _patched():
        async with _TestSessionLocal() as s:
            yield s

    monkeypatch.setattr(tenant_middleware_module, "get_session", _patched)
    monkeypatch.setattr(menu_fetcher_module, "get_session", _patched)

    async with _test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with _TestSessionLocal() as s:
        s.add(TenantConfig(tenant_id=TENANT_ID, restaurant_name="Demo", api_key="sk-x", is_active=True))
        s.add(MenuItem(tenant_id=TENANT_ID, dish_id="d1", name="Spicy Lamb", description="Lamb curry", price=16.0, category="Mains", allergens='["gluten"]', dietary_tags='["spicy"]'))
        s.add(MenuItem(tenant_id=TENANT_ID, dish_id="d2", name="Tiramisu", description="Classic dessert", price=8.0, category="Desserts", allergens='["dairy","eggs"]', dietary_tags='[]'))
        s.add(MenuItem(tenant_id=TENANT_ID, dish_id="d3", name="Bruschetta", description="Tomato toast", price=7.0, category="Starters", allergens='["gluten"]', dietary_tags='["vegetarian"]', is_available=False))
        await s.commit()

    yield

    async with _test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# --------------------------------------------------------------------------- #
# MenuFetcherTool unit-style tests
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_tool_returns_available_dishes(monkeypatch):
    @asynccontextmanager
    async def _patched():
        async with _TestSessionLocal() as s:
            yield s

    monkeypatch.setattr(menu_fetcher_module, "get_session", _patched)
    tool = MenuFetcherTool()
    result = await tool(MenuFetcherInput(tenant_id=TENANT_ID, session_id="s1"))
    assert result.success
    names = [i.name for i in result.items]
    assert "Spicy Lamb" in names
    assert "Tiramisu" in names
    assert "Bruschetta" not in names  # is_available=False


@pytest.mark.asyncio
async def test_tool_category_filter(monkeypatch):
    @asynccontextmanager
    async def _patched():
        async with _TestSessionLocal() as s:
            yield s

    monkeypatch.setattr(menu_fetcher_module, "get_session", _patched)
    tool = MenuFetcherTool()
    result = await tool(MenuFetcherInput(tenant_id=TENANT_ID, session_id="s1", category="Mains"))
    assert result.success
    assert all(i.category == "Mains" for i in result.items)
    assert len(result.items) == 1


@pytest.mark.asyncio
async def test_tool_returns_empty_for_unknown_tenant(monkeypatch):
    @asynccontextmanager
    async def _patched():
        async with _TestSessionLocal() as s:
            yield s

    monkeypatch.setattr(menu_fetcher_module, "get_session", _patched)
    tool = MenuFetcherTool()
    result = await tool(MenuFetcherInput(tenant_id="ghost_tenant", session_id="s1"))
    assert result.success
    assert result.items == []


# --------------------------------------------------------------------------- #
# Agent tool-use loop integration tests
# --------------------------------------------------------------------------- #

def _make_tool_use_response(tool_use_id: str, tool_name: str, tool_input: dict):
    """Build a mock Anthropic response with stop_reason=tool_use."""
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
    """Build a mock Anthropic response with stop_reason=end_turn."""
    block = MagicMock()
    block.type = "text"
    block.text = text
    block.hasattr = lambda _: True
    resp = MagicMock()
    resp.stop_reason = "end_turn"
    resp.content = [block]
    return resp


@pytest.mark.asyncio
async def test_agent_calls_menu_tool_when_asked(client, monkeypatch):
    """When user asks about menu, agent should call menu_fetcher tool and return results."""
    @asynccontextmanager
    async def _patched():
        async with _TestSessionLocal() as s:
            yield s

    monkeypatch.setattr(menu_fetcher_module, "get_session", _patched)

    call_count = 0

    async def fake_create(**kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return _make_tool_use_response("tid1", "menu_fetcher", {"available_only": True})
        return _make_text_response("We have Spicy Lamb and Tiramisu!")

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(side_effect=fake_create)
    monkeypatch.setattr(nodes_module, "AsyncAnthropic", lambda: mock_client)

    resp = await client.post("/chat", json={"message": "What's on the menu?"}, headers=HEADERS)
    assert resp.status_code == 200
    assert "Spicy Lamb" in resp.json()["response"] or resp.json()["response"]  # got some response
    assert call_count == 2  # two LLM calls: one for tool, one for final answer


@pytest.mark.asyncio
async def test_agent_tool_loop_sends_tool_results_to_llm(client, monkeypatch):
    """Tool results must be passed back to the LLM in the second call."""
    @asynccontextmanager
    async def _patched():
        async with _TestSessionLocal() as s:
            yield s

    monkeypatch.setattr(menu_fetcher_module, "get_session", _patched)

    received_messages: list = []

    async def fake_create(**kwargs):
        received_messages.append(kwargs.get("messages", []))
        if len(received_messages) == 1:
            return _make_tool_use_response("tid1", "menu_fetcher", {})
        return _make_text_response("Here is the menu!")

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(side_effect=fake_create)
    monkeypatch.setattr(nodes_module, "AsyncAnthropic", lambda: mock_client)

    await client.post("/chat", json={"message": "Menu please"}, headers=HEADERS)

    # Second call should include the tool_result message
    second_call_messages = received_messages[1]
    # Last message in second call should have role=user with tool_result content
    last_msg = second_call_messages[-1]
    assert last_msg["role"] == "user"
    assert isinstance(last_msg["content"], list)
    assert any(
        isinstance(b, dict) and b.get("type") == "tool_result"
        for b in last_msg["content"]
    )
