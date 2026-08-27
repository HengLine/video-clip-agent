"""PluginAgent — proxy agent for third-party plugins (V2.0)."""

from typing import Any, Dict, Optional

from penclip.agents.base import BaseAgent, ExecutionContext
from penclip.domain.value_objects.capability import CapabilityDeclaration
from penclip.domain.value_objects.execution_result import ExecutionResult
from penclip.domain.value_objects.intent import IntentType
from penclip.domain.value_objects.risk import RiskLevel
from penclip.logger import info


class PluginAgent(BaseAgent):
    agent_id = "plugin_proxy"
    agent_name = "PluginAgent"
    version = "0.1.0"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._plugins: Dict[str, Any] = {}
        super().__init__(config=config)

    def register_plugin(self, plugin: Any):
        self._plugins[plugin.plugin_id] = plugin
        info(f"PluginAgent: registered plugin '{plugin.plugin_id}'")

    def declare_capabilities(self) -> CapabilityDeclaration:
        return CapabilityDeclaration(
            name="plugin_proxy",
            intents=[IntentType.EXECUTE],
            description="Proxy agent that delegates to registered third-party plugins",
            risk_level=RiskLevel.LOW,
            version=self.version,
            agent_id=self.agent_id,
        )

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        plugin_id = params.get("plugin_id", "")
        plugin = self._plugins.get(plugin_id)
        if plugin is None:
            return ExecutionResult(success=False, message=f"Plugin not found: {plugin_id}")
        return plugin.execute(params, context)
