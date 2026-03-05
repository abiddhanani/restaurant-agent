"""Pydantic models for evaluation pipeline."""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class ConversationTurn(BaseModel):
    """Single turn in a golden dataset conversation."""
    role: str
    content: str


class EvalScores(BaseModel):
    """Rubric scores for a single golden conversation."""
    task_completion: int = Field(..., ge=0, le=1, description="Did agent complete the user's goal?")
    hallucination_free: int = Field(..., ge=0, le=1, description="No invented dishes or reviews?")
    allergen_safe: int = Field(..., ge=0, le=1, description="Respected all dietary hard stops?")
    on_scope: int = Field(..., ge=0, le=1, description="Stayed on food/restaurant topic?")

    @property
    def overall(self) -> float:
        """Average score across all dimensions."""
        scores = [self.task_completion, self.hallucination_free, self.allergen_safe, self.on_scope]
        return sum(scores) / len(scores)


class GoldenConversation(BaseModel):
    """Single entry in the golden evaluation dataset."""
    id: str
    description: str
    tenant_id: str
    conversation: list[ConversationTurn]
    expected_dishes_mentioned: list[str] = []
    expected_allergens_blocked: list[str] = []
    tags: list[str] = []
    expected_scores: EvalScores


class EvalResult(BaseModel):
    """Result of running a single golden conversation through the agent."""
    golden_id: str
    passed: bool
    actual_scores: EvalScores
    expected_scores: EvalScores
    agent_response: str
    failure_reasons: list[str] = []
    run_at: datetime = Field(default_factory=datetime.utcnow)


class EvalReport(BaseModel):
    """Aggregated evaluation report across all golden conversations."""
    total: int
    passed: int
    failed: int
    pass_rate: float
    avg_task_completion: float
    avg_hallucination_free: float
    avg_allergen_safe: float
    avg_on_scope: float
    results: list[EvalResult]
    run_at: datetime = Field(default_factory=datetime.utcnow)

    @property
    def meets_threshold(self) -> bool:
        """True if pass rate >= 0.85 across all dimensions."""
        return self.pass_rate >= 0.85
