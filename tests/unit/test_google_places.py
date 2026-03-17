"""Unit tests for GooglePlacesClient and PlaceReview."""
import time
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from rag.scraper.google_places import GooglePlacesClient, PlaceReview, RateLimitError


# ---------------------------------------------------------------------------
# PlaceReview freshness_score
# ---------------------------------------------------------------------------

def test_freshness_score_today():
    review = PlaceReview(
        author="Alice",
        rating=5,
        text="Great food!",
        published_at=datetime.utcnow(),
    )
    assert review.freshness_score == pytest.approx(1.0, abs=0.01)


def test_freshness_score_old():
    review = PlaceReview(
        author="Bob",
        rating=3,
        text="Okay.",
        published_at=datetime.utcnow() - timedelta(days=365),
    )
    assert review.freshness_score == pytest.approx(0.0, abs=0.01)


def test_freshness_score_mid():
    review = PlaceReview(
        author="Carol",
        rating=4,
        text="Pretty good.",
        published_at=datetime.utcnow() - timedelta(days=182),
    )
    assert 0.0 < review.freshness_score < 1.0


def test_freshness_score_very_old_clamps_to_zero():
    review = PlaceReview(
        author="Dave",
        rating=2,
        text="Old review.",
        published_at=datetime.utcnow() - timedelta(days=730),
    )
    assert review.freshness_score == 0.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_api_response(reviews=None, status="OK"):
    payload = {"status": status}
    if reviews is not None:
        payload["result"] = {"reviews": reviews}
    else:
        payload["result"] = {}
    return payload


def _fake_review_raw(offset_days=10):
    return {
        "author_name": "Tester",
        "rating": 4,
        "text": "Delicious!",
        "time": int((datetime.utcnow() - timedelta(days=offset_days)).timestamp()),
    }


def _mock_response(json_data, status_code=200):
    mock = MagicMock()
    mock.json.return_value = json_data
    mock.status_code = status_code
    mock.raise_for_status = MagicMock()
    return mock


# ---------------------------------------------------------------------------
# GooglePlacesClient.get_reviews
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_get_reviews_success():
    raw = _fake_review_raw(offset_days=10)
    json_data = _make_api_response(reviews=[raw])

    mock_response = _mock_response(json_data)
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("rag.scraper.google_places.httpx.AsyncClient", return_value=mock_client):
        client = GooglePlacesClient()
        reviews = await client.get_reviews("ChIJtest123")

    assert len(reviews) == 1
    assert reviews[0].author == "Tester"
    assert reviews[0].rating == 4
    assert reviews[0].text == "Delicious!"
    assert 0.0 < reviews[0].freshness_score <= 1.0


@pytest.mark.asyncio
async def test_get_reviews_no_reviews_field():
    json_data = _make_api_response(reviews=None)

    mock_response = _mock_response(json_data)
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("rag.scraper.google_places.httpx.AsyncClient", return_value=mock_client):
        client = GooglePlacesClient()
        reviews = await client.get_reviews("ChIJtest123")

    assert reviews == []


@pytest.mark.asyncio
async def test_get_reviews_http_error_returns_empty():
    import httpx as _httpx

    mock_client = AsyncMock()
    mock_client.get = AsyncMock(side_effect=_httpx.HTTPError("connection failed"))
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("rag.scraper.google_places.httpx.AsyncClient", return_value=mock_client):
        client = GooglePlacesClient()
        reviews = await client.get_reviews("ChIJtest123")

    assert reviews == []


@pytest.mark.asyncio
async def test_get_reviews_rate_limit_raises():
    json_data = _make_api_response(reviews=None, status="OVER_QUERY_LIMIT")

    mock_response = _mock_response(json_data)
    mock_client = AsyncMock()
    mock_client.get = AsyncMock(return_value=mock_response)
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)

    with patch("rag.scraper.google_places.httpx.AsyncClient", return_value=mock_client):
        client = GooglePlacesClient()
        with pytest.raises(RateLimitError):
            await client.get_reviews("ChIJtest123")
