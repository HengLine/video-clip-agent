"""CLI entry point — interactive REPL console."""

import argparse
from uuid import uuid4

from neoclip.core.hub.central_hub import get_hub
from neoclip.cli.repl import run_repl
from neoclip.logger import info


def register_default_agents(hub) -> None:
    """注册核心智能体，使交互控制台具备完整能力覆盖。"""
    from neoclip.agents.planner import get_planner_agent
    from neoclip.agents.analyzer import AnalyzerAgent
    from neoclip.agents.matcher import MatcherAgent
    from neoclip.agents.composer import ComposerAgent

    for agent in (get_planner_agent(), AnalyzerAgent(), MatcherAgent(), ComposerAgent()):
        hub.register_agent(agent)


def main():
    parser = argparse.ArgumentParser(description="NeoClip — 视频混剪智能体交互控制台")
    parser.add_argument("--session", "-s", type=str, help="会话 ID（不指定则自动生成）")
    args = parser.parse_args()

    hub = get_hub()
    register_default_agents(hub)

    session_id = args.session or f"sess_{uuid4().hex[:8]}"
    info(f"启动交互控制台 session={session_id}")
    run_repl(hub, session_id)


if __name__ == "__main__":
    main()
