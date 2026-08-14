"""Bridge module — re-exports LangGraphEngine for backward compatibility.

Existing code imports:
    from neoclip.graph.hub_graph import get_graph
"""

from neoclip.core.orchestration.graph_engine import get_graph, LangGraphEngine

__all__ = ["get_graph", "LangGraphEngine"]
