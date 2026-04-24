"""Integration tests for GooglePlacesClient — require a real API key."""
import os

import pytest

from rag.scraper.google_places import GooglePlacesClient

# Well-known place: Google Sydney office (stable, has reviews)
_TEST_PLACE_ID = "ChIJN1t_tDeuEmsRUsoyG83frY4"


@pytest.mark.skipif(
    not os.getenv("GOOGLE_PLACES_API_KEY"),
    reason="GOOGLE_PLACES_API_KEY not set — skipped in CI",
)
@pytest.mark.asyncio
async def test_get_reviews_real_api():
    client = GooglePlacesClient()
    reviews = await client.get_reviews(_TEST_PLACE_ID)

    assert isinstance(reviews, list)
    assert len(reviews) > 0

    for review in reviews:
        assert review.author
        assert 1 <= review.rating <= 5
        assert isinstance(review.text, str)
        assert 0.0 <= review.freshness_score <= 1.0
