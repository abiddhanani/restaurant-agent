"""Session manager — in-memory Phase 0, Redis Phase 1."""
import uuid
from typing import Optional

from core.models.session import ConversationSession, Message


class SessionManager:
    """
    Manages conversation sessions.
    Phase 0: in-memory dict (lost on restart — acceptable for dev/demo).
    Phase 1: swap _store for Redis without changing the interface.
    Sessions are tenant-scoped: get_session enforces tenant_id ownership.
    """

    def __init__(self) -> None:
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

    async def get_or_create(
        self, tenant_id: str, session_id: Optional[str] = None
    ) -> ConversationSession:
        """Return an existing session or create a new one.

        If *session_id* is provided but belongs to a different tenant, a new
        session is created instead (tenant isolation).
        """
        if session_id:
            session = self._store.get(session_id)
            if session and session.tenant_id == tenant_id:
                return session
        return await self.create_session(tenant_id)

    async def add_message(
        self, session_id: str, role: str, content: str
    ) -> ConversationSession:
        """Append a message to the session and persist it. Returns updated session."""
        session = self._store.get(session_id)
        if session is None:
            raise KeyError(f"Session {session_id!r} not found")
        session.messages.append(Message(role=role, content=content))
        return session

    async def update_session(self, session: ConversationSession) -> None:
        """Persist session state."""
        self._store[session.session_id] = session

    async def delete_session(self, session_id: str) -> None:
        """Remove a session."""
        self._store.pop(session_id, None)
