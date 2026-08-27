"""LLM 配置层单测：类型化配置 + 供应商自注册。"""

import pytest

from penclip.services.llm_config import (
    LLMProviderRegistry,
    LLMSettings,
    load_llm_settings,
    resolve_provider_config,
)

# 触发 4 个供应商客户端自注册（import 副作用）
import penclip.client.client_factory as _cf  # noqa: F401

EXPECTED_PROVIDERS = {"openai", "qwen", "deepseek", "ollama"}

_LLM_ENV_VARS = (
    "AI_PROVIDER",
    "QWEN_API_KEY", "QWEN_BASE_URL", "QWEN_MODEL",
    "OPENAI_API_KEY", "OPENAI_BASE_URL", "OPENAI_MODEL",
    "DEEPSEEK_API_KEY", "DEEPSEEK_BASE_URL", "DEEPSEEK_MODEL",
    "OLLAMA_BASE_URL", "OLLAMA_MODEL",
)


@pytest.fixture(autouse=True)
def _clean_llm_env(monkeypatch):
    """清空环境变量，避免 .env 泄露影响断言。"""
    for var in _LLM_ENV_VARS:
        monkeypatch.delenv(var, raising=False)


def test_all_providers_self_registered():
    assert set(LLMProviderRegistry.names()) == EXPECTED_PROVIDERS


def test_resolve_provider_merges_spec_defaults():
    cfg = resolve_provider_config("qwen")
    assert cfg.name == "qwen"
    assert cfg.model == "qwen-plus"
    assert cfg.base_url == "https://dashscope.aliyuncs.com/compatible-mode/v1"
    assert cfg.api_key == ""


def test_resolve_provider_config_overrides_defaults():
    cfg = resolve_provider_config("qwen", {"model": "qwen-max", "api_key": "sk-x", "base_url": "http://x"})
    assert cfg.model == "qwen-max"
    assert cfg.api_key == "sk-x"
    assert cfg.base_url == "http://x"


def test_resolve_provider_env_override(monkeypatch):
    monkeypatch.setenv("QWEN_API_KEY", "env-key")
    monkeypatch.setenv("QWEN_MODEL", "qwen-env")
    monkeypatch.setenv("QWEN_BASE_URL", "http://env-url")
    cfg = resolve_provider_config("qwen", {"model": "qwen-max"})
    assert cfg.api_key == "env-key"
    assert cfg.model == "qwen-env"
    assert cfg.base_url == "http://env-url"


def test_resolve_provider_empty_base_url_falls_back_to_default():
    cfg = resolve_provider_config("openai", {"base_url": ""})
    assert cfg.base_url == "https://api.openai.com/v1"


def test_unknown_provider_raises():
    with pytest.raises(ValueError):
        LLMProviderRegistry.get("foo")
    with pytest.raises(ValueError):
        resolve_provider_config("foo")


def test_load_settings_active_provider():
    raw = {"provider": "deepseek", "temperature": 0.5, "max_tokens": 100, "timeout": 60}
    settings = load_llm_settings(raw)
    assert settings.provider == "deepseek"
    assert settings.temperature == 0.5
    assert settings.max_tokens == 100
    assert settings.timeout == 60
    assert settings.get_active().name == "deepseek"
    assert settings.get_active().model == "deepseek-chat"


def test_load_settings_ai_provider_env_override(monkeypatch):
    monkeypatch.setenv("AI_PROVIDER", "ollama")
    settings = load_llm_settings({"provider": "qwen"})
    assert settings.provider == "ollama"
    assert settings.get_active().name == "ollama"


def test_settings_get_unknown_raises():
    settings = load_llm_settings({"provider": "qwen"})
    with pytest.raises(ValueError):
        settings.get("foo")


def test_settings_model_is_typed():
    settings = load_llm_settings({"provider": "qwen"})
    assert isinstance(settings, LLMSettings)
    assert isinstance(settings.get_active().model, str)


def test_default_config_ai_model_has_all_providers():
    from penclip.config.config import DEFAULT_CONFIG

    ai_model = DEFAULT_CONFIG["ai_model"]
    assert set(ai_model) >= EXPECTED_PROVIDERS
