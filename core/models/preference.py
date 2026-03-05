"""User taste preference model — evolves through conversation."""
from datetime import datetime
from pydantic import BaseModel, Field


class UserTasteProfile(BaseModel):
    """
    Builds incrementally from conversation signals.
    Never populated via a form — only from natural conversation.
    dietary_hard_stops is the single source of truth for allergen guardrails.
    """
    session_id: str
    tenant_id: str
    positive_signals: list[str] = Field(
        default_factory=list,
        description="e.g. loves spicy, enjoys umami, prefers bold flavours"
    )
    negative_signals: list[str] = Field(
        default_factory=list,
        description="e.g. dislikes cilantro, finds lamb too rich"
    )
    dietary_hard_stops: list[str] = Field(
        default_factory=list,
        description="Allergens and non-negotiables. Fed directly to Layer 2 guardrails."
    )
    adventure_score: float = Field(
        default=0.5, ge=0.0, le=1.0,
        description="0=safe/familiar, 1=adventurous. Inferred from conversation."
    )
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0,
        description="How much signal gathered. Low = recommend popular dishes."
    )
    derived_at: datetime = Field(default_factory=datetime.utcnow)
