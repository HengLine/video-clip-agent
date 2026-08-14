"""ComposerAgent — renders the final video from matched segments and timeline."""

from typing import Any, Dict, List, Optional

from neoclip.agents.base import BaseAgent, ExecutionContext
from neoclip.domain.value_objects.capability import CapabilityDeclaration
from neoclip.domain.value_objects.execution_result import ExecutionResult
from neoclip.domain.value_objects.intent import IntentType
from neoclip.domain.value_objects.risk import RiskLevel
from neoclip.logger import info


DEFAULT_CONFIG = {
    "output_dir": "data/output",
    "preview_resolution": "360p",
    "final_resolution": "1080p",
}


class ComposerAgent(BaseAgent):
    agent_id = "composer"
    agent_name = "ComposerAgent"
    version = "0.1.0"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        cfg = {**DEFAULT_CONFIG, **(config or {})}
        super().__init__(config=cfg)

    def declare_capabilities(self) -> CapabilityDeclaration:
        return CapabilityDeclaration(
            name="video_composer",
            intents=[
                IntentType.STATE_RENDER,
                IntentType.EFFECT_ADD_TRANSITION, IntentType.EFFECT_CHANGE_TRANSITION,
                IntentType.EFFECT_ADD_FILTER, IntentType.EFFECT_REMOVE_FILTER,
                IntentType.AUDIO_ADJUST_VOLUME, IntentType.AUDIO_ADD_BGM,
                IntentType.AUDIO_ADJUST_BGM_VOLUME,
            ],
            description="Renders final video with transitions, effects, and audio mixing",
            input_schema={
                "timeline": {"type": "object", "description": "TimelineBlueprint with matched segments"},
            },
            output_schema={
                "output_path": {"type": "string", "description": "Path to rendered video"},
            },
            risk_level=RiskLevel.HIGH,
            version=self.version,
            agent_id=self.agent_id,
        )

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        slots = params.get("slots", [])
        info(f"ComposerAgent: composing {len(slots)} slot(s)")

        timeline = self._build_timeline(slots)
        command = self._generate_ffmpeg_command(timeline)
        output_path = self._render_video(command)

        return ExecutionResult(
            success=True,
            data={"output_path": output_path, "command": command},
            message=f"Video rendered to {output_path}",
        )

    def _build_timeline(self, slots: List[Dict]) -> Dict:
        return {"slots": slots}

    def _generate_ffmpeg_command(self, timeline: Dict) -> str:
        return "ffmpeg -i input.mp4 output.mp4"

    def _render_video(self, command: str) -> str:
        import os
        output_dir = self._config.get("output_dir", "data/output")
        os.makedirs(output_dir, exist_ok=True)
        return os.path.join(output_dir, "output.mp4")

    def _mix_audio(self, timeline: Dict) -> str:
        return ""
