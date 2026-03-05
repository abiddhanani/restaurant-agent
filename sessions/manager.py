"""Session manager — in-memory Phase 0, Redis Phase 1."""
from typing import Optional
from core.models.session import ConversationSession
from core.models.preference import UserTasteProfile
import uuid


class SessionManager:
    """
    Manages conversation sessions.
    Phase 0: in-memory dict (lost on restart — acceptable for dev/demo).
    Phase 1: swap _store for Redis without changing the interface.
    """

    def __init__(self) -> None:
        """Initialise with in-memory store."""
        self._store: dict[str, ConversationSession] = {}

    async def create_session(self, tenant_id: str) -> ConversationSession:
        """Create a new session for a tenant."""
        session = ConversationSession(
            session_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
        )
        self._store[session.session_id] = session
        return session

    async def get_session(self, session_id: str) -> Optional[ConversationSession]:
        """Retrieve an existing session. Returns None if not found."""
        return self._store.get(session_id)

    async def update_session(self, session: ConversationSession) -> None:
        """Persist session state."""
        self._store[session.session_id] = session

    async def delete_session(self, session_id: str) -> None:
        """Remove a session."""
        self._store.pop(session_id, None)
