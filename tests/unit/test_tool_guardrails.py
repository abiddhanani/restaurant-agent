"""Unit tests for Layer 2 tool-execution guardrails (RA-16)."""
import json
from unittest.mock import MagicMock, patch

import pytest

from core.guardrails.layer2_tool import AllergenCircuitBreaker, MenuGroundingValidator
from core.guardrails.pipeline import GuardrailPipeline


# ---------------------------------------------------------------------------
# AllergenCircuitBreaker
# ---------------------------------------------------------------------------

class TestAllergenCircuitBreaker:
    def setup_method(self):
        self.checker = AllergenCircuitBreaker()

    def test_no_overlap_passes(self):
        result = self.checker.check(
            dish_allergens=["fish", "sesame"],
            dietary_hard_stops=["gluten", "dairy"],
        )
        assert result.passed

    def test_overlap_blocks(self):
        result = self.checker.check(
            dish_allergens=["gluten", "eggs"],
            dietary_hard_stops=["gluten"],
        )
        assert not result.passed
        assert result.check_name == "allergen_circuit_breaker"
        assert "gluten" in result.reason.lower()

    def test_case_insensitive_match(self):
        result = self.checker.check(
            dish_allergens=["PEANUTS", "Dairy"],
            dietary_hard_stops=["peanuts"],
        )
        assert not result.passed

    def test_empty_dish_allergens_passes(self):
        result = self.checker.check(
            dish_allergens=[],
            dietary_hard_stops=["nuts", "gluten"],
        )
        assert result.passed

    def test_empty_hard_stops_passes(self):
        result = self.checker.check(
            dish_allergens=["nuts", "gluten"],
            dietary_hard_stops=[],
        )
        assert result.passed

    def test_peanut_allergy_blocks_peanut_dish(self):
        """Core allergen safety: peanut allergy must never result in a peanut dish."""
        result = self.checker.check(
            dish_allergens=["peanuts", "sesame"],
            dietary_hard_stops=["peanuts"],
        )
        assert not result.passed

    def test_circuit_breaker_cannot_be_bypassed_by_any_input(self):
        """Even if all allergens are listed, the check is deterministic code."""
        for allergen in ["gluten", "dairy", "eggs", "fish", "nuts", "soy"]:
            result = self.checker.check(
                dish_allergens=[allergen],
                dietary_hard_stops=[allergen],
            )
            assert not result.passed, f"Circuit breaker should have blocked {allergen}"


# ---------------------------------------------------------------------------
# MenuGroundingValidator
# ---------------------------------------------------------------------------

class TestMenuGroundingValidator:
    def setup_method(self):
        self.validator = MenuGroundingValidator()

    def test_existing_dish_passes(self):
        result = self.validator.check(
            dish_name="Spicy Lamb",
            tenant_menu_dish_names=["Spicy Lamb", "Tiramisu", "Bruschetta"],
        )
        assert result.passed

    def test_case_insensitive_match(self):
        result = self.validator.check(
            dish_name="spicy lamb",
            tenant_menu_dish_names=["Spicy Lamb"],
        )
        assert result.passed

    def test_phantom_dish_blocked(self):
        result = self.validator.check(
            dish_name="Unicorn Steak",
            tenant_menu_dish_names=["Spicy Lamb", "Tiramisu"],
        )
        assert not result.passed
        assert result.check_name == "menu_grounding"
        assert "Unicorn Steak" in result.reason

    def test_empty_menu_list_passes(self):
        # If menu list is empty, grounding check is skipped in pipeline
        result = self.validator.check(
            dish_name="Any Dish",
            tenant_menu_dish_names=[],
        )
        assert not result.passed  # validator itself blocks unknown dish

    def test_whitespace_normalised(self):
        result = self.validator.check(
            dish_name="  Tiramisu  ",
            tenant_menu_dish_names=["Tiramisu"],
        )
        assert result.passed


# ---------------------------------------------------------------------------
# GuardrailPipeline.check_tool_execution (integration)
# ---------------------------------------------------------------------------

class TestPipelineCheckToolExecution:
    @pytest.mark.asyncio
    async def test_no_dish_info_passes(self):
        pipeline = GuardrailPipeline()
        result = await pipeline.check_tool_execution(
            tool_name="menu_fetcher",
            tool_input={"available_only": True},
            dietary_hard_stops=["gluten"],
            tenant_menu_dish_names=["Spicy Lamb"],
        )
        assert result.passed

    @pytest.mark.asyncio
    async def test_allergen_in_tool_input_blocked(self):
        pipeline = GuardrailPipeline()
        result = await pipeline.check_tool_execution(
            tool_name="dish_recommender",
            tool_input={"dish_allergens": ["peanuts"], "dish_name": ""},
            dietary_hard_stops=["peanuts"],
            tenant_menu_dish_names=["Satay Chicken"],
        )
        assert not result.passed
        assert result.check_name == "allergen_circuit_breaker"

    @pytest.mark.asyncio
    async def test_phantom_dish_blocked(self):
        pipeline = GuardrailPipeline()
        result = await pipeline.check_tool_execution(
            tool_name="dish_recommender",
            tool_input={"dish_name": "Ghost Burger"},
            dietary_hard_stops=[],
            tenant_menu_dish_names=["Spicy Lamb", "Tiramisu"],
        )
        assert not result.passed
        assert result.check_name == "menu_grounding"


# ---------------------------------------------------------------------------
# _execute_tool: guardrail blocks before tool runs
# ---------------------------------------------------------------------------

import core.agent.nodes as nodes_module


@pytest.mark.asyncio
async def test_execute_tool_blocked_by_allergen_guardrail():
    """_execute_tool must return a blocked error when allergen circuit breaker fires."""
    state = MagicMock()
    state.tenant_id = "t1"
    state.session_id = "s1"
    state.taste_profile = MagicMock()
    state.taste_profile.dietary_hard_stops = ["peanuts"]

    result_str = await nodes_module._execute_tool(
        "dish_recommender",
        {"dish_allergens": ["peanuts"], "query": "recommend me something"},
        state,
    )
    result = json.loads(result_str)
    assert result.get("blocked") is True
    assert "peanut" in result.get("error", "").lower()
