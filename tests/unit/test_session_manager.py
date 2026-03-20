"""Unit tests for SessionManager — pure in-memory, all sync-via-asyncio."""
import asyncio

import pytest

from sessions.manager import SessionManager


def run(coro):
    return asyncio.get_event_loop().run_until_complete(coro)


@pytest.fixture()
def mgr() -> SessionManager:
    return SessionManager()


def test_create_session_returns_session_with_correct_tenant(mgr):
    session = run(mgr.create_session("tenant_a"))
    assert session.tenant_id == "tenant_a"
    assert session.session_id


def test_create_session_generates_unique_ids(mgr):
    s1 = run(mgr.create_session("tenant_a"))
    s2 = run(mgr.create_session("tenant_a"))
    assert s1.session_id != s2.session_id


def test_get_session_returns_existing(mgr):
    s = run(mgr.create_session("tenant_a"))
    fetched = run(mgr.get_session(s.session_id))
    assert fetched is not None
    assert fetched.session_id == s.session_id


def test_get_session_returns_none_for_unknown(mgr):
    fetched = run(mgr.get_session("nonexistent"))
    assert fetched is None


def test_get_or_create_creates_new_when_no_session_id(mgr):
    s = run(mgr.get_or_create("tenant_a", session_id=None))
    assert s.tenant_id == "tenant_a"
    assert s.session_id


def test_get_or_create_returns_existing_session(mgr):
    s1 = run(mgr.create_session("tenant_a"))
    s2 = run(mgr.get_or_create("tenant_a", session_id=s1.session_id))
    assert s2.session_id == s1.session_id


def test_get_or_create_tenant_isolation(mgr):
    """Session belonging to tenant_a must not be returned for tenant_b."""
    s1 = run(mgr.create_session("tenant_a"))
    s2 = run(mgr.get_or_create("tenant_b", session_id=s1.session_id))
    # Must create a new session for tenant_b
    assert s2.session_id != s1.session_id
    assert s2.tenant_id == "tenant_b"


def test_add_message_appends_to_history(mgr):
    s = run(mgr.create_session("tenant_a"))
    run(mgr.add_message(s.session_id, "user", "Hello"))
    run(mgr.add_message(s.session_id, "assistant", "Hi there!"))
    updated = run(mgr.get_session(s.session_id))
    assert len(updated.messages) == 2
    assert updated.messages[0].role == "user"
    assert updated.messages[1].role == "assistant"


def test_add_message_unknown_session_raises(mgr):
    with pytest.raises(KeyError):
        run(mgr.add_message("ghost-session", "user", "Hello"))


def test_messages_are_isolated_between_sessions(mgr):
    s1 = run(mgr.create_session("tenant_a"))
    s2 = run(mgr.create_session("tenant_a"))
    run(mgr.add_message(s1.session_id, "user", "Message for s1"))
    run(mgr.add_message(s2.session_id, "user", "Message for s2"))
    assert len(run(mgr.get_session(s1.session_id)).messages) == 1
    assert len(run(mgr.get_session(s2.session_id)).messages) == 1


def test_delete_session_removes_it(mgr):
    s = run(mgr.create_session("tenant_a"))
    run(mgr.delete_session(s.session_id))
    assert run(mgr.get_session(s.session_id)) is None


def test_update_session_persists_changes(mgr):
    s = run(mgr.create_session("tenant_a"))
    run(mgr.add_message(s.session_id, "user", "Ping"))
    fetched = run(mgr.get_session(s.session_id))
    assert len(fetched.messages) == 1
