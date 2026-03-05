"""Base class all agent tools must inherit."""
from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel


class ToolInput(BaseModel):
    """Base input model for all tools."""
    tenant_id: str
    session_id: str


class ToolOutput(BaseModel):
    """Base output model for all tools."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    confidence: float = 1.0


class BaseTool(ABC):
    """
    All agent tools inherit this.
    Enforces typed inputs/outputs and consistent error handling.
    """
    name: str
    description: str

    @abstractmethod
    async def execute(self, input_data: ToolInput) -> ToolOutput:
        """Execute the tool. Must be implemented by all subclasses."""
        ...

    async def __call__(self, input_data: ToolInput) -> ToolOutput:
        """Wraps execute with error handling."""
        try:
            return await self.execute(input_data)
        except Exception as e:
            return ToolOutput(success=False, error=str(e), confidence=0.0)
