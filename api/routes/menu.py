"""Menu management endpoints."""
from fastapi import APIRouter, HTTPException, Request
from core.models.menu import Menu

router = APIRouter(prefix="/menu", tags=["menu"])


@router.get("", response_model=Menu)
async def get_menu(request: Request) -> Menu:
    """Get full menu for tenant resolved via X-Tenant-ID middleware. Implemented Week 1."""
    raise HTTPException(status_code=501, detail="Not yet implemented")


@router.post("")
async def upsert_menu(menu: Menu, request: Request) -> dict:
    """Upsert full menu for tenant resolved via X-Tenant-ID middleware. Implemented Week 1."""
    raise HTTPException(status_code=501, detail="Not yet implemented")
