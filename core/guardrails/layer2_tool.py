"""Layer 2 tool-execution guardrails: hard-stop constraint checker + catalog grounding."""
from core.guardrails.pipeline import GuardrailResult


class HardStopChecker:
    """
    Hard-coded constraint check — cannot be overridden by LLM.
    Blocks tool execution if the requested item contains any of the user's
    hard_stops. This is pure code comparison, not a prompt.
    """

    def check(
        self,
        item_constraints: list[str],
        hard_stops: list[str],
    ) -> GuardrailResult:
        stops_lower = {s.lower() for s in hard_stops}
        constraints_lower = {c.lower() for c in item_constraints}
        overlap = stops_lower & constraints_lower
        if overlap:
            return GuardrailResult(
                passed=False,
                layer="tool_execution",
                check_name="hard_stop_checker",
                reason=f"Item contains constraint(s) matching hard stops: {', '.join(sorted(overlap))}",
                blocked_content=str(item_constraints),
            )
        return GuardrailResult(
            passed=True,
            layer="tool_execution",
            check_name="hard_stop_checker",
        )


class CatalogGroundingValidator:
    """
    Ensures that any item referenced by the LLM actually exists in the tenant catalog.
    Blocks phantom/hallucinated item names.
    """

    def check(
        self,
        item_name: str,
        catalog_item_names: list[str],
    ) -> GuardrailResult:
        normalised_name = item_name.strip().lower()
        normalised_catalog = [n.lower() for n in catalog_item_names]
        if normalised_name not in normalised_catalog:
            return GuardrailResult(
                passed=False,
                layer="tool_execution",
                check_name="catalog_grounding",
                reason=f"Item '{item_name}' does not exist in the catalog.",
                blocked_content=item_name,
            )
        return GuardrailResult(
            passed=True,
            layer="tool_execution",
            check_name="catalog_grounding",
        )


# Backward-compatible aliases
AllergenCircuitBreaker = HardStopChecker
MenuGroundingValidator = CatalogGroundingValidator
