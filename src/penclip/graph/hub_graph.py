"""Bridge module — re-exports LangGraphEngine for backward compatibility.

Existing code imports:
    from penclip.graph.hub_graph import get_graph
"""

from penclip.core.orchestration.graph_engine import get_graph, LangGraphEngine

__all__ = ["get_graph", "LangGraphEngine"]
