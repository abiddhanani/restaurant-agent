"""Catalog item data models — domain-agnostic, works for any business type."""
import json
from typing import Optional
from pydantic import BaseModel
from sqlmodel import SQLModel, Field


class ConstraintInfo(BaseModel):
    """Hard-stop constraints for a catalog item (allergens, sensitivities, etc.)."""
    contains: list[str] = []
    may_contain: list[str] = []


class CatalogItemDTO(BaseModel):
    """Single catalog item (Pydantic DTO)."""
    item_id: str
    name: str
    description: str
    price: float
    category: str
    constraints: ConstraintInfo = ConstraintInfo()
    tags: list[str] = []
    is_available: bool = True
    image_url: Optional[str] = None


class Catalog(BaseModel):
    """Full tenant catalog."""
    tenant_id: str
    items: list[CatalogItemDTO]
    last_updated: str


class CatalogItem(SQLModel, table=True):
    """Persisted catalog item row — one per item per tenant."""
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: str = Field(index=True)
    item_id: str = Field(index=True)
    name: str
    description: str
    price: float
    category: str
    constraints: str = Field(default="[]")   # JSON list of strings
    tags: str = Field(default="[]")           # JSON list of strings
    attributes: str = Field(default="{}")     # JSON dict for domain-specific extras
    is_available: bool = Field(default=True)
    image_url: Optional[str] = None
    video_url: Optional[str] = None


class CatalogItemRead(BaseModel):
    """API response DTO — deserialises JSON fields back to lists/dicts."""
    item_id: str
    name: str
    description: str
    price: float
    category: str
    constraints: list[str]
    tags: list[str]
    attributes: dict
    is_available: bool
    image_url: Optional[str] = None
    video_url: Optional[str] = None

    @classmethod
    def from_db(cls, item: CatalogItem) -> "CatalogItemRead":
        return cls(
            item_id=item.item_id,
            name=item.name,
            description=item.description,
            price=item.price,
            category=item.category,
            constraints=json.loads(item.constraints),
            tags=json.loads(item.tags),
            attributes=json.loads(item.attributes),
            is_available=item.is_available,
            image_url=item.image_url,
            video_url=item.video_url,
        )
