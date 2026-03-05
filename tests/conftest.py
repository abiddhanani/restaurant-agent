"""Shared pytest fixtures."""
import pytest
from core.models.preference import UserTasteProfile
from core.models.menu import Menu, Dish, AllergenInfo


@pytest.fixture
def demo_tenant_id() -> str:
    """Standard tenant ID for tests."""
    return "demo_restaurant"


@pytest.fixture
def demo_session_id() -> str:
    """Standard session ID for tests."""
    return "test_session_001"


@pytest.fixture
def empty_taste_profile(demo_tenant_id, demo_session_id) -> UserTasteProfile:
    """Fresh taste profile with no signals."""
    return UserTasteProfile(
        session_id=demo_session_id,
        tenant_id=demo_tenant_id,
    )


@pytest.fixture
def nut_allergy_profile(demo_tenant_id, demo_session_id) -> UserTasteProfile:
    """Taste profile with nut allergy declared."""
    return UserTasteProfile(
        session_id=demo_session_id,
        tenant_id=demo_tenant_id,
        dietary_hard_stops=["nuts"],
        confidence=0.8,
    )


@pytest.fixture
def demo_menu(demo_tenant_id) -> Menu:
    """Small demo menu for tests."""
    return Menu(
        tenant_id=demo_tenant_id,
        last_updated="2025-01-01",
        dishes=[
            Dish(
                dish_id="dish_001",
                name="Spicy Lamb Curry",
                description="Rich lamb in aromatic spices",
                price=16.50,
                category="Mains",
                allergens=AllergenInfo(contains=["gluten"]),
                dietary_tags=["spicy"],
            ),
            Dish(
                dish_id="dish_002",
                name="Satay Chicken Skewers",
                description="Grilled chicken with peanut sauce",
                price=12.00,
                category="Starters",
                allergens=AllergenInfo(contains=["nuts", "gluten"]),
                dietary_tags=["gluten-free"],
            ),
            Dish(
                dish_id="dish_003",
                name="Mushroom Risotto",
                description="Creamy wild mushroom risotto",
                price=14.00,
                category="Mains",
                allergens=AllergenInfo(contains=["dairy"]),
                dietary_tags=["vegetarian"],
            ),
        ]
    )
