from abc import ABC, abstractmethod

from models.domain import SessionData


class SessionStore(ABC):
    @abstractmethod
    def create(self, session_id: str, data: SessionData) -> None: ...

    @abstractmethod
    def get(self, session_id: str) -> SessionData | None: ...

    @abstractmethod
    def update(self, session_id: str, data: SessionData) -> None: ...

    @abstractmethod
    def delete(self, session_id: str) -> None: ...

    @abstractmethod
    def session_count(self) -> int: ...
