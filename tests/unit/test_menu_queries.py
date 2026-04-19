"""Integration-style tests for catalog CRUD endpoints and CatalogFetcherTool."""
import json
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

import api.middleware.tenant as tenant_middleware_module
import api.routes.menu as catalog_route_module
import core.tools.menu_fetcher as catalog_fetcher_module
from api.main import app
from core.models.tenant import TenantConfig
from core.models.menu import CatalogItem
from core.tools.menu_fetcher import CatalogFetcherTool, CatalogFetcherInput

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"

_test_engine = create_async_engine(TEST_DB_URL, echo=False)
_TestSessionLocal = async_sessionmaker(_test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(autouse=True)
async def setup_test_db(monkeypatch):
    """Create schema, seed demo data, and patch session factories."""

    @asynccontextmanager
    async def _patched_get_session():
        async with _TestSessionLocal() as s:
            yield s

    monkeypatch.setattr(tenant_middleware_module, "get_session", _patched_get_session)
    monkeypatch.setattr(catalog_route_module, "get_session", _patched_get_session)
    monkeypatch.setattr(catalog_fetcher_module, "get_session", _patched_get_session)

    async with _test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with _TestSessionLocal() as session:
        session.add(
            TenantConfig(
                tenant_id="restaurant_demo",
                business_name="Demo Restaurant",
                api_key="sk-demo-key",
                is_active=True,
            )
        )
        session.add(
            TenantConfig(
                tenant_id="other_tenant",
                business_name="Other Place",
                api_key="sk-other-key",
                is_active=True,
            )
        )
        session.add(CatalogItem(
            tenant_id="restaurant_demo",
            item_id="item_001",
            name="Spicy Chicken",
            description="Hot and spicy",
            price=14.99,
            category="mains",
            constraints=json.dumps(["soy"]),
            tags=json.dumps(["spicy"]),
            is_available=True,
            attributes=json.dumps({"spice_level": 4}),
        ))
        session.add(CatalogItem(
            tenant_id="restaurant_demo",
            item_id="item_002",
            name="Mango Salad",
            description="Fresh and tangy",
            price=8.99,
            category="starters",
            constraints=json.dumps(["peanuts"]),
            tags=json.dumps(["vegan"]),
            is_available=True,
        ))
        session.add(CatalogItem(
            tenant_id="restaurant_demo",
            item_id="item_003",
            name="Off-Menu Special",
            description="Not currently available",
            price=19.99,
            category="mains",
            constraints=json.dumps([]),
            tags=json.dumps([]),
            is_available=False,
        ))
        await session.commit()

    yield

    async with _test_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_get_catalog_returns_tenant_items(client):
    """GET /catalog returns all available items for the tenant."""
    resp = await client.get("/catalog", headers={"X-Tenant-ID": "restaurant_demo"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    names = {d["name"] for d in data}
    assert "Spicy Chicken" in names
    assert "Mango Salad" in names


@pytest.mark.asyncio
async def test_get_catalog_filters_unavailable(client):
    """GET /catalog excludes is_available=False items by default."""
    resp = await client.get("/catalog", headers={"X-Tenant-ID": "restaurant_demo"})
    assert resp.status_code == 200
    names = [d["name"] for d in resp.json()]
    assert "Off-Menu Special" not in names


@pytest.mark.asyncio
async def test_get_catalog_available_only_false(client):
    """GET /catalog?available_only=false returns all items including unavailable."""
    resp = await client.get(
        "/catalog?available_only=false", headers={"X-Tenant-ID": "restaurant_demo"}
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 3


@pytest.mark.asyncio
async def test_get_catalog_wrong_tenant_returns_empty(client):
    """GET /catalog for a tenant with no items returns an empty list."""
    resp = await client.get("/catalog", headers={"X-Tenant-ID": "other_tenant"})
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_upsert_catalog_replaces_items(client):
    """POST /catalog replaces all existing items for the tenant."""
    new_items = [
        {
            "item_id": "new_001",
            "name": "New Item",
            "description": "Brand new",
            "price": 9.99,
            "category": "mains",
            "constraints": ["gluten"],
            "tags": [],
            "attributes": {},
            "is_available": True,
        }
    ]
    resp = await client.post(
        "/catalog",
        json=new_items,
        headers={"X-Tenant-ID": "restaurant_demo"},
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["name"] == "New Item"

    resp2 = await client.get(
        "/catalog?available_only=false", headers={"X-Tenant-ID": "restaurant_demo"}
    )
    assert len(resp2.json()) == 1
    assert resp2.json()[0]["item_id"] == "new_001"


@pytest.mark.asyncio
async def test_catalog_fetcher_tool_returns_available_items():
    """CatalogFetcherTool.execute() returns available items via DB."""
    tool = CatalogFetcherTool()

    @asynccontextmanager
    async def _patched_get_session():
        async with _TestSessionLocal() as s:
            yield s

    import core.tools.menu_fetcher as cfm
    original = cfm.get_session
    cfm.get_session = _patched_get_session
    try:
        result = await tool.execute(
            CatalogFetcherInput(tenant_id="restaurant_demo", session_id="test-session")
        )
        assert result.success is True
        assert len(result.items) == 2
        assert all(item.is_available for item in result.items)
    finally:
        cfm.get_session = original
