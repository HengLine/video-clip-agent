"""Interactive REPL loop — the primary human-in-the-loop console."""

from typing import Any, Callable

from neoclip.core.hub.central_hub import CentralHub
from neoclip.cli.renderer import render_response

BANNER = (
    "NeoClip 视频混剪智能体 — 交互控制台\n"
    "输入自然语言指令开始（help 查看命令，exit 退出）"
)

HELP_TEXT = (
    "可用命令：\n"
    "  help           显示本帮助\n"
    "  capabilities   列出已注册能力\n"
    "  status         查看系统状态\n"
    "  exit / quit    退出\n"
    "\n"
    "自然语言示例：\n"
    "  \"做个旅行Vlog，风景放开头\"  （全局规划）\n"
    "  \"把这段剪到10秒\"            （智能体操作）\n"
    "  \"渲染 / 合成\"               （高风险，需确认）"
)

_EXIT_KEYWORDS = ("exit", "quit", "退出")
_CONFIRM_KEYWORDS = ("y", "yes", "确认", "是")


def run_repl(
    hub: CentralHub,
    session_id: str,
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[..., Any] = print,
) -> None:
    print_fn(f"NeoClip 交互控制台 — session: {session_id}")
    print_fn("输入自然语言指令开始（help 查看命令，exit 退出）")

    while True:
        try:
            raw = input_fn("neoclip> ")
        except (EOFError, KeyboardInterrupt):
            print_fn()
            break

        line = raw.strip()
        if not line:
            continue

        lowered = line.lower()
        if lowered in _EXIT_KEYWORDS:
            break
        if lowered in ("help", "帮助"):
            print_fn(HELP_TEXT)
            continue
        if lowered in ("capabilities", "能力", "能做什么", "功能"):
            _print_capabilities(hub, print_fn)
            continue
        if lowered in ("status", "状态"):
            print_fn("系统运行中")
            continue

        response = hub.process(line, session_id)

        if response.needs_clarification:
            print_fn(response.clarification)
            continue

        if response.needs_confirmation:
            print_fn(response.confirmation_message)
            answer = input_fn("确认执行? [y/N] ").strip().lower()
            if answer in _CONFIRM_KEYWORDS:
                response = hub.confirm(session_id)
            else:
                response = hub.cancel(session_id)

        render_response(response, print_fn=print_fn)


def _print_capabilities(hub: CentralHub, print_fn: Callable[..., Any]) -> None:
    caps = hub.get_capabilities()
    if not caps:
        print_fn("暂无已注册能力")
        return
    print_fn(f"{len(caps)} 个能力已注册：")
    for cap in caps:
        print_fn(f"  - {cap.name}")
