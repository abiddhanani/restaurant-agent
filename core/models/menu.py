"""Menu and dish data models."""
import json
from typing import Optional
from pydantic import BaseModel
from sqlmodel import SQLModel, Field


class AllergenInfo(BaseModel):
    """Allergen information for a dish."""
    contains: list[str] = []
    may_contain: list[str] = []


class Dish(BaseModel):
    """Single menu item (Pydantic DTO)."""
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


class MenuItem(SQLModel, table=True):
    """Persisted menu item row — one per dish per tenant."""
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: str = Field(index=True)
    dish_id: str = Field(index=True)
    name: str
    description: str
    price: float
    category: str
    allergens: str = Field(default="[]")    # JSON list of strings
    dietary_tags: str = Field(default="[]") # JSON list of strings
    is_available: bool = Field(default=True)
    spice_level: Optional[int] = None
    image_url: Optional[str] = None


class MenuItemRead(BaseModel):
    """API response DTO — deserialises JSON fields back to lists."""
    dish_id: str
    name: str
    description: str
    price: float
    category: str
    allergens: list[str]
    dietary_tags: list[str]
    is_available: bool
    spice_level: Optional[int] = None
    image_url: Optional[str] = None

    @classmethod
    def from_db(cls, item: MenuItem) -> "MenuItemRead":
        return cls(
            dish_id=item.dish_id,
            name=item.name,
            description=item.description,
            price=item.price,
            category=item.category,
            allergens=json.loads(item.allergens),
            dietary_tags=json.loads(item.dietary_tags),
            is_available=item.is_available,
            spice_level=item.spice_level,
            image_url=item.image_url,
        )
