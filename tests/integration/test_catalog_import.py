"""Integration tests for catalog import endpoints (GEN-6)."""
import json
from contextlib import asynccontextmanager
from io import BytesIO

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

import api.middleware.tenant as tenant_middleware_module
import api.routes.catalog_import as catalog_import_module
from api.main import app
from core.models.menu import CatalogItem
from core.models.tenant import TenantConfig

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
_engine = create_async_engine(TEST_DB_URL, echo=False)
_Session = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
TENANT_ID = "import-test-tenant"
HEADERS = {"X-Tenant-ID": TENANT_ID}


@asynccontextmanager
async def _patched_session():
    async with _Session() as s:
        yield s


@pytest_asyncio.fixture(autouse=True)
async def setup_db(monkeypatch):
    monkeypatch.setattr(tenant_middleware_module, "get_session", _patched_session)
    monkeypatch.setattr(catalog_import_module, "get_session", _patched_session)

    async with _engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with _Session() as s:
        s.add(TenantConfig(tenant_id=TENANT_ID, business_name="Import Co", api_key="sk-imp", is_active=True))
        await s.commit()

    yield

    async with _engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_json_import_creates_items(client):
    payload = [
        {"name": "Chair", "description": "Comfy chair", "price": 99.0, "category": "Furniture"},
        {"name": "Table", "description": "Oak table", "price": 199.0, "category": "Furniture"},
    ]
    resp = await client.post("/catalog/import", json=payload, headers=HEADERS)
    assert resp.status_code == 201
    assert resp.json()["items_imported"] == 2
    assert resp.json()["errors"] == []


@pytest.mark.asyncio
async def test_csv_import_creates_items(client):
    csv_data = "name,description,price,category\nSofa,Big sofa,299.0,Furniture\nLamp,Desk lamp,49.0,Lighting\n"
    resp = await client.post(
        "/catalog/import/csv",
        headers=HEADERS,
        files={"file": ("items.csv", BytesIO(csv_data.encode()), "text/csv")},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["items_imported"] == 2
    assert data["errors"] == []


@pytest.mark.asyncio
async def test_csv_import_skips_bad_rows(client):
    csv_data = "name,description,price,category\nGoodItem,Desc,10.0,Cat\nBadItem,Desc,not_a_float,Cat\n"
    resp = await client.post(
        "/catalog/import/csv",
        headers=HEADERS,
        files={"file": ("items.csv", BytesIO(csv_data.encode()), "text/csv")},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["items_imported"] == 1
    assert len(data["errors"]) == 1
    assert "Row 3" in data["errors"][0]
