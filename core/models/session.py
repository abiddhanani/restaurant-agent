"""Session and conversation data models."""
from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


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
    preference_profile_id: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_active: datetime = Field(default_factory=datetime.utcnow)
