"""LangGraphEngine — wrapper around LangGraph for state-machine workflows."""

from typing import Any, Dict, List, Optional

from neoclip.logger import debug, info


class LangGraphEngine:
    """V0.1 thin wrapper — full LangGraph integration in V0.2."""

    def __init__(self):
        self._graph: Any = None
        self._compiled: bool = False
        debug("LangGraphEngine initialized (stub)")

    def compile(self, state_graph: Any) -> Any:
        self._graph = state_graph
        self._compiled = True
        info("LangGraphEngine: graph compiled")
        return self

    def invoke(self, state: Dict[str, Any], config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return state

    def stream(self, state: Dict[str, Any], config: Optional[Dict[str, Any]] = None):
        yield state


_graph: LangGraphEngine = None


def get_graph() -> LangGraphEngine:
    global _graph
    if _graph is None:
        _graph = LangGraphEngine()
    return _graph
