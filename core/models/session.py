"""Session and conversation data models."""
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional
from pydantic import BaseModel, Field

if TYPE_CHECKING:
    from core.models.preference import CustomerProfile


class Message(BaseModel):
    """Single conversation message."""
    role: str  # "user" or "assistant"
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: dict[str, Any] = Field(default_factory=dict)


class ConversationSession(BaseModel):
    """Active conversation session."""
    session_id: str
    tenant_id: str
    messages: list[Message] = Field(default_factory=list)
    customer_profile: Optional[Any] = None  # CustomerProfile at runtime
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)
