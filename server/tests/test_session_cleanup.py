from datetime import datetime, timedelta

import pytest

from models.domain import SessionData
from session.memory_store import MemorySessionStore


def _make_session(minutes_ago: int) -> SessionData:
    data = SessionData(files=[], profiles=[])
    data.last_accessed_at = datetime.now() - timedelta(minutes=minutes_ago)
    return data


def test_cleanup_expired_sessions():
    store = MemorySessionStore(max_sessions=50, ttl_minutes=30)
    store.create("fresh", _make_session(5))
    store.create("expired1", _make_session(35))
    store.create("expired2", _make_session(60))

    removed = store.cleanup_expired()

    assert removed == 2
    assert store.get("fresh") is not None
    assert store.get("expired1") is None
    assert store.get("expired2") is None


def test_cleanup_no_expired():
    store = MemorySessionStore(max_sessions=50, ttl_minutes=30)
    store.create("s1", _make_session(5))
    store.create("s2", _make_session(10))

    removed = store.cleanup_expired()
    assert removed == 0
    assert store.session_count() == 2


def test_cleanup_frees_capacity():
    store = MemorySessionStore(max_sessions=2, ttl_minutes=30)
    store.create("old", _make_session(35))
    store.create("current", _make_session(5))

    # At capacity
    with pytest.raises(RuntimeError):
        store.create("new", _make_session(0))

    store.cleanup_expired()

    # Now has room
    store.create("new", _make_session(0))
    assert store.session_count() == 2
