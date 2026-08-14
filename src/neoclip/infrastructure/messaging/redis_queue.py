"""RedisQueue — Redis-backed message queue implementation."""

from typing import Any, Dict, Optional
from neoclip.infrastructure.messaging.message_queue import MessageQueue
from neoclip.logger import debug


class RedisQueue(MessageQueue):
    def __init__(self, redis_url: str = ""):
        self._redis_url = redis_url
        debug("RedisQueue initialized (stub)")

    def enqueue(self, queue: str, message: Dict[str, Any]) -> bool:
        return True

    def dequeue(self, queue: str, timeout: int = 0) -> Optional[Dict[str, Any]]:
        return None

    def length(self, queue: str) -> int:
        return 0
