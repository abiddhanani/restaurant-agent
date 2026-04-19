"""Seed demo data for development and testing."""
import json

from sqlmodel import select

from core.db.session import AsyncSessionLocal
from core.models.menu import CatalogItem


async def seed_demo_menu() -> None:
    """Insert demo catalog items for restaurant_demo if not already present."""
    async with AsyncSessionLocal() as session:
        result = await session.exec(
            select(CatalogItem).where(CatalogItem.tenant_id == "restaurant_demo").limit(1)
        )
        if result.first() is not None:
            return  # already seeded

        items = [
            CatalogItem(
                tenant_id="restaurant_demo",
                item_id="item_001",
                name="Spicy Basil Chicken",
                description="Stir-fried chicken with Thai basil, chilies, and garlic over jasmine rice.",
                price=14.99,
                category="mains",
                constraints=json.dumps(["soy", "fish sauce"]),
                tags=json.dumps(["spicy", "gluten-free"]),
                attributes=json.dumps({"spice_level": 4}),
            ),
            CatalogItem(
                tenant_id="restaurant_demo",
                item_id="item_002",
                name="Pad Thai",
                description="Rice noodles with egg, tofu, bean sprouts, and roasted peanuts.",
                price=13.99,
                category="mains",
                constraints=json.dumps(["peanuts", "eggs", "soy"]),
                tags=json.dumps(["vegetarian"]),
                attributes=json.dumps({"spice_level": 2}),
            ),
            CatalogItem(
                tenant_id="restaurant_demo",
                item_id="item_003",
                name="Green Curry",
                description="Creamy coconut green curry with vegetables and your choice of protein.",
                price=15.99,
                category="mains",
                constraints=json.dumps(["coconut", "fish sauce"]),
                tags=json.dumps(["spicy", "gluten-free", "dairy-free"]),
                attributes=json.dumps({"spice_level": 3}),
            ),
            CatalogItem(
                tenant_id="restaurant_demo",
                item_id="item_004",
                name="Tom Yum Soup",
                description="Fragrant lemongrass broth with mushrooms, shrimp, lime, and chili.",
                price=9.99,
                category="starters",
                constraints=json.dumps(["shellfish", "fish sauce"]),
                tags=json.dumps(["spicy", "gluten-free"]),
                attributes=json.dumps({"spice_level": 3}),
            ),
            CatalogItem(
                tenant_id="restaurant_demo",
                item_id="item_005",
                name="Spring Rolls",
                description="Crispy fried rolls filled with glass noodles, carrot, and cabbage.",
                price=7.99,
                category="starters",
                constraints=json.dumps(["gluten", "soy"]),
                tags=json.dumps(["vegetarian"]),
                attributes=json.dumps({"spice_level": 0}),
            ),
            CatalogItem(
                tenant_id="restaurant_demo",
                item_id="item_006",
                name="Mango Salad",
                description="Shredded green mango tossed with lime, chili, roasted peanuts, and herbs.",
                price=8.99,
                category="starters",
                constraints=json.dumps(["peanuts", "fish sauce"]),
                tags=json.dumps(["vegan", "gluten-free", "spicy"]),
                attributes=json.dumps({"spice_level": 3}),
            ),
            CatalogItem(
                tenant_id="restaurant_demo",
                item_id="item_007",
                name="Massaman Lamb",
                description="Slow-braised lamb in rich Massaman curry with potatoes and peanuts.",
                price=18.99,
                category="mains",
                constraints=json.dumps(["peanuts", "coconut"]),
                tags=json.dumps(["gluten-free", "dairy-free"]),
                attributes=json.dumps({"spice_level": 2}),
            ),
            CatalogItem(
                tenant_id="restaurant_demo",
                item_id="item_008",
                name="Panang Tofu",
                description="Firm tofu in Panang curry paste with kaffir lime leaf and coconut cream.",
                price=12.99,
                category="mains",
                constraints=json.dumps(["coconut", "soy"]),
                tags=json.dumps(["vegan", "gluten-free"]),
                attributes=json.dumps({"spice_level": 2}),
            ),
            CatalogItem(
                tenant_id="restaurant_demo",
                item_id="item_009",
                name="Prawn Satay",
                description="Grilled prawns on skewers with peanut dipping sauce and cucumber relish.",
                price=11.99,
                category="starters",
                constraints=json.dumps(["shellfish", "peanuts", "gluten"]),
                tags=json.dumps(["spicy"]),
                attributes=json.dumps({"spice_level": 1}),
            ),
            CatalogItem(
                tenant_id="restaurant_demo",
                item_id="item_010",
                name="Sticky Rice with Mango",
                description="Glutinous sweet rice with fresh mango slices and coconut cream.",
                price=7.99,
                category="desserts",
                constraints=json.dumps(["coconut"]),
                tags=json.dumps(["vegan", "gluten-free"]),
                attributes=json.dumps({"spice_level": 0}),
            ),
            CatalogItem(
                tenant_id="restaurant_demo",
                item_id="item_011",
                name="Coconut Ice Cream",
                description="House-made coconut ice cream topped with toasted sesame and palm sugar.",
                price=6.99,
                category="desserts",
                constraints=json.dumps(["coconut", "sesame"]),
                tags=json.dumps(["vegan", "gluten-free"]),
                attributes=json.dumps({"spice_level": 0}),
            ),
            CatalogItem(
                tenant_id="restaurant_demo",
                item_id="item_012",
                name="Thai Iced Tea",
                description="Sweetened black tea with condensed milk served over ice.",
                price=4.99,
                category="drinks",
                constraints=json.dumps(["dairy"]),
                tags=json.dumps(["vegetarian"]),
                attributes=json.dumps({"spice_level": 0}),
            ),
        ]

        for item in items:
            session.add(item)
        await session.commit()
