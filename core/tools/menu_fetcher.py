"""Tool: fetch structured menu for a tenant."""
from typing import Optional

from pydantic import Field
from sqlmodel import select

from core.db.session import get_session
from core.models.menu import MenuItem, MenuItemRead
from core.tools.base import BaseTool, ToolInput, ToolOutput


class MenuFetcherInput(ToolInput):
    """Input for MenuFetcherTool."""
    available_only: bool = Field(default=True)


class MenuFetcherOutput(ToolOutput):
    """Output for MenuFetcherTool."""
    items: list[MenuItemRead] = Field(default_factory=list)


class MenuFetcherTool(BaseTool):
    """Fetches the current menu for a tenant from the database."""
    name = "menu_fetcher"
    description = "Fetches restaurant menu including dishes, prices, allergens."

    async def execute(self, input_data: MenuFetcherInput) -> MenuFetcherOutput:
        """Fetch menu items for the given tenant from the DB."""
        async with get_session() as session:
            q = select(MenuItem).where(MenuItem.tenant_id == input_data.tenant_id)
            if input_data.available_only:
                q = q.where(MenuItem.is_available == True)  # noqa: E712
            results = await session.exec(q)
            items = results.all()
        return MenuFetcherOutput(
            success=True,
            items=[MenuItemRead.from_db(item) for item in items],
        )
