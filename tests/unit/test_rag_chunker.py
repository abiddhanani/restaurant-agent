"""Unit tests for rag/pipeline/chunker.py — pure function, sync."""
from datetime import datetime

import pytest

from rag.pipeline.chunker import ReviewChunk, chunk_review
from rag.scraper.google_places import PlaceReview


def _review(text: str, rating: int = 4) -> PlaceReview:
    return PlaceReview(
        author="Tester",
        rating=rating,
        text=text,
        published_at=datetime(2025, 6, 1),
    )


SOURCE_ID = "abc123"
TENANT_ID = "rest_demo"


def test_single_sentence_yields_one_chunk():
    r = _review("Great food.")
    chunks = chunk_review(r, SOURCE_ID, TENANT_ID)
    assert len(chunks) == 1
    assert chunks[0].text == "Great food."


def test_two_sentences_default_params_yields_one_chunk():
    r = _review("Great food. Amazing service.")
    chunks = chunk_review(r, SOURCE_ID, TENANT_ID)
    assert len(chunks) == 1


def test_three_sentences_yields_two_chunks_with_overlap():
    r = _review("First sentence. Second sentence. Third sentence.")
    chunks = chunk_review(r, SOURCE_ID, TENANT_ID, min_sentences=2, overlap=1)
    assert len(chunks) == 2
    # Second sentence must appear in both chunks
    assert "Second sentence" in chunks[0].text
    assert "Second sentence" in chunks[1].text


def test_five_sentences_yields_four_chunks():
    text = "One. Two. Three. Four. Five."
    r = _review(text)
    chunks = chunk_review(r, SOURCE_ID, TENANT_ID, min_sentences=2, overlap=1)
    assert len(chunks) == 4


def test_chunk_id_is_deterministic():
    r = _review("Great food. Amazing service. Will return.")
    chunks_a = chunk_review(r, SOURCE_ID, TENANT_ID)
    chunks_b = chunk_review(r, SOURCE_ID, TENANT_ID)
    assert [c.chunk_id for c in chunks_a] == [c.chunk_id for c in chunks_b]


def test_metadata_propagated_to_all_chunks():
    r = _review("Dish one was great. Dish two was okay. Dish three was fine.", rating=3)
    chunks = chunk_review(r, SOURCE_ID, TENANT_ID)
    for c in chunks:
        assert c.freshness_score == pytest.approx(r.freshness_score, abs=1e-6)
        assert c.rating == 3
        assert c.source_review_id == SOURCE_ID
        assert c.tenant_id == TENANT_ID


def test_chunk_index_sequential():
    r = _review("A. B. C. D. E.")
    chunks = chunk_review(r, SOURCE_ID, TENANT_ID, min_sentences=2, overlap=1)
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_empty_text_returns_empty_list():
    r = _review("")
    chunks = chunk_review(r, SOURCE_ID, TENANT_ID)
    assert chunks == []


def test_exclamation_and_question_mark_split_correctly():
    text = "Wow, amazing! Is the pasta good? Yes it is."
    r = _review(text)
    chunks = chunk_review(r, SOURCE_ID, TENANT_ID, min_sentences=2, overlap=1)
    # Three sentences → two chunks with overlap=1
    assert len(chunks) == 2


def test_no_leading_trailing_whitespace_in_chunks():
    r = _review("  Sentence one.  Sentence two.  Sentence three.  ")
    chunks = chunk_review(r, SOURCE_ID, TENANT_ID)
    for c in chunks:
        assert c.text == c.text.strip()
