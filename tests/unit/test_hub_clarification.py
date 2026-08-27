"""CentralHub 澄清式对话单元测试 —— 过短/模糊输入触发反问。"""

from penclip.core.hub.central_hub import CentralHub
from penclip.domain.value_objects.intent import IntentType


def test_short_input_triggers_clarification():
    hub = CentralHub()
    resp = hub.process("剪", session_id="s1")

    assert resp.needs_clarification is True
    assert resp.success is False
    assert resp.clarification


def test_normal_input_does_not_clarify(hub_with_render):
    hub, _ = hub_with_render
    resp = hub.process("渲染", session_id="s1")

    assert resp.needs_clarification is False


def test_url_input_not_clarified_as_asset_add():
    hub = CentralHub()
    resp = hub.process("https://example.com/a.mp4", session_id="s1")

    assert resp.needs_clarification is False
    assert resp.intent == IntentType.ASSET_ADD


def test_meaningful_input_not_clarified_routes_to_plan():
    hub = CentralHub()
    resp = hub.process("把自我介绍放开头，活动放中间，风景放结尾", session_id="s1")

    assert resp.needs_clarification is False
    assert resp.intent == IntentType.PLAN_CREATE
