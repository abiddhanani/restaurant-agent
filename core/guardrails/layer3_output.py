"""Layer 3 output guardrails: hallucination check, claim verifier, scope drift."""
import re

from core.guardrails.pipeline import GuardrailResult

# ---------------------------------------------------------------------------
# Hallucination checker
# ---------------------------------------------------------------------------

# Patterns that indicate the LLM is introducing a specific item name
_ITEM_INTRO_PATTERNS = [
    re.compile(r"\b(?:try|recommend|suggest|order|have|get)\s+(?:the\s+)?([A-Z][A-Za-z\s']{2,30}?)(?:\s*[,!.]|$)", re.M | re.I),
    re.compile(r"\bthe\s+([A-Z][A-Za-z\s']{2,25})(?:\s+is\b|\s+dish\b|\s+here\b|\s+service\b|\s+plan\b)", re.M),
]


def _extract_capitalised_phrases(text: str) -> list[str]:
    """Extract capitalised noun phrases (likely item names) from text."""
    phrases: list[str] = []
    for pattern in _ITEM_INTRO_PATTERNS:
        for match in pattern.finditer(text):
            phrase = match.group(1).strip()
            if phrase and phrase[0].isupper() and 2 <= len(phrase.split()) <= 5:
                phrases.append(phrase)
    return phrases


class HallucinationChecker:
    """
    Verifies that capitalised item-like phrases in the response actually
    exist in the tenant catalog. Blocks hallucinated item names.
    """

    def check(
        self,
        response: str,
        catalog_item_names: list[str],
    ) -> GuardrailResult:
        if not catalog_item_names:
            return GuardrailResult(passed=True, layer="output", check_name="hallucination_checker")

        catalog_lower = {n.lower() for n in catalog_item_names}
        candidate_phrases = _extract_capitalised_phrases(response)

        for phrase in candidate_phrases:
            if phrase.lower() not in catalog_lower:
                return GuardrailResult(
                    passed=False,
                    layer="output",
                    check_name="hallucination_checker",
                    reason=f"Response mentions '{phrase}' which is not in the catalog.",
                    blocked_content=phrase,
                )

        return GuardrailResult(passed=True, layer="output", check_name="hallucination_checker")


# ---------------------------------------------------------------------------
# Claim verifier
# ---------------------------------------------------------------------------

_QUOTE_PATTERN = re.compile(r'"([^"]{10,200})"')


class ClaimVerifier:
    """
    Verifies that quoted text in the response appears in the retrieved documents.
    Blocks fabricated quotes.
    """

    def check(
        self,
        response: str,
        retrieved_docs: list[str],
    ) -> GuardrailResult:
        quotes = _QUOTE_PATTERN.findall(response)
        if not quotes:
            return GuardrailResult(passed=True, layer="output", check_name="claim_verifier")

        combined_docs = " ".join(retrieved_docs).lower()
        for quote in quotes:
            if quote.lower() not in combined_docs:
                return GuardrailResult(
                    passed=False,
                    layer="output",
                    check_name="claim_verifier",
                    reason=f"Quote not found in retrieved documents: \"{quote[:80]}\"",
                    blocked_content=quote,
                )

        return GuardrailResult(passed=True, layer="output", check_name="claim_verifier")


# ---------------------------------------------------------------------------
# Scope drift checker
# ---------------------------------------------------------------------------

_DRIFT_PATTERNS = [
    re.compile(r"\b(invest|stock market|portfolio|crypto)\b", re.I),
    re.compile(r"\b(diagnos\w*|prescri\w*|medical advice|symptom\w*|treatment)\b", re.I),
    re.compile(r"\b(legal advice|attorney|lawsuit|sue)\b", re.I),
    re.compile(r"\b(vote for|political party|candidate|election result)\b", re.I),
]


class ScopeDriftChecker:
    """Checks that the response hasn't drifted into off-topic territory."""

    def check(self, response: str) -> GuardrailResult:
        for pattern in _DRIFT_PATTERNS:
            if pattern.search(response):
                return GuardrailResult(
                    passed=False,
                    layer="output",
                    check_name="scope_drift",
                    reason="Response contains off-topic content.",
                    blocked_content=response[:200],
                )
        return GuardrailResult(passed=True, layer="output", check_name="scope_drift")
