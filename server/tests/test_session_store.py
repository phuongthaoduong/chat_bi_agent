import pytest
from session.memory_store import MemorySessionStore
from models.domain import SessionData

def _make_session_data() -> SessionData:
    return SessionData(files=[], profiles=[])

def test_create_and_get():
    store = MemorySessionStore(max_sessions=50, ttl_minutes=30)
    data = _make_session_data()
    store.create("s1", data)
    result = store.get("s1")
    assert result is not None
    assert result.files == []

def test_get_nonexistent_returns_none():
    store = MemorySessionStore(max_sessions=50, ttl_minutes=30)
    assert store.get("missing") is None

def test_get_updates_last_accessed():
    store = MemorySessionStore(max_sessions=50, ttl_minutes=30)
    data = _make_session_data()
    store.create("s1", data)
    first_access = store.get("s1").last_accessed_at
    result = store.get("s1")
    assert result.last_accessed_at >= first_access

def test_delete():
    store = MemorySessionStore(max_sessions=50, ttl_minutes=30)
    store.create("s1", _make_session_data())
    store.delete("s1")
    assert store.get("s1") is None

def test_capacity_limit():
    store = MemorySessionStore(max_sessions=2, ttl_minutes=30)
    store.create("s1", _make_session_data())
    store.create("s2", _make_session_data())
    with pytest.raises(RuntimeError, match="capacity"):
        store.create("s3", _make_session_data())

def test_session_count():
    store = MemorySessionStore(max_sessions=50, ttl_minutes=30)
    store.create("s1", _make_session_data())
    store.create("s2", _make_session_data())
    assert store.session_count() == 2
