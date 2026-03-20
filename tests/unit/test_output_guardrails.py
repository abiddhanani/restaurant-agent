"""Unit tests for Layer 3 output guardrails (RA-17)."""
import pytest

from core.guardrails.layer3_output import ClaimVerifier, HallucinationChecker, ScopeDriftChecker
from core.guardrails.pipeline import GuardrailPipeline


# ---------------------------------------------------------------------------
# HallucinationChecker
# ---------------------------------------------------------------------------

class TestHallucinationChecker:
    def setup_method(self):
        self.checker = HallucinationChecker()

    def test_response_with_menu_dish_passes(self):
        result = self.checker.check(
            response="I recommend the Spicy Lamb — it's excellent!",
            tenant_menu_dish_names=["Spicy Lamb", "Tiramisu", "Bruschetta"],
        )
        assert result.passed

    def test_response_with_phantom_dish_blocked(self):
        result = self.checker.check(
            response="Try the Unicorn Burger, it's our best seller!",
            tenant_menu_dish_names=["Spicy Lamb", "Tiramisu"],
        )
        assert not result.passed
        assert result.check_name == "hallucination_checker"
        assert "Unicorn Burger" in result.reason

    def test_empty_menu_skips_check(self):
        result = self.checker.check(
            response="Try the Spicy Lamb!",
            tenant_menu_dish_names=[],
        )
        assert result.passed

    def test_response_without_dish_names_passes(self):
        result = self.checker.check(
            response="Our restaurant is open from 12pm to 10pm daily.",
            tenant_menu_dish_names=["Spicy Lamb"],
        )
        assert result.passed


# ---------------------------------------------------------------------------
# ClaimVerifier
# ---------------------------------------------------------------------------

class TestClaimVerifier:
    def setup_method(self):
        self.verifier = ClaimVerifier()

    def test_response_without_quotes_passes(self):
        result = self.verifier.check(
            response="The pasta is great.",
            retrieved_docs=["pasta is great"],
        )
        assert result.passed

    def test_quote_in_retrieved_docs_passes(self):
        result = self.verifier.check(
            response='Customers say "the lamb is incredible and perfectly spiced".',
            retrieved_docs=["the lamb is incredible and perfectly spiced this place"],
        )
        assert result.passed

    def test_fabricated_quote_blocked(self):
        result = self.verifier.check(
            response='Reviews say "this is the best restaurant in the world".',
            retrieved_docs=["food was decent", "service was ok"],
        )
        assert not result.passed
        assert result.check_name == "claim_verifier"

    def test_short_quotes_below_threshold_ignored(self):
        # Quotes shorter than 10 chars are not checked
        result = self.verifier.check(
            response='The dish is "superb".',
            retrieved_docs=["nothing about this"],
        )
        assert result.passed


# ---------------------------------------------------------------------------
# ScopeDriftChecker
# ---------------------------------------------------------------------------

class TestScopeDriftChecker:
    def setup_method(self):
        self.checker = ScopeDriftChecker()

    def test_food_response_passes(self):
        result = self.checker.check("I recommend the Spicy Lamb curry for its bold flavour.")
        assert result.passed

    def test_investment_drift_blocked(self):
        result = self.checker.check("You should invest in crypto for better returns.")
        assert not result.passed
        assert result.check_name == "scope_drift"

    def test_medical_drift_blocked(self):
        result = self.checker.check("Based on your symptoms, I would diagnose you with...")
        assert not result.passed

    def test_political_drift_blocked(self):
        result = self.checker.check("You should vote for this political party candidate.")
        assert not result.passed

    def test_legal_drift_blocked(self):
        result = self.checker.check("You should sue the restaurant and hire an attorney.")
        assert not result.passed


# ---------------------------------------------------------------------------
# GuardrailPipeline.check_output (integration)
# ---------------------------------------------------------------------------

class TestPipelineCheckOutput:
    @pytest.mark.asyncio
    async def test_clean_food_response_passes(self):
        pipeline = GuardrailPipeline()
        result = await pipeline.check_output(
            response="I recommend our Spicy Lamb, it's packed with bold spices.",
            retrieved_docs=[],
            tenant_menu_dish_names=["Spicy Lamb", "Tiramisu"],
        )
        assert result.passed
        assert result.check_name == "all_passed"

    @pytest.mark.asyncio
    async def test_scope_drift_blocked_first(self):
        pipeline = GuardrailPipeline()
        result = await pipeline.check_output(
            response="You should invest in crypto to pay for dinner.",
            retrieved_docs=[],
            tenant_menu_dish_names=["Spicy Lamb"],
        )
        assert not result.passed
        assert result.check_name == "scope_drift"

    @pytest.mark.asyncio
    async def test_fabricated_quote_blocked(self):
        pipeline = GuardrailPipeline()
        result = await pipeline.check_output(
            response='Reviews confirm "absolutely the finest dining experience anywhere".',
            retrieved_docs=["the food was good"],
            tenant_menu_dish_names=["Spicy Lamb"],
        )
        assert not result.passed
        assert result.check_name == "claim_verifier"
