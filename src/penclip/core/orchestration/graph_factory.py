"""GraphFactory — builds LangGraph StateGraph instances for different workflows."""

from typing import Any, Dict, Optional

from penclip.core.orchestration.graph_engine import LangGraphEngine
from penclip.logger import debug


class GraphFactory:
    """Factory for creating pre-configured LangGraph state graphs."""

    @staticmethod
    def create_linear_clip_graph() -> Any:
        """Create the standard linear clip workflow graph."""
        debug("GraphFactory: creating linear clip graph (stub)")
        return LangGraphEngine()

    @staticmethod
    def create_hub_graph() -> Any:
        """Create the hub dispatch graph."""
        debug("GraphFactory: creating hub graph (stub)")
        return LangGraphEngine()
