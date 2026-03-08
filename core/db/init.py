"""Database initialisation: create tables and seed demo data."""
import os

from sqlmodel import SQLModel, select

from core.db.session import AsyncSessionLocal, async_engine
from core.models.tenant import TenantConfig  # noqa: F401 – registers table with metadata
from core.models.menu import MenuItem  # noqa: F401 – registers table with metadata


async def create_db_and_tables() -> None:
    """Create all SQLModel tables if they don't exist."""
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def seed_demo_tenant() -> None:
    """Insert the restaurant_demo tenant if it is not already present."""
    async with AsyncSessionLocal() as session:
        result = await session.exec(
            select(TenantConfig).where(TenantConfig.tenant_id == "restaurant_demo")
        )
        if result.first() is None:
            demo = TenantConfig(
                tenant_id="restaurant_demo",
                restaurant_name="Demo Restaurant",
                api_key=os.getenv("DEMO_API_KEY", "demo-api-key-local"),
                google_place_id="ChIJDemo123",
            )
            session.add(demo)
            await session.commit()
