"""
@FileName: risk_evaluator.py
@Description: 风险评估器 — 在命令路由前评估操作风险等级
    LOW → 直接执行（可撤销）
    MEDIUM → 执行并高亮变化（用户可回滚）
    HIGH → 必须先确认再执行
@Author: HiPeng
@Time: 2026/08
"""
from typing import Dict, List, Optional

from neoclip.logger import debug
from neoclip.state.models import IntentType, RiskLevel


# ============================================================================
# 默认风险分级映射（架构文档定义）
# ============================================================================

DEFAULT_RISK_MAP: Dict[IntentType, RiskLevel] = {
    # ── 低风险：可逆操作，直接执行 ──
    IntentType.CLIP_PREVIEW: RiskLevel.LOW,
    IntentType.CLIP_SWAP: RiskLevel.LOW,
    IntentType.EFFECT_CHANGE_TRANSITION: RiskLevel.LOW,
    IntentType.AUDIO_ADJUST_VOLUME: RiskLevel.LOW,
    IntentType.AUDIO_ADJUST_BGM_VOLUME: RiskLevel.LOW,
    IntentType.STATE_QUERY_PROGRESS: RiskLevel.LOW,
    IntentType.STATE_QUERY_CAPABILITIES: RiskLevel.LOW,
    IntentType.ANALYZE_CANCEL: RiskLevel.LOW,
    IntentType.PLAN_DUPLICATE: RiskLevel.LOW,

    # ── 中风险：局部影响，执行并高亮 ──
    IntentType.CLIP_TRIM: RiskLevel.MEDIUM,
    IntentType.CLIP_REPLACE: RiskLevel.MEDIUM,
    IntentType.CLIP_REMOVE: RiskLevel.MEDIUM,
    IntentType.EFFECT_ADD_FILTER: RiskLevel.MEDIUM,
    IntentType.EFFECT_REMOVE_FILTER: RiskLevel.MEDIUM,
    IntentType.EFFECT_ADD_TRANSITION: RiskLevel.MEDIUM,
    IntentType.AUDIO_ADD_BGM: RiskLevel.MEDIUM,
    IntentType.PLAN_REORDER: RiskLevel.MEDIUM,
    IntentType.PLAN_APPEND: RiskLevel.MEDIUM,
    IntentType.PLAN_INSERT: RiskLevel.MEDIUM,
    IntentType.STATE_UNDO: RiskLevel.MEDIUM,
    IntentType.STATE_REDO: RiskLevel.MEDIUM,
    IntentType.ANALYZE_INCREMENTAL: RiskLevel.MEDIUM,
    IntentType.ANALYZE_PRIORITY: RiskLevel.MEDIUM,

    # ── 高风险：全局影响，必须确认 ──
    IntentType.PLAN_CREATE: RiskLevel.HIGH,
    IntentType.PLAN_DELETE: RiskLevel.HIGH,
    IntentType.ANALYZE_FULL: RiskLevel.HIGH,
}


class RiskEvaluator:
    """风险评估器 — 决定操作是否需要用户确认"""

    def __init__(self, risk_map: Optional[Dict[IntentType, RiskLevel]] = None):
        self._risk_map = risk_map or DEFAULT_RISK_MAP.copy()

    def evaluate(self, intent_type: IntentType, _params: Optional[Dict] = None) -> RiskLevel:
        """评估单个意图的风险等级"""
        risk = self._risk_map.get(intent_type)
        if risk is not None:
            return risk
        # 默认：未知意图保守处理
        if intent_type.tier.value == 1:  # 规划类默认高风险
            return RiskLevel.HIGH
        if intent_type.value.startswith("state_"):
            return RiskLevel.LOW
        return RiskLevel.MEDIUM

    def requires_confirmation(self, intent_type: IntentType, _params: Optional[Dict] = None) -> bool:
        """该意图是否需要用户确认"""
        return self.evaluate(intent_type, _params) == RiskLevel.HIGH

    def get_level(self, intent_type: IntentType) -> RiskLevel:
        return self.evaluate(intent_type)


# ============================================================================
# 单例
# ============================================================================

_risk_evaluator: Optional[RiskEvaluator] = None


def get_risk_evaluator() -> RiskEvaluator:
    global _risk_evaluator
    if _risk_evaluator is None:
        _risk_evaluator = RiskEvaluator()
    return _risk_evaluator
