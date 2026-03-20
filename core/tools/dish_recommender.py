"""Tool: cross-reference menu + taste profile + reviews to recommend dishes."""
import os
from typing import Optional

from pydantic import BaseModel, Field
from sqlmodel import select

from core.db.session import get_session
from core.models.menu import MenuItem, MenuItemRead
from core.tools.base import BaseTool, ToolInput, ToolOutput
from rag.retrieval.engine import RetrievalEngine

_CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")

# Stop-words excluded from query keyword matching
_STOP_WORDS = {"the", "a", "an", "and", "or", "is", "i", "want", "like", "some", "me", "can", "you"}


class DishRecommenderInput(ToolInput):
    """Input for DishRecommenderTool."""
    query: str = Field(description="User's free-text preference query")
    allergen_stops: list[str] = Field(default_factory=list)
    positive_signals: list[str] = Field(default_factory=list)
    negative_signals: list[str] = Field(default_factory=list)
    top_n: int = Field(default=3)


class DishRecommendation(BaseModel):
    """A single dish recommendation with scoring rationale."""
    dish_id: str
    name: str
    category: str
    price: float
    match_reason: str
    review_snippet: Optional[str] = None
    score: float


class DishRecommenderOutput(ToolOutput):
    """Output for DishRecommenderTool."""
    recommendations: list[DishRecommendation] = Field(default_factory=list)


class DishRecommenderTool(BaseTool):
    """Cross-references menu, taste profile, and reviews to recommend dishes."""

    name = "dish_recommender"
    description = (
        "Recommends top dishes by cross-referencing the menu with the user's taste profile "
        "and customer reviews. Always respects allergen hard stops."
    )

    def __init__(self, chroma_path: str = _CHROMA_PATH) -> None:
        self._engine = RetrievalEngine(chroma_path=chroma_path)

    async def execute(self, input_data: DishRecommenderInput) -> DishRecommenderOutput:
        """Score and rank menu items for the user's taste profile."""
        # 1. Fetch available menu items from DB
        async with get_session() as session:
            q = (
                select(MenuItem)
                .where(MenuItem.tenant_id == input_data.tenant_id)
                .where(MenuItem.is_available == True)  # noqa: E712
            )
            rows = await session.exec(q)
            items = [MenuItemRead.from_db(row) for row in rows.all()]

        if not items:
            return DishRecommenderOutput(success=True, recommendations=[], confidence=0.0)

        # 2. ALLERGEN CIRCUIT BREAKER — hard filter, cannot be overridden by LLM
        stops_lower = {s.lower() for s in input_data.allergen_stops}
        safe_items = [
            item for item in items
            if not any(a.lower() in stops_lower for a in item.allergens)
        ]

        if not safe_items:
            return DishRecommenderOutput(success=True, recommendations=[], confidence=0.5)

        # 3. Score each dish by preference signal overlap
        pos_lower = [s.lower() for s in input_data.positive_signals]
        neg_lower = [s.lower() for s in input_data.negative_signals]
        query_words = set(input_data.query.lower().split()) - _STOP_WORDS

        scored: list[tuple[MenuItemRead, float, list[str]]] = []
        for item in safe_items:
            haystack = (
                f"{item.name} {item.description} {' '.join(item.dietary_tags)}"
            ).lower()
            score = 0.0
            reasons: list[str] = []

            for sig in pos_lower:
                if sig in haystack:
                    score += 0.2
                    reasons.append(f"matches your love of {sig}")

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
        enriched: list[tuple[MenuItemRead, float, str, Optional[str]]] = []
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
            match_reason = "; ".join(reasons) if reasons else "popular menu item"
            enriched.append((item, final_score, match_reason, snippet))

        enriched.sort(key=lambda x: x[1], reverse=True)

        recommendations = [
            DishRecommendation(
                dish_id=item.dish_id,
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
        n_signals = len(input_data.positive_signals) + len(input_data.allergen_stops)
        confidence = round(min(1.0, 0.4 + 0.1 * n_signals), 2)

        return DishRecommenderOutput(
            success=True,
            recommendations=recommendations,
            confidence=confidence,
        )
