"""Pydantic models for the self-serve onboarding API (GEN-6)."""
from typing import Any, Optional
from pydantic import BaseModel


class OnboardCatalogItem(BaseModel):
    name: str
    description: str
    price: float
    category: str
    constraints: list[str] = []
    tags: list[str] = []
    attributes: dict[str, Any] = {}
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    is_available: bool = True


class OnboardRequest(BaseModel):
    business_name: str
    industry: str = "restaurant"
    domain_config: dict[str, Any] = {}
    widget_primary_color: str = "#000000"
    widget_welcome_message: str = "Hi! How can I help you today?"
    catalog: list[OnboardCatalogItem] = []


class OnboardResponse(BaseModel):
    tenant_id: str
    api_key: str
    embed_snippet: str
    items_imported: int


class ImportResponse(BaseModel):
    items_imported: int
    errors: list[str] = []
