"""CentralHub 澄清式对话单元测试 —— 过短/模糊输入触发反问。"""

from neoclip.core.hub.central_hub import CentralHub


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
