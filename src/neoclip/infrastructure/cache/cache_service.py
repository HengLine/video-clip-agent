"""CacheService — abstract caching interface."""

from abc import ABC, abstractmethod
from typing import Any, Optional


class CacheService(ABC):
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        ...

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        ...

    @abstractmethod
    def delete(self, key: str) -> bool:
        ...

    @abstractmethod
    def clear(self) -> None:
        ...
