"""Preference model — builds UserTasteProfile from conversation."""
from core.models.preference import UserTasteProfile
from datetime import datetime


class PreferenceExtractor:
    """
    Extracts taste signals from conversation incrementally.
    Never asks form-style questions — listens and infers.
    Updates dietary_hard_stops which feeds Layer 2 guardrails.
    Implemented Week 3.
    """

    async def update_from_message(
        self,
        profile: UserTasteProfile,
        message: str,
        role: str,
    ) -> UserTasteProfile:
        """
        Extract signals from a single message and return updated profile.
        Positive/negative signals update adventure_score.
        Allergens always go to dietary_hard_stops.
        Confidence increases with each signal extracted.
        """
        # TODO Week 3: implement with Claude structured output extraction
        raise NotImplementedError("Implement in Week 3")

    def _increase_confidence(self, profile: UserTasteProfile, delta: float = 0.1) -> float:
        """Increment confidence, capped at 1.0."""
        return min(1.0, profile.confidence + delta)
