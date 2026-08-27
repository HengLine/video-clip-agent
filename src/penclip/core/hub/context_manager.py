"""ContextManager — maintains per-session interaction context for reference resolution."""

import threading
from typing import Any, Dict, List, Optional

from penclip.domain.entities.assembly_state import InteractionContext
from penclip.logger import debug


class ContextManager:
    def __init__(self, max_history: int = 50):
        self._sessions: Dict[str, InteractionContext] = {}
        self._max_history = max_history
        self._lock = threading.Lock()
        debug(f"ContextManager initialized (max_history={max_history})")

    def get_context(self, session_id: str) -> InteractionContext:
        with self._lock:
            if session_id not in self._sessions:
                self._sessions[session_id] = InteractionContext()
            return self._sessions[session_id]

    def update_context(self, session_id: str, update: Dict[str, Any]):
        ctx = self.get_context(session_id)
        with self._lock:
            for key, value in update.items():
                if hasattr(ctx, key):
                    setattr(ctx, key, value)

    def resolve_reference(self, session_id: str, reference: str) -> Optional[str]:
        ctx = self.get_context(session_id)
        if reference in ("它", "这个", "那个", "这段"):
            return ctx.active_slot_id or ctx.last_previewed_clip
        return None

    def add_history(self, session_id: str, entry: Dict[str, Any]):
        ctx = self.get_context(session_id)
        with self._lock:
            ctx.conversation_history.append(entry)
            if len(ctx.conversation_history) > self._max_history:
                ctx.conversation_history = ctx.conversation_history[-self._max_history:]

    def clear_context(self, session_id: str):
        with self._lock:
            self._sessions.pop(session_id, None)
