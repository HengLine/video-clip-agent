"""LLMService — abstract interface + factory for LLM provider switching (strategy pattern)."""

from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional

from penclip.logger import debug


class LLMService(ABC):
    @abstractmethod
    def generate(self, prompt: str, schema: Optional[Dict] = None) -> Dict[str, Any]:
        ...

    @abstractmethod
    def embed(self, text: str) -> List[float]:
        ...

    @abstractmethod
    def classify(self, text: str, classes: List[str]) -> Dict[str, float]:
        ...

    @abstractmethod
    async def chat(self, messages: List[Dict], stream: bool = False) -> AsyncIterator[str]:
        ...


class LLMFactory:
    _registry: Dict[str, type] = {}

    @classmethod
    def register(cls, name: str, impl: type):
        cls._registry[name] = impl
        debug(f"LLMFactory: registered provider '{name}'")

    @classmethod
    def create(cls, provider: str, config: Optional[Dict] = None) -> LLMService:
        impl = cls._registry.get(provider)
        if impl is None:
            raise ValueError(f"Unknown LLM provider: {provider}")
        return impl(**(config or {}))
