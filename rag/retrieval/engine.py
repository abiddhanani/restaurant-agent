"""ChromaDB retrieval engine with freshness-score filtering."""
import os
from dataclasses import dataclass

import chromadb

from rag.pipeline.embeddings import EmbeddingService

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")


@dataclass
class RetrievalResult:
    text: str
    source_review_id: str
    tenant_id: str
    chunk_index: int
    freshness_score: float
    rating: int
    relevance_score: float  # 1.0 - cosine_distance


class RetrievalEngine:
    """Query ChromaDB for relevant review chunks filtered by freshness."""

    def __init__(self, chroma_path: str = CHROMA_PATH) -> None:
        self._chroma_path = chroma_path
        self._embedding_svc = EmbeddingService()
        self._client: chromadb.PersistentClient | None = None

    def _get_client(self) -> chromadb.PersistentClient:
        if self._client is None:
            self._client = chromadb.PersistentClient(path=self._chroma_path)
        return self._client

    def query(
        self,
        tenant_id: str,
        query_text: str,
        top_k: int = 5,
        min_freshness: float = 0.0,
    ) -> list[RetrievalResult]:
        """Return top-k relevant chunks for *tenant_id*, filtered by *min_freshness*.

        Results are sorted descending by relevance_score (1.0 - cosine_distance).
        Returns [] if the collection doesn't exist or no results pass the filter.
        """
        client = self._get_client()

        try:
            collection = client.get_collection(f"reviews_{tenant_id}")
        except Exception:
            return []

        query_embedding = self._embedding_svc.embed_one(query_text)

        where: dict | None = (
            {"freshness_score": {"$gte": min_freshness}} if min_freshness > 0.0 else None
        )

        try:
            raw = collection.query(
                query_embeddings=[query_embedding],
                n_results=min(top_k, collection.count()),
                where=where,
                include=["documents", "metadatas", "distances"],
            )
        except Exception:
            return []

        results: list[RetrievalResult] = []
        documents = raw.get("documents", [[]])[0]
        metadatas = raw.get("metadatas", [[]])[0]
        distances = raw.get("distances", [[]])[0]

        for text, meta, dist in zip(documents, metadatas, distances):
            results.append(
                RetrievalResult(
                    text=text,
                    source_review_id=meta["source_review_id"],
                    tenant_id=meta["tenant_id"],
                    chunk_index=int(meta["chunk_index"]),
                    freshness_score=float(meta["freshness_score"]),
                    rating=int(meta["rating"]),
                    relevance_score=round(max(0.0, min(1.0, 1.0 - dist)), 6),
                )
            )

        results.sort(key=lambda r: r.relevance_score, reverse=True)
        return results
