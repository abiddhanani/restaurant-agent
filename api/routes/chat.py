"""Chat endpoint — main entry point for widget conversations."""
from fastapi import APIRouter, HTTPException, Request
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
    body: ChatRequest,
    request: Request,
) -> ChatResponse:
    """
    Main chat endpoint. Tenant resolved from X-Tenant-ID header via middleware.
    Runs: input guardrail → agent graph → output guardrail → response.
    Implemented Week 3.
    """
    # TODO Week 3: use request.state.tenant_id, run agent graph
    raise HTTPException(status_code=501, detail="Chat not yet implemented")
