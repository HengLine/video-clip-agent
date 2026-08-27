"""AssetAgent — records video asset URLs into session state (record-only, no download)."""

from typing import Any, Dict, Optional
from urllib.parse import urlparse

from penclip.agents.base import BaseAgent, ExecutionContext
from penclip.core.state.state_manager import get_state_manager
from penclip.domain.entities.video_asset import AssetStatus, VideoAsset
from penclip.domain.value_objects.capability import CapabilityDeclaration
from penclip.domain.value_objects.execution_result import ExecutionResult
from penclip.domain.value_objects.intent import IntentType
from penclip.domain.value_objects.risk import RiskLevel
from penclip.logger import info, warning


DEFAULT_CONFIG = {
    "record_only": True,
}


class AssetAgent(BaseAgent):
    agent_id = "asset_manager"
    agent_name = "AssetAgent"
    version = "0.1.0"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        cfg = {**DEFAULT_CONFIG, **(config or {})}
        super().__init__(config=cfg)

    def declare_capabilities(self) -> CapabilityDeclaration:
        return CapabilityDeclaration(
            name="asset_manager",
            intents=[IntentType.ASSET_ADD],
            description="Records video asset URLs into session state (record-only, no download)",
            input_schema={
                "url": {"type": "string", "description": "Asset URL or local video file path"},
            },
            output_schema={
                "asset": {"type": "object", "description": "The registered VideoAsset"},
            },
            risk_level=RiskLevel.LOW,
            version=self.version,
            agent_id=self.agent_id,
        )

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        url = (params.get("url") or "").strip()
        if not url:
            return ExecutionResult(
                success=False,
                message="缺少资源 URL",
                status="failed",
            )

        session_id = self._extract_session_id(context)
        filename = self._filename_from_url(url)
        asset = VideoAsset(
            filename=filename,
            file_path=url,
            status=AssetStatus.UPLOADED,
        )

        state_manager = get_state_manager()
        state = state_manager.get_session(session_id) if session_id else None
        if state is None:
            state = state_manager.create_session(session_id)
        state.add_asset(asset)
        state_manager.update_session(state)

        info(f"AssetAgent: recorded asset '{filename}' for session {state.session_id[:8]}")
        return ExecutionResult(
            success=True,
            data={"asset": asset.model_dump()},
            message=f"已添加素材: {filename}",
        )

    @staticmethod
    def _extract_session_id(context: Any) -> Optional[str]:
        if isinstance(context, dict):
            return context.get("session_id")
        if isinstance(context, ExecutionContext):
            return context.session_id
        return None

    @staticmethod
    def _filename_from_url(url: str) -> str:
        path = urlparse(url).path
        name = path.rsplit("/", 1)[-1] if path else ""
        return name or "video"
