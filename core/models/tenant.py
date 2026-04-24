"""Tenant data models — domain-agnostic business configuration."""
from datetime import datetime
from typing import Optional
from sqlmodel import SQLModel, Field


class TenantConfig(SQLModel, table=True):
    """Per-tenant configuration stored in DB."""
    id: Optional[int] = Field(default=None, primary_key=True)
    tenant_id: str = Field(unique=True, index=True)
    business_name: str
    industry: str = Field(default="restaurant")  # restaurant, salon, software, construction, etc.
    api_key: str = Field(unique=True, index=True)
    domain_config: str = Field(default="{}")  # JSON dict — industry-specific settings
    widget_primary_color: str = "#000000"
    widget_welcome_message: str = "Hi! How can I help you today?"
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class TenantConfigRead(SQLModel):
    """Public-safe tenant config (no secrets)."""
    tenant_id: str
    business_name: str
    industry: str
    widget_primary_color: str
    widget_welcome_message: str
    is_active: bool
