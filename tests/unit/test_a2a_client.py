"""Unit tests for A2A client, cuisine-expert stub, and agent routing (RA-14)."""
import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from a2a.agents.cuisine_expert import CuisineExpertAgent, CuisineExpertConnector
from a2a.client import A2AClient, AgentRequest, AgentResponse


# ---------------------------------------------------------------------------
# CuisineExpertAgent (stub server)
# ---------------------------------------------------------------------------

class TestCuisineExpertAgent:
    def setup_method(self):
        self.agent = CuisineExpertAgent()

    def test_get_cuisine_info_known_cuisine(self):
        result = self.agent.get_cuisine_info("Italian")
        assert result["cuisine_type"] == "Italian"
        assert result["origin"] == "Italy"
        assert "history" in result
        assert "key_ingredients" in result

    def test_get_cuisine_info_case_insensitive(self):
        result = self.agent.get_cuisine_info("JAPANESE")
        assert result["origin"] == "Japan"

    def test_get_cuisine_info_unknown_returns_default(self):
        result = self.agent.get_cuisine_info("AlienFood")
        assert result["cuisine_type"] == "AlienFood"
        assert "history" in result

    def test_handle_get_cuisine_info_capability(self):
        req = AgentRequest(capability="get_cuisine_info", payload={"cuisine_type": "Thai"})
        response = self.agent.handle(req.capability, req.payload)
        assert response.success is True
        assert response.data["origin"] == "Thailand"

    def test_handle_unknown_capability_returns_error(self):
        response = self.agent.handle("fly_to_moon", {})
        assert response.success is False
        assert "Unknown capability" in response.error


# ---------------------------------------------------------------------------
# CuisineExpertConnector (outbound HTTP call)
# ---------------------------------------------------------------------------

class TestCuisineExpertConnector:
    def setup_method(self):
        self.connector = CuisineExpertConnector()

    @pytest.mark.asyncio
    async def test_successful_call_returns_agent_response(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "success": True,
            "data": {"cuisine_type": "Indian", "origin": "Indian subcontinent"},
            "error": None,
            "responding_agent_id": "cuisine-expert-v1",
            "correlation_id": None,
        }
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client_cls.return_value = mock_client

            response = await self.connector.call("get_domain_context", {"context_type": "Indian"})

        assert response.success is True
        assert response.data["cuisine_type"] == "Indian"

    @pytest.mark.asyncio
    async def test_timeout_returns_fallback_response(self):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))
            mock_client_cls.return_value = mock_client

            response = await self.connector.call("get_domain_context", {"context_type": "Italian"})

        assert response.success is False
        assert "unavailable" in response.error.lower()

    @pytest.mark.asyncio
    async def test_http_error_returns_fallback(self):
        with patch("httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.post = AsyncMock(side_effect=httpx.ConnectError("connection refused"))
            mock_client_cls.return_value = mock_client

            response = await self.connector.call("get_cuisine_info", {})

        assert response.success is False


# ---------------------------------------------------------------------------
# A2AClient dispatch
# ---------------------------------------------------------------------------

class TestA2AClient:
    def setup_method(self):
        self.client = A2AClient()

    @pytest.mark.asyncio
    async def test_dispatch_to_unregistered_agent_returns_error(self):
        response = await self.client.dispatch("ghost-agent", "do_something", {})
        assert response.success is False
        assert "ghost-agent" in response.error

    @pytest.mark.asyncio
    async def test_dispatch_routes_to_registered_connector(self):
        mock_connector = AsyncMock()
        mock_connector.agent_id = "test-agent"
        mock_connector.call = AsyncMock(return_value=AgentResponse(
            success=True, data={"result": "ok"}, responding_agent_id="test-agent"
        ))
        self.client.register(mock_connector)

        response = await self.client.dispatch("test-agent", "do_thing", {"key": "val"})
        assert response.success is True
        mock_connector.call.assert_awaited_once_with("do_thing", {"key": "val"})


# ---------------------------------------------------------------------------
# Agent node: get_cuisine_info routing with timeout + fallback
# ---------------------------------------------------------------------------

import core.agent.nodes as nodes_module


@pytest.mark.asyncio
async def test_agent_node_cuisine_tool_returns_info():
    """_execute_tool with get_cuisine_info should return cuisine data."""
    state = MagicMock()
    state.tenant_id = "t1"
    state.session_id = "s1"
    state.customer_profile = None

    mock_response = AgentResponse(
        success=True,
        data={"cuisine_type": "Italian", "origin": "Italy"},
        responding_agent_id="cuisine-expert-v1",
    )
    mock_a2a = AsyncMock()
    mock_a2a.dispatch = AsyncMock(return_value=mock_response)

    with patch.object(nodes_module, "_a2a_client", mock_a2a):
        result_str = await nodes_module._execute_tool(
            "get_domain_context", {"context_type": "Italian"}, state
        )

    result = json.loads(result_str)
    assert result["origin"] == "Italy"


@pytest.mark.asyncio
async def test_agent_node_cuisine_tool_timeout_returns_fallback():
    """When A2A call times out, fallback message is returned (not an exception)."""
    state = MagicMock()
    state.tenant_id = "t1"
    state.session_id = "s1"
    state.customer_profile = None

    async def _slow_dispatch(*args, **kwargs):
        await asyncio.sleep(10)  # will be cancelled by wait_for

    mock_a2a = AsyncMock()
    mock_a2a.dispatch = _slow_dispatch

    with patch.object(nodes_module, "_a2a_client", mock_a2a), \
         patch.object(nodes_module, "_DOMAIN_A2A_TIMEOUT", 0.01):
        result_str = await nodes_module._execute_tool(
            "get_domain_context", {"context_type": "Thai"}, state
        )

    result = json.loads(result_str)
    assert "Context info unavailable" in result.get("info", "")
