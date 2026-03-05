"""FastAPI application entry point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import chat, menu, tenants, health
from a2a.server import router as a2a_router
from mcp.server import router as mcp_router

app = FastAPI(
    title="Restaurant Agent API",
    description="Multi-tenant restaurant chat agent with RAG, A2A, and MCP",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(chat.router)
app.include_router(menu.router)
app.include_router(tenants.router)
app.include_router(a2a_router)
app.include_router(mcp_router)
