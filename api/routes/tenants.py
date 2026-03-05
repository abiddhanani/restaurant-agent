"""Tenant management endpoints (admin only)."""
from fastapi import APIRouter, HTTPException
from core.models.tenant import TenantConfig, TenantConfigRead

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("", response_model=TenantConfigRead)
async def create_tenant(config: TenantConfig) -> TenantConfigRead:
    """Create a new restaurant tenant. Implemented Week 1."""
    raise HTTPException(status_code=501, detail="Not yet implemented")
