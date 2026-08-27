"""AssetAgent 单元测试 —— 记录资源 URL 到会话状态（仅记录，不下载）。"""

from uuid import uuid4

from penclip.agents.asset_agent import AssetAgent
from penclip.core.state.state_manager import get_state_manager


def test_asset_agent_records_asset():
    agent = AssetAgent()
    session_id = f"s_{uuid4().hex[:8]}"
    url = "https://example.com/video.mp4"

    result = agent.execute({"url": url}, {"session_id": session_id})

    assert result.success is True
    state = get_state_manager().get_session(session_id)
    assert state is not None
    assert len(state.assets) == 1
    assert state.assets[0].file_path == url
    assert state.assets[0].filename == "video.mp4"


def test_asset_agent_missing_url_fails():
    agent = AssetAgent()
    result = agent.execute({}, {"session_id": f"s_{uuid4().hex[:8]}"})

    assert result.success is False
