"""CentralHub 确认门单元测试 —— 高风险操作须确认后才执行。"""

from penclip.core.hub.central_hub import CentralHub


def test_high_risk_returns_confirmation_without_executing(hub_with_render):
    hub, agent = hub_with_render
    resp = hub.process("渲染", session_id="s1")

    assert resp.needs_confirmation is True
    assert resp.confirmation_message
    assert agent.executed is False


def test_confirm_executes_pending_operation(hub_with_render):
    hub, agent = hub_with_render
    hub.process("渲染", session_id="s1")

    resp = hub.confirm("s1")

    assert resp.success is True
    assert agent.executed is True


def test_cancel_discards_pending_operation(hub_with_render):
    hub, agent = hub_with_render
    hub.process("渲染", session_id="s1")

    resp = hub.cancel("s1")

    assert resp.success is True
    assert agent.executed is False
    assert hub.confirm("s1").success is False


def test_confirm_without_pending_fails():
    hub = CentralHub()

    assert hub.confirm("no_session").success is False
    assert hub.cancel("no_session").success is False
