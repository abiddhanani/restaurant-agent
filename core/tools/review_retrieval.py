"""Tool: semantic review retrieval from ChromaDB."""
import os
from typing import Optional

from pydantic import BaseModel

from core.tools.base import BaseTool, ToolInput, ToolOutput
from rag.retrieval.engine import RetrievalEngine

_CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")


class ReviewRetrievalInput(ToolInput):
    """Input for ReviewRetrievalTool."""
    query: str
    top_k: int = 5
    min_freshness_score: float = 0.3


class ReviewSnippet(BaseModel):
    """Single retrieved review snippet."""
    text: str
    source: str  # google_places (only source in Phase 0)
    rating: float
    freshness_score: float
    relevance_score: float
    dish_mentioned: Optional[str] = None


class ReviewRetrievalOutput(ToolOutput):
    """Output for ReviewRetrievalTool."""
    snippets: list[ReviewSnippet] = []


class ReviewRetrievalTool(BaseTool):
    """Semantic search over tenant review vector store with freshness filtering."""

    name = "review_retrieval"
    description = "Retrieves relevant review snippets from verified customer reviews."

    def __init__(self, chroma_path: str = _CHROMA_PATH) -> None:
        self._engine = RetrievalEngine(chroma_path=chroma_path)

    async def execute(self, input_data: ReviewRetrievalInput) -> ReviewRetrievalOutput:
        """Query ChromaDB for relevant review chunks, filtered by freshness."""
        results = self._engine.query(
            tenant_id=input_data.tenant_id,
            query_text=input_data.query,
            top_k=input_data.top_k,
            min_freshness=input_data.min_freshness_score,
        )
        snippets = [
            ReviewSnippet(
                text=r.text,
                source="google_places",
                rating=float(r.rating),
                freshness_score=r.freshness_score,
                relevance_score=r.relevance_score,
            )
            for r in results
        ]
        return ReviewRetrievalOutput(success=True, snippets=snippets)
