"""
@FileName: __init__.py
@Description: state 包 — 全局数据模型
@Author: HiPeng
@Time: 2026/08
"""
from neoclip.state.models import (
    # 枚举
    RiskLevel,
    CommandTier,
    TaskLifecycleStage,
    IntentType,
    # 命令协议
    Command,
    AgentResult,
    # 核心状态
    Slot,
    TimelineBlueprint,
    ClipMetadata,
    MatchResult,
    VideoAssemblyState,
    InteractionContext,
    # 意图识别
    RecognizedIntent,
    ExtractedParams,
    RouteDecision,
)

__all__ = [
    "RiskLevel",
    "CommandTier",
    "TaskLifecycleStage",
    "IntentType",
    "Command",
    "AgentResult",
    "Slot",
    "TimelineBlueprint",
    "ClipMetadata",
    "MatchResult",
    "VideoAssemblyState",
    "InteractionContext",
    "RecognizedIntent",
    "ExtractedParams",
    "RouteDecision",
]
