"""Review chunking logic — splits PlaceReview text into overlapping sentence windows."""
import re

from pydantic import BaseModel

from rag.scraper.google_places import PlaceReview


class ReviewChunk(BaseModel):
    chunk_id: str
    text: str
    source_review_id: str
    tenant_id: str
    chunk_index: int
    freshness_score: float
    rating: int


def chunk_review(
    review: PlaceReview,
    source_review_id: str,
    tenant_id: str,
    min_sentences: int = 2,
    overlap: int = 1,
) -> list[ReviewChunk]:
    """Split a review into overlapping sentence-window chunks."""
    raw = review.text.strip()
    if not raw:
        return []

    sentences = re.split(r"(?<=[.!?])\s+", raw)
    sentences = [s.strip() for s in sentences if s.strip()]

    if len(sentences) <= min_sentences:
        return [
            ReviewChunk(
                chunk_id=f"{source_review_id}_chunk_0",
                text=raw,
                source_review_id=source_review_id,
                tenant_id=tenant_id,
                chunk_index=0,
                freshness_score=review.freshness_score,
                rating=review.rating,
            )
        ]

    stride = min_sentences - overlap
    chunks: list[ReviewChunk] = []
    i = 0
    while i + min_sentences <= len(sentences):
        window = sentences[i : i + min_sentences]
        chunk_text = " ".join(window).strip()
        chunks.append(
            ReviewChunk(
                chunk_id=f"{source_review_id}_chunk_{len(chunks)}",
                text=chunk_text,
                source_review_id=source_review_id,
                tenant_id=tenant_id,
                chunk_index=len(chunks),
                freshness_score=review.freshness_score,
                rating=review.rating,
            )
        )
        i += stride

    return chunks
