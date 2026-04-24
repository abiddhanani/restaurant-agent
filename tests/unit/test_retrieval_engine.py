"""Unit/integration tests for RetrievalEngine — uses tmp_path ChromaDB, no network."""
import asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from rag.pipeline.ingest import SYNTHETIC_REVIEWS, run_ingest
from rag.retrieval.engine import RetrievalEngine, RetrievalResult


# --------------------------------------------------------------------------- #
# Fixtures
# --------------------------------------------------------------------------- #

@pytest.fixture(scope="module")
def chroma_path(tmp_path_factory) -> str:
    return str(tmp_path_factory.mktemp("chroma_retrieval"))


@pytest.fixture(scope="module", autouse=True)
def ingested_data(chroma_path):
    """Ingest synthetic data for two tenants once per module."""
    with patch("rag.pipeline.ingest._fetch_tenant", new=AsyncMock(return_value=None)):
        asyncio.get_event_loop().run_until_complete(
            run_ingest("tenant_a", chroma_path=chroma_path)
        )
        asyncio.get_event_loop().run_until_complete(
            run_ingest("tenant_b", chroma_path=chroma_path)
        )


@pytest.fixture()
def engine(chroma_path) -> RetrievalEngine:
    return RetrievalEngine(chroma_path=chroma_path)


# --------------------------------------------------------------------------- #
# Tests
# --------------------------------------------------------------------------- #

def test_query_returns_list_of_results(engine):
    results = engine.query("tenant_a", "great food", top_k=3)
    assert isinstance(results, list)
    assert len(results) > 0
    assert all(isinstance(r, RetrievalResult) for r in results)


def test_query_respects_top_k(engine):
    results = engine.query("tenant_a", "pasta tiramisu", top_k=3)
    assert len(results) <= 3


def test_results_sorted_by_relevance_descending(engine):
    results = engine.query("tenant_a", "amazing food", top_k=5)
    scores = [r.relevance_score for r in results]
    assert scores == sorted(scores, reverse=True)


def test_freshness_filter_excludes_old_chunks(chroma_path):
    """Chunks from a very-old review should be excluded when min_freshness is high."""
    import chromadb
    from rag.pipeline.chunker import chunk_review
    from rag.pipeline.embeddings import EmbeddingService
    from rag.scraper.google_places import PlaceReview

    old_review = PlaceReview(
        author="OldReviewer",
        rating=5,
        text="Ancient review that should be filtered. Very old content here.",
        published_at=datetime(2020, 1, 1),  # ~6 years ago → freshness ≈ 0
    )
    client = chromadb.PersistentClient(path=chroma_path)
    col = client.get_or_create_collection("reviews_tenant_fresh")
    chunks = chunk_review(old_review, "old_src", "tenant_fresh")
    if chunks:
        svc = EmbeddingService()
        embs = svc.embed([c.text for c in chunks])
        col.upsert(
            ids=[c.chunk_id for c in chunks],
            embeddings=embs,
            documents=[c.text for c in chunks],
            metadatas=[
                {
                    "freshness_score": c.freshness_score,
                    "rating": c.rating,
                    "source_review_id": c.source_review_id,
                    "tenant_id": c.tenant_id,
                    "chunk_index": c.chunk_index,
                }
                for c in chunks
            ],
        )

    engine = RetrievalEngine(chroma_path=chroma_path)
    results = engine.query("tenant_fresh", "old content", top_k=10, min_freshness=0.5)
    for r in results:
        assert r.freshness_score >= 0.5


def test_tenant_isolation(engine):
    """Querying tenant_a must not return results with tenant_id == tenant_b."""
    results = engine.query("tenant_a", "food", top_k=10)
    for r in results:
        assert r.tenant_id == "tenant_a"


def test_result_fields_are_correct_types(engine):
    results = engine.query("tenant_a", "delicious", top_k=3)
    for r in results:
        assert isinstance(r.text, str)
        assert isinstance(r.source_review_id, str)
        assert isinstance(r.tenant_id, str)
        assert isinstance(r.chunk_index, int)
        assert isinstance(r.freshness_score, float)
        assert isinstance(r.rating, int)
        assert isinstance(r.relevance_score, float)


def test_relevance_score_bounded(engine):
    results = engine.query("tenant_a", "pasta wine dessert", top_k=5)
    for r in results:
        assert 0.0 <= r.relevance_score <= 1.0


def test_unknown_tenant_returns_empty(engine):
    results = engine.query("tenant_nonexistent", "food")
    assert results == []


def test_zero_min_freshness_returns_all_chunks(engine):
    results_no_filter = engine.query("tenant_a", "food", top_k=10, min_freshness=0.0)
    results_filtered = engine.query("tenant_a", "food", top_k=10, min_freshness=0.99)
    assert len(results_no_filter) >= len(results_filtered)


def test_realistic_query_spicy_dishes(engine):
    results = engine.query("tenant_a", "spicy dishes", top_k=5)
    assert isinstance(results, list)


def test_realistic_query_vegetarian_options(engine):
    results = engine.query("tenant_a", "vegetarian options", top_k=5)
    assert isinstance(results, list)
