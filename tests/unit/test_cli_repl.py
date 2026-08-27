"""REPL 循环单元测试 —— 注入 input/print 验证交互分支。"""

from uuid import uuid4

from penclip.agents.asset_agent import AssetAgent
from penclip.cli.repl import run_repl
from penclip.core.hub.central_hub import CentralHub


URL = "https://example.com/video.mp4"


def _run(hub, script, session_id=None):
    session_id = session_id or f"sess_{uuid4().hex[:8]}"
    inputs = iter(script)
    out = []
    run_repl(hub, session_id, input_fn=lambda _prompt: next(inputs), print_fn=out.append)
    return out


def _hub_with_assets(hub):
    hub.register_agent(AssetAgent())
    return hub


def test_repl_exits_on_exit_command():
    out = _run(CentralHub(), ["exit"])
    assert any("session: " in line for line in out)


def test_repl_does_not_block_non_url_command():
    out = _run(CentralHub(), ["做视频", "exit"])
    # URL 不再强制前置：非 URL 指令直接进入 hub 处理（此处未注册规划能力，返回 no capability）
    assert any("No capability" in line for line in out)


def test_repl_clarification_prompts_user():
    hub = _hub_with_assets(CentralHub())
    out = _run(hub, [URL, "剪", "exit"])
    assert any("请详细描述" in line for line in out)


def test_repl_confirmation_confirm_executes(hub_with_render):
    hub, agent = hub_with_render
    _hub_with_assets(hub)
    out = _run(hub, [URL, "渲染", "y", "exit"])

    assert agent.executed is True
    assert any("渲染完成" in line for line in out)


def test_repl_confirmation_cancel_skips(hub_with_render):
    hub, agent = hub_with_render
    _hub_with_assets(hub)
    out = _run(hub, [URL, "渲染", "n", "exit"])

    assert agent.executed is False
    assert any("已取消" in line for line in out)
