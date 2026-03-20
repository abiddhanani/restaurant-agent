"""Integration tests for the LangGraph agent / chat endpoint (RA-7)."""
from unittest.mock import AsyncMock, MagicMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

import api.middleware.tenant as tenant_middleware_module
import core.agent.nodes as nodes_module
from api.main import app
from core.models.tenant import TenantConfig

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
_test_engine = create_async_engine(TEST_DB_URL, echo=False)
_TestSessionLocal = async_sessionmaker(_test_engine, class_=AsyncSession, expire_on_commit=False)

TENANT_ID = "restaurant_demo"
HEADERS = {"X-Tenant-ID": TENANT_ID}


def _mock_llm(monkeypatch, reply: str = "I recommend the pasta!"):
    """Patch AsyncAnthropic so no real API calls are made."""
    mock_response = MagicMock()
    mock_response.content = [MagicMock(text=reply)]
    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)
    monkeypatch.setattr(nodes_module, "AsyncAnthropic", lambda: mock_client)
    return mock_client


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db(monkeypatch):
    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _patched_get_session():
        async with _TestSessionLocal() as s:
            yield s

    monkeypatch.setattr(tenant_middleware_module, "get_session", _patched_get_session)

    async with _test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with _TestSessionLocal() as session:
        session.add(
            TenantConfig(
                tenant_id=TENANT_ID,
                restaurant_name="Demo Restaurant",
                api_key="sk-demo-key",
                is_active=True,
            )
        )
        await session.commit()

    yield

    async with _test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_first_message_returns_200_with_session_id(client, monkeypatch):
    _mock_llm(monkeypatch)
    resp = await client.post("/chat", json={"message": "Hello"}, headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert "session_id" in data
    assert "response" in data
    assert data["session_id"]  # non-empty


@pytest.mark.asyncio
async def test_response_contains_llm_text(client, monkeypatch):
    _mock_llm(monkeypatch, reply="Try the carbonara!")
    resp = await client.post("/chat", json={"message": "What should I eat?"}, headers=HEADERS)
    assert resp.json()["response"] == "Try the carbonara!"


@pytest.mark.asyncio
async def test_second_message_reuses_session(client, monkeypatch):
    """Same session_id must be returned on follow-up messages."""
    _mock_llm(monkeypatch)
    r1 = await client.post("/chat", json={"message": "Hi"}, headers=HEADERS)
    session_id = r1.json()["session_id"]

    r2 = await client.post(
        "/chat",
        json={"message": "What do you recommend?", "session_id": session_id},
        headers=HEADERS,
    )
    assert r2.status_code == 200
    assert r2.json()["session_id"] == session_id


@pytest.mark.asyncio
async def test_multi_turn_history_passed_to_llm(client, monkeypatch):
    """LLM must receive the full conversation history on the second turn."""
    captured_messages: list = []

    async def fake_create(**kwargs):
        captured_messages.extend(kwargs.get("messages", []))
        mock = MagicMock()
        mock.content = [MagicMock(text="Got it!")]
        return mock

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(side_effect=fake_create)
    monkeypatch.setattr(nodes_module, "AsyncAnthropic", lambda: mock_client)

    r1 = await client.post("/chat", json={"message": "I love spicy food"}, headers=HEADERS)
    session_id = r1.json()["session_id"]

    await client.post(
        "/chat",
        json={"message": "What do you recommend?", "session_id": session_id},
        headers=HEADERS,
    )

    # Second call should have included prior messages
    user_contents = [m["content"] for m in captured_messages if m["role"] == "user"]
    assert "I love spicy food" in user_contents
    assert "What do you recommend?" in user_contents


@pytest.mark.asyncio
async def test_unknown_session_id_creates_new_session(client, monkeypatch):
    _mock_llm(monkeypatch)
    resp = await client.post(
        "/chat",
        json={"message": "Hello", "session_id": "nonexistent-session-id"},
        headers=HEADERS,
    )
    assert resp.status_code == 200
    # A new session should have been created
    assert resp.json()["session_id"] != "nonexistent-session-id"


@pytest.mark.asyncio
async def test_three_turn_conversation(client, monkeypatch):
    _mock_llm(monkeypatch, reply="Happy to help!")
    r1 = await client.post("/chat", json={"message": "Hi"}, headers=HEADERS)
    sid = r1.json()["session_id"]

    r2 = await client.post("/chat", json={"message": "Any pasta?", "session_id": sid}, headers=HEADERS)
    assert r2.status_code == 200

    r3 = await client.post("/chat", json={"message": "Thanks", "session_id": sid}, headers=HEADERS)
    assert r3.status_code == 200
    assert r3.json()["session_id"] == sid


@pytest.mark.asyncio
async def test_missing_tenant_header_still_returns_400(client, monkeypatch):
    _mock_llm(monkeypatch)
    resp = await client.post("/chat", json={"message": "Hello"})
    assert resp.status_code == 400
