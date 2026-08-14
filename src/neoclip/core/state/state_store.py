"""StateStore — abstract interface for state persistence."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class StateStore(ABC):
    @abstractmethod
    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        ...

    @abstractmethod
    def put(self, session_id: str, state: Dict[str, Any]) -> None:
        ...

    @abstractmethod
    def delete(self, session_id: str) -> bool:
        ...

    @abstractmethod
    def list_sessions(self) -> list:
        ...
