"""BaseAgent — abstract base class for all agents. Template Method pattern."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from neoclip.domain.value_objects.capability import CapabilityDeclaration
from neoclip.domain.value_objects.execution_result import ExecutionResult
from neoclip.domain.value_objects.risk import RiskLevel
from neoclip.logger import debug, info


@dataclass
class ExecutionContext:
    session_id: Optional[str] = None
    hub_state: Optional[Dict[str, Any]] = None
    user_preferences: Dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    agent_id: str = ""
    agent_name: str = ""
    version: str = "0.1.0"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self._config = config or {}
        debug(f"BaseAgent: {self.agent_name} v{self.version} loaded")

    @abstractmethod
    def declare_capabilities(self) -> CapabilityDeclaration:
        ...

    @abstractmethod
    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        ...

    def execute_incremental(self, params: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        """Override for agents that support incremental operations."""
        return self.execute(params, context)

    def on_load(self):
        """Called when agent is loaded by the hub."""
        info(f"Agent loaded: {self.agent_name}")

    def on_unload(self):
        """Called when agent is unloaded."""
        info(f"Agent unloaded: {self.agent_name}")

    def _validate_params(self, params: Dict[str, Any]) -> bool:
        return True

    def _log_execution(self, result: ExecutionResult):
        debug(f"Agent {self.agent_name}: execution {'ok' if result.success else 'failed'}")
