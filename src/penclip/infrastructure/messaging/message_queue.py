"""MessageQueue — abstract message queue interface."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class MessageQueue(ABC):
    @abstractmethod
    def enqueue(self, queue: str, message: Dict[str, Any]) -> bool:
        ...

    @abstractmethod
    def dequeue(self, queue: str, timeout: int = 0) -> Optional[Dict[str, Any]]:
        ...

    @abstractmethod
    def length(self, queue: str) -> int:
        ...
