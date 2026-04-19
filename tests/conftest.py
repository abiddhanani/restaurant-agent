"""Shared pytest fixtures."""
import numpy as np
import pytest
from unittest.mock import patch

from core.models.preference import CustomerProfile
from core.models.menu import Catalog, CatalogItemDTO, ConstraintInfo

_RNG = np.random.default_rng(42)


@pytest.fixture(scope="session", autouse=True)
def mock_embedding_service():
    """Replace slow SentenceTransformer with deterministic 384-dim random vectors."""
    def _fast_embed(self, texts: list[str]) -> list[list[float]]:
        return _RNG.random((len(texts), 384)).tolist()

    def _fast_embed_one(self, text: str) -> list[float]:
        return _RNG.random(384).tolist()

    with patch("rag.pipeline.embeddings.EmbeddingService.embed", _fast_embed), \
         patch("rag.pipeline.embeddings.EmbeddingService.embed_one", _fast_embed_one):
        yield


@pytest.fixture
def demo_tenant_id() -> str:
    return "demo_restaurant"


@pytest.fixture
def demo_session_id() -> str:
    return "test_session_001"


@pytest.fixture
def empty_taste_profile(demo_tenant_id, demo_session_id) -> CustomerProfile:
    """Fresh customer profile with no signals."""
    return CustomerProfile(
        session_id=demo_session_id,
        tenant_id=demo_tenant_id,
    )


@pytest.fixture
def nut_allergy_profile(demo_tenant_id, demo_session_id) -> CustomerProfile:
    """Customer profile with nut allergy declared."""
    return CustomerProfile(
        session_id=demo_session_id,
        tenant_id=demo_tenant_id,
        hard_stops=["nuts"],
        confidence=0.8,
    )


@pytest.fixture
def demo_menu(demo_tenant_id) -> Catalog:
    """Small demo catalog for tests."""
    return Catalog(
        tenant_id=demo_tenant_id,
        last_updated="2025-01-01",
        items=[
            CatalogItemDTO(
                item_id="item_001",
                name="Spicy Lamb Curry",
                description="Rich lamb in aromatic spices",
                price=16.50,
                category="Mains",
                constraints=ConstraintInfo(contains=["gluten"]),
                tags=["spicy"],
            ),
            CatalogItemDTO(
                item_id="item_002",
                name="Satay Chicken Skewers",
                description="Grilled chicken with peanut sauce",
                price=12.00,
                category="Starters",
                constraints=ConstraintInfo(contains=["nuts", "gluten"]),
                tags=["gluten-free"],
            ),
            CatalogItemDTO(
                item_id="item_003",
                name="Mushroom Risotto",
                description="Creamy wild mushroom risotto",
                price=14.00,
                category="Mains",
                constraints=ConstraintInfo(contains=["dairy"]),
                tags=["vegetarian"],
            ),
        ]
    )
