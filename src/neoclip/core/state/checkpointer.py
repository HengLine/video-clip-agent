"""Checkpointer — LangGraph-compatible state persistence wrapper."""

from typing import Any, Dict, Optional

from neoclip.core.state.state_store import StateStore
from neoclip.core.state.memory_store import MemoryStateStore
from neoclip.logger import debug


class Checkpointer:
    """Wraps StateStore with LangGraph-compatible put/get interface."""

    def __init__(self, store: Optional[StateStore] = None):
        self._store = store or MemoryStateStore()

    def get(self, config: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        thread_id = config.get("configurable", {}).get("thread_id", "")
        return self._store.get(thread_id)

    def put(self, config: Dict[str, Any], checkpoint: Dict[str, Any], metadata: Dict[str, Any]) -> Dict[str, Any]:
        thread_id = config.get("configurable", {}).get("thread_id", "")
        self._store.put(thread_id, checkpoint)
        return config

    def list(self, config: Optional[Dict[str, Any]] = None, *, filter: Optional[Dict[str, Any]] = None,
             before: Optional[Dict[str, Any]] = None, limit: Optional[int] = None):
        return []
