"""Layer 2 tool-execution guardrails: allergen circuit breaker + menu grounding."""
from core.guardrails.pipeline import GuardrailResult


class AllergenCircuitBreaker:
    """
    Hard-coded allergen check — cannot be overridden by LLM.
    Blocks tool execution if the requested dish contains any of the user's
    dietary_hard_stops. This is pure code comparison, not a prompt.
    """

    def check(
        self,
        dish_allergens: list[str],
        dietary_hard_stops: list[str],
    ) -> GuardrailResult:
        stops_lower = {s.lower() for s in dietary_hard_stops}
        allergens_lower = {a.lower() for a in dish_allergens}
        overlap = stops_lower & allergens_lower
        if overlap:
            return GuardrailResult(
                passed=False,
                layer="tool_execution",
                check_name="allergen_circuit_breaker",
                reason=f"Dish contains allergen(s) matching hard stops: {', '.join(sorted(overlap))}",
                blocked_content=str(dish_allergens),
            )
        return GuardrailResult(
            passed=True,
            layer="tool_execution",
            check_name="allergen_circuit_breaker",
        )


class MenuGroundingValidator:
    """
    Ensures that any dish referenced by the LLM actually exists in the tenant menu.
    Blocks phantom/hallucinated dish names.
    """

    def check(
        self,
        dish_name: str,
        tenant_menu_dish_names: list[str],
    ) -> GuardrailResult:
        normalised_name = dish_name.strip().lower()
        normalised_menu = [d.lower() for d in tenant_menu_dish_names]
        if normalised_name not in normalised_menu:
            return GuardrailResult(
                passed=False,
                layer="tool_execution",
                check_name="menu_grounding",
                reason=f"Dish '{dish_name}' does not exist on the menu.",
                blocked_content=dish_name,
            )
        return GuardrailResult(
            passed=True,
            layer="tool_execution",
            check_name="menu_grounding",
        )
