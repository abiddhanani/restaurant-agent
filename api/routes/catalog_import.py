"""Catalog import endpoints — JSON and CSV bulk upsert."""
import csv
import io
import json
from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request, UploadFile
from sqlmodel import select

from core.db.session import get_session
from core.models.menu import CatalogItem
from core.models.onboard import ImportResponse, OnboardCatalogItem

router = APIRouter(prefix="/catalog", tags=["catalog"])


async def _upsert_items(tenant_id: str, items: list[OnboardCatalogItem]) -> tuple[int, list[str]]:
    imported = 0
    errors: list[str] = []
    async with get_session() as session:
        for item_data in items:
            try:
                row = CatalogItem(
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
                )
                session.add(row)
                imported += 1
            except Exception as exc:
                errors.append(f"Row '{item_data.name}': {exc}")
        await session.commit()
    return imported, errors


@router.post("/import", response_model=ImportResponse, status_code=201)
async def import_json(request: Request, items: list[OnboardCatalogItem]):
    tenant_id = request.state.tenant_id
    imported, errors = await _upsert_items(tenant_id, items)
    return ImportResponse(items_imported=imported, errors=errors)


@router.post("/import/csv", response_model=ImportResponse, status_code=201)
async def import_csv(request: Request, file: UploadFile):
    if file.content_type not in ("text/csv", "application/csv", "text/plain"):
        raise HTTPException(status_code=422, detail="File must be a CSV")

    tenant_id = request.state.tenant_id
    raw = await file.read()
    text = raw.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))

    items: list[OnboardCatalogItem] = []
    errors: list[str] = []
    for i, row in enumerate(reader, start=2):
        try:
            items.append(OnboardCatalogItem(
                name=row["name"],
                description=row.get("description", ""),
                price=float(row["price"]),
                category=row.get("category", "General"),
                constraints=json.loads(row.get("constraints") or "[]"),
                tags=json.loads(row.get("tags") or "[]"),
                attributes=json.loads(row.get("attributes") or "{}"),
                image_url=row.get("image_url") or None,
                video_url=row.get("video_url") or None,
                is_available=str(row.get("is_available", "true")).lower() != "false",
            ))
        except Exception as exc:
            errors.append(f"Row {i}: {exc}")

    imported, db_errors = await _upsert_items(tenant_id, items)
    return ImportResponse(items_imported=imported, errors=errors + db_errors)
