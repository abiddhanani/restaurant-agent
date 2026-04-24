"""Health check endpoint."""
import os
from datetime import datetime

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["health"])

APP_VERSION = "0.1.0"


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    timestamp: datetime
    version: str
    model: str
    environment: str


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Basic health check — used by Railway/EKS liveness probe."""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        version=APP_VERSION,
        model=os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-20250514"),
        environment=os.getenv("ENVIRONMENT", "development"),
    )
