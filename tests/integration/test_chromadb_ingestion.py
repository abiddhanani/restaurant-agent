"""Integration tests for ChromaDB ingestion pipeline. Uses tmp_path — no network."""
import asyncio
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import pytest

from rag.pipeline.ingest import SYNTHETIC_REVIEWS, run_ingest


@pytest.fixture()
def chroma_path(tmp_path: Path) -> str:
    return str(tmp_path / "chroma_test")


def _run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


# Patch DB lookup — no DB needed in integration tests
@pytest.fixture(autouse=True)
def no_db(monkeypatch):
    monkeypatch.setattr(
        "rag.pipeline.ingest._fetch_tenant",
        AsyncMock(return_value=None),
    )


def test_synthetic_reviews_produce_at_least_20_chunks(chroma_path):
    count = _run(run_ingest("tenant_a", chroma_path=chroma_path))
    assert count >= 20


def test_two_tenants_have_separate_collections(chroma_path):
    count_a = _run(run_ingest("tenant_a", chroma_path=chroma_path))
    count_b = _run(run_ingest("tenant_b", chroma_path=chroma_path))

    import chromadb

    client = chromadb.PersistentClient(path=chroma_path)
    col_a = client.get_collection("reviews_tenant_a")
    col_b = client.get_collection("reviews_tenant_b")

    assert col_a.count() == count_a
    assert col_b.count() == count_b
    assert col_a.count() > 0
    assert col_b.count() > 0


def test_all_metadata_keys_present(chroma_path):
    _run(run_ingest("tenant_meta", chroma_path=chroma_path))

    import chromadb

    client = chromadb.PersistentClient(path=chroma_path)
    col = client.get_collection("reviews_tenant_meta")
    result = col.peek(limit=1)
    meta = result["metadatas"][0]

    expected_keys = {"freshness_score", "rating", "source_review_id", "tenant_id", "chunk_index"}
    assert expected_keys.issubset(meta.keys())


def test_metadata_value_types(chroma_path):
    _run(run_ingest("tenant_types", chroma_path=chroma_path))

    import chromadb

    client = chromadb.PersistentClient(path=chroma_path)
    col = client.get_collection("reviews_tenant_types")
    result = col.peek(limit=5)

    for meta in result["metadatas"]:
        assert isinstance(meta["freshness_score"], float)
        assert isinstance(meta["rating"], int)
        assert isinstance(meta["source_review_id"], str)
        assert isinstance(meta["tenant_id"], str)
        assert isinstance(meta["chunk_index"], int)


def test_upsert_is_idempotent(chroma_path):
    count_first = _run(run_ingest("tenant_idem", chroma_path=chroma_path))
    count_second = _run(run_ingest("tenant_idem", chroma_path=chroma_path))

    import chromadb

    client = chromadb.PersistentClient(path=chroma_path)
    col = client.get_collection("reviews_tenant_idem")
    assert col.count() == count_first == count_second


def test_embedding_dimension_is_384(chroma_path):
    _run(run_ingest("tenant_dim", chroma_path=chroma_path))

    import chromadb

    client = chromadb.PersistentClient(path=chroma_path)
    col = client.get_collection("reviews_tenant_dim")
    result = col.get(include=["embeddings"], limit=1)
    embedding = result["embeddings"][0]
    assert len(embedding) == 384


def test_tenant_without_place_id_uses_synthetic_fallback(chroma_path):
    # _fetch_tenant returns None (no google_place_id) — already patched by autouse fixture
    count = _run(run_ingest("tenant_no_place", chroma_path=chroma_path))
    assert count >= 20
