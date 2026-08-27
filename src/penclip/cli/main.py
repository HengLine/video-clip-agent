"""CLI entry point — interactive REPL console."""

import argparse
from uuid import uuid4

from penclip.core.hub.central_hub import get_hub
from penclip.cli.repl import run_repl
from penclip.logger import info


def register_default_agents(hub) -> None:
    """注册核心智能体，使交互控制台具备完整能力覆盖。"""
    from penclip.agents.planner import get_planner_agent
    from penclip.agents.analyzer import AnalyzerAgent
    from penclip.agents.matcher import MatcherAgent
    from penclip.agents.composer import ComposerAgent
    from penclip.agents.asset_agent import AssetAgent

    for agent in (
        get_planner_agent(), AnalyzerAgent(), MatcherAgent(), ComposerAgent(), AssetAgent(),
    ):
        hub.register_agent(agent)


def main():
    parser = argparse.ArgumentParser(description="PenClip — 视频混剪智能体交互控制台")
    parser.add_argument("--session", "-s", type=str, help="会话 ID（不指定则自动生成）")
    args = parser.parse_args()

    hub = get_hub()
    register_default_agents(hub)

    session_id = args.session or f"sess_{uuid4().hex[:8]}"
    info(f"启动交互控制台 session={session_id}")
    run_repl(hub, session_id)


if __name__ == "__main__":
    main()
