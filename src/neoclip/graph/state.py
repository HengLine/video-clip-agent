"""
@FileName: state.py
@Description: LangGraph State 定义 — 星型中枢 + 线性管道的统一状态 Schema
    HubState 用 TypedDict 定义，带 reducer 的字段使用 Annotated
    VideoAssemblyState / InteractionContext 作为嵌套子对象
@Author: HiPeng
@Time: 2026/08
"""
import operator
from typing import Annotated, Any, Dict, List, Optional, TypedDict

from neoclip.state.models import (
    InteractionContext,
    IntentType,
    MatchResult,
    RecognizedIntent,
    RiskLevel,
    TimelineBlueprint,
)


# ============================================================================
# Reducer: dict 合并（用于 match_results）
# ============================================================================


def merge_dicts(left: Dict[str, Any], right: Dict[str, Any]) -> Dict[str, Any]:
    """合并两个 dict，右侧覆盖左侧同名键"""
    merged = dict(left)
    merged.update(right)
    return merged


# ============================================================================
# HubState — 中枢主状态
# ============================================================================


class HubState(TypedDict, total=False):
    """星型中枢的 LangGraph 统一状态

    所有节点共享此状态。checkpointer 在每个 super-step 后持久化。
    InteractionContext 作为子对象嵌入（架构文档要求）。
    """

    # ── 输入 ──
    user_input: str
    session_id: str

    # ── 意图处理（RecognizedIntent / ExtractedParams 字段展开） ──
    recognized_intent: Optional[str]   # IntentType.value
    intent_confidence: float
    extracted_params: Dict[str, Any]
    missing_params: List[str]
    clarification_needed: bool
    clarification_message: Optional[str]

    # ── 风险 & 路由 ──
    risk_level: Optional[str]           # RiskLevel.value
    target_agent: Optional[str]
    requires_confirmation: bool
    confirmed: bool                      # 用户已确认（HIGH 风险恢复用）

    # ── 产品状态 (VideoAssemblyState 展开) ──
    timeline: Optional[Dict[str, Any]]   # TimelineBlueprint as dict
    match_results: Annotated[Dict[str, Any], merge_dicts]
    phase: str                           # TaskLifecycleStage.value
    errors: Annotated[List[Dict[str, Any]], operator.add]
    uploaded_videos: List[str]

    # ── 交互上下文 (InteractionContext 展开) ──
    active_slot_id: Optional[str]
    last_previewed_clip: Optional[str]
    pending_clarification: Optional[str]
    conversation_history: Annotated[List[Dict[str, Any]], operator.add]
    last_intent: Optional[str]

    # ── 输出 ──
    agent_result: Optional[Dict[str, Any]]  # AgentResult as dict
    response_message: str

    # ── 控制 ──
    auto_confirm: bool                   # API 模式跳过 interrupt
    messages: Annotated[List[Dict[str, Any]], operator.add]
