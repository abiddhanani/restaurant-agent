"""CLI ingestion script: fetch reviews → chunk → embed → upsert into ChromaDB.

Usage:
    uv run python rag/pipeline/ingest.py --tenant restaurant_demo
"""
import argparse
import asyncio
import hashlib
import logging
import os
from datetime import datetime

import chromadb

from core.db.session import get_session
from core.models.tenant import TenantConfig
from rag.pipeline.chunker import chunk_review
from rag.pipeline.embeddings import EmbeddingService
from rag.scraper.google_places import GooglePlacesClient, PlaceReview
from sqlmodel import select

logger = logging.getLogger(__name__)

CHROMA_PATH = os.getenv("CHROMA_PATH", "./chroma_db")

SYNTHETIC_REVIEWS: list[PlaceReview] = [
    PlaceReview(
        author="Alice",
        rating=5,
        text=(
            "The pasta here is absolutely incredible. "
            "The sauce is rich and perfectly seasoned. "
            "I've been coming here for years and it never disappoints. "
            "Highly recommend the carbonara. "
            "The fresh bread they serve beforehand is also fantastic. "
            "This is my favourite restaurant in the city."
        ),
        published_at=datetime(2025, 12, 1),
    ),
    PlaceReview(
        author="Bob",
        rating=4,
        text=(
            "Great atmosphere and friendly staff. "
            "The pizza was crispy and delicious. "
            "Service was a bit slow on a busy Friday night. "
            "Would still definitely come back. "
            "The dessert menu is worth saving room for."
        ),
        published_at=datetime(2025, 11, 15),
    ),
    PlaceReview(
        author="Carol",
        rating=5,
        text=(
            "Best tiramisu I've ever had! "
            "The espresso flavor was strong without being bitter. "
            "The portion sizes are generous and the prices are fair. "
            "This place is a hidden gem. "
            "I brought my family and everyone loved it."
        ),
        published_at=datetime(2026, 1, 20),
    ),
    PlaceReview(
        author="Dave",
        rating=3,
        text=(
            "Decent food but nothing exceptional. "
            "The risotto was slightly underseasoned. "
            "The wine list is impressive though. "
            "Might try again with different dishes. "
            "The ambiance in the evening is lovely."
        ),
        published_at=datetime(2025, 10, 5),
    ),
    PlaceReview(
        author="Eve",
        rating=5,
        text=(
            "Outstanding dining experience from start to finish. "
            "The bruschetta appetizer was fresh and vibrant. "
            "The lamb chops were perfectly cooked medium-rare. "
            "Our server Marco was knowledgeable and attentive. "
            "The sommelier's wine pairing recommendation was spot on. "
            "Can't wait to return for a special occasion."
        ),
        published_at=datetime(2026, 2, 10),
    ),
]


def _source_review_id(tenant_id: str, author: str, text: str) -> str:
    digest = hashlib.sha256(f"{tenant_id}{author}{text}".encode()).hexdigest()
    return digest[:16]


async def _fetch_tenant(tenant_id: str) -> TenantConfig | None:
    async with get_session() as session:
        result = await session.exec(
            select(TenantConfig).where(TenantConfig.tenant_id == tenant_id)
        )
        return result.first()


async def run_ingest(tenant_id: str, chroma_path: str = CHROMA_PATH) -> int:
    """Fetch, chunk, embed, and upsert reviews for *tenant_id*.

    Returns the number of chunks stored.
    """
    tenant = await _fetch_tenant(tenant_id)
    google_place_id = tenant.google_place_id if tenant else None

    if google_place_id:
        reviews = await GooglePlacesClient().get_reviews(google_place_id)
        if not reviews:
            logger.warning("No reviews returned from Google Places — falling back to synthetic data")
            reviews = SYNTHETIC_REVIEWS
    else:
        logger.info("No google_place_id configured — using synthetic reviews")
        reviews = SYNTHETIC_REVIEWS

    all_chunks = []
    for review in reviews:
        rid = _source_review_id(tenant_id, review.author, review.text)
        all_chunks.extend(chunk_review(review, rid, tenant_id))

    if not all_chunks:
        logger.warning("No chunks produced for tenant %s", tenant_id)
        return 0

    svc = EmbeddingService()
    embeddings = svc.embed([c.text for c in all_chunks])

    client = chromadb.PersistentClient(path=chroma_path)
    collection = client.get_or_create_collection(f"reviews_{tenant_id}")

    collection.upsert(
        ids=[c.chunk_id for c in all_chunks],
        embeddings=embeddings,
        documents=[c.text for c in all_chunks],
        metadatas=[
            {
                "freshness_score": c.freshness_score,
                "rating": c.rating,
                "source_review_id": c.source_review_id,
                "tenant_id": c.tenant_id,
                "chunk_index": c.chunk_index,
            }
            for c in all_chunks
        ],
    )

    logger.info("Stored %d chunks for tenant %s", len(all_chunks), tenant_id)
    return len(all_chunks)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Ingest reviews into ChromaDB")
    parser.add_argument("--tenant", required=True, help="Tenant ID")
    args = parser.parse_args()
    count = asyncio.run(run_ingest(args.tenant))
    print(f"Stored {count} chunks for tenant {args.tenant}")


if __name__ == "__main__":
    main()
