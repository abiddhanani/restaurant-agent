"""Integration tests for TenantMiddleware (RA-2 acceptance criteria)."""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlmodel import SQLModel
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel.ext.asyncio.session import AsyncSession

import api.middleware.tenant as tenant_middleware_module
from api.main import app
from core.models.tenant import TenantConfig

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

_test_engine = create_async_engine(TEST_DB_URL, echo=False)
_TestSessionLocal = async_sessionmaker(_test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db(monkeypatch):
    """Create schema and seed a demo tenant; patch app's session factory."""
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
                tenant_id="restaurant_demo",
                restaurant_name="Demo Restaurant",
                api_key="sk-demo-key",
                is_active=True,
            )
        )
        session.add(
            TenantConfig(
                tenant_id="inactive_tenant",
                restaurant_name="Closed Restaurant",
                api_key="sk-inactive-key",
                is_active=False,
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


@pytest.mark.asyncio
async def test_missing_header_returns_400(client):
    """AC1: Requests without X-Tenant-ID are rejected with 400."""
    resp = await client.post("/chat", json={"message": "hello"})
    assert resp.status_code == 400
    assert "X-Tenant-ID" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_invalid_tenant_returns_404(client):
    """AC2: Unknown tenant ID returns 404."""
    resp = await client.post(
        "/chat",
        json={"message": "hello"},
        headers={"X-Tenant-ID": "unknown_tenant"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_inactive_tenant_returns_404(client):
    """AC2: Inactive tenant returns 404."""
    resp = await client.post(
        "/chat",
        json={"message": "hello"},
        headers={"X-Tenant-ID": "inactive_tenant"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_valid_tenant_passes_through(client, monkeypatch):
    """AC3: Valid active tenant proceeds past middleware (chat returns 200)."""
    from unittest.mock import AsyncMock, MagicMock
    import core.agent.nodes as nodes_module

    mock_response = MagicMock()
    mock_response.content = [MagicMock(text="Hello! How can I help?")]

    mock_client = AsyncMock()
    mock_client.messages.create = AsyncMock(return_value=mock_response)
    monkeypatch.setattr(nodes_module, "AsyncAnthropic", lambda: mock_client)

    resp = await client.post(
        "/chat",
        json={"message": "hello"},
        headers={"X-Tenant-ID": "restaurant_demo"},
    )
    assert resp.status_code == 200  # middleware passed, agent responded


@pytest.mark.asyncio
async def test_health_exempt_from_tenant_check(client):
    """AC4: /health endpoint requires no X-Tenant-ID header."""
    resp = await client.get("/health")
    assert resp.status_code == 200
