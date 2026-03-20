"""Embedding service using sentence-transformers (all-MiniLM-L6-v2, 384-dim)."""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer


class EmbeddingService:
    """Lazy-loaded sentence-transformer embeddings. No API key required."""

    _model: SentenceTransformer | None = None
    MODEL_NAME = "all-MiniLM-L6-v2"

    def _load(self) -> SentenceTransformer:
        if self._model is None:
            from sentence_transformers import SentenceTransformer  # noqa: PLC0415

            EmbeddingService._model = SentenceTransformer(self.MODEL_NAME)
        return self._model  # type: ignore[return-value]

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Batch-encode texts, returning a list of 384-dim float vectors."""
        model = self._load()
        return model.encode(texts, convert_to_numpy=True).tolist()

    def embed_one(self, text: str) -> list[float]:
        """Convenience wrapper for a single text."""
        return self.embed([text])[0]
