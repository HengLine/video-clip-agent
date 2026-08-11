"""
@FileName: models.py
@Description: 全局数据模型定义 — 星型中枢架构的通用类型系统
    所有 Pydantic 数据契约，供 hub、agents、api 层共享
@Author: HiPeng
@Time: 2026/08
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ============================================================================
# 核心枚举
# ============================================================================


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class CommandTier(int, Enum):
    TIER_1 = 1  # global planning
    TIER_2 = 2  # agent operations
    TIER_3 = 3  # property modification / state query


class TaskLifecycleStage(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    ANALYZING = "analyzing"
    MATCHING = "matching"
    COMPOSING = "composing"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class IntentType(str, Enum):
    # 规划类 (TIER_1)
    PLAN_CREATE = "plan_create"
    PLAN_APPEND = "plan_append"
    PLAN_INSERT = "plan_insert"
    PLAN_DELETE = "plan_delete"
    PLAN_REORDER = "plan_reorder"
    PLAN_DUPLICATE = "plan_duplicate"

    # 分析类 (TIER_2)
    ANALYZE_FULL = "analyze_full"
    ANALYZE_INCREMENTAL = "analyze_incremental"
    ANALYZE_PRIORITY = "analyze_priority"
    ANALYZE_CANCEL = "analyze_cancel"

    # 素材操作类 (TIER_2)
    CLIP_TRIM = "clip_trim"
    CLIP_REPLACE = "clip_replace"
    CLIP_SWAP = "clip_swap"
    CLIP_PREVIEW = "clip_preview"
    CLIP_REMOVE = "clip_remove"

    # 效果类 (TIER_2)
    EFFECT_ADD_TRANSITION = "effect_add_transition"
    EFFECT_CHANGE_TRANSITION = "effect_change_transition"
    EFFECT_ADD_FILTER = "effect_add_filter"
    EFFECT_REMOVE_FILTER = "effect_remove_filter"
    AUDIO_ADJUST_VOLUME = "audio_adjust_volume"
    AUDIO_ADD_BGM = "audio_add_bgm"
    AUDIO_ADJUST_BGM_VOLUME = "audio_adjust_bgm_volume"

    # 状态类 (TIER_3)
    STATE_QUERY_PROGRESS = "state_query_progress"
    STATE_QUERY_CAPABILITIES = "state_query_capabilities"
    STATE_UNDO = "state_undo"
    STATE_REDO = "state_redo"

    @property
    def tier(self) -> CommandTier:
        if self.value.startswith("plan_"):
            return CommandTier.TIER_1
        if self.value.startswith("state_"):
            return CommandTier.TIER_3
        return CommandTier.TIER_2

    @classmethod
    def planning_intents(cls) -> List["IntentType"]:
        return [i for i in cls if i.tier == CommandTier.TIER_1]

    @classmethod
    def agent_intents(cls) -> List["IntentType"]:
        return [i for i in cls if i.tier == CommandTier.TIER_2]

    @classmethod
    def state_intents(cls) -> List["IntentType"]:
        return [i for i in cls if i.tier == CommandTier.TIER_3]


# ============================================================================
# 命令协议
# ============================================================================


class Command(BaseModel):
    """Hub → Agent 统一命令结构"""

    command_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    intent_type: IntentType
    parameters: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)

    @property
    def tier(self) -> CommandTier:
        return self.intent_type.tier


class AgentResult(BaseModel):
    """Agent → Hub 统一返回结构"""

    status: Literal["success", "failed", "partial"] = "success"
    data: Optional[Dict[str, Any]] = None
    message: str = ""
    suggestions: Optional[List[str]] = None


# ============================================================================
# 核心状态模型
# ============================================================================


class Slot(BaseModel):
    """时间线的一个镜头位"""

    slot_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    semantic_description: str = ""
    target_duration_min: float = Field(default=1.0, ge=0.1, description="最小时长(秒)")
    target_duration_max: float = Field(default=10.0, ge=0.1, description="最大时长(秒)")
    priority: int = Field(default=5, ge=1, le=10)
    hard_constraints: Dict[str, Any] = Field(default_factory=dict)
    soft_constraints: Dict[str, Any] = Field(default_factory=dict)
    transition_type: str = "fade"
    assigned_clip_id: Optional[str] = None
    volume_level: float = Field(default=1.0, ge=0.0, le=2.0)


class TimelineBlueprint(BaseModel):
    """全局时间线蓝图 — 整个编辑任务的结构描述"""

    blueprint_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    slots: List[Slot] = Field(default_factory=list)
    global_context: Dict[str, Any] = Field(
        default_factory=lambda: {
            "mood": "",
            "bgm_preference": "",
            "duration_constraint": 0,
            "resolution": {"width": 1920, "height": 1080},
        }
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1


class ClipMetadata(BaseModel):
    """视频分析结果 — 单个片段单元的语义标注"""

    clip_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    source_video_path: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    duration: float = 0.0
    scene_labels: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    thumbnail_path: Optional[str] = None
    audio_features: Dict[str, Any] = Field(default_factory=dict)


class MatchResult(BaseModel):
    """片段匹配结果"""

    slot_id: str = ""
    matched_clip: Optional[ClipMetadata] = None
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    alternatives: List[ClipMetadata] = Field(default_factory=list)
    is_vacant: bool = False
    vacancy_reason: Optional[str] = None


class VideoAssemblyState(BaseModel):
    """全局产品状态 — 所有 Agent 共享的"画板" """

    timeline: Optional[TimelineBlueprint] = None
    match_results: Dict[str, MatchResult] = Field(default_factory=dict)
    phase: TaskLifecycleStage = TaskLifecycleStage.PENDING
    errors: List[Dict[str, Any]] = Field(default_factory=list)
    metrics: Dict[str, Any] = Field(default_factory=dict)
    uploaded_videos: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class InteractionContext(BaseModel):
    """交互层上下文 — 与产品状态分离"""

    active_slot_id: Optional[str] = None
    last_previewed_clip: Optional[str] = None
    pending_clarification: Optional[str] = None
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    last_intent: Optional[IntentType] = None
    context_vars: Dict[str, Any] = Field(default_factory=dict)

    def record_turn(self, role: str, text: str) -> None:
        self.conversation_history.append(
            {"role": role, "text": text, "timestamp": datetime.now(timezone.utc).isoformat()}
        )
        if len(self.conversation_history) > 20:
            self.conversation_history = self.conversation_history[-20:]


# ============================================================================
# 意图识别结果
# ============================================================================


class RecognizedIntent(BaseModel):
    """意图识别结果"""

    intent_type: IntentType
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    raw_input: str = ""
    tier: CommandTier = CommandTier.TIER_2

    @classmethod
    def from_match(cls, intent_type: IntentType, raw_input: str, confidence: float = 1.0) -> "RecognizedIntent":
        return cls(
            intent_type=intent_type,
            confidence=confidence,
            raw_input=raw_input,
            tier=intent_type.tier,
        )


class ExtractedParams(BaseModel):
    """参数提取结果"""

    parameters: Dict[str, Any] = Field(default_factory=dict)
    missing_params: List[str] = Field(default_factory=list)
    clarification_needed: bool = False
    clarification_message: Optional[str] = None


class RouteDecision(BaseModel):
    """路由决策"""

    target_agent: Optional[str] = None
    command: Command = Field(default_factory=lambda: Command(intent_type=IntentType.STATE_QUERY_CAPABILITIES, parameters={}))
    risk_level: RiskLevel = RiskLevel.LOW
    requires_confirmation: bool = False
    is_direct_update: bool = False
