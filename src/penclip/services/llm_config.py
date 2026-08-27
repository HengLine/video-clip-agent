"""LLM 配置层 — 类型化配置 + 供应商自注册（registry/strategy/factory）。

不 import ``penclip.config.config``，避免循环依赖；env 注入与默认值合并均为纯函数，可独立测试。
"""

import os
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Type

from pydantic import BaseModel, Field

from penclip.logger import debug

# 默认供应商（与 config.json 的 ai_model.provider 默认值一致）
_DEFAULT_PROVIDER = "qwen"


class LLMProviderConfig(BaseModel):
    """单个供应商的运行时配置（默认值 + config.json + env 合并后的结果）。"""

    name: str
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    extra: Dict[str, Any] = Field(default_factory=dict)


class LLMSettings(BaseModel):
    """LLM 全局配置（对应 config.json 的 ai_model 段）。"""

    provider: str = _DEFAULT_PROVIDER
    temperature: float = 0.1
    max_tokens: int = 2000
    timeout: int = 30
    providers: Dict[str, LLMProviderConfig] = Field(default_factory=dict)

    def get_active(self) -> LLMProviderConfig:
        """返回当前激活供应商的配置。"""
        return self.providers[self.provider]

    def get(self, name: str) -> LLMProviderConfig:
        """按名称返回供应商配置，未知名称抛 ValueError。"""
        try:
            return self.providers[name]
        except KeyError as exc:
            raise ValueError(f"Unknown LLM provider: {name}") from exc


@dataclass(frozen=True)
class ProviderSpec:
    """供应商元数据的单一事实来源，随客户端类自注册。"""

    name: str
    client_cls: Type[Any]
    default_base_url: str = ""
    default_model: str = ""
    api_key_env: str = ""
    base_url_env: str = ""
    model_env: str = ""


class LLMProviderRegistry:
    """供应商注册表 — 自注册，无硬编码列表。"""

    _specs: Dict[str, ProviderSpec] = {}

    @classmethod
    def register(cls, spec: ProviderSpec) -> None:
        cls._specs[spec.name] = spec
        debug(f"LLMProviderRegistry: registered provider '{spec.name}'")

    @classmethod
    def get(cls, name: str) -> ProviderSpec:
        try:
            return cls._specs[name]
        except KeyError as exc:
            raise ValueError(f"Unknown LLM provider: {name}") from exc

    @classmethod
    def all(cls) -> Dict[str, ProviderSpec]:
        return dict(cls._specs)

    @classmethod
    def names(cls) -> List[str]:
        return list(cls._specs.keys())


def register_provider(cls: Type[Any]) -> Type[Any]:
    """类装饰器：读取客户端类属性并自注册到 LLMProviderRegistry。"""
    spec = ProviderSpec(
        name=getattr(cls, "PROVIDER_NAME", cls.__name__),
        client_cls=cls,
        default_base_url=getattr(cls, "DEFAULT_BASE_URL", ""),
        default_model=getattr(cls, "DEFAULT_MODEL", ""),
        api_key_env=getattr(cls, "API_KEY_ENV_VAR", ""),
        base_url_env=getattr(cls, "BASE_URL_ENV_VAR", ""),
        model_env=getattr(cls, "MODEL_ENV_VAR", ""),
    )
    LLMProviderRegistry.register(spec)
    return cls


def _env_or(env_name: str, fallback: str) -> str:
    """返回环境变量值，未设置则返回 fallback。"""
    if env_name:
        value = os.environ.get(env_name)
        if value:
            return value
    return fallback


def resolve_provider_config(
    name: str, raw_provider: Optional[Dict[str, Any]] = None
) -> LLMProviderConfig:
    """按 env > config.json > ProviderSpec 默认值 合并出类型化供应商配置。"""
    spec = LLMProviderRegistry.get(name)
    raw = raw_provider or {}

    api_key = _env_or(spec.api_key_env, raw.get("api_key", ""))
    base_url = _env_or(spec.base_url_env, raw.get("base_url", "") or spec.default_base_url)
    model = _env_or(spec.model_env, raw.get("model", "") or spec.default_model)

    return LLMProviderConfig(name=name, api_key=api_key, base_url=base_url, model=model)


def load_llm_settings(raw_ai_model: Optional[Dict[str, Any]] = None) -> LLMSettings:
    """从原始 ai_model dict 构建类型化 LLMSettings（遍历注册表，可扩展）。"""
    raw = raw_ai_model or {}

    provider = _env_or("AI_PROVIDER", raw.get("provider", _DEFAULT_PROVIDER))

    settings = LLMSettings(
        provider=provider,
        temperature=raw.get("temperature", 0.1),
        max_tokens=raw.get("max_tokens", 2000),
        timeout=raw.get("timeout", 30),
    )

    for name in LLMProviderRegistry.names():
        settings.providers[name] = resolve_provider_config(name, raw.get(name))

    return settings
