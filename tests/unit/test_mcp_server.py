"""Unit tests for MCP server — tool schemas, HTTP endpoints, dispatch."""
import json
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlmodel import SQLModel
from sqlmodel.ext.asyncio.session import AsyncSession

import api.middleware.tenant as tenant_middleware_module
import core.tools.dish_recommender as recommender_module
import core.tools.menu_fetcher as catalog_fetcher_module
from api.main import app
from core.models.menu import CatalogItem
from core.models.tenant import TenantConfig
from mcp.server import TOOL_SCHEMAS, MCP_MANIFEST, _call_tool

TENANT_ID = "mcp_test_tenant"
HEADERS = {"X-Tenant-ID": TENANT_ID}

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
_engine = create_async_engine(TEST_DB_URL, echo=False)
_Session = async_sessionmaker(_engine, class_=AsyncSession, expire_on_commit=False)


@pytest.fixture(autouse=True)
async def setup_db(monkeypatch):
    @asynccontextmanager
    async def _patched():
        async with _Session() as s:
            yield s

    for mod in (tenant_middleware_module, recommender_module, catalog_fetcher_module):
        monkeypatch.setattr(mod, "get_session", _patched)

    async with _engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

    async with _Session() as s:
        s.add(TenantConfig(tenant_id=TENANT_ID, business_name="MCP Test",
                           api_key="sk-mcp", is_active=True))
        s.add(CatalogItem(tenant_id=TENANT_ID, item_id="i1", name="Spicy Lamb",
                          description="Bold lamb curry", price=18.0, category="Mains",
                          constraints='["gluten"]', tags='["spicy"]'))
        await s.commit()

    yield

    async with _engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.drop_all)


# ---------------------------------------------------------------------------
# Tool schema discovery
# ---------------------------------------------------------------------------

def test_tool_schemas_list_returns_three_tools():
    assert len(TOOL_SCHEMAS) == 3


def test_tool_names_are_correct():
    names = {t["name"] for t in TOOL_SCHEMAS}
    assert names == {"recommend", "get_catalog", "search_reviews"}


def test_each_tool_has_required_fields():
    for tool in TOOL_SCHEMAS:
        assert "name" in tool
        assert "description" in tool
        assert "inputSchema" in tool
        assert "properties" in tool["inputSchema"]


def test_manifest_contains_tools():
    assert len(MCP_MANIFEST["tools"]) == 3
    assert MCP_MANIFEST["name"] == "catalog-agent"


# ---------------------------------------------------------------------------
# HTTP endpoints
# ---------------------------------------------------------------------------

@pytest.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_mcp_tools_endpoint_returns_schemas(client):
    resp = await client.get("/mcp/tools", headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert "tools" in data
    assert len(data["tools"]) == 3


@pytest.mark.asyncio
async def test_mcp_manifest_sse_returns_200(client):
    resp = await client.get("/mcp", headers=HEADERS)
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_mcp_call_get_catalog(client):
    resp = await client.post("/mcp/call", json={
        "tool_name": "get_catalog",
        "tool_input": {"tenant_id": TENANT_ID},
    }, headers=HEADERS)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "result" in data


@pytest.mark.asyncio
async def test_mcp_call_unknown_tool_returns_404(client):
    resp = await client.post("/mcp/call", json={
        "tool_name": "fly_to_moon",
        "tool_input": {},
    }, headers=HEADERS)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# _call_tool dispatcher
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_call_tool_get_catalog_returns_items():
    result = await _call_tool("get_catalog", {"tenant_id": TENANT_ID})
    assert "items" in result or "success" in result


@pytest.mark.asyncio
async def test_call_tool_unknown_raises_value_error():
    with pytest.raises(ValueError, match="Unknown tool"):
        await _call_tool("nonexistent_tool", {})
