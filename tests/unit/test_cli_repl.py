"""REPL 循环单元测试 —— 注入 input/print 验证交互分支。"""

from neoclip.cli.repl import run_repl
from neoclip.core.hub.central_hub import CentralHub


def _run(hub, script):
    inputs = iter(script)
    out = []
    run_repl(hub, "s1", input_fn=lambda _prompt: next(inputs), print_fn=out.append)
    return out


def test_repl_exits_on_exit_command():
    out = _run(CentralHub(), script=["exit"])
    assert any("session: s1" in line for line in out)


def test_repl_clarification_prompts_user():
    out = _run(CentralHub(), script=["剪", "exit"])
    assert any("请详细描述" in line for line in out)


def test_repl_confirmation_confirm_executes(hub_with_render):
    hub, agent = hub_with_render
    out = _run(hub, script=["渲染", "y", "exit"])

    assert agent.executed is True
    assert any("渲染完成" in line for line in out)


def test_repl_confirmation_cancel_skips(hub_with_render):
    hub, agent = hub_with_render
    out = _run(hub, script=["渲染", "n", "exit"])

    assert agent.executed is False
    assert any("已取消" in line for line in out)
