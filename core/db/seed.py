"""Seed demo data for development and testing."""
import json

from sqlmodel import select

from core.db.session import AsyncSessionLocal
from core.models.menu import MenuItem


async def seed_demo_menu() -> None:
    """Insert demo menu items for restaurant_demo if not already present."""
    async with AsyncSessionLocal() as session:
        result = await session.exec(
            select(MenuItem).where(MenuItem.tenant_id == "restaurant_demo").limit(1)
        )
        if result.first() is not None:
            return  # already seeded

        dishes = [
            MenuItem(
                tenant_id="restaurant_demo",
                dish_id="dish_001",
                name="Spicy Basil Chicken",
                description="Stir-fried chicken with Thai basil, chilies, and garlic over jasmine rice.",
                price=14.99,
                category="mains",
                allergens=json.dumps(["soy", "fish sauce"]),
                dietary_tags=json.dumps(["spicy", "gluten-free"]),
                spice_level=4,
            ),
            MenuItem(
                tenant_id="restaurant_demo",
                dish_id="dish_002",
                name="Pad Thai",
                description="Rice noodles with egg, tofu, bean sprouts, and roasted peanuts.",
                price=13.99,
                category="mains",
                allergens=json.dumps(["peanuts", "eggs", "soy"]),
                dietary_tags=json.dumps(["vegetarian"]),
                spice_level=2,
            ),
            MenuItem(
                tenant_id="restaurant_demo",
                dish_id="dish_003",
                name="Green Curry",
                description="Creamy coconut green curry with vegetables and your choice of protein.",
                price=15.99,
                category="mains",
                allergens=json.dumps(["coconut", "fish sauce"]),
                dietary_tags=json.dumps(["spicy", "gluten-free", "dairy-free"]),
                spice_level=3,
            ),
            MenuItem(
                tenant_id="restaurant_demo",
                dish_id="dish_004",
                name="Tom Yum Soup",
                description="Fragrant lemongrass broth with mushrooms, shrimp, lime, and chili.",
                price=9.99,
                category="starters",
                allergens=json.dumps(["shellfish", "fish sauce"]),
                dietary_tags=json.dumps(["spicy", "gluten-free"]),
                spice_level=3,
            ),
            MenuItem(
                tenant_id="restaurant_demo",
                dish_id="dish_005",
                name="Spring Rolls",
                description="Crispy fried rolls filled with glass noodles, carrot, and cabbage.",
                price=7.99,
                category="starters",
                allergens=json.dumps(["gluten", "soy"]),
                dietary_tags=json.dumps(["vegetarian"]),
                spice_level=0,
            ),
            MenuItem(
                tenant_id="restaurant_demo",
                dish_id="dish_006",
                name="Mango Salad",
                description="Shredded green mango tossed with lime, chili, roasted peanuts, and herbs.",
                price=8.99,
                category="starters",
                allergens=json.dumps(["peanuts", "fish sauce"]),
                dietary_tags=json.dumps(["vegan", "gluten-free", "spicy"]),
                spice_level=3,
            ),
            MenuItem(
                tenant_id="restaurant_demo",
                dish_id="dish_007",
                name="Massaman Lamb",
                description="Slow-braised lamb in rich Massaman curry with potatoes and peanuts.",
                price=18.99,
                category="mains",
                allergens=json.dumps(["peanuts", "coconut"]),
                dietary_tags=json.dumps(["gluten-free", "dairy-free"]),
                spice_level=2,
            ),
            MenuItem(
                tenant_id="restaurant_demo",
                dish_id="dish_008",
                name="Panang Tofu",
                description="Firm tofu in Panang curry paste with kaffir lime leaf and coconut cream.",
                price=12.99,
                category="mains",
                allergens=json.dumps(["coconut", "soy"]),
                dietary_tags=json.dumps(["vegan", "gluten-free"]),
                spice_level=2,
            ),
            MenuItem(
                tenant_id="restaurant_demo",
                dish_id="dish_009",
                name="Prawn Satay",
                description="Grilled prawns on skewers with peanut dipping sauce and cucumber relish.",
                price=11.99,
                category="starters",
                allergens=json.dumps(["shellfish", "peanuts", "gluten"]),
                dietary_tags=json.dumps(["spicy"]),
                spice_level=1,
            ),
            MenuItem(
                tenant_id="restaurant_demo",
                dish_id="dish_010",
                name="Sticky Rice with Mango",
                description="Glutinous sweet rice with fresh mango slices and coconut cream.",
                price=7.99,
                category="desserts",
                allergens=json.dumps(["coconut"]),
                dietary_tags=json.dumps(["vegan", "gluten-free"]),
                spice_level=0,
            ),
            MenuItem(
                tenant_id="restaurant_demo",
                dish_id="dish_011",
                name="Coconut Ice Cream",
                description="House-made coconut ice cream topped with toasted sesame and palm sugar.",
                price=6.99,
                category="desserts",
                allergens=json.dumps(["coconut", "sesame"]),
                dietary_tags=json.dumps(["vegan", "gluten-free"]),
                spice_level=0,
            ),
            MenuItem(
                tenant_id="restaurant_demo",
                dish_id="dish_012",
                name="Thai Iced Tea",
                description="Sweetened black tea with condensed milk served over ice.",
                price=4.99,
                category="drinks",
                allergens=json.dumps(["dairy"]),
                dietary_tags=json.dumps(["vegetarian"]),
                spice_level=0,
            ),
        ]

        for dish in dishes:
            session.add(dish)
        await session.commit()
