"""SessionRepository interface — abstract persistence for user sessions."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class SessionRepository(ABC):
    @abstractmethod
    def save(self, session: Dict[str, Any]) -> None:
        ...

    @abstractmethod
    def find_by_id(self, session_id: str) -> Optional[Dict[str, Any]]:
        ...

    @abstractmethod
    def find_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        ...

    @abstractmethod
    def delete(self, session_id: str) -> bool:
        ...

    @abstractmethod
    def update(self, session: Dict[str, Any]) -> None:
        ...
