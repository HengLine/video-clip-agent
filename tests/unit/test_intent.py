"""意图枚举单元测试（领域层）。"""

from neoclip.domain.value_objects.intent import IntentType


def test_intent_categories():
    """六类意图的关键值。"""
    assert IntentType.PLAN_CREATE.value == "plan_create"
    assert IntentType.ANALYZE_FULL.value == "analyze_full"
    assert IntentType.CLIP_TRIM.value == "clip_trim"
    assert IntentType.EFFECT_ADD_TRANSITION.value == "effect_add_transition"
    assert IntentType.STATE_RENDER.value == "state_render"
    assert IntentType.EXECUTE.value == "execute"


def test_intent_unknown_fallback():
    """未知值回退到 UNKNOWN。"""
    assert IntentType("not_a_real_intent") == IntentType.UNKNOWN
