"""RedisCache — Redis-backed cache implementation."""

from typing import Any, Optional
from penclip.infrastructure.cache.cache_service import CacheService
from penclip.logger import debug


class RedisCache(CacheService):
    def __init__(self, redis_url: str = ""):
        self._redis_url = redis_url
        self._client = None
        debug("RedisCache initialized (stub)")

    def get(self, key: str) -> Optional[Any]:
        return None

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        pass

    def delete(self, key: str) -> bool:
        return True

    def clear(self) -> None:
        pass
