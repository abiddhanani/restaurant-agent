"""Tenant management endpoints (admin only)."""
from fastapi import APIRouter, HTTPException
from core.models.tenant import TenantConfig, TenantConfigRead

router = APIRouter(prefix="/tenants", tags=["tenants"])


@router.post("", response_model=TenantConfigRead)
async def create_tenant(config: TenantConfig) -> TenantConfigRead:
    """Create a new tenant. Accepts any industry type."""
    raise HTTPException(status_code=501, detail="Not yet implemented")
