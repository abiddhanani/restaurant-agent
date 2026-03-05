"""Menu and dish data models."""
from typing import Optional
from pydantic import BaseModel


class AllergenInfo(BaseModel):
    """Allergen information for a dish."""
    contains: list[str] = []
    may_contain: list[str] = []


class Dish(BaseModel):
    """Single menu item."""
    dish_id: str
    name: str
    description: str
    price: float
    category: str
    allergens: AllergenInfo = AllergenInfo()
    dietary_tags: list[str] = []
    is_available: bool = True
    image_url: Optional[str] = None


class Menu(BaseModel):
    """Full restaurant menu."""
    tenant_id: str
    dishes: list[Dish]
    last_updated: str
