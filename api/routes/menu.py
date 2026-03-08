"""Menu management endpoints."""
import json

from fastapi import APIRouter, Request
from sqlmodel import select

from core.db.session import get_session
from core.models.menu import MenuItem, MenuItemRead

router = APIRouter(prefix="/menu", tags=["menu"])


@router.get("", response_model=list[MenuItemRead])
async def get_menu(request: Request, available_only: bool = True) -> list[MenuItemRead]:
    """Get menu for the tenant resolved via X-Tenant-ID middleware."""
    tenant_id = request.state.tenant_id
    async with get_session() as session:
        q = select(MenuItem).where(MenuItem.tenant_id == tenant_id)
        if available_only:
            q = q.where(MenuItem.is_available == True)  # noqa: E712
        results = await session.exec(q)
        items = results.all()
    return [MenuItemRead.from_db(item) for item in items]


@router.post("", response_model=list[MenuItemRead])
async def upsert_menu(items: list[MenuItemRead], request: Request) -> list[MenuItemRead]:
    """Replace the full menu for the tenant with the supplied list of items."""
    tenant_id = request.state.tenant_id
    async with get_session() as session:
        existing = await session.exec(
            select(MenuItem).where(MenuItem.tenant_id == tenant_id)
        )
        for row in existing.all():
            await session.delete(row)
        for item in items:
            session.add(
                MenuItem(
                    tenant_id=tenant_id,
                    dish_id=item.dish_id,
                    name=item.name,
                    description=item.description,
                    price=item.price,
                    category=item.category,
                    allergens=json.dumps(item.allergens),
                    dietary_tags=json.dumps(item.dietary_tags),
                    is_available=item.is_available,
                    spice_level=item.spice_level,
                    image_url=item.image_url,
                )
            )
        await session.commit()
    return items
