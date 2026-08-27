"""AgentFactory — creates and caches agent instances."""

from typing import Dict, List, Optional, Type

from penclip.agents.base import BaseAgent
from penclip.logger import debug


class AgentFactory:
    def __init__(self):
        self._agent_types: Dict[str, Type[BaseAgent]] = {}
        self._instances: Dict[str, BaseAgent] = {}
        debug("AgentFactory initialized")

    def register_agent_type(self, name: str, agent_class: Type[BaseAgent]):
        self._agent_types[name] = agent_class
        debug(f"AgentFactory: registered type '{name}'")

    def create_agent(self, name: str, config: Optional[Dict] = None) -> BaseAgent:
        if name in self._instances:
            return self._instances[name]
        agent_class = self._agent_types.get(name)
        if agent_class is None:
            raise ValueError(f"Unknown agent type: {name}")
        instance = agent_class(config=config)
        self._instances[name] = instance
        return instance

    def create_all_agents(self, config: Optional[Dict] = None) -> List[BaseAgent]:
        return [self.create_agent(name, config) for name in self._agent_types]
