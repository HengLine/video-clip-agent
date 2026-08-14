"""MemoryStateStore — in-memory state store (V0.1 default)."""

import threading
from typing import Any, Dict, List, Optional

from neoclip.core.state.state_store import StateStore


class MemoryStateStore(StateStore):
    def __init__(self):
        self._store: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()

    def get(self, session_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            return self._store.get(session_id)

    def put(self, session_id: str, state: Dict[str, Any]) -> None:
        with self._lock:
            self._store[session_id] = state

    def delete(self, session_id: str) -> bool:
        with self._lock:
            return self._store.pop(session_id, None) is not None

    def list_sessions(self) -> List[str]:
        with self._lock:
            return list(self._store.keys())
