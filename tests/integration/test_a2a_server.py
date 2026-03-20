"""Integration tests for A2A server (RA-10 acceptance criteria)."""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from api.main import app

BASE = "http://test"


@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url=BASE) as c:
        yield c


# --------------------------------------------------------------------------- #
# Agent Card — /a2a/agent-card
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_agent_card_returns_200(client):
    resp = await client.get("/a2a/agent-card")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_agent_card_has_required_fields(client):
    data = (await client.get("/a2a/agent-card")).json()
    assert "agent_id" in data
    assert "name" in data
    assert "capabilities" in data
    assert "endpoint_url" in data
    assert "version" in data


@pytest.mark.asyncio
async def test_agent_card_has_capabilities(client):
    data = (await client.get("/a2a/agent-card")).json()
    cap_names = [c["name"] for c in data["capabilities"]]
    assert "recommend_dish" in cap_names
    assert "search_reviews" in cap_names


# --------------------------------------------------------------------------- #
# Well-known agent card — /.well-known/agent-card
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_well_known_agent_card_returns_200(client):
    resp = await client.get("/.well-known/agent-card")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_well_known_matches_a2a_card(client):
    a2a = (await client.get("/a2a/agent-card")).json()
    wk = (await client.get("/.well-known/agent-card")).json()
    assert a2a["agent_id"] == wk["agent_id"]
    assert a2a["capabilities"] == wk["capabilities"]


# --------------------------------------------------------------------------- #
# A2A invoke — /a2a/invoke
# --------------------------------------------------------------------------- #

@pytest.mark.asyncio
async def test_invoke_recommend_dish_returns_200(client):
    payload = {
        "capability": "recommend_dish",
        "payload": {"taste_preferences": ["spicy", "umami"]},
        "calling_agent_id": "test-agent",
    }
    resp = await client.post("/a2a/invoke", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "recommendations" in data["data"]


@pytest.mark.asyncio
async def test_invoke_search_reviews_returns_200(client):
    payload = {
        "capability": "search_reviews",
        "payload": {"query": "pasta", "top_k": 3},
        "calling_agent_id": "test-agent",
    }
    resp = await client.post("/a2a/invoke", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert "snippets" in data["data"]


@pytest.mark.asyncio
async def test_invoke_unknown_capability_returns_error(client):
    payload = {
        "capability": "nonexistent_capability",
        "payload": {},
        "calling_agent_id": "test-agent",
    }
    resp = await client.post("/a2a/invoke", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is False
    assert "Unknown capability" in data["error"]


@pytest.mark.asyncio
async def test_invoke_correlation_id_echoed(client):
    payload = {
        "capability": "search_reviews",
        "payload": {"query": "wine"},
        "calling_agent_id": "test-agent",
        "correlation_id": "corr-abc-123",
    }
    resp = await client.post("/a2a/invoke", json=payload)
    assert resp.json()["correlation_id"] == "corr-abc-123"


@pytest.mark.asyncio
async def test_a2a_paths_exempt_from_tenant_middleware(client):
    """A2A endpoints must not require X-Tenant-ID header."""
    resp = await client.get("/a2a/agent-card")
    assert resp.status_code == 200  # no 400 from missing tenant header
