"""Unit tests for deployment configuration (RA-21)."""
import json
import os
from pathlib import Path

import pytest
import httpx
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

ROOT = Path(__file__).parent.parent.parent


# ---------------------------------------------------------------------------
# railway.json
# ---------------------------------------------------------------------------

def test_railway_json_exists():
    assert (ROOT / "railway.json").exists()


def test_railway_json_valid():
    config = json.loads((ROOT / "railway.json").read_text())
    assert "deploy" in config or "build" in config


def test_railway_json_has_healthcheck():
    config = json.loads((ROOT / "railway.json").read_text())
    assert config.get("deploy", {}).get("healthcheckPath") == "/health"


def test_railway_json_has_start_command():
    config = json.loads((ROOT / "railway.json").read_text())
    start_cmd = config.get("deploy", {}).get("startCommand", "")
    assert "uvicorn" in start_cmd and "api.main:app" in start_cmd


# ---------------------------------------------------------------------------
# railway.toml
# ---------------------------------------------------------------------------

def test_railway_toml_exists():
    assert (ROOT / "railway.toml").exists()


def test_railway_toml_has_healthcheck():
    content = (ROOT / "railway.toml").read_text()
    assert "healthcheckPath" in content


# ---------------------------------------------------------------------------
# .env.example
# ---------------------------------------------------------------------------

def test_env_example_exists():
    assert (ROOT / ".env.example").exists()


def test_env_example_documents_anthropic_key():
    content = (ROOT / ".env.example").read_text()
    assert "ANTHROPIC_API_KEY" in content


def test_env_example_documents_anthropic_model():
    content = (ROOT / ".env.example").read_text()
    assert "ANTHROPIC_MODEL" in content


def test_env_example_documents_database_url():
    content = (ROOT / ".env.example").read_text()
    assert "DATABASE_URL" in content


def test_env_example_documents_langfuse():
    content = (ROOT / ".env.example").read_text()
    assert "LANGFUSE_SECRET_KEY" in content
    assert "LANGFUSE_PUBLIC_KEY" in content


def test_env_example_documents_chroma():
    content = (ROOT / ".env.example").read_text()
    assert "CHROMA" in content


def test_env_example_documents_port():
    content = (ROOT / ".env.example").read_text()
    assert "PORT" in content


# ---------------------------------------------------------------------------
# Health endpoint schema
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_endpoint_returns_200():
    from api.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_health_endpoint_returns_version():
    from api.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    data = response.json()
    assert "version" in data
    assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_health_endpoint_returns_model():
    from api.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    data = response.json()
    assert "model" in data
    assert "claude" in data["model"]


@pytest.mark.asyncio
async def test_health_endpoint_returns_environment():
    from api.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    data = response.json()
    assert "environment" in data


@pytest.mark.asyncio
async def test_health_endpoint_returns_status_healthy():
    from api.main import app
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/health")
    data = response.json()
    assert data["status"] == "healthy"


# ---------------------------------------------------------------------------
# Langfuse tracing wired in nodes.py
# ---------------------------------------------------------------------------

def test_langfuse_observe_decorator_on_llm_node():
    nodes_py = (ROOT / "core" / "agent" / "nodes.py").read_text()
    assert "@_observe" in nodes_py, "llm_node must have @_observe() Langfuse decorator"


def test_langfuse_metadata_injected():
    nodes_py = (ROOT / "core" / "agent" / "nodes.py").read_text()
    assert "session_id" in nodes_py
    assert "tenant_id" in nodes_py
