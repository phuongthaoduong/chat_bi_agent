from datetime import datetime

from models.domain import SessionData
from session.interface import SessionStore


class MemorySessionStore(SessionStore):
    def __init__(self, max_sessions: int, ttl_minutes: int):
        self._store: dict[str, SessionData] = {}
        self._max_sessions = max_sessions
        self._ttl_minutes = ttl_minutes

    def create(self, session_id: str, data: SessionData) -> None:
        if len(self._store) >= self._max_sessions:
            raise RuntimeError("Server at capacity")
        self._store[session_id] = data

    def get(self, session_id: str) -> SessionData | None:
        data = self._store.get(session_id)
        if data is not None:
            data.last_accessed_at = datetime.now()
        return data

    def update(self, session_id: str, data: SessionData) -> None:
        if session_id not in self._store:
            return
        data.last_accessed_at = datetime.now()
        self._store[session_id] = data

    def delete(self, session_id: str) -> None:
        self._store.pop(session_id, None)

    def session_count(self) -> int:
        return len(self._store)

    def cleanup_expired(self) -> int:
        now = datetime.now()
        expired = [
            sid
            for sid, data in self._store.items()
            if (now - data.last_accessed_at).total_seconds() > self._ttl_minutes * 60
        ]
        for sid in expired:
            del self._store[sid]
        return len(expired)
