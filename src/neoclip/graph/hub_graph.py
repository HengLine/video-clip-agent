"""
@FileName: hub_graph.py
@Description: LangGraph StateGraph 编译 — 星型中枢主图
    recognize → extract → risk_gate → route → dispatch_agent/state_update → END
    管道路由到 pipeline 子图；Tier 3 路由到 state_update
@Author: HiPeng
@Time: 2026/08
"""
from typing import Optional

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph

from neoclip.graph.nodes import (
    decide_route,
    dispatch_agent,
    extract_params,
    recognize_intent,
    risk_gate,
    state_update,
)
from neoclip.graph.state import HubState


def compile_hub_graph():
    """构建并编译中枢 StateGraph

    Graph topology (static):
        START → recognize → extract → risk_gate → route → dispatch_agent → END
                                                       → state_update  → END

    Route decision (dynamic):
        - clarification_needed → END (return clarification)
        - HIGH risk + unconfirmed → END (return confirmation request, interrupt fires in risk_gate)
        - Tier 3 (STATE_*) → state_update
        - Tier 1/2 → dispatch_agent (runtime CapabilityRegistry lookup)
    """
    builder = StateGraph(HubState)

    # 添加节点
    builder.add_node("recognize", recognize_intent)
    builder.add_node("extract", extract_params)
    builder.add_node("risk_gate", risk_gate)
    builder.add_node("dispatch_agent", dispatch_agent)
    builder.add_node("state_update", state_update)

    # 边
    builder.add_edge(START, "recognize")
    builder.add_edge("recognize", "extract")
    builder.add_edge("extract", "risk_gate")

    # 条件路由 — dispatch_agent 或 state_update 或 END
    builder.add_conditional_edges(
        "risk_gate",
        decide_route,
        {
            "dispatch_agent": "dispatch_agent",
            "state_updater": "state_update",
            "state_update": "state_update",
            "end": END,
        },
    )

    builder.add_edge("dispatch_agent", END)
    builder.add_edge("state_update", END)

    checkpointer = get_checkpointer()
    graph = builder.compile(checkpointer=checkpointer)
    return graph


# ============================================================================
# 单例 — 编译图 + checkpointer
# ============================================================================

_compiled_graph = None
_checkpointer: Optional[MemorySaver] = None


def get_checkpointer() -> MemorySaver:
    """V0.1 MemorySaver → V0.2 SqliteSaver → V1.0 PostgresSaver"""
    global _checkpointer
    if _checkpointer is None:
        _checkpointer = MemorySaver()
    return _checkpointer


def get_graph():
    """获取编译后的中枢图（懒编译单例）"""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = compile_hub_graph()
    return _compiled_graph


def reset_graph():
    """重置编译图和 checkpointer（用于测试）"""
    global _compiled_graph, _checkpointer
    _compiled_graph = None
    _checkpointer = None
