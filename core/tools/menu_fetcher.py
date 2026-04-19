"""Tool: fetch structured catalog for a tenant."""
from typing import Optional

from pydantic import Field
from sqlmodel import select

from core.db.session import get_session
from core.models.menu import CatalogItem, CatalogItemRead
from core.tools.base import BaseTool, ToolInput, ToolOutput


class CatalogFetcherInput(ToolInput):
    """Input for CatalogFetcherTool."""
    available_only: bool = Field(default=True)
    category: Optional[str] = Field(default=None, description="Optional category filter")


class CatalogFetcherOutput(ToolOutput):
    """Output for CatalogFetcherTool."""
    items: list[CatalogItemRead] = Field(default_factory=list)


class CatalogFetcherTool(BaseTool):
    """Fetches the current catalog for a tenant from the database."""
    name = "catalog_fetcher"
    description = "Fetches catalog items including names, prices, and constraints."

    async def execute(self, input_data: CatalogFetcherInput) -> CatalogFetcherOutput:
        """Fetch catalog items for the given tenant from the DB."""
        async with get_session() as session:
            q = select(CatalogItem).where(CatalogItem.tenant_id == input_data.tenant_id)
            if input_data.available_only:
                q = q.where(CatalogItem.is_available == True)  # noqa: E712
            if input_data.category:
                q = q.where(CatalogItem.category == input_data.category)
            results = await session.exec(q)
            items = results.all()
        return CatalogFetcherOutput(
            success=True,
            items=[CatalogItemRead.from_db(item) for item in items],
        )


# Backward-compatible aliases
MenuFetcherInput = CatalogFetcherInput
MenuFetcherOutput = CatalogFetcherOutput
MenuFetcherTool = CatalogFetcherTool
