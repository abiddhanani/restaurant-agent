"""File upload endpoints for catalog item images and videos."""
import os

import aiofiles
from fastapi import APIRouter, HTTPException, Request, UploadFile
from sqlmodel import select

from core.db.session import get_session
from core.models.menu import CatalogItem

router = APIRouter(prefix="/catalog/items", tags=["uploads"])

_IMAGE_TYPES = {"image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif", "image/webp": ".webp"}
_VIDEO_TYPES = {"video/mp4": ".mp4", "video/quicktime": ".mov", "video/webm": ".webm"}
_IMAGE_MAX_BYTES = 5 * 1024 * 1024   # 5 MB
_VIDEO_MAX_BYTES = 50 * 1024 * 1024  # 50 MB


async def _get_item(tenant_id: str, item_id: str) -> CatalogItem:
    async with get_session() as session:
        result = await session.exec(
            select(CatalogItem).where(
                CatalogItem.tenant_id == tenant_id,
                CatalogItem.item_id == item_id,
            )
        )
        item = result.first()
    if not item:
        raise HTTPException(status_code=404, detail=f"Item '{item_id}' not found")
    return item


async def _save_file(data: bytes, tenant_id: str, item_id: str, filename: str) -> str:
    dir_path = os.path.join("static", "uploads", tenant_id, item_id)
    os.makedirs(dir_path, exist_ok=True)
    file_path = os.path.join(dir_path, filename)
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(data)
    return f"/static/uploads/{tenant_id}/{item_id}/{filename}"


@router.post("/{item_id}/image")
async def upload_image(item_id: str, request: Request, file: UploadFile):
    tenant_id = request.state.tenant_id
    content_type = file.content_type or ""
    if content_type not in _IMAGE_TYPES:
        raise HTTPException(status_code=422, detail=f"Unsupported image type: {content_type}")

    data = await file.read()
    if len(data) > _IMAGE_MAX_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds 5 MB limit")

    ext = _IMAGE_TYPES[content_type]
    url = await _save_file(data, tenant_id, item_id, f"image{ext}")

    async with get_session() as session:
        result = await session.exec(
            select(CatalogItem).where(
                CatalogItem.tenant_id == tenant_id,
                CatalogItem.item_id == item_id,
            )
        )
        item = result.first()
        if not item:
            raise HTTPException(status_code=404, detail=f"Item '{item_id}' not found")
        item.image_url = url
        session.add(item)
        await session.commit()

    return {"image_url": url}


@router.post("/{item_id}/video")
async def upload_video(item_id: str, request: Request, file: UploadFile):
    tenant_id = request.state.tenant_id
    content_type = file.content_type or ""
    if content_type not in _VIDEO_TYPES:
        raise HTTPException(status_code=422, detail=f"Unsupported video type: {content_type}")

    data = await file.read()
    if len(data) > _VIDEO_MAX_BYTES:
        raise HTTPException(status_code=413, detail="Video exceeds 50 MB limit")

    ext = _VIDEO_TYPES[content_type]
    url = await _save_file(data, tenant_id, item_id, f"video{ext}")

    async with get_session() as session:
        result = await session.exec(
            select(CatalogItem).where(
                CatalogItem.tenant_id == tenant_id,
                CatalogItem.item_id == item_id,
            )
        )
        item = result.first()
        if not item:
            raise HTTPException(status_code=404, detail=f"Item '{item_id}' not found")
        item.video_url = url
        session.add(item)
        await session.commit()

    return {"video_url": url}
