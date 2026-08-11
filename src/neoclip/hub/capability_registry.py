"""
@FileName: capability_registry.py
@Description: 能力注册表 — 星型中枢的核心注册机制
    Agent 初始化时提交能力声明，Registry 维护 intent→agent 映射表
    新增能力只需注册新 Agent + 新 intent 类型，中枢核心无需修改
@Author: HiPeng
@Time: 2026/08
"""
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from neoclip.logger import debug, info, warning
from neoclip.state.models import CommandTier, IntentType, RiskLevel


@dataclass
class CapabilityRecord:
    """Agent 向 Registry 提交的能力声明"""

    agent_name: str
    intents: List[IntentType]
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.MEDIUM
    version: str = "0.1.0"
    description: str = ""
    tier: CommandTier = CommandTier.TIER_2


class CapabilityRegistry:
    """能力注册表 — 维护 intent_type → agent_name 的路由映射

    V0.1: 一个 intent 映射到一个 agent（后注册覆盖前者）
    Future: 支持多 agent 竞争 + 优先级路由
    """

    def __init__(self):
        self._intent_map: Dict[IntentType, str] = {}
        self._records: Dict[str, CapabilityRecord] = {}
        self._capabilities_help: Dict[IntentType, str] = {}

    def register(self, record: CapabilityRecord) -> None:
        """注册一个 Agent 的所有能力"""
        if not record.intents:
            warning(f"Agent '{record.agent_name}' registered with empty intents list")
            return

        self._records[record.agent_name] = record

        for intent in record.intents:
            if intent in self._intent_map:
                old_agent = self._intent_map[intent]
                debug(f"Intent {intent.value} reassigned: '{old_agent}' → '{record.agent_name}'")
            self._intent_map[intent] = record.agent_name
            self._capabilities_help[intent] = record.description or f"Handled by {record.agent_name}"

        info(f"Agent '{record.agent_name}' registered {len(record.intents)} capability(s) [v{record.version}]")

    def lookup(self, intent_type: IntentType) -> Optional[str]:
        """查询处理某意图的 agent 名称"""
        return self._intent_map.get(intent_type)

    def get_record(self, agent_name: str) -> Optional[CapabilityRecord]:
        """获取某个 Agent 的完整注册记录"""
        return self._records.get(agent_name)

    def list_all(self) -> List[CapabilityRecord]:
        """列出所有已注册的能力"""
        return list(self._records.values())

    def unregister(self, agent_name: str) -> bool:
        """取消注册某个 Agent 的所有能力"""
        record = self._records.pop(agent_name, None)
        if record is None:
            return False
        for intent in record.intents:
            if self._intent_map.get(intent) == agent_name:
                del self._intent_map[intent]
                self._capabilities_help.pop(intent, None)
        info(f"Agent '{agent_name}' unregistered")
        return True

    def get_capabilities_text(self) -> str:
        """生成可供用户阅读的能力列表"""
        if not self._records:
            return "No capabilities registered yet."

        lines = ["Available capabilities:"]
        for record in self._records.values():
            intent_names = ", ".join(i.value for i in record.intents)
            lines.append(f"  [{record.agent_name}] {intent_names} — {record.description}")
        return "\n".join(lines)


# ============================================================================
# 单例
# ============================================================================

_registry: Optional[CapabilityRegistry] = None


def get_capability_registry() -> CapabilityRegistry:
    """获取 CapabilityRegistry 全局单例"""
    global _registry
    if _registry is None:
        _registry = CapabilityRegistry()
    return _registry
