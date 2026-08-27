"""StateManager — manages AssemblyState instances per session."""

from typing import Any, Dict, Optional

from penclip.core.state.memory_store import MemoryStateStore
from penclip.core.state.state_store import StateStore
from penclip.core.event.event_bus import get_event_bus
from penclip.core.event.event_types import Event, EventType
from penclip.domain.entities.assembly_state import AssemblyState
from penclip.logger import debug, info


class StateManager:
    def __init__(self, store: Optional[StateStore] = None):
        self._store = store or MemoryStateStore()
        self._event_bus = get_event_bus()

    def create_session(self, session_id: Optional[str] = None) -> AssemblyState:
        state = AssemblyState(session_id=session_id) if session_id else AssemblyState()
        self._store.put(state.session_id, state.model_dump())
        self._event_bus.publish(Event(
            event_type=EventType.SESSION_CREATED,
            session_id=state.session_id,
        ))
        info(f"StateManager: created session {state.session_id[:8]}")
        return state

    def get_session(self, session_id: str) -> Optional[AssemblyState]:
        raw = self._store.get(session_id)
        if raw is None:
            return None
        return AssemblyState(**raw)

    def update_session(self, state: AssemblyState):
        self._store.put(state.session_id, state.model_dump())
        self._event_bus.publish(Event(
            event_type=EventType.STATE_UPDATED,
            session_id=state.session_id,
        ))

    def delete_session(self, session_id: str) -> bool:
        return self._store.delete(session_id)


_manager: StateManager = None


def get_state_manager() -> StateManager:
    global _manager
    if _manager is None:
        _manager = StateManager()
    return _manager
