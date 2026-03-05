"""GuardrailPipeline — orchestrates all three guardrail layers."""
from enum import Enum
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
        # TODO Week 5: implement scope classifier, PII detector, toxicity filter
        return GuardrailResult(passed=True, layer="input", check_name="passthrough")

    async def check_tool_execution(
        self,
        tool_name: str,
        tool_input: Any,
        dietary_hard_stops: list[str],
        tenant_menu_dish_ids: list[str],
    ) -> GuardrailResult:
        """
        Layer 2: validate before any tool runs.
        Allergen check here is deterministic code — not a prompt.
        """
        # TODO Week 5: implement menu grounding + allergen circuit breaker
        return GuardrailResult(passed=True, layer="tool_execution", check_name="passthrough")

    async def check_output(
        self,
        response: str,
        retrieved_docs: list[str],
        tenant_menu_dish_names: list[str],
    ) -> GuardrailResult:
        """Layer 3: validate agent response before sending to user."""
        # TODO Week 5: implement hallucination check, claim verifier, scope drift
        return GuardrailResult(passed=True, layer="output", check_name="passthrough")
