"""Unit tests for PreferenceExtractor — no API calls, pure keyword extraction."""
import asyncio

import pytest

from core.models.preference import UserTasteProfile
from core.preferences.profile import PreferenceExtractor


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture()
def extractor() -> PreferenceExtractor:
    return PreferenceExtractor()


@pytest.fixture()
def empty_profile() -> UserTasteProfile:
    return UserTasteProfile(session_id="s1", tenant_id="t1")


# --------------------------------------------------------------------------- #
# Allergen hard stops
# --------------------------------------------------------------------------- #

def test_explicit_allergy_adds_to_hard_stops(extractor, empty_profile):
    profile = run(extractor.update_from_message(empty_profile, "I'm allergic to nuts", "user"))
    assert "nuts" in profile.dietary_hard_stops


def test_cant_eat_pattern(extractor, empty_profile):
    profile = run(extractor.update_from_message(empty_profile, "I can't eat dairy", "user"))
    assert "dairy" in profile.dietary_hard_stops


def test_vegan_adds_multiple_hard_stops(extractor, empty_profile):
    profile = run(extractor.update_from_message(empty_profile, "I'm a vegan", "user"))
    assert "dairy" in profile.dietary_hard_stops
    assert "eggs" in profile.dietary_hard_stops


def test_vegetarian_adds_meat_fish(extractor, empty_profile):
    profile = run(extractor.update_from_message(empty_profile, "I'm vegetarian", "user"))
    assert "meat" in profile.dietary_hard_stops
    assert "fish" in profile.dietary_hard_stops


def test_allergens_deduplicated(extractor, empty_profile):
    p1 = run(extractor.update_from_message(empty_profile, "I'm allergic to nuts", "user"))
    p2 = run(extractor.update_from_message(p1, "I'm allergic to nuts", "user"))
    assert p2.dietary_hard_stops.count("nuts") == 1


def test_multiple_allergens_in_one_message(extractor, empty_profile):
    profile = run(extractor.update_from_message(
        empty_profile, "I can't eat gluten or dairy", "user"
    ))
    assert "gluten" in profile.dietary_hard_stops
    assert "dairy" in profile.dietary_hard_stops


# --------------------------------------------------------------------------- #
# Positive / negative signals
# --------------------------------------------------------------------------- #

def test_positive_signal_extracted(extractor, empty_profile):
    profile = run(extractor.update_from_message(empty_profile, "I love spicy food", "user"))
    assert any("spicy" in s for s in profile.positive_signals)


def test_negative_signal_extracted(extractor, empty_profile):
    profile = run(extractor.update_from_message(empty_profile, "I hate cilantro", "user"))
    assert any("cilantro" in s for s in profile.negative_signals)


def test_assistant_messages_are_ignored(extractor, empty_profile):
    profile = run(extractor.update_from_message(
        empty_profile, "I'm allergic to nuts and I love pasta", "assistant"
    ))
    assert profile.dietary_hard_stops == []
    assert profile.positive_signals == []


# --------------------------------------------------------------------------- #
# Adventure score
# --------------------------------------------------------------------------- #

def test_adventure_score_increases_for_bold_taste(extractor, empty_profile):
    profile = run(extractor.update_from_message(empty_profile, "I'm an adventurous eater", "user"))
    assert profile.adventure_score > empty_profile.adventure_score


def test_adventure_score_decreases_for_safe_preference(extractor, empty_profile):
    profile = run(extractor.update_from_message(empty_profile, "I prefer safe, plain food", "user"))
    assert profile.adventure_score < empty_profile.adventure_score


def test_adventure_score_clamped_at_1(extractor, empty_profile):
    p = empty_profile.model_copy(update={"adventure_score": 0.95})
    for _ in range(10):
        p = run(extractor.update_from_message(p, "I love bold exotic food", "user"))
    assert p.adventure_score <= 1.0


def test_adventure_score_clamped_at_0(extractor, empty_profile):
    p = empty_profile.model_copy(update={"adventure_score": 0.05})
    for _ in range(10):
        p = run(extractor.update_from_message(p, "I prefer plain safe food", "user"))
    assert p.adventure_score >= 0.0


# --------------------------------------------------------------------------- #
# Confidence
# --------------------------------------------------------------------------- #

def test_confidence_increases_when_signals_extracted(extractor, empty_profile):
    profile = run(extractor.update_from_message(empty_profile, "I love pasta", "user"))
    assert profile.confidence > empty_profile.confidence


def test_confidence_unchanged_for_no_signal(extractor, empty_profile):
    profile = run(extractor.update_from_message(empty_profile, "Hello there!", "user"))
    assert profile.confidence == empty_profile.confidence


# --------------------------------------------------------------------------- #
# Profile persists across messages
# --------------------------------------------------------------------------- #

def test_profile_accumulates_across_messages(extractor, empty_profile):
    p1 = run(extractor.update_from_message(empty_profile, "I'm allergic to shellfish", "user"))
    p2 = run(extractor.update_from_message(p1, "I love spicy Thai food", "user"))
    assert "shellfish" in p2.dietary_hard_stops
    assert any("spicy" in s for s in p2.positive_signals)
