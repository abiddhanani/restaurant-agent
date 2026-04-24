"""Unit tests for image/video upload endpoints (GEN-6)."""
from contextlib import asynccontextmanager
from io import BytesIO

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

import api.middleware.tenant as tenant_middleware_module
import api.routes.uploads as uploads_module
from api.main import app
from core.models.menu import CatalogItem
from core.models.tenant import TenantConfig

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
_engine = create_async_engine(TEST_DB_URL, echo=False)
_Session = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)
TENANT_ID = "upload-test-tenant"
ITEM_ID = "item-001"
HEADERS = {"X-Tenant-ID": TENANT_ID}


@asynccontextmanager
async def _patched_session():
    async with _Session() as s:
        yield s


@pytest_asyncio.fixture(autouse=True)
async def setup_db(monkeypatch, tmp_path, monkeypatch_session):
    monkeypatch.setattr(tenant_middleware_module, "get_session", _patched_session)
    monkeypatch.setattr(uploads_module, "get_session", _patched_session)

    # Redirect uploads to tmp dir so we don't litter the project
    monkeypatch.chdir(tmp_path)
    import os
    os.makedirs("static/uploads", exist_ok=True)

    async with _engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with _Session() as s:
        s.add(TenantConfig(tenant_id=TENANT_ID, business_name="Upload Co", api_key="sk-up", is_active=True))
        s.add(CatalogItem(tenant_id=TENANT_ID, item_id=ITEM_ID, name="Widget", description="A widget", price=9.99, category="Things"))
        await s.commit()

    yield

    async with _engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


@pytest.fixture
def monkeypatch_session():
    """Alias to allow autouse fixture to request monkeypatch."""
    return None


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_image_upload_accepted(client):
    resp = await client.post(
        f"/catalog/items/{ITEM_ID}/image",
        headers=HEADERS,
        files={"file": ("photo.jpg", BytesIO(b"fake-image-data"), "image/jpeg")},
    )
    assert resp.status_code == 200
    assert resp.json()["image_url"].endswith(".jpg")


@pytest.mark.asyncio
async def test_image_upload_invalid_type_rejected(client):
    resp = await client.post(
        f"/catalog/items/{ITEM_ID}/image",
        headers=HEADERS,
        files={"file": ("doc.pdf", BytesIO(b"fake"), "application/pdf")},
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_image_upload_too_large_rejected(client):
    big = b"x" * (5 * 1024 * 1024 + 1)
    resp = await client.post(
        f"/catalog/items/{ITEM_ID}/image",
        headers=HEADERS,
        files={"file": ("big.png", BytesIO(big), "image/png")},
    )
    assert resp.status_code == 413


@pytest.mark.asyncio
async def test_video_upload_accepted(client):
    resp = await client.post(
        f"/catalog/items/{ITEM_ID}/video",
        headers=HEADERS,
        files={"file": ("clip.mp4", BytesIO(b"fake-video-data"), "video/mp4")},
    )
    assert resp.status_code == 200
    assert resp.json()["video_url"].endswith(".mp4")


@pytest.mark.asyncio
async def test_video_upload_invalid_type_rejected(client):
    resp = await client.post(
        f"/catalog/items/{ITEM_ID}/video",
        headers=HEADERS,
        files={"file": ("clip.avi", BytesIO(b"fake"), "video/avi")},
    )
    assert resp.status_code == 422
