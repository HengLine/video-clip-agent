"""PluginManager — manages plugin lifecycle (load, activate, deactivate, unload)."""

from typing import Any, Dict, List, Optional

from neoclip.logger import info


class PluginManager:
    def __init__(self):
        self._plugins: Dict[str, Any] = {}
        info("PluginManager initialized")

    def register(self, plugin: Any):
        self._plugins[plugin.plugin_id] = plugin
        plugin.on_load()

    def unregister(self, plugin_id: str):
        plugin = self._plugins.pop(plugin_id, None)
        if plugin:
            plugin.on_unload()

    def list_plugins(self) -> List[str]:
        return list(self._plugins.keys())

    def get_plugin(self, plugin_id: str) -> Optional[Any]:
        return self._plugins.get(plugin_id)
