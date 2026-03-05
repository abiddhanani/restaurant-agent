"""Menu management endpoints."""
from fastapi import APIRouter, HTTPException, Header
from core.models.menu import Menu

router = APIRouter(prefix="/menu", tags=["menu"])


@router.get("", response_model=Menu)
async def get_menu(x_api_key: str = Header(..., alias="X-API-Key")) -> Menu:
    """Get full menu for authenticated tenant. Implemented Week 1."""
    raise HTTPException(status_code=501, detail="Not yet implemented")


@router.post("")
async def upsert_menu(
    menu: Menu,
    x_api_key: str = Header(..., alias="X-API-Key"),
) -> dict:
    """Upsert full menu for tenant. Implemented Week 1."""
    raise HTTPException(status_code=501, detail="Not yet implemented")
