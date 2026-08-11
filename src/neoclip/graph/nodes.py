"""
@FileName: nodes.py
@Description: LangGraph 节点函数 — 中枢处理链的每一步
    recognize → extract → risk_gate → dispatch → (pipeline | state_update | state_query)
    每个节点接收 HubState，返回 HubState 的部分更新
@Author: HiPeng
@Time: 2026/08
"""
import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from langgraph.types import interrupt

from neoclip.hub.capability_registry import get_capability_registry
from neoclip.hub.intent_recognizer import get_intent_recognizer, get_parameter_extractor
from neoclip.hub.risk_evaluator import get_risk_evaluator
from neoclip.logger import debug, info, warning
from neoclip.state.models import (
    AgentResult,
    Command,
    IntentType,
    InteractionContext,
    RecognizedIntent,
    RiskLevel,
    Slot,
    TimelineBlueprint,
)


# ============================================================================
# 1. recognize_intent — 意图识别
# ============================================================================


def recognize_intent(state: dict) -> dict:
    """V0.1 关键字识别 → RecognizedIntent"""
    user_input = state.get("user_input", "")
    recognizer = get_intent_recognizer()
    recognized = recognizer.recognize(user_input)

    update: Dict[str, Any] = {
        "recognized_intent": recognized.intent_type.value,
        "intent_confidence": recognized.confidence,
        "messages": [{"role": "user", "content": user_input, "timestamp": datetime.now(timezone.utc).isoformat()}],
    }
    debug(f"[recognize] '{user_input[:50]}' → {recognized.intent_type.value} ({recognized.confidence:.2f})")
    return update


# ============================================================================
# 2. extract_params — 参数提取
# ============================================================================


def extract_params(state: dict) -> dict:
    """从用户输入中提取参数，从 InteractionContext 补全"""
    user_input = state.get("user_input", "")
    intent_value = state.get("recognized_intent", "")

    try:
        intent_type = IntentType(intent_value)
    except ValueError:
        return {"clarification_needed": True, "clarification_message": f"Unknown intent: {intent_value}"}

    recognized = RecognizedIntent.from_match(intent_type, user_input, state.get("intent_confidence", 1.0))

    # 构建 InteractionContext
    ctx = InteractionContext(
        active_slot_id=state.get("active_slot_id"),
        last_previewed_clip=state.get("last_previewed_clip"),
        pending_clarification=state.get("pending_clarification"),
        conversation_history=state.get("conversation_history", []),
        last_intent=IntentType(state.get("last_intent")) if state.get("last_intent") else None,
    )

    extractor = get_parameter_extractor()
    params = extractor.extract(user_input, recognized, ctx)

    # PLAN_CREATE: 将用户输入全文作为 description
    if intent_type == IntentType.PLAN_CREATE:
        params.parameters["description"] = user_input
        params.clarification_needed = False
        params.clarification_message = None
        if "timeline_description" in params.missing_params:
            params.missing_params.remove("timeline_description")

    update: Dict[str, Any] = {
        "extracted_params": params.parameters,
        "missing_params": params.missing_params,
        "clarification_needed": params.clarification_needed,
        "clarification_message": params.clarification_message,
    }

    # 回写上下文
    if params.parameters.get("slot_id") is not None:
        update["active_slot_id"] = params.parameters["slot_id"]

    debug(f"[extract] params={params.parameters}, missing={params.missing_params}")
    return update


# ============================================================================
# 3. risk_gate — 风险评估门
# ============================================================================


def risk_gate(state: dict) -> dict:
    """评估操作风险，HIGH 风险触发 interrupt"""
    intent_value = state.get("recognized_intent", "")
    try:
        intent_type = IntentType(intent_value)
    except ValueError:
        return {"risk_level": RiskLevel.LOW.value, "requires_confirmation": False}

    evaluator = get_risk_evaluator()
    risk = evaluator.evaluate(intent_type, state.get("extracted_params"))

    update: Dict[str, Any] = {
        "risk_level": risk.value,
        "requires_confirmation": risk == RiskLevel.HIGH,
    }

    # HIGH 风险 & 未确认 & 非自动模式 → interrupt 等待确认
    if risk == RiskLevel.HIGH and not state.get("confirmed", False) and not state.get("auto_confirm", False):
        info(f"[risk_gate] HIGH risk for {intent_value} — interrupting for confirmation")
        interrupt({
            "type": "confirmation_required",
            "intent": intent_value,
            "risk_level": risk.value,
            "message": f"操作 '{intent_value}' 风险等级为 HIGH，请确认是否继续？",
        })

    # auto_confirm 模式：标记为已确认
    if state.get("auto_confirm", False) and risk == RiskLevel.HIGH:
        update["confirmed"] = True

    debug(f"[risk_gate] {intent_value} → {risk.value}")
    return update


