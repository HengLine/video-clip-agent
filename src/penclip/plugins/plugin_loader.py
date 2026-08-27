"""PluginLoader — discovers and loads plugins from filesystem."""

from typing import Any, Dict, List

from penclip.logger import info


class PluginLoader:
    def __init__(self, plugin_dir: str = "plugins"):
        self._plugin_dir = plugin_dir
        info(f"PluginLoader initialized (dir={plugin_dir})")

    def discover(self) -> List[Dict[str, Any]]:
        return []

    def load(self, plugin_path: str) -> Any:
        return None
