"""Tests for preference model — runs in Week 3."""
import pytest
from core.models.preference import UserTasteProfile


def test_empty_profile_defaults(empty_taste_profile):
    """Fresh profile starts with zero confidence and neutral adventure score."""
    assert empty_taste_profile.confidence == 0.0
    assert empty_taste_profile.adventure_score == 0.5
    assert len(empty_taste_profile.dietary_hard_stops) == 0


def test_nut_allergy_in_hard_stops(nut_allergy_profile):
    """Nut allergy is in dietary_hard_stops, not just negative_signals."""
    assert "nuts" in nut_allergy_profile.dietary_hard_stops


def test_hard_stops_not_empty_means_guardrail_fires(nut_allergy_profile):
    """If dietary_hard_stops is non-empty, guardrails must act on it."""
    assert len(nut_allergy_profile.dietary_hard_stops) > 0
    # Guardrail integration test in tests/integration/
