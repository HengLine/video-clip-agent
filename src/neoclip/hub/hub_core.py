"""
@FileName: hub_core.py
@Description: 星型中枢核心 — 统一入口，命令处理链
    recognize → extract → (clarify?) → evaluate risk → decide route → dispatch
    V0.1 关键字识别，V0.2 升级 LLM 语义理解（接口不变）
@Author: HiPeng
@Time: 2026/08
"""
from typing import Any, Dict, List, Optional

from neoclip.logger import debug, info, warning, error
from neoclip.state.models import (
    AgentResult,
    Command,
    CommandTier,
    ExtractedParams,
    IntentType,
    InteractionContext,
    RecognizedIntent,
    RiskLevel,
    RouteDecision,
    Slot,
    TimelineBlueprint,
    VideoAssemblyState,
)
from neoclip.hub.capability_registry import CapabilityRegistry, get_capability_registry
from neoclip.hub.intent_recognizer import (
    IntentRecognizer,
    ParameterExtractor,
    get_intent_recognizer,
    get_parameter_extractor,
)
from neoclip.hub.risk_evaluator import RiskEvaluator, get_risk_evaluator


# ============================================================================
# 路由决策引擎
# ============================================================================


class RouteDecisionEngine:
    """根据意图 + 风险评估决定路由目标"""

    def __init__(self, registry: CapabilityRegistry, risk_evaluator: RiskEvaluator):
        self.registry = registry
        self.risk_evaluator = risk_evaluator

    def decide(self, intent: RecognizedIntent, params: ExtractedParams) -> RouteDecision:
        intent_type = intent.intent_type
        command = Command(
            intent_type=intent_type,
            parameters=params.parameters,
        )

        # Tier 3 (STATE_*) → 直接状态操作，不路由到 Agent
        if intent.tier == CommandTier.TIER_3:
            return RouteDecision(
                target_agent=None,
                command=command,
                risk_level=RiskLevel.LOW,
                requires_confirmation=False,
                is_direct_update=True,
            )

        # Tier 1 / Tier 2 → 查注册表找到目标 Agent
        target = self.registry.lookup(intent_type)
        risk = self.risk_evaluator.evaluate(intent_type, params.parameters)
        requires = risk == RiskLevel.HIGH

        if target is None:
            warning(f"No agent registered for intent: {intent_type.value}")

        return RouteDecision(
            target_agent=target,
            command=command,
            risk_level=risk,
            requires_confirmation=requires,
            is_direct_update=False,
        )


# ============================================================================
# 上下文管理器
# ============================================================================


class ContextManager:
    """管理每个 session 的 InteractionContext"""

    def __init__(self):
        self._contexts: Dict[str, InteractionContext] = {}

    def get_context(self, session_id: str) -> InteractionContext:
        if session_id not in self._contexts:
            self._contexts[session_id] = InteractionContext()
        return self._contexts[session_id]

    def resolve_reference(self, text: str, session_id: str) -> Dict[str, Any]:
        """指代消解 — 解析 '它' / '那个' / '第三个片段' 等"""
        ctx = self.get_context(session_id)
        result: Dict[str, Any] = {}

        # 尝试从上下文推断 slot_id
        if ctx.active_slot_id:
            result["slot_id"] = ctx.active_slot_id
        elif ctx.last_previewed_clip:
            result["clip_id"] = ctx.last_previewed_clip

        return result

    def generate_clarification(self, session_id: str, missing: List[str]) -> str:
        """生成澄清问题"""
        ctx = self.get_context(session_id)
        labels = {
            "slot_id": "要操作哪个片段？",
            "timeline_description": "请描述你想要的视频结构",
            "video_path": "请指定视频文件路径",
        }
        questions = [labels.get(m, m) for m in missing]
        return "；".join(questions)

    def update_context(self, session_id: str, **updates: Any) -> None:
        ctx = self.get_context(session_id)
        for key, value in updates.items():
            if hasattr(ctx, key):
                setattr(ctx, key, value)

    def record_turn(self, session_id: str, role: str, text: str) -> None:
        ctx = self.get_context(session_id)
        ctx.record_turn(role, text)


# ============================================================================
# 状态更新器 (Tier 3)
# ============================================================================


