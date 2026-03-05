"""Tests for guardrail pipeline — runs in Week 5."""
import pytest
from core.guardrails.pipeline import GuardrailPipeline, GuardrailViolation


@pytest.fixture
def pipeline():
    """Fresh GuardrailPipeline for each test."""
    return GuardrailPipeline()


@pytest.mark.asyncio
async def test_passthrough_returns_passed(pipeline):
    """Before implementation, pipeline stubs return passed=True."""
    result = await pipeline.check_input("I want something spicy", "demo_restaurant")
    assert result.passed is True


@pytest.mark.asyncio
async def test_allergen_check_structure(pipeline):
    """Layer 2 allergen check method exists and accepts dietary_hard_stops."""
    result = await pipeline.check_tool_execution(
        tool_name="dish_recommender",
        tool_input={},
        dietary_hard_stops=["nuts"],
        tenant_menu_dish_ids=["dish_001"],
    )
    # Will assert False once implemented — stub passes for now
    assert result.layer == "tool_execution"
