"""Tool: fetch structured menu for a tenant."""
from core.models.menu import Menu
from core.tools.base import BaseTool, ToolInput, ToolOutput
from pydantic import BaseModel
from typing import Optional


class MenuFetcherInput(ToolInput):
    """Input for MenuFetcherTool."""
    pass


class MenuFetcherOutput(ToolOutput):
    """Output for MenuFetcherTool."""
    menu: Optional[Menu] = None


class MenuFetcherTool(BaseTool):
    """Fetches the current menu for a tenant. Implemented Week 1."""
    name = "menu_fetcher"
    description = "Fetches restaurant menu including dishes, prices, allergens."

    async def execute(self, input_data: MenuFetcherInput) -> MenuFetcherOutput:
        """Fetch menu from tenant config store."""
        # TODO Week 1: implement against SQLModel tenant menu store
        raise NotImplementedError("Implement in Week 1")