class StateUpdater:
    """Tier 3 处理 — 直接修改 VideoAssemblyState，不调用 Agent"""

    def __init__(self):
        self._states: Dict[str, VideoAssemblyState] = {}
        self._undo_stacks: Dict[str, List[Dict[str, Any]]] = {}

    def get_state(self, session_id: str) -> VideoAssemblyState:
        if session_id not in self._states:
            self._states[session_id] = VideoAssemblyState()
        return self._states[session_id]

    def update(self, session_id: str, intent_type: IntentType, params: Dict[str, Any]) -> Dict[str, Any]:
        """执行属性修改并返回结果"""
        state = self.get_state(session_id)

        # 保存 undo 快照
        self._push_undo(session_id, state)

        changes: List[str] = []

        try:
            if intent_type == IntentType.STATE_UNDO:
                return self._undo(session_id)
            if intent_type == IntentType.STATE_REDO:
                return self._redo(session_id)

            if intent_type == IntentType.AUDIO_ADJUST_VOLUME:
                slot_id = params.get("slot_id")
                volume = params.get("volume", 1.0)
                if slot_id is not None and state.timeline:
                    for slot in state.timeline.slots:
                        if slot.slot_id == slot_id:
                            slot.volume_level = volume
                            changes.append(f"slot {slot_id} volume → {volume}")
                else:
                    # 全局音量
                    state.timeline.global_context["volume"] = volume if state.timeline else {}
                    changes.append(f"global volume → {volume}")

            elif intent_type == IntentType.PLAN_REORDER:
                from_idx = params.get("from_index")
                to_idx = params.get("to_index")
                if state.timeline and from_idx is not None and to_idx is not None:
                    slots = state.timeline.slots
                    if 0 <= from_idx < len(slots) and 0 <= to_idx < len(slots):
                        slots.insert(to_idx, slots.pop(from_idx))
                        changes.append(f"slot {from_idx} ↔ {to_idx}")

            elif intent_type == IntentType.PLAN_DELETE:
                slot_id = params.get("slot_id")
                if slot_id and state.timeline:
                    state.timeline.slots = [s for s in state.timeline.slots if s.slot_id != slot_id]
                    changes.append(f"removed slot {slot_id}")

            elif intent_type == IntentType.PLAN_DUPLICATE:
                slot_id = params.get("slot_id")
                if slot_id and state.timeline:
                    for slot in state.timeline.slots:
                        if slot.slot_id == slot_id:
                            import copy
                            import uuid
                            new_slot = copy.deepcopy(slot)
                            new_slot.slot_id = str(uuid.uuid4())
                            state.timeline.slots.append(new_slot)
                            changes.append(f"duplicated slot {slot_id} → {new_slot.slot_id}")
                            break

            else:
                debug(f"StateUpdater: no handler for {intent_type.value}, storing params as-is")
                changes.append(f"stored params for {intent_type.value}")

            return {"success": True, "changes": changes, "message": "; ".join(changes) if changes else "no changes"}

        except Exception as e:
            error(f"StateUpdater failed: {e}")
            return {"success": False, "error": str(e)}

    def _push_undo(self, session_id: str, state: VideoAssemblyState) -> None:
        if session_id not in self._undo_stacks:
            self._undo_stacks[session_id] = []
        import copy
        self._undo_stacks[session_id].append(copy.deepcopy(state.model_dump()))
        if len(self._undo_stacks[session_id]) > 50:
            self._undo_stacks[session_id] = self._undo_stacks[session_id][-50:]

    def _undo(self, session_id: str) -> Dict[str, Any]:
        stack = self._undo_stacks.get(session_id, [])
        if not stack:
            return {"success": False, "message": "Nothing to undo"}
        import copy
        # 当前状态入 redo，出 undo
        snapshot = stack.pop()
        self._states[session_id] = VideoAssemblyState(**snapshot)
        return {"success": True, "message": "Undo successful"}

    def _redo(self, session_id: str) -> Dict[str, Any]:
        return {"success": False, "message": "Redo not implemented yet"}


# ============================================================================
# 状态查询器
# ============================================================================


class StateQueryer:
    """处理 STATE_QUERY_* 查询"""

    def __init__(self, state_updater: StateUpdater, registry: CapabilityRegistry):
        self.state_updater = state_updater
        self.registry = registry

    def query(self, session_id: str, intent_type: IntentType) -> Dict[str, Any]:
        if intent_type == IntentType.STATE_QUERY_PROGRESS:
            state = self.state_updater.get_state(session_id)
            return {
                "session_id": session_id,
                "phase": state.phase.value,
                "timeline_slots": len(state.timeline.slots) if state.timeline else 0,
                "match_results": len(state.match_results),
                "errors": len(state.errors),
                "videos": state.uploaded_videos,
            }
        if intent_type == IntentType.STATE_QUERY_CAPABILITIES:
            records = self.registry.list_all()
            return {
                "capabilities": [
                    {"agent": r.agent_name, "intents": [i.value for i in r.intents], "description": r.description}
                    for r in records
                ],
                "text": self.registry.get_capabilities_text(),
            }
        return {"message": f"Unknown query: {intent_type.value}"}


