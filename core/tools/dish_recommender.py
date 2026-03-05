"""Tool: recommend dishes based on user taste profile."""
from core.models.menu import Dish
from core.models.preference import UserTasteProfile
from core.tools.base import BaseTool, ToolInput, ToolOutput
from pydantic import BaseModel


class DishRecommenderInput(ToolInput):
    """Input for DishRecommenderTool."""
    taste_profile: UserTasteProfile
    top_k: int = 3


class DishRecommendation(BaseModel):
    """Single dish recommendation with reasoning."""
    dish: Dish
    match_reason: str
    confidence: float
    review_snippets: list[str] = []


class DishRecommenderOutput(ToolOutput):
    """Output for DishRecommenderTool."""
    recommendations: list[DishRecommendation] = []


class DishRecommenderTool(BaseTool):
    """
    Recommends dishes using taste profile + RAG reviews.
    Respects dietary_hard_stops — never overridden.
    Implemented Week 3-4.
    """
    name = "dish_recommender"
    description = "Recommends dishes based on user taste and verified reviews."

    async def execute(self, input_data: DishRecommenderInput) -> DishRecommenderOutput:
        """Cross-reference taste profile with menu and review embeddings."""
        # TODO Week 3: implement with RAG retrieval + preference model
        raise NotImplementedError("Implement in Week 3")
