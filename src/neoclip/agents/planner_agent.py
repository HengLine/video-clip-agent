"""Bridge module — re-exports PlannerAgent for backward compatibility.

Existing code imports:
    from neoclip.agents.planner_agent import get_planner_agent
"""

from neoclip.agents.planner import get_planner_agent, PlannerAgent

__all__ = ["get_planner_agent", "PlannerAgent"]
