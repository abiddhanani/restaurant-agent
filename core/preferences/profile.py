"""Preference model — builds CustomerProfile from conversation signals."""
import re

from core.models.preference import CustomerProfile

# --------------------------------------------------------------------------- #
# Constraint keyword registry (food domain defaults — overridable via tenant config)
# --------------------------------------------------------------------------- #
_CONSTRAINT_CANONICAL: dict[str, list[str]] = {
    "nuts": ["nut", "nuts", "peanut", "peanuts", "tree nut", "cashew", "almond", "walnut", "pecan", "pistachio", "hazelnut"],
    "dairy": ["dairy", "milk", "lactose", "cheese", "butter", "cream", "yogurt", "whey"],
    "gluten": ["gluten", "wheat", "barley", "rye"],
    "shellfish": ["shellfish", "shrimp", "prawn", "crab", "lobster", "crayfish", "scallop"],
    "fish": ["fish", "salmon", "tuna", "cod", "halibut", "anchovy"],
    "eggs": ["egg", "eggs"],
    "soy": ["soy", "soya", "tofu", "edamame"],
    "sesame": ["sesame", "tahini"],
}

# Patterns that indicate a constraint
_CONSTRAINT_TRIGGER_RE = re.compile(
    r"""
    (?:
        (?:i'?m?\s+)?allergic\s+to |
        can't\s+(?:have|eat|use) |
        cannot\s+(?:have|eat|use) |
        don't\s+(?:eat|want|like) |
        no\s+ |
        avoid |
        intolerant\s+to |
        intolerance\s+to
    )
    \s+(.+?)
    (?:\.|,|!|\?|$|\band\b)
    """,
    re.IGNORECASE | re.VERBOSE,
)

_VEGAN_RE = re.compile(r"\bi'?m\s+(?:a\s+)?vegan\b", re.IGNORECASE)
_VEGETARIAN_RE = re.compile(r"\bi'?m\s+(?:a\s+)?vegetarian\b", re.IGNORECASE)

# Positive/negative signal patterns
_POSITIVE_RE = re.compile(
    r"(?:love|enjoy|like|adore|fan of|obsessed with|prefer|great lover of)\s+(.+?)(?:\.|,|!|\?|$)",
    re.IGNORECASE,
)
_NEGATIVE_RE = re.compile(
    r"(?:hate|dislike|don't like|not a fan of|can't stand|detest|not fond of)\s+(.+?)(?:\.|,|!|\?|$)",
    re.IGNORECASE,
)

_OPENNESS_UP_WORDS = frozenset(
    ["adventurous", "exotic", "try anything", "love trying", "new things", "unusual", "bold", "different", "adventurous eater"]
)
_OPENNESS_DOWN_WORDS = frozenset(
    ["safe", "plain", "mild", "nothing weird", "comfortable", "familiar", "nothing too spicy", "simple", "boring"]
)


def _to_canonical_constraint(phrase: str) -> str | None:
    """Map a free-text phrase to a canonical constraint name, or None."""
    phrase_lower = phrase.lower()
    for canonical, keywords in _CONSTRAINT_CANONICAL.items():
        for kw in keywords:
            if kw in phrase_lower:
                return canonical
    return None


class PreferenceExtractor:
    """
    Extracts preference signals from user messages and updates CustomerProfile
    incrementally. Keyword/regex-based — no LLM call required.
    """

    async def update_from_message(
        self,
        profile: CustomerProfile,
        message: str,
        role: str,
    ) -> CustomerProfile:
        """Extract signals from a single message and return updated profile.

        Only processes user messages — assistant messages are skipped.
        Constraints → hard_stops (deduplicated, canonical).
        Positive/negative phrases → respective signal lists.
        Openness cues → openness_score ±0.1, clamped [0, 1].
        Confidence increases by 0.05 per extraction pass.
        """
        if role != "user":
            return profile

        hard_stops = list(profile.hard_stops)
        positive = list(profile.positive_signals)
        negative = list(profile.negative_signals)
        openness = profile.openness_score
        changed = False

        # --- Vegan / vegetarian shorthands ---
        if _VEGAN_RE.search(message):
            for constraint in ("dairy", "eggs", "fish", "shellfish", "meat"):
                if constraint not in hard_stops:
                    hard_stops.append(constraint)
                    changed = True

        if _VEGETARIAN_RE.search(message):
            for constraint in ("meat", "fish", "shellfish"):
                if constraint not in hard_stops:
                    hard_stops.append(constraint)
                    changed = True

        # --- Explicit constraint triggers ---
        for match in _CONSTRAINT_TRIGGER_RE.finditer(message):
            phrase = match.group(1).strip()
            parts = re.split(r"\s+(?:or|and)\s+", phrase, flags=re.IGNORECASE)
            for part in parts:
                canonical = _to_canonical_constraint(part)
                if canonical and canonical not in hard_stops:
                    hard_stops.append(canonical)
                    changed = True

        # --- Positive signals ---
        for match in _POSITIVE_RE.finditer(message):
            signal = match.group(1).strip().lower().rstrip(".,!?")
            if signal and signal not in positive:
                positive.append(signal)
                changed = True

        # --- Negative signals ---
        for match in _NEGATIVE_RE.finditer(message):
            signal = match.group(1).strip().lower().rstrip(".,!?")
            if signal and signal not in negative:
                negative.append(signal)
                changed = True

        # --- Openness score ---
        msg_lower = message.lower()
        for word in _OPENNESS_UP_WORDS:
            if word in msg_lower:
                openness = min(1.0, openness + 0.1)
                changed = True
                break
        for word in _OPENNESS_DOWN_WORDS:
            if word in msg_lower:
                openness = max(0.0, openness - 0.1)
                changed = True
                break

        if not changed:
            return profile

        return profile.model_copy(
            update={
                "hard_stops": hard_stops,
                "positive_signals": positive,
                "negative_signals": negative,
                "openness_score": round(openness, 4),
                "confidence": self._increase_confidence(profile),
            }
        )

    def _increase_confidence(self, profile: CustomerProfile, delta: float = 0.05) -> float:
        """Increment confidence, capped at 1.0."""
        return min(1.0, profile.confidence + delta)
