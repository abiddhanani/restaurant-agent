"""Self-serve tenant onboarding — POST /onboard (exempt from TenantMiddleware)."""
import json
import os
import re
import secrets
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from core.db.session import get_session
from core.models.menu import CatalogItem
from core.models.onboard import OnboardRequest, OnboardResponse
from core.models.tenant import TenantConfig

router = APIRouter(tags=["onboard"])


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


@router.post("/onboard", response_model=OnboardResponse, status_code=201)
async def onboard_tenant(body: OnboardRequest):
    base_slug = _slugify(body.business_name) or "tenant"
    tenant_id = f"{base_slug}-{secrets.token_hex(3)}"
    api_key = f"sk-{secrets.token_urlsafe(32)}"

    async with get_session() as session:
        tenant = TenantConfig(
            tenant_id=tenant_id,
            business_name=body.business_name,
            industry=body.industry,
            api_key=api_key,
            domain_config=json.dumps(body.domain_config),
            widget_primary_color=body.widget_primary_color,
            widget_welcome_message=body.widget_welcome_message,
            is_active=True,
        )
        session.add(tenant)

        for item_data in body.catalog:
            session.add(CatalogItem(
                tenant_id=tenant_id,
                item_id=str(uuid4()),
                name=item_data.name,
                description=item_data.description,
                price=item_data.price,
                category=item_data.category,
                constraints=json.dumps(item_data.constraints),
                tags=json.dumps(item_data.tags),
                attributes=json.dumps(item_data.attributes),
                image_url=item_data.image_url,
                video_url=item_data.video_url,
                is_available=item_data.is_available,
            ))

        await session.commit()

    base_url = os.getenv("WIDGET_BASE_URL", "http://localhost:8000")
    embed_snippet = (
        f'<script src="{base_url}/static/widget.js" '
        f'data-tenant="{tenant_id}" defer></script>'
    )

    return OnboardResponse(
        tenant_id=tenant_id,
        api_key=api_key,
        embed_snippet=embed_snippet,
        items_imported=len(body.catalog),
    )
