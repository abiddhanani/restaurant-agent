"""Tests for guardrail pipeline."""
import pytest
from core.guardrails.pipeline import GuardrailPipeline, GuardrailViolation


@pytest.fixture
def pipeline():
    return GuardrailPipeline()


@pytest.mark.asyncio
async def test_passthrough_returns_passed(pipeline):
    result = await pipeline.check_input("I want something spicy", "demo_restaurant")
    assert result.passed is True


@pytest.mark.asyncio
async def test_constraint_check_structure(pipeline):
    """Layer 2 constraint check method exists and accepts hard_stops."""
    result = await pipeline.check_tool_execution(
        tool_name="recommender",
        tool_input={},
        hard_stops=["nuts"],
        catalog_item_names=["item_001"],
    )
    assert result.layer == "tool_execution"
