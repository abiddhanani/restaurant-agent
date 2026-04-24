"""Tool: cross-reference catalog + customer profile + reviews to recommend items."""
import os
from typing import Optional

from pydantic import BaseModel, Field
from sqlmodel import select

from core.db.session import get_session
from core.models.menu import CatalogItem, CatalogItemRead
from core.tools.base import BaseTool, ToolInput, ToolOutput
from rag.retrieval.engine import RetrievalEngine

_CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")

# Stop-words excluded from query keyword matching
_STOP_WORDS = {"the", "a", "an", "and", "or", "is", "i", "want", "like", "some", "me", "can", "you"}


class RecommenderInput(ToolInput):
    """Input for RecommenderTool."""
    query: str = Field(description="User's free-text preference query")
    hard_stops: list[str] = Field(default_factory=list)
    positive_signals: list[str] = Field(default_factory=list)
    negative_signals: list[str] = Field(default_factory=list)
    top_n: int = Field(default=3)


class Recommendation(BaseModel):
    """A single item recommendation with scoring rationale."""
    item_id: str
    name: str
    category: str
    price: float
    match_reason: str
    review_snippet: Optional[str] = None
    score: float


class RecommenderOutput(ToolOutput):
    """Output for RecommenderTool."""
    recommendations: list[Recommendation] = Field(default_factory=list)


class RecommenderTool(BaseTool):
    """Cross-references catalog, customer profile, and reviews to recommend items."""

    name = "recommender"
    description = (
        "Recommends top items by cross-referencing the catalog with the user's preference profile "
        "and customer reviews. Always respects hard-stop constraints."
    )

    def __init__(self, chroma_path: str = _CHROMA_PATH) -> None:
        self._engine = RetrievalEngine(chroma_path=chroma_path)

    async def execute(self, input_data: RecommenderInput) -> RecommenderOutput:
        """Score and rank catalog items for the user's preference profile."""
        # 1. Fetch available items from DB
        async with get_session() as session:
            q = (
                select(CatalogItem)
                .where(CatalogItem.tenant_id == input_data.tenant_id)
                .where(CatalogItem.is_available == True)  # noqa: E712
            )
            rows = await session.exec(q)
            items = [CatalogItemRead.from_db(row) for row in rows.all()]

        if not items:
            return RecommenderOutput(success=True, recommendations=[], confidence=0.0)

        # 2. HARD STOP CONSTRAINT CHECK — cannot be overridden by LLM
        stops_lower = {s.lower() for s in input_data.hard_stops}
        safe_items = [
            item for item in items
            if not any(c.lower() in stops_lower for c in item.constraints)
        ]

        if not safe_items:
            return RecommenderOutput(success=True, recommendations=[], confidence=0.5)

        # 3. Score each item by preference signal overlap
        pos_lower = [s.lower() for s in input_data.positive_signals]
        neg_lower = [s.lower() for s in input_data.negative_signals]
        query_words = set(input_data.query.lower().split()) - _STOP_WORDS

        scored: list[tuple[CatalogItemRead, float, list[str]]] = []
        for item in safe_items:
            haystack = (
                f"{item.name} {item.description} {' '.join(item.tags)}"
            ).lower()
            score = 0.0
            reasons: list[str] = []

            for sig in pos_lower:
                if sig in haystack:
                    score += 0.2
                    reasons.append(f"matches your preference for {sig}")

            for sig in neg_lower:
                if sig in haystack:
                    score -= 0.3

            overlap = query_words & set(haystack.split())
            if overlap:
                score += 0.15 * min(len(overlap), 4)
                top_words = sorted(overlap)[:3]
                reasons.append(f"fits your request for {', '.join(top_words)}")

            scored.append((item, score, reasons))

        # Sort and take top 2× candidates before review enrichment
        scored.sort(key=lambda x: x[1], reverse=True)
        candidates = scored[: input_data.top_n * 2]

        # 4. Augment candidates with review sentiment
        enriched: list[tuple[CatalogItemRead, float, str, Optional[str]]] = []
        for item, base_score, reasons in candidates:
            review_results = self._engine.query(
                tenant_id=input_data.tenant_id,
                query_text=item.name,
                top_k=3,
                min_freshness=0.2,
            )
            review_bonus = 0.0
            snippet: Optional[str] = None
            if review_results:
                avg_relevance = sum(r.relevance_score for r in review_results) / len(review_results)
                avg_rating = sum(r.rating for r in review_results) / len(review_results)
                review_bonus = (avg_relevance * 0.5 + (avg_rating / 5.0) * 0.5) * 0.4
                snippet = review_results[0].text[:200]
                reasons = [*reasons, f"avg customer rating {avg_rating:.1f}/5"]

            final_score = round(base_score + review_bonus, 4)
            match_reason = "; ".join(reasons) if reasons else "popular item"
            enriched.append((item, final_score, match_reason, snippet))

        enriched.sort(key=lambda x: x[1], reverse=True)

        recommendations = [
            Recommendation(
                item_id=item.item_id,
                name=item.name,
                category=item.category,
                price=item.price,
                match_reason=match_reason,
                review_snippet=snippet,
                score=score,
            )
            for item, score, match_reason, snippet in enriched[: input_data.top_n]
        ]

        # Confidence scales with how much profile signal we have
        n_signals = len(input_data.positive_signals) + len(input_data.hard_stops)
        confidence = round(min(1.0, 0.4 + 0.1 * n_signals), 2)

        return RecommenderOutput(
            success=True,
            recommendations=recommendations,
            confidence=confidence,
        )


# Backward-compatible aliases
DishRecommenderInput = RecommenderInput
DishRecommendation = Recommendation
DishRecommenderOutput = RecommenderOutput
DishRecommenderTool = RecommenderTool
