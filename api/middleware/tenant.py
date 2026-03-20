"""Tenant resolution middleware — validates X-Tenant-ID header on every request."""
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from sqlmodel import select

from core.db.session import get_session
from core.models.tenant import TenantConfig

EXEMPT_PATHS = {"/health"}
EXEMPT_PREFIXES = ("/a2a", "/.well-known")


class TenantMiddleware(BaseHTTPMiddleware):
    """Resolve X-Tenant-ID header → TenantConfig, inject into request.state."""

    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path in EXEMPT_PATHS or path.startswith(EXEMPT_PREFIXES):
            return await call_next(request)

        tenant_id = request.headers.get("X-Tenant-ID") or request.query_params.get("tenant_id")
        if not tenant_id:
            return JSONResponse(
                status_code=400,
                content={"detail": "X-Tenant-ID header (or ?tenant_id= query param) is required"},
            )

        async with get_session() as session:
            result = await session.exec(
                select(TenantConfig).where(TenantConfig.tenant_id == tenant_id)
            )
            tenant = result.first()

        if not tenant or not tenant.is_active:
            return JSONResponse(
                status_code=404,
                content={"detail": f"Tenant '{tenant_id}' not found or inactive"},
            )

        request.state.tenant_id = tenant.tenant_id
        request.state.tenant = tenant
        return await call_next(request)
