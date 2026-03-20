"""Unit tests for Layer 1 input guardrails (RA-15)."""
import pytest

from core.guardrails.layer1_input import PIIDetector, ScopeClassifier, ToxicityFilter
from core.guardrails.pipeline import GuardrailPipeline


# ---------------------------------------------------------------------------
# ScopeClassifier
# ---------------------------------------------------------------------------

class TestScopeClassifier:
    def setup_method(self):
        self.classifier = ScopeClassifier()

    def test_food_query_passes(self):
        result = self.classifier.check("What dishes do you recommend?")
        assert result.passed

    def test_menu_query_passes(self):
        result = self.classifier.check("Show me the menu")
        assert result.passed

    def test_allergen_query_passes(self):
        result = self.classifier.check("I have a gluten allergy, what can I eat?")
        assert result.passed

    def test_investment_query_blocked(self):
        result = self.classifier.check("What stocks should I invest in today?")
        assert not result.passed
        assert result.check_name == "scope_classifier"

    def test_medical_query_blocked(self):
        result = self.classifier.check("I have symptoms of a disease, give me a diagnosis")
        assert not result.passed

    def test_politics_blocked(self):
        result = self.classifier.check("Who should I vote for in the election?")
        assert not result.passed

    def test_short_greeting_passes(self):
        # Short messages (≤4 words) pass even without food keywords
        result = self.classifier.check("Hello!")
        assert result.passed

    def test_spicy_food_passes(self):
        result = self.classifier.check("I want something spicy for dinner")
        assert result.passed


# ---------------------------------------------------------------------------
# PIIDetector
# ---------------------------------------------------------------------------

class TestPIIDetector:
    def setup_method(self):
        self.detector = PIIDetector()

    def test_clean_message_passes(self):
        result = self.detector.check("I'd like to order the pasta")
        assert result.passed
        assert result.reason is None

    def test_email_detected_and_flagged(self):
        result = self.detector.check("Contact me at john@example.com for the reservation")
        assert result.passed  # PII is allowed but flagged/scrubbed
        assert result.reason is not None
        assert "email" in result.reason.lower()
        assert "[EMAIL_REDACTED]" in result.blocked_content

    def test_phone_detected(self):
        result = self.detector.check("Call me on +44 7700 900123 to confirm")
        assert result.passed
        assert "phone" in result.reason.lower()

    def test_credit_card_detected(self):
        result = self.detector.check("Charge my card 4111 1111 1111 1111 please")
        assert result.passed
        assert "credit_card" in result.reason.lower()
        assert "REDACTED" in result.blocked_content

    def test_ssn_detected(self):
        result = self.detector.check("My SSN is 123-45-6789")
        assert result.passed
        assert "ssn" in result.reason.lower()


# ---------------------------------------------------------------------------
# ToxicityFilter
# ---------------------------------------------------------------------------

class TestToxicityFilter:
    def setup_method(self):
        self.filter = ToxicityFilter()

    def test_normal_message_passes(self):
        result = self.filter.check("I love the food here!")
        assert result.passed

    def test_toxic_word_blocked(self):
        result = self.filter.check("I want to kill the spicy chicken")
        assert not result.passed
        assert result.check_name == "toxicity_filter"

    def test_hate_blocked(self):
        result = self.filter.check("I hate this place")
        assert not result.passed

    def test_partial_word_not_blocked(self):
        # "killer" is not in the blocklist — only exact word "kill"
        result = self.filter.check("This killer pasta is amazing!")
        assert result.passed


# ---------------------------------------------------------------------------
# GuardrailPipeline.check_input (integration)
# ---------------------------------------------------------------------------

class TestPipelineCheckInput:
    @pytest.mark.asyncio
    async def test_food_message_passes_all_layers(self):
        pipeline = GuardrailPipeline()
        result = await pipeline.check_input("What's your best pasta dish?", "tenant1")
        assert result.passed
        assert result.check_name == "all_passed"

    @pytest.mark.asyncio
    async def test_toxic_message_blocked_before_scope(self):
        pipeline = GuardrailPipeline()
        result = await pipeline.check_input("I hate everything kill it all", "tenant1")
        assert not result.passed
        assert result.check_name == "toxicity_filter"

    @pytest.mark.asyncio
    async def test_out_of_scope_blocked(self):
        pipeline = GuardrailPipeline()
        result = await pipeline.check_input("Tell me about cryptocurrency investments", "tenant1")
        assert not result.passed
        assert result.check_name == "scope_classifier"

    @pytest.mark.asyncio
    async def test_pii_message_passes_with_flag(self):
        pipeline = GuardrailPipeline()
        result = await pipeline.check_input("Book a table for john@test.com", "tenant1")
        # PII flagged but not blocked (passed=True, flagged in reason)
        assert result.passed
