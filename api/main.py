"""FastAPI application entry point."""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from a2a.server import router as a2a_router
from api.middleware.tenant import TenantMiddleware
from api.routes import chat, health, menu, tenants
from core.db.init import create_db_and_tables, seed_demo_tenant
from core.db.seed import seed_demo_menu
from mcp.server import router as mcp_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Run DB setup on startup."""
    await create_db_and_tables()
    await seed_demo_tenant()
    await seed_demo_menu()
    yield


app = FastAPI(
    title="Restaurant Agent API",
    description="Multi-tenant restaurant chat agent with RAG, A2A, and MCP",
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
app.include_router(chat.router)
app.include_router(menu.router)
app.include_router(tenants.router)
app.include_router(a2a_router)
app.include_router(mcp_router)
