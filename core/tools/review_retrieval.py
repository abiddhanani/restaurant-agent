"""Tool: semantic review retrieval from ChromaDB."""
from core.tools.base import BaseTool, ToolInput, ToolOutput
from pydantic import BaseModel
from typing import Optional


class ReviewRetrievalInput(ToolInput):
    """Input for ReviewRetrievalTool."""
    query: str
    top_k: int = 5
    min_freshness_score: float = 0.3


class ReviewSnippet(BaseModel):
    """Single retrieved review snippet."""
    text: str
    source: str  # google_places | yelp
    rating: float
    freshness_score: float
    dish_mentioned: Optional[str] = None


class ReviewRetrievalOutput(ToolOutput):
    """Output for ReviewRetrievalTool."""
    snippets: list[ReviewSnippet] = []


class ReviewRetrievalTool(BaseTool):
    """
    Semantic search over tenant review vector store.
    Filters by freshness score. Implemented Week 2.
    """
    name = "review_retrieval"
    description = "Retrieves relevant review snippets from verified sources."

    async def execute(self, input_data: ReviewRetrievalInput) -> ReviewRetrievalOutput:
        """Query ChromaDB for relevant review chunks."""
        # TODO Week 2: implement against ChromaDB retrieval engine
        raise NotImplementedError("Implement in Week 2")
