"""Unit 测试夹具 —— 共享的 fake agent 与 hub。"""

import sys
from pathlib import Path

import pytest

SRC = Path(__file__).resolve().parents[2] / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from penclip.agents.base import BaseAgent
from penclip.core.hub.central_hub import CentralHub
from penclip.domain.value_objects.capability import CapabilityDeclaration
from penclip.domain.value_objects.execution_result import ExecutionResult
from penclip.domain.value_objects.intent import IntentType
from penclip.domain.value_objects.risk import RiskLevel


class RecordingRenderAgent(BaseAgent):
    """声明 STATE_RENDER（高风险）能力的记录型 agent。"""

    agent_id = "test_render_agent"
    agent_name = "TestRenderAgent"

    def __init__(self):
        super().__init__()
        self.executed = False

    def declare_capabilities(self):
        return CapabilityDeclaration(
            name="render",
            intents=[IntentType.STATE_RENDER],
            risk_level=RiskLevel.HIGH,
        )

    def execute(self, params, context):
        self.executed = True
        return ExecutionResult(success=True, message="渲染完成", data={"rendered": True})


@pytest.fixture
def render_agent():
    return RecordingRenderAgent()


@pytest.fixture
def hub_with_render(render_agent):
    hub = CentralHub()
    hub.register_agent(render_agent)
    return hub, render_agent
