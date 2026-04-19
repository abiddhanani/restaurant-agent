"""Customer preference model — evolves through conversation."""
from datetime import datetime
from pydantic import BaseModel, Field


class CustomerProfile(BaseModel):
    """
    Builds incrementally from conversation signals.
    Never populated via a form — only from natural conversation.
    hard_stops is the single source of truth for constraint guardrails.
    """
    session_id: str
    tenant_id: str
    positive_signals: list[str] = Field(
        default_factory=list,
        description="e.g. loves spicy, enjoys bold flavours, wants volume"
    )
    negative_signals: list[str] = Field(
        default_factory=list,
        description="e.g. dislikes cilantro, no chemical treatments"
    )
    hard_stops: list[str] = Field(
        default_factory=list,
        description="Non-negotiables fed directly to Layer 2 guardrails (allergens, sensitivities, budget limits)."
    )
    openness_score: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="0=safe/familiar, 1=adventurous/experimental. Inferred from conversation."
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="How much signal gathered. Low = recommend popular items."
    )
    derived_at: datetime = Field(default_factory=datetime.utcnow)
