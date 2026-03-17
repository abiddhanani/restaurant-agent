"""Google Places API client for fetching restaurant reviews."""
import logging
import os
from datetime import datetime

import httpx
from pydantic import BaseModel, computed_field

logger = logging.getLogger(__name__)

PLACES_DETAILS_URL = "https://maps.googleapis.com/maps/api/place/details/json"


class RateLimitError(Exception):
    """Raised when Google Places API returns a rate limit error."""


class PlaceReview(BaseModel):
    """A single review from Google Places."""

    author: str
    rating: int
    text: str
    published_at: datetime

    @computed_field
    @property
    def freshness_score(self) -> float:
        age_days = (datetime.utcnow() - self.published_at).days
        return max(0.0, 1.0 - (age_days / 365))


class GooglePlacesClient:
    """Async client for the Google Places Details API."""

    def __init__(self) -> None:
        self._api_key = os.getenv("GOOGLE_PLACES_API_KEY")

    async def get_reviews(self, place_id: str) -> list[PlaceReview]:
        """Fetch reviews for a place. Raises RateLimitError on quota exceeded."""
        params = {
            "place_id": place_id,
            "fields": "reviews",
            "key": self._api_key,
        }
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(PLACES_DETAILS_URL, params=params)
                response.raise_for_status()
                data = response.json()
        except httpx.HTTPError as exc:
            logger.warning("Google Places HTTP error for place_id=%s: %s", place_id, exc)
            return []

        status = data.get("status", "")
        if status == "OVER_QUERY_LIMIT":
            raise RateLimitError(f"Google Places rate limit exceeded for place_id={place_id}")

        reviews_raw = data.get("result", {}).get("reviews", [])
        reviews: list[PlaceReview] = []
        for r in reviews_raw:
            reviews.append(
                PlaceReview(
                    author=r.get("author_name", ""),
                    rating=int(r.get("rating", 0)),
                    text=r.get("text", ""),
                    published_at=datetime.utcfromtimestamp(r["time"]),
                )
            )
        return reviews
