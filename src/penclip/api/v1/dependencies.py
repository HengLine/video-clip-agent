"""Dependency injection — FastAPI dependency providers for hub, state, agents."""

from penclip.core.hub.central_hub import get_hub, CentralHub
from penclip.core.state.state_manager import get_state_manager, StateManager


def get_central_hub() -> CentralHub:
    return get_hub()


def get_state_manager_dep() -> StateManager:
    return get_state_manager()
