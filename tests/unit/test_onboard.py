"""Unit tests for POST /onboard (GEN-6)."""
from contextlib import asynccontextmanager

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

import api.middleware.tenant as tenant_middleware_module
import api.routes.onboard as onboard_module
from api.main import app

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
_engine = create_async_engine(TEST_DB_URL, echo=False)
_Session = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def _patched_session():
    async with _Session() as s:
        yield s


@pytest_asyncio.fixture(autouse=True)
async def setup_db(monkeypatch):
    monkeypatch.setattr(tenant_middleware_module, "get_session", _patched_session)
    monkeypatch.setattr(onboard_module, "get_session", _patched_session)
    async with _engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    async with _engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_onboard_creates_tenant(client):
    resp = await client.post("/onboard", json={"business_name": "Test Salon", "industry": "salon"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["tenant_id"].startswith("test-salon-")
    assert data["api_key"].startswith("sk-")
    assert "widget.js" in data["embed_snippet"]
    assert data["items_imported"] == 0


@pytest.mark.asyncio
async def test_onboard_with_catalog_imports_items(client):
    payload = {
        "business_name": "Pizza Place",
        "industry": "restaurant",
        "catalog": [
            {"name": "Margherita", "description": "Classic pizza", "price": 12.0, "category": "Pizza"},
            {"name": "Pepperoni", "description": "Spicy pizza", "price": 14.0, "category": "Pizza"},
        ],
    }
    resp = await client.post("/onboard", json=payload)
    assert resp.status_code == 201
    assert resp.json()["items_imported"] == 2


@pytest.mark.asyncio
async def test_onboard_duplicate_name_gets_unique_tenant_id(client):
    r1 = await client.post("/onboard", json={"business_name": "My Shop"})
    r2 = await client.post("/onboard", json={"business_name": "My Shop"})
    assert r1.status_code == 201
    assert r2.status_code == 201
    assert r1.json()["tenant_id"] != r2.json()["tenant_id"]
