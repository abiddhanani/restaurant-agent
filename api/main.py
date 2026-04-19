"""FastAPI application entry point."""
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from a2a.server import router as a2a_router, well_known_router
from api.middleware.tenant import TenantMiddleware
from api.routes import chat, health, menu, tenants
from api.routes.catalog_import import router as catalog_import_router
from api.routes.onboard import router as onboard_router
from api.routes.uploads import router as uploads_router
from core.db.init import create_db_and_tables, seed_demo_tenant
from core.db.seed import seed_demo_menu
from mcp.server import router as mcp_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run DB setup on startup."""
    os.makedirs("static/uploads", exist_ok=True)
    await create_db_and_tables()
    await seed_demo_tenant()
    await seed_demo_menu()
    yield


app = FastAPI(
    title="Catalog Agent API",
    description="Multi-tenant catalog recommendation agent with RAG, A2A, and MCP",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(TenantMiddleware)

app.include_router(health.router)
app.include_router(onboard_router)
app.include_router(chat.router)
app.include_router(menu.router)
app.include_router(tenants.router)
app.include_router(uploads_router)
app.include_router(catalog_import_router)
app.include_router(a2a_router)
app.include_router(well_known_router)
app.include_router(mcp_router)

_static_dir = Path(__file__).parent.parent / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir)), name="static")
