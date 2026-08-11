"""
@FileName: pipeline.py
@Description: 线性管道子图 — Upload→Sample→Parse→REVIEW→Analyze→Match→Compose
    LangGraph 编译子图，注册为 PLAN capability
    REVIEW 节点用 interrupt() 实现人机协同检查点
@Author: HiPeng
@Time: 2026/08
"""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TypedDict

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt

from neoclip.logger import info, warning
from neoclip.state.models import Slot, TimelineBlueprint


# ============================================================================
# PipelineState — 管道子图状态
# ============================================================================


class PipelineState(TypedDict, total=False):
    """线性管道状态 — 与 HubState 键重叠以便作为子图"""

    session_id: str
    user_input: str

    # 管道阶段
    pipeline_stage: str
    timeline: Optional[Dict[str, Any]]
    uploaded_videos: List[str]
    review_confirmed: bool
    compose_output_path: Optional[str]

    # 输出
    response_message: str
    errors: List[Dict[str, Any]]


# ============================================================================
# 管道节点
# ============================================================================


def pipeline_parse(state: dict) -> dict:
    """Parse: 将用户输入解析为 TimelineBlueprint（V0.1 简单分拆，V0.2 LLM）"""
    user_input = state.get("user_input", "")
    import re
    parts = re.split(r"[。，；;,\n]", user_input)
    parts = [p.strip() for p in parts if p.strip()]

    if not parts:
        parts = ["未命名镜头"]

    slots = []
    for i, text in enumerate(parts[:20]):
        slots.append(Slot(
            semantic_description=text,
            target_duration_min=2.0,
            target_duration_max=8.0,
            transition_type="fade",
            priority=max(1, 10 - i),
        ).model_dump())

    timeline = TimelineBlueprint(
        slots=[Slot(**s) for s in slots],
        global_context={"description": user_input},
        version=1,
    )

    info(f"[pipeline.parse] Created timeline with {len(slots)} slots")
    return {
        "pipeline_stage": "parse",
        "timeline": timeline.model_dump(),
        "response_message": f"已创建时间线：{len(slots)} 个镜头位",
    }


def pipeline_review(state: dict) -> dict:
    """REVIEW: 人机协同检查点 — interrupt 暂停等待用户确认

    用户通过 Command(resume=...) 恢复：
    - resume={"confirmed": True} → 继续到 Analyze
    - resume={"edits": {...}} → 应用编辑 → 返回 REVIEW
    """
    timeline = state.get("timeline") or {}
    slots = timeline.get("slots", [])

    info(f"[pipeline.review] Interrupting for review of {len(slots)} slots")

    # interrupt — 暂停图执行，等待用户输入
    user_response = interrupt({
        "type": "review_checkpoint",
        "stage": "review",
        "timeline": timeline,
        "message": f"时间线包含 {len(slots)} 个镜头位，请审核确认或修改",
    })

    # 处理恢复
    if isinstance(user_response, dict):
        if user_response.get("confirmed"):
            return {"pipeline_stage": "review", "review_confirmed": True,
                    "response_message": "审核通过，开始视频分析"}
        if "edits" in user_response:
            return {"pipeline_stage": "review", "review_confirmed": False,
                    "timeline": user_response["edits"],
                    "response_message": "已应用修改，请重新审核"}
        if "timeline" in user_response:
            return {"pipeline_stage": "review", "review_confirmed": False,
                    "timeline": user_response["timeline"],
                    "response_message": "时间线已更新，请重新审核"}

    # 默认：确认通过
    return {"pipeline_stage": "review", "review_confirmed": True,
            "response_message": "审核通过"}


def pipeline_analyze(state: dict) -> dict:
    """Analyze: 视频分析 — V0.1 stub"""
    info("[pipeline.analyze] Stub — no analysis performed")
    return {
        "pipeline_stage": "analyze",
        "response_message": "视频分析完成（V0.1 stub）",
    }


def pipeline_match(state: dict) -> dict:
    """Match: 片段匹配 — V0.1 stub"""
    info("[pipeline.match] Stub — no matching performed")
    return {
        "pipeline_stage": "match",
        "response_message": "片段匹配完成（V0.1 stub）",
    }


def pipeline_compose(state: dict) -> dict:
    """Compose: 视频合成 — V0.1 stub"""
    info("[pipeline.compose] Stub — no composition performed")
    return {
        "pipeline_stage": "compose",
        "compose_output_path": "",
        "response_message": "视频合成完成（V0.1 stub）",
    }


# ============================================================================
# 条件路由
# ============================================================================


def review_router(state: dict) -> str:
    """REVIEW 后的路由：确认 → analyze, 未确认 → 回到 review"""
    if state.get("review_confirmed"):
        return "analyze"
    return "review"


# ============================================================================
# 编译管道子图
# ============================================================================


def compile_pipeline():
    """编译线性管道子图"""
    builder = StateGraph(PipelineState)

    builder.add_node("parse", pipeline_parse)
    builder.add_node("review", pipeline_review)
    builder.add_node("analyze", pipeline_analyze)
    builder.add_node("match", pipeline_match)
    builder.add_node("compose", pipeline_compose)

    builder.add_edge(START, "parse")
    builder.add_edge("parse", "review")

    builder.add_conditional_edges("review", review_router, {
        "analyze": "analyze",
        "review": "review",
    })

    builder.add_edge("analyze", "match")
    builder.add_edge("match", "compose")
    builder.add_edge("compose", END)

    return builder.compile(checkpointer=MemorySaver())