# ============================================================================
# 中央中枢
# ============================================================================


class CentralHub:
    """星型中枢 — 所有用户输入的单一入口

    处理链:
    1. IntentRecognizer.recognize() → RecognizedIntent
    2. ParameterExtractor.extract() → ExtractedParams
    3. (if clarification_needed) → ContextManager.generate_clarification() → return
    4. RiskEvaluator.evaluate() → RiskLevel
    5. RouteDecisionEngine.decide() → RouteDecision
    6. Tier 3 → StateUpdater / StateQueryer
    7. Tier 1/2 → dispatch Command to Agent
    8. Record context, return result
    """

    def __init__(self):
        self.registry = get_capability_registry()
        self.intent_recognizer = IntentRecognizer()
        self.param_extractor = ParameterExtractor()
        self.risk_evaluator = RiskEvaluator()
        self.route_engine = RouteDecisionEngine(self.registry, self.risk_evaluator)
        self.context_manager = ContextManager()
        self.state_updater = StateUpdater()
        self.state_queryer = StateQueryer(self.state_updater, self.registry)
        self._agents: Dict[str, Any] = {}

    def register_agent(self, agent: Any) -> None:
        """注册 Agent 实例到中枢"""
        self._agents[agent.name] = agent
        info(f"Hub: agent '{agent.name}' registered")

    def process(self, user_input: str, session_id: str, auto_confirm: bool = True) -> Dict[str, Any]:
        """主入口 — 委托 LangGraph 编译图执行处理链

        Args:
            user_input: 用户原始输入
            session_id: 会话 ID
            auto_confirm: API 模式下跳过确认（人工确认由前端处理）

        Returns:
            {
                "success": bool,
                "intent": str,
                "tier": int,
                "result": {...},
                "requires_confirmation": bool,
                "clarification": Optional[str],
                "message": str,
            }
        """
        debug(f"Hub.process: session={session_id[:8]}, input='{user_input[:80]}'")

        # 懒导入避免循环依赖（nodes.py → hub_core → graph）
        from neoclip.graph.hub_graph import get_graph

        graph = get_graph()
        config = {"configurable": {"thread_id": session_id}}
        initial_state = {
            "user_input": user_input,
            "session_id": session_id,
            "auto_confirm": auto_confirm,
        }

        result = graph.invoke(initial_state, config)

        # 映射图状态 → process() 响应格式
        intent_value = result.get("recognized_intent", "")
        agent_result = result.get("agent_result") or {}
        tier = _get_tier(intent_value)

        # 记录上下文
        self.context_manager.record_turn(session_id, "user", user_input)
        if intent_value:
            try:
                intent_type = IntentType(intent_value)
                self.context_manager.update_context(session_id, last_intent=intent_type)
            except ValueError:
                pass

        return {
            "success": agent_result.get("status") != "failed",
            "intent": intent_value,
            "tier": tier,
            "result": agent_result,
            "requires_confirmation": result.get("requires_confirmation", False),
            "clarification": result.get("clarification_message") if result.get("clarification_needed") else None,
            "message": result.get("response_message", agent_result.get("message", "")),
        }

    def _update_state_from_result(
        self, session_id: str, intent_type: IntentType, data: Dict[str, Any]
    ) -> None:
        """将 Agent 执行结果同步到产品状态"""
        state = self.state_updater.get_state(session_id)

        if "timeline" in data and data["timeline"]:
            if isinstance(data["timeline"], dict):
                state.timeline = TimelineBlueprint(**data["timeline"])
            elif isinstance(data["timeline"], TimelineBlueprint):
                state.timeline = data["timeline"]

        if "match_results" in data:
            state.match_results.update(data["match_results"])

        if "videos" in data:
            state.uploaded_videos.extend(data["videos"])

        if "phase" in data:
            from neoclip.state.models import TaskLifecycleStage
            try:
                state.phase = TaskLifecycleStage(data["phase"])
            except ValueError:
                pass


def _get_tier(intent_value: str) -> int:
    """从 intent 字符串推算 tier，解析失败返回 0"""
    if not intent_value:
        return 0
    try:
        return IntentType(intent_value).tier.value
    except ValueError:
        return 0


# ============================================================================
# 单例
# ============================================================================

_hub: Optional[CentralHub] = None


def get_hub() -> CentralHub:
    global _hub
    if _hub is None:
        _hub = CentralHub()
    return _hub
