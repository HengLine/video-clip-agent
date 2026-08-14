"""PluginBase — abstract base class for third-party plugins (V2.0)."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from neoclip.domain.value_objects.capability import CapabilityDeclaration
from neoclip.domain.value_objects.execution_result import ExecutionResult


class PluginBase(ABC):
    plugin_id: str = ""
    plugin_name: str = ""
    version: str = "0.1.0"

    @abstractmethod
    def declare_capabilities(self) -> List[CapabilityDeclaration]:
        ...

    @abstractmethod
    def execute(self, params: Dict[str, Any], context: Dict[str, Any]) -> ExecutionResult:
        ...

    def on_load(self):
        pass

    def on_unload(self):
        pass
