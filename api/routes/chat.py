"""Chat endpoint — main entry point for widget conversations."""
from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatRequest(BaseModel):
    """Incoming chat message from widget."""
    session_id: Optional[str] = None  # None = start new session
    message: str


class ChatResponse(BaseModel):
    """Response back to widget."""
    session_id: str
    response: str
    suggestions: list[str] = []


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    x_api_key: str = Header(..., alias="X-API-Key"),
) -> ChatResponse:
    """
    Main chat endpoint. Tenant resolved from API key.
    Runs: input guardrail → agent graph → output guardrail → response.
    Implemented Week 3.
    """
    # TODO Week 3: resolve tenant from API key, run agent graph
    raise HTTPException(status_code=501, detail="Chat not yet implemented")
