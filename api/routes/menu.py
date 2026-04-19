"""Catalog management endpoints."""
import json

from fastapi import APIRouter, Request
from sqlmodel import select

from core.db.session import get_session
from core.models.menu import CatalogItem, CatalogItemRead

router = APIRouter(prefix="/catalog", tags=["catalog"])


@router.get("", response_model=list[CatalogItemRead])
async def get_catalog(request: Request, available_only: bool = True) -> list[CatalogItemRead]:
    """Get catalog for the tenant resolved via X-Tenant-ID middleware."""
    tenant_id = request.state.tenant_id
    async with get_session() as session:
        q = select(CatalogItem).where(CatalogItem.tenant_id == tenant_id)
        if available_only:
            q = q.where(CatalogItem.is_available == True)  # noqa: E712
        results = await session.exec(q)
        items = results.all()
    return [CatalogItemRead.from_db(item) for item in items]


@router.post("", response_model=list[CatalogItemRead])
async def upsert_catalog(items: list[CatalogItemRead], request: Request) -> list[CatalogItemRead]:
    """Replace the full catalog for the tenant with the supplied list of items."""
    tenant_id = request.state.tenant_id
    async with get_session() as session:
        existing = await session.exec(
            select(CatalogItem).where(CatalogItem.tenant_id == tenant_id)
        )
        for row in existing.all():
            await session.delete(row)
        for item in items:
            session.add(
                CatalogItem(
                    tenant_id=tenant_id,
                    item_id=item.item_id,
                    name=item.name,
                    description=item.description,
                    price=item.price,
                    category=item.category,
                    constraints=json.dumps(item.constraints),
                    tags=json.dumps(item.tags),
                    attributes=json.dumps(item.attributes),
                    is_available=item.is_available,
                    image_url=item.image_url,
                )
            )
        await session.commit()
    return items
