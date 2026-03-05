"""Tenant (restaurant) data models."""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class TenantConfig(SQLModel, table=True):
    """Per-restaurant configuration stored in DB."""
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: str = Field(unique=True, index=True)
    restaurant_name: str
    api_key: str = Field(unique=True, index=True)
    google_place_id: Optional[str] = None
    yelp_business_id: Optional[str] = None
    widget_primary_color: str = "#000000"
    widget_welcome_message: str = "Hi! I can help you find the perfect dish."
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TenantConfigRead(SQLModel):
    """Public-safe tenant config (no secrets)."""
    tenant_id: str
    restaurant_name: str
    widget_primary_color: str
    widget_welcome_message: str
    is_active: bool
