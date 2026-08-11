"""
@FileName: base_agent.py
@Description: Agent 抽象基类 — 所有 Agent 的统一契约
    每个 Agent 必须: 定义 name, 覆写 capabilities(), 覆写 execute()
    初始化末尾调用 self.register() 向 CapabilityRegistry 注册
@Author: HiPeng
@Time: 2026/08
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from neoclip.logger import info
from neoclip.state.models import AgentResult, Command
from neoclip.hub.capability_registry import CapabilityRecord


class BaseAgent(ABC):
    """所有 Agent 的抽象基类

    子类必须:
    1. __init__ 中设置 self.name（唯一标识）
    2. 覆写 capabilities() → List[CapabilityRecord]
    3. 覆写 execute(command) → AgentResult
    4. __init__ 末尾调用 self.register()
    """

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.config = config or {}
        self._registered = False

    @abstractmethod
    def capabilities(self) -> List[CapabilityRecord]:
        """返回该 Agent 提供的所有能力声明"""
        ...

    @abstractmethod
    def execute(self, command: Command) -> AgentResult:
        """主分发方法 — Hub 路由到本 Agent 时调用"""
        ...

    def register(self) -> None:
        """向全局 CapabilityRegistry 注册所有能力"""
        from neoclip.hub.capability_registry import get_capability_registry

        registry = get_capability_registry()
        caps = self.capabilities()
        for cap in caps:
            registry.register(cap)
        self._registered = True

    def _init_config_defaults(self, defaults: Dict[str, Any]) -> None:
        """将默认配置合并到 self.config（不覆盖已有值）"""
        for k, v in defaults.items():
            if k not in self.config:
                self.config[k] = v

    def _result_ok(self, data: Optional[Dict] = None, message: str = "") -> AgentResult:
        return AgentResult(status="success", data=data, message=message)

    def _result_fail(self, message: str, suggestions: Optional[List[str]] = None) -> AgentResult:
        return AgentResult(status="failed", message=message, suggestions=suggestions)

    def _result_partial(self, data: Optional[Dict] = None, message: str = "", suggestions: Optional[List[str]] = None) -> AgentResult:
        return AgentResult(status="partial", data=data, message=message, suggestions=suggestions)