# ============================================================================
# 4. dispatch_agent — 运行时路由分发
# ============================================================================


def dispatch_agent(state: dict) -> dict:
    """查 CapabilityRegistry → 调用 Agent.execute() → 返回 AgentResult

    图拓扑静态，路由在运行时动态完成。Agent 热插拔无需重新编译图。
    """
    intent_value = state.get("recognized_intent", "")
    try:
        intent_type = IntentType(intent_value)
    except ValueError:
        return _no_handler_result(intent_value)

    registry = get_capability_registry()
    target = registry.lookup(intent_type)

    if target is None:
        # Tier 3 → 直接状态操作
        if intent_type.tier.value == 3:
            return {"target_agent": None}
        return _no_handler_result(intent_value)

    from neoclip.hub.hub_core import get_hub
    hub = get_hub()

    if target not in hub._agents:
        warning(f"[dispatch] Agent '{target}' not found in hub")
        return _no_handler_result(intent_value)

    agent = hub._agents[target]
    command = Command(
        intent_type=intent_type,
        parameters=state.get("extracted_params", {}),
        context={"session_id": state.get("session_id", ""), "timeline": state.get("timeline")},
    )

    try:
        result: AgentResult = agent.execute(command)
        info(f"[dispatch] {target}.execute({intent_value}) → {result.status}")
        return {
            "target_agent": target,
            "agent_result": result.model_dump(),
            "response_message": result.message,
            "messages": [{"role": "assistant", "content": result.message, "timestamp": datetime.now(timezone.utc).isoformat()}],
        }
    except Exception as e:
        warning(f"[dispatch] {target} execution error: {e}")
        return {
            "target_agent": target,
            "agent_result": AgentResult(status="failed", message=str(e)).model_dump(),
            "response_message": str(e),
        }


def _no_handler_result(intent_value: str) -> dict:
    msg = f"No handler registered for '{intent_value}'"
    return {
        "target_agent": None,
        "agent_result": AgentResult(status="failed", message=msg).model_dump(),
        "response_message": msg,
    }


# ============================================================================
# 5. state_update — Tier 3 直接状态操作
# ============================================================================


def state_update(state: dict) -> dict:
    """Tier 3 处理：直接修改属性，不经过 Agent"""
    intent_value = state.get("recognized_intent", "")
    params = state.get("extracted_params", {})
    session_id = state.get("session_id", "")

    try:
        intent_type = IntentType(intent_value)
    except ValueError:
        return {"response_message": f"Unknown intent: {intent_value}"}

    from neoclip.hub.hub_core import get_hub
    hub = get_hub()

    if intent_value.startswith("state_query"):
        result = hub.state_queryer.query(session_id, intent_type)
        return {
            "response_message": str(result),
            "agent_result": {"status": "success", "data": result},
        }
    else:
        result = hub.state_updater.update(session_id, intent_type, params)
        return {
            "response_message": result.get("message", ""),
            "agent_result": {"status": "success" if result.get("success") else "failed", "data": result},
        }


# ============================================================================
# 6. decide_route — 条件路由函数
# ============================================================================


def decide_route(state: dict) -> str:
    """条件边：根据意图和澄清状态决定下一步"""
    # 自动确认模式：跳过澄清
    if state.get("clarification_needed") and not state.get("auto_confirm"):
        return "end"

    intent_value = state.get("recognized_intent", "")
    risk = state.get("risk_level", "")

    # HIGH risk + 未确认 + 非自动模式 → 等待
    if risk == RiskLevel.HIGH.value and not state.get("confirmed") and not state.get("auto_confirm"):
        return "end"

    try:
        intent_type = IntentType(intent_value)
    except ValueError:
        return "state_updater"

    # Tier 3 → 直接状态更新
    if intent_type.tier.value == 3:
        return "state_updater"

    # Tier 1/2 → 查注册表
    registry = get_capability_registry()
    target = registry.lookup(intent_type)
    if target:
        return "dispatch_agent"

    return "state_updater"
