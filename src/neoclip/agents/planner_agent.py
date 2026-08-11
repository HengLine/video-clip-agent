"""
@FileName: planner_agent.py
@Description: 规划师 Agent — 首个注册能力，实现线性链路节点模式
    处理所有 PLAN_* intent，内部管道: upload → sample → parse → REVIEW → analyze → match → compose
    V0.1: 管道节点为骨架 stub，V0.2 起逐步实现真实逻辑
@Author: HiPeng
@Time: 2026/08
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from neoclip.agents.base_agent import BaseAgent
from neoclip.logger import debug, info, warning
from neoclip.hub.capability_registry import CapabilityRecord
from neoclip.state.models import (
    AgentResult,
    Command,
    CommandTier,
    IntentType,
    MatchResult,
    RiskLevel,
    Slot,
    TaskLifecycleStage,
    TimelineBlueprint,
)


DEFAULT_PLANNER_CONFIG: Dict[str, Any] = {
    "pipeline_stages": ["upload", "sample", "parse", "review", "analyze", "match", "compose"],
    "review_checkpoint": True,
    "max_slots": 20,
    "default_transition": "fade",
    "default_duration_min": 2.0,
    "default_duration_max": 8.0,
}


class PlannerAgent(BaseAgent):
    """规划师 Agent — 处理全局规划指令

    注册 6 个 PLAN_* intent 到 CapabilityRegistry。
    内部维护线性管道状态，每个阶段可按需暂停/恢复。
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(name="planner_agent", config=config)
        self._init_config_defaults(DEFAULT_PLANNER_CONFIG)
        self._timelines: Dict[str, TimelineBlueprint] = {}
        self._pipeline_states: Dict[str, str] = {}  # session_id → current_stage
        self.register()

    def capabilities(self) -> List[CapabilityRecord]:
        return [
            CapabilityRecord(
                agent_name=self.name,
                intents=IntentType.planning_intents(),
                input_schema={
                    "type": "object",
                    "properties": {
                        "description": {"type": "string", "description": "视频结构描述"},
                        "video_paths": {"type": "array", "items": {"type": "string"}},
                        "slot_count": {"type": "integer", "description": "镜头数量"},
                        "mood": {"type": "string", "description": "氛围/风格"},
                    },
                },
                output_schema={
                    "type": "object",
                    "properties": {
                        "timeline": {"type": "object"},
                        "stage": {"type": "string"},
                    },
                },
                risk_level=RiskLevel.HIGH,
                version="0.1.0",
                description="Linear video clip planning pipeline — 从描述生成时间线蓝图",
                tier=CommandTier.TIER_1,
            )
        ]

    # ── 主分发 ──────────────────────────────────────────────

    def execute(self, command: Command) -> AgentResult:
        handlers = {
            IntentType.PLAN_CREATE: self._handle_create,
            IntentType.PLAN_APPEND: self._handle_append,
            IntentType.PLAN_INSERT: self._handle_insert,
            IntentType.PLAN_DELETE: self._handle_delete,
            IntentType.PLAN_REORDER: self._handle_reorder,
            IntentType.PLAN_DUPLICATE: self._handle_duplicate,
        }
        handler = handlers.get(command.intent_type)
        if handler is None:
            return self._result_fail(
                f"PlannerAgent does not handle '{command.intent_type.value}'",
                suggestions=["Try: plan_create, plan_append, plan_delete, plan_reorder"],
            )
        try:
            return handler(command)
        except Exception as e:
            warning(f"PlannerAgent.{command.intent_type.value} error: {e}")
            return self._result_fail(str(e))

    # ── PLAN_CREATE — 创建新时间线 ──────────────────────────

    def _handle_create(self, command: Command) -> AgentResult:
        params = command.parameters
        description = params.get("description", params.get("script", ""))
        video_paths = params.get("video_paths", params.get("videos", []))
        slot_count = params.get("slot_count", 3)
        mood = params.get("mood", params.get("style", ""))

        slot_count = min(slot_count, self.config["max_slots"])

        # 根据描述生成 slots（V0.1: 简单切分，V0.2: LLM 解析）
        slots = self._parse_slots_from_description(description, slot_count)

        timeline = TimelineBlueprint(
            slots=slots,
            global_context={
                "mood": mood,
                "bgm_preference": params.get("bgm", ""),
                "duration_constraint": params.get("max_duration", 0),
                "resolution": {"width": 1920, "height": 1080},
                "description": description,
            },
            version=1,
        )

        session_id = params.get("session_id", command.command_id)
        self._timelines[session_id] = timeline
        self._pipeline_states[session_id] = "parse"

        info(f"PlannerAgent: created timeline with {len(slots)} slots [session={session_id[:8]}]")

        return self._result_ok(
            data={
                "timeline": timeline.model_dump(),
                "stage": "parse",
                "next_stage": "review",
                "review_required": self.config["review_checkpoint"],
                "videos": video_paths,
                "slot_count": len(slots),
            },
            message=f"已创建时间线：{len(slots)} 个镜头位，等待审核确认",
        )

    # ── PLAN_APPEND — 追加镜头 ──────────────────────────────

    def _handle_append(self, command: Command) -> AgentResult:
        params = command.parameters
        session_id = params.get("session_id", "")
        timeline = self._get_timeline(session_id)

        if timeline is None:
            return self._result_fail("No active timeline. Use plan_create first.")

        if len(timeline.slots) >= self.config["max_slots"]:
            return self._result_fail(f"Max slots ({self.config['max_slots']}) reached")

        new_slot = Slot(
            semantic_description=params.get("description", ""),
            target_duration_min=params.get("duration_min", self.config["default_duration_min"]),
            target_duration_max=params.get("duration_max", self.config["default_duration_max"]),
            transition_type=params.get("transition", self.config["default_transition"]),
        )
        timeline.slots.append(new_slot)
        timeline.version += 1
        timeline.updated_at = datetime.now(timezone.utc)

        return self._result_ok(
            data={"timeline": timeline.model_dump(), "appended_slot_id": new_slot.slot_id},
            message=f"已追加镜头位 #{len(timeline.slots)}: {new_slot.semantic_description[:30]}",
        )

    # ── PLAN_INSERT — 插入镜头 ──────────────────────────────

    def _handle_insert(self, command: Command) -> AgentResult:
        params = command.parameters
        session_id = params.get("session_id", "")
        timeline = self._get_timeline(session_id)

        if timeline is None:
            return self._result_fail("No active timeline. Use plan_create first.")

        if len(timeline.slots) >= self.config["max_slots"]:
            return self._result_fail(f"Max slots ({self.config['max_slots']}) reached")

        after_idx = params.get("after_index", len(timeline.slots) - 1)
        new_slot = Slot(
            semantic_description=params.get("description", ""),
            target_duration_min=params.get("duration_min", self.config["default_duration_min"]),
            target_duration_max=params.get("duration_max", self.config["default_duration_max"]),
            transition_type=params.get("transition", self.config["default_transition"]),
        )
        insert_at = min(after_idx + 1, len(timeline.slots))
        timeline.slots.insert(insert_at, new_slot)
        timeline.version += 1
        timeline.updated_at = datetime.now(timezone.utc)

        return self._result_ok(
            data={"timeline": timeline.model_dump(), "inserted_slot_id": new_slot.slot_id, "position": insert_at},
            message=f"已在位置 {insert_at} 插入镜头位",
        )

    # ── PLAN_DELETE — 删除镜头 ──────────────────────────────

    def _handle_delete(self, command: Command) -> AgentResult:
        params = command.parameters
        session_id = params.get("session_id", "")
        timeline = self._get_timeline(session_id)

        if timeline is None:
            return self._result_fail("No active timeline.")

        slot_id = params.get("slot_id")
        slot_idx = params.get("slot_index")

        if slot_id:
            before = len(timeline.slots)
            timeline.slots = [s for s in timeline.slots if s.slot_id != slot_id]
            if len(timeline.slots) == before:
                return self._result_fail(f"Slot not found: {slot_id}")
        elif slot_idx is not None and 0 <= slot_idx < len(timeline.slots):
            removed = timeline.slots.pop(slot_idx)
            slot_id = removed.slot_id
        else:
            return self._result_fail("Specify slot_id or slot_index to delete")

        timeline.version += 1
        timeline.updated_at = datetime.now(timezone.utc)

        return self._result_ok(
            data={"timeline": timeline.model_dump(), "deleted_slot_id": slot_id},
            message=f"已删除镜头位 {slot_id[:8]}",
        )

    # ── PLAN_REORDER — 重新排序 ─────────────────────────────

    def _handle_reorder(self, command: Command) -> AgentResult:
        params = command.parameters
        session_id = params.get("session_id", "")
        timeline = self._get_timeline(session_id)

        if timeline is None:
            return self._result_fail("No active timeline.")

        from_idx = params.get("from_index")
        to_idx = params.get("to_index")

        if from_idx is None or to_idx is None:
            return self._result_fail("Specify from_index and to_index")

        if not (0 <= from_idx < len(timeline.slots) and 0 <= to_idx < len(timeline.slots)):
            return self._result_fail(f"Index out of range (0–{len(timeline.slots)-1})")

        timeline.slots.insert(to_idx, timeline.slots.pop(from_idx))
        timeline.version += 1
        timeline.updated_at = datetime.now(timezone.utc)

        return self._result_ok(
            data={"timeline": timeline.model_dump()},
            message=f"已将镜头位 {from_idx} 移动到 {to_idx}",
        )

    # ── PLAN_DUPLICATE — 复制镜头 ────────────────────────────

    def _handle_duplicate(self, command: Command) -> AgentResult:
        params = command.parameters
        session_id = params.get("session_id", "")
        timeline = self._get_timeline(session_id)

        if timeline is None:
            return self._result_fail("No active timeline.")

        slot_id = params.get("slot_id")
        if not slot_id:
            return self._result_fail("Specify slot_id to duplicate")

        for slot in timeline.slots:
            if slot.slot_id == slot_id:
                import copy
                new_slot = copy.deepcopy(slot)
                new_slot.slot_id = str(uuid.uuid4())
                timeline.slots.append(new_slot)
                timeline.version += 1
                timeline.updated_at = datetime.now(timezone.utc)
                return self._result_ok(
                    data={"timeline": timeline.model_dump(), "new_slot_id": new_slot.slot_id},
                    message=f"已复制镜头位 → {new_slot.slot_id[:8]}",
                )

        return self._result_fail(f"Slot not found: {slot_id}")

    # ── 管道阶段 (V0.1 stub) ─────────────────────────────────

    def run_pipeline(self, session_id: str, video_paths: List[str]) -> Dict[str, Any]:
        """执行完整线性管道（V0.1 骨架）"""
        stages = self.config["pipeline_stages"]
        results: Dict[str, Any] = {"stages_completed": [], "pipeline": "linear_clip_workflow"}

        for stage in stages:
            self._pipeline_states[session_id] = stage
            handler = getattr(self, f"_stage_{stage}", None)
            if handler:
                results[stage] = handler(session_id, video_paths)
            results["stages_completed"].append(stage)

        return results

    def _stage_upload(self, session_id: str, video_paths: List[str]) -> Dict[str, Any]:
        """Stub: 视频上传 & 格式校验"""
        return {"success": True, "videos_received": len(video_paths), "data": {"paths": video_paths}}

    def _stage_sample(self, session_id: str, video_paths: List[str]) -> Dict[str, Any]:
        """Stub: 快速采样 — 每视频提取 3-5 关键帧"""
        return {"success": True, "data": {"thumbnail_count": len(video_paths) * 3, "thumbnails": []}}

    def _stage_parse(self, session_id: str, video_paths: List[str]) -> Dict[str, Any]:
        """Stub: 指令解析 — V0.2 升级为多模态 LLM 结构化输出"""
        timeline = self._get_timeline(session_id)
        return {"success": True, "data": {"timeline": timeline.model_dump() if timeline else None}}

    def _stage_review(self, session_id: str, video_paths: List[str]) -> Dict[str, Any]:
        """Stub: 用户审核 — 最关键的检查点"""
        return {
            "success": True,
            "data": {"awaiting_confirmation": True, "message": "时间线待审核确认"},
            "checkpoint": True,
        }

    def _stage_analyze(self, session_id: str, video_paths: List[str]) -> Dict[str, Any]:
        """Stub: 视频分析 — 场景分割 + 语义标注 (PySceneDetect + CLIP)"""
        return {"success": True, "data": {"scene_count": 0, "metadata": []}}

    def _stage_match(self, session_id: str, video_paths: List[str]) -> Dict[str, Any]:
        """Stub: 片段匹配 — 语义检索 + 空缺标记"""
        return {"success": True, "data": {"match_results": {}, "vacancies": []}}

    def _stage_compose(self, session_id: str, video_paths: List[str]) -> Dict[str, Any]:
        """Stub: 视频合成 — FFmpeg 命令生成 + 子进程执行"""
        return {"success": True, "data": {"output_path": "", "command": ""}}

    # ── 辅助 ─────────────────────────────────────────────────

    def _get_timeline(self, session_id: str) -> Optional[TimelineBlueprint]:
        return self._timelines.get(session_id)

    def _parse_slots_from_description(self, description: str, slot_count: int) -> List[Slot]:
        """V0.1: 按句子/逗号分拆为镜头位；V0.2: LLM 语义解析"""
        if not description:
            return [Slot(semantic_description=f"镜头 {i+1}") for i in range(slot_count)]

        # 按中英文标点分拆
        import re
        parts = re.split(r"[。，；;,\n]", description)
        parts = [p.strip() for p in parts if p.strip()]

        if len(parts) < slot_count:
            # 补全到目标数量
            for i in range(len(parts), slot_count):
                parts.append(f"镜头 {i+1}")

        slots = []
        for i, text in enumerate(parts[:slot_count]):
            slots.append(Slot(
                semantic_description=text,
                target_duration_min=self.config["default_duration_min"],
                target_duration_max=self.config["default_duration_max"],
                transition_type=self.config["default_transition"],
                priority=max(1, 10 - i),  # 前面镜头优先级更高
            ))

        return slots

    def get_pipeline_stage(self, session_id: str) -> str:
        return self._pipeline_states.get(session_id, "idle")


# ============================================================================
# 单例
# ============================================================================

_planner_agent: Optional[PlannerAgent] = None


def get_planner_agent() -> PlannerAgent:
    global _planner_agent
    if _planner_agent is None:
        _planner_agent = PlannerAgent()
    return _planner_agent
