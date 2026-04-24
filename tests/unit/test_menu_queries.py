"""Integration-style tests for menu CRUD endpoints and MenuFetcherTool (RA-3)."""
import json
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

import api.middleware.tenant as tenant_middleware_module
import api.routes.menu as menu_route_module
import core.tools.menu_fetcher as menu_fetcher_module
from api.main import app
from core.models.tenant import TenantConfig
from core.models.menu import MenuItem
from core.tools.menu_fetcher import MenuFetcherTool, MenuFetcherInput

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
    monkeypatch.setattr(menu_route_module, "get_session", _patched_get_session)
    monkeypatch.setattr(menu_fetcher_module, "get_session", _patched_get_session)

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
                tenant_id="other_tenant",
                restaurant_name="Other Place",
                api_key="sk-other-key",
                is_active=True,
            )
        )
        # Seed 3 dishes for restaurant_demo
        session.add(MenuItem(
            tenant_id="restaurant_demo",
            dish_id="dish_001",
            name="Spicy Chicken",
            description="Hot and spicy",
            price=14.99,
            category="mains",
            allergens=json.dumps(["soy"]),
            dietary_tags=json.dumps(["spicy"]),
            is_available=True,
            spice_level=4,
        ))
        session.add(MenuItem(
            tenant_id="restaurant_demo",
            dish_id="dish_002",
            name="Mango Salad",
            description="Fresh and tangy",
            price=8.99,
            category="starters",
            allergens=json.dumps(["peanuts"]),
            dietary_tags=json.dumps(["vegan"]),
            is_available=True,
        ))
        session.add(MenuItem(
            tenant_id="restaurant_demo",
            dish_id="dish_003",
            name="Off-Menu Special",
            description="Not currently available",
            price=19.99,
            category="mains",
            allergens=json.dumps([]),
            dietary_tags=json.dumps([]),
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
async def test_get_menu_returns_tenant_dishes(client):
    """GET /menu/ returns all available dishes for the tenant."""
    resp = await client.get("/menu", headers={"X-Tenant-ID": "restaurant_demo"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2  # only the 2 available dishes
    names = {d["name"] for d in data}
    assert "Spicy Chicken" in names
    assert "Mango Salad" in names


@pytest.mark.asyncio
async def test_get_menu_filters_unavailable(client):
    """GET /menu/ excludes is_available=False dishes by default."""
    resp = await client.get("/menu", headers={"X-Tenant-ID": "restaurant_demo"})
    assert resp.status_code == 200
    names = [d["name"] for d in resp.json()]
    assert "Off-Menu Special" not in names


@pytest.mark.asyncio
async def test_get_menu_available_only_false(client):
    """GET /menu/?available_only=false returns all dishes including unavailable ones."""
    resp = await client.get(
        "/menu?available_only=false", headers={"X-Tenant-ID": "restaurant_demo"}
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 3


@pytest.mark.asyncio
async def test_get_menu_wrong_tenant_returns_empty(client):
    """GET /menu/ for a tenant with no dishes returns an empty list."""
    resp = await client.get("/menu", headers={"X-Tenant-ID": "other_tenant"})
    assert resp.status_code == 200
    assert resp.json() == []


@pytest.mark.asyncio
async def test_upsert_menu_replaces_dishes(client):
    """POST /menu/ replaces all existing dishes for the tenant."""
    new_items = [
        {
            "dish_id": "new_001",
            "name": "New Dish",
            "description": "Brand new",
            "price": 9.99,
            "category": "mains",
            "allergens": ["gluten"],
            "dietary_tags": [],
            "is_available": True,
        }
    ]
    resp = await client.post(
        "/menu",
        json=new_items,
        headers={"X-Tenant-ID": "restaurant_demo"},
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 1
    assert resp.json()[0]["name"] == "New Dish"

    # Verify old dishes are gone
    resp2 = await client.get(
        "/menu?available_only=false", headers={"X-Tenant-ID": "restaurant_demo"}
    )
    assert len(resp2.json()) == 1
    assert resp2.json()[0]["dish_id"] == "new_001"


@pytest.mark.asyncio
async def test_menu_fetcher_tool_returns_available_dishes():
    """MenuFetcherTool.execute() returns available dishes via DB."""
    tool = MenuFetcherTool()

    @asynccontextmanager
    async def _patched_get_session():
        async with _TestSessionLocal() as s:
            yield s

    import core.tools.menu_fetcher as mfm
    original = mfm.get_session
    mfm.get_session = _patched_get_session
    try:
        result = await tool.execute(
            MenuFetcherInput(tenant_id="restaurant_demo", session_id="test-session")
        )
        assert result.success is True
        assert len(result.items) == 2
        assert all(item.is_available for item in result.items)
    finally:
        mfm.get_session = original
