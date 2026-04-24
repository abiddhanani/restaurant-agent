"""Unit tests for Layer 2 tool-execution guardrails."""
import json
from unittest.mock import MagicMock, patch

import pytest

from core.guardrails.layer2_tool import HardStopChecker, CatalogGroundingValidator
from core.guardrails.pipeline import GuardrailPipeline


# ---------------------------------------------------------------------------
# HardStopChecker
# ---------------------------------------------------------------------------

class TestHardStopChecker:
    def setup_method(self):
        self.checker = HardStopChecker()

    def test_no_overlap_passes(self):
        result = self.checker.check(
            item_constraints=["fish", "sesame"],
            hard_stops=["gluten", "dairy"],
        )
        assert result.passed

    def test_overlap_blocks(self):
        result = self.checker.check(
            item_constraints=["gluten", "eggs"],
            hard_stops=["gluten"],
        )
        assert not result.passed
        assert result.check_name == "hard_stop_checker"
        assert "gluten" in result.reason.lower()

    def test_case_insensitive_match(self):
        result = self.checker.check(
            item_constraints=["PEANUTS", "Dairy"],
            hard_stops=["peanuts"],
        )
        assert not result.passed

    def test_empty_item_constraints_passes(self):
        result = self.checker.check(
            item_constraints=[],
            hard_stops=["nuts", "gluten"],
        )
        assert result.passed

    def test_empty_hard_stops_passes(self):
        result = self.checker.check(
            item_constraints=["nuts", "gluten"],
            hard_stops=[],
        )
        assert result.passed

    def test_peanut_stop_blocks_peanut_item(self):
        result = self.checker.check(
            item_constraints=["peanuts", "sesame"],
            hard_stops=["peanuts"],
        )
        assert not result.passed

    def test_hard_stop_checker_cannot_be_bypassed(self):
        for constraint in ["gluten", "dairy", "eggs", "fish", "nuts", "soy"]:
            result = self.checker.check(
                item_constraints=[constraint],
                hard_stops=[constraint],
            )
            assert not result.passed, f"Hard stop checker should have blocked {constraint}"


# ---------------------------------------------------------------------------
# CatalogGroundingValidator
# ---------------------------------------------------------------------------

class TestCatalogGroundingValidator:
    def setup_method(self):
        self.validator = CatalogGroundingValidator()

    def test_existing_item_passes(self):
        result = self.validator.check(
            item_name="Spicy Lamb",
            catalog_item_names=["Spicy Lamb", "Tiramisu", "Bruschetta"],
        )
        assert result.passed

    def test_case_insensitive_match(self):
        result = self.validator.check(
            item_name="spicy lamb",
            catalog_item_names=["Spicy Lamb"],
        )
        assert result.passed

    def test_phantom_item_blocked(self):
        result = self.validator.check(
            item_name="Unicorn Steak",
            catalog_item_names=["Spicy Lamb", "Tiramisu"],
        )
        assert not result.passed
        assert result.check_name == "catalog_grounding"
        assert "Unicorn Steak" in result.reason

    def test_empty_catalog_list_blocks(self):
        result = self.validator.check(
            item_name="Any Item",
            catalog_item_names=[],
        )
        assert not result.passed

    def test_whitespace_normalised(self):
        result = self.validator.check(
            item_name="  Tiramisu  ",
            catalog_item_names=["Tiramisu"],
        )
        assert result.passed


# ---------------------------------------------------------------------------
# GuardrailPipeline.check_tool_execution (integration)
# ---------------------------------------------------------------------------

class TestPipelineCheckToolExecution:
    @pytest.mark.asyncio
    async def test_no_item_info_passes(self):
        pipeline = GuardrailPipeline()
        result = await pipeline.check_tool_execution(
            tool_name="catalog_fetcher",
            tool_input={"available_only": True},
            hard_stops=["gluten"],
            catalog_item_names=["Spicy Lamb"],
        )
        assert result.passed

    @pytest.mark.asyncio
    async def test_constraint_in_tool_input_blocked(self):
        pipeline = GuardrailPipeline()
        result = await pipeline.check_tool_execution(
            tool_name="recommender",
            tool_input={"item_constraints": ["peanuts"], "item_name": ""},
            hard_stops=["peanuts"],
            catalog_item_names=["Satay Chicken"],
        )
        assert not result.passed
        assert result.check_name == "hard_stop_checker"

    @pytest.mark.asyncio
    async def test_phantom_item_blocked(self):
        pipeline = GuardrailPipeline()
        result = await pipeline.check_tool_execution(
            tool_name="recommender",
            tool_input={"item_name": "Ghost Burger"},
            hard_stops=[],
            catalog_item_names=["Spicy Lamb", "Tiramisu"],
        )
        assert not result.passed
        assert result.check_name == "catalog_grounding"


# ---------------------------------------------------------------------------
# _execute_tool: guardrail blocks before tool runs
# ---------------------------------------------------------------------------

import core.agent.nodes as nodes_module


@pytest.mark.asyncio
async def test_execute_tool_blocked_by_hard_stop_guardrail():
    """_execute_tool must return a blocked error when hard-stop checker fires."""
    state = MagicMock()
    state.tenant_id = "t1"
    state.session_id = "s1"
    state.customer_profile = MagicMock()
    state.customer_profile.hard_stops = ["peanuts"]

    result_str = await nodes_module._execute_tool(
        "recommender",
        {"item_constraints": ["peanuts"], "query": "recommend me something"},
        state,
    )
    result = json.loads(result_str)
    assert result.get("blocked") is True
    assert "peanut" in result.get("error", "").lower()
