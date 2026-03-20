"""GuardrailPipeline — orchestrates all three guardrail layers."""
from typing import Any, Optional
from pydantic import BaseModel


class GuardrailResult(BaseModel):
    """Result from a guardrail check."""
    passed: bool
    layer: str
    check_name: str
    reason: Optional[str] = None
    blocked_content: Optional[str] = None


class GuardrailViolation(Exception):
    """Raised when a guardrail hard-blocks execution."""
    def __init__(self, result: GuardrailResult):
        self.result = result
        super().__init__(f"Guardrail [{result.layer}/{result.check_name}] blocked: {result.reason}")


class GuardrailPipeline:
    """
    Three-layer guardrail system.
    Layer 1: Input validation (before LLM)
    Layer 2: Tool execution validation (before tools run)
    Layer 3: Output validation (before response sent)

    Allergen circuit breaker in Layer 2 is CODE — it cannot be
    softened, overridden, or bypassed by the LLM under any circumstances.
    """

    async def check_input(self, message: str, tenant_id: str) -> GuardrailResult:
        """Layer 1: validate user input before LLM sees it."""
        from core.guardrails.layer1_input import ScopeClassifier, PIIDetector, ToxicityFilter

        for checker in (ToxicityFilter(), ScopeClassifier(), PIIDetector()):
            result = checker.check(message)
            if not result.passed:
                return result
        return GuardrailResult(passed=True, layer="input", check_name="all_passed")

    async def check_tool_execution(
        self,
        tool_name: str,
        tool_input: Any,
        dietary_hard_stops: list[str],
        tenant_menu_dish_names: list[str],
    ) -> GuardrailResult:
        """
        Layer 2: validate before any tool runs.
        Allergen check here is deterministic code — not a prompt.
        """
        from core.guardrails.layer2_tool import AllergenCircuitBreaker, MenuGroundingValidator

        # Allergen circuit breaker: check dish_allergens if provided in tool_input
        dish_allergens = tool_input.get("dish_allergens", []) if isinstance(tool_input, dict) else []
        if dish_allergens and dietary_hard_stops:
            result = AllergenCircuitBreaker().check(dish_allergens, dietary_hard_stops)
            if not result.passed:
                return result

        # Menu grounding: check dish_name if provided
        dish_name = tool_input.get("dish_name", "") if isinstance(tool_input, dict) else ""
        if dish_name and tenant_menu_dish_names:
            result = MenuGroundingValidator().check(dish_name, tenant_menu_dish_names)
            if not result.passed:
                return result

        return GuardrailResult(passed=True, layer="tool_execution", check_name="all_passed")

    async def check_output(
        self,
        response: str,
        retrieved_docs: list[str],
        tenant_menu_dish_names: list[str],
    ) -> GuardrailResult:
        """Layer 3: validate agent response before sending to user."""
        from core.guardrails.layer3_output import HallucinationChecker, ClaimVerifier, ScopeDriftChecker

        for checker, args in [
            (ScopeDriftChecker(), (response,)),
            (ClaimVerifier(), (response, retrieved_docs)),
            (HallucinationChecker(), (response, tenant_menu_dish_names)),
        ]:
            result = checker.check(*args)
            if not result.passed:
                return result

        return GuardrailResult(passed=True, layer="output", check_name="all_passed")
