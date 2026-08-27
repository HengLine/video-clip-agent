"""RiskAssessor — evaluates operation risk and determines confirmation policy."""

from typing import Any, Dict, Optional

from penclip.domain.value_objects.intent import IntentType
from penclip.domain.value_objects.risk import RiskLevel
from penclip.logger import debug


_INTENT_RISK_MAP: Dict[IntentType, RiskLevel] = {
    IntentType.PLAN_CREATE: RiskLevel.HIGH,
    IntentType.PLAN_DELETE: RiskLevel.HIGH,
    IntentType.PLAN_REORDER: RiskLevel.MEDIUM,
    IntentType.STATE_RENDER: RiskLevel.HIGH,
    IntentType.STATE_UNDO: RiskLevel.LOW,
    IntentType.STATE_REDO: RiskLevel.LOW,
    IntentType.ASSET_ADD: RiskLevel.LOW,
    IntentType.CLIP_REPLACE: RiskLevel.MEDIUM,
    IntentType.CLIP_TRIM: RiskLevel.MEDIUM,
    IntentType.CLIP_PREVIEW: RiskLevel.LOW,
    IntentType.EFFECT_ADD_TRANSITION: RiskLevel.LOW,
    IntentType.EFFECT_ADD_FILTER: RiskLevel.MEDIUM,
    IntentType.AUDIO_ADJUST_VOLUME: RiskLevel.LOW,
    IntentType.AUDIO_ADD_BGM: RiskLevel.LOW,
    IntentType.STATE_QUERY_PROGRESS: RiskLevel.LOW,
    IntentType.STATE_QUERY_CAPABILITIES: RiskLevel.LOW,
}


class RiskAssessor:
    def __init__(self):
        self._intent_risk_map = dict(_INTENT_RISK_MAP)
        debug("RiskAssessor initialized")

    def assess(self, intent: IntentType, params: Optional[Dict] = None, context: Optional[Dict] = None) -> RiskLevel:
        return self._intent_risk_map.get(intent, RiskLevel.MEDIUM)

    def needs_confirmation(self, risk: RiskLevel) -> bool:
        return risk == RiskLevel.HIGH

    def generate_confirmation_message(self, intent: IntentType, params: Optional[Dict] = None) -> str:
        messages = {
            IntentType.PLAN_CREATE: "确认根据此需求创建新的时间线规划？",
            IntentType.PLAN_DELETE: "确认删除该槽位？此操作不可撤销。",
            IntentType.STATE_RENDER: "确认开始最终渲染？渲染开始后中途取消可能导致不完整输出。",
        }
        return messages.get(intent, f"确认执行 {intent.value}？")
