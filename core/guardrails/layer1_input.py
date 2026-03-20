"""Layer 1 input guardrails: scope classifier, PII detector, toxicity filter."""
import re

from core.guardrails.pipeline import GuardrailResult

# ---------------------------------------------------------------------------
# Scope classifier — food/restaurant keywords
# ---------------------------------------------------------------------------

_FOOD_KEYWORDS = {
    "menu", "dish", "dishes", "food", "eat", "eating", "drink", "drinks",
    "order", "ordering", "recommend", "recommendation", "suggestions", "suggest",
    "restaurant", "cuisine", "meal", "meals", "appetizer", "starter", "main",
    "dessert", "desserts", "snack", "beverage", "beverages", "wine", "beer",
    "cocktail", "vegan", "vegetarian", "gluten", "dairy", "allergen", "allergy",
    "allergies", "spicy", "mild", "taste", "flavour", "flavor", "chef", "cook",
    "ingredient", "ingredients", "calories", "nutrition", "price", "cost",
    "special", "specials", "today", "available", "availability", "table",
    "reservation", "booking", "takeaway", "delivery", "dine", "dining",
    "pasta", "pizza", "burger", "sushi", "salad", "soup", "steak", "seafood",
    "chicken", "lamb", "beef", "pork", "fish", "prawn", "shrimp", "tofu",
    "halal", "kosher", "organic", "fresh", "seasonal", "local", "review",
    "reviews", "rating", "what", "which", "can", "could", "have", "like",
    "want", "need", "looking", "something", "anything", "everything",
}

_OUT_OF_SCOPE_PATTERNS = [
    re.compile(r"\b(stock|stocks|invest|investment|portfolio|crypto|bitcoin|forex)\b", re.I),
    re.compile(r"\b(medical|diagnosis|diagnose|prescription|symptom|disease|illness|doctor|therapy|treatment)\b", re.I),
    re.compile(r"\b(politics|election|vote|president|congress|senate|democrat|republican)\b", re.I),
    re.compile(r"\b(hack|hacking|exploit|vulnerability|malware|ransomware|phishing)\b", re.I),
    re.compile(r"\b(legal advice|lawsuit|attorney|lawyer|sue|litigation)\b", re.I),
]


class ScopeClassifier:
    """Blocks messages unrelated to food/restaurant domain."""

    def check(self, message: str) -> GuardrailResult:
        lower = message.lower()
        words = set(re.findall(r"\b\w+\b", lower))

        # If any hard out-of-scope pattern matches, block
        for pattern in _OUT_OF_SCOPE_PATTERNS:
            if pattern.search(lower):
                return GuardrailResult(
                    passed=False,
                    layer="input",
                    check_name="scope_classifier",
                    reason="Message appears to be out of scope for a restaurant assistant.",
                    blocked_content=message,
                )

        # If no food keyword overlap AND message is longer than a trivial greeting, block
        if len(words) > 4 and not (words & _FOOD_KEYWORDS):
            return GuardrailResult(
                passed=False,
                layer="input",
                check_name="scope_classifier",
                reason="I can only help with food, menu, and restaurant-related questions.",
                blocked_content=message,
            )

        return GuardrailResult(passed=True, layer="input", check_name="scope_classifier")


# ---------------------------------------------------------------------------
# PII detector — scrubs email, phone, SSN, credit card
# ---------------------------------------------------------------------------

_PII_PATTERNS = [
    ("email", re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b")),
    ("ssn", re.compile(r"\b\d{3}[-\s]\d{2}[-\s]\d{4}\b")),
    ("credit_card", re.compile(r"\b(?:\d[ -]?){15,16}\b")),
    ("phone", re.compile(r"\b(\+?\d[\d\s\-().]{7,}\d)\b")),
]


def _scrub_pii(text: str) -> str:
    for label, pattern in _PII_PATTERNS:
        text = pattern.sub(f"[{label.upper()}_REDACTED]", text)
    return text


class PIIDetector:
    """Detects and scrubs PII from user messages."""

    def check(self, message: str) -> GuardrailResult:
        for label, pattern in _PII_PATTERNS:
            if pattern.search(message):
                scrubbed = _scrub_pii(message)
                return GuardrailResult(
                    passed=True,  # allow but flag — scrubbed content passed along
                    layer="input",
                    check_name="pii_detector",
                    reason=f"PII detected and scrubbed ({label})",
                    blocked_content=scrubbed,
                )
        return GuardrailResult(passed=True, layer="input", check_name="pii_detector")


# ---------------------------------------------------------------------------
# Toxicity filter — keyword blocklist
# ---------------------------------------------------------------------------

_TOXIC_WORDS = {
    "hate", "kill", "murder", "rape", "terrorist", "bomb", "suicide",
    "slur", "racist", "sexist", "nazi", "genocide",
}


class ToxicityFilter:
    """Blocks messages containing toxic or abusive language."""

    def check(self, message: str) -> GuardrailResult:
        lower = message.lower()
        words = set(re.findall(r"\b\w+\b", lower))
        hits = words & _TOXIC_WORDS
        if hits:
            return GuardrailResult(
                passed=False,
                layer="input",
                check_name="toxicity_filter",
                reason="Message contains language that cannot be processed.",
                blocked_content=message,
            )
        return GuardrailResult(passed=True, layer="input", check_name="toxicity_filter")
