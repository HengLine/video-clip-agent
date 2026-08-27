# -*- coding: utf-8 -*-
"""
@FileName: client_factory.py
@Description: 客户端工厂模块，通过 LLMProviderRegistry 自注册机制统一创建不同厂商的客户端
@Author: neopen
@Time: 2025/10/6
"""
import os
from typing import Any, Dict, Optional

from penclip.config.config import get_settings_config

# 以下 import 仅用于触发 @register_provider 自注册副作用
from penclip.llm.deepseek_client import DeepSeekClient  # noqa: F401
from penclip.llm.ollama_client import OllamaClient  # noqa: F401
from penclip.llm.openai_client import OpenAIClient  # noqa: F401
from penclip.llm.qwen_client import QwenClient  # noqa: F401
from penclip.logger import error, debug
from penclip.services.llm_config import LLMProviderRegistry, resolve_provider_config


class AIClientFactory:
    """AI 客户端工厂，根据注册表创建对应的客户端实例（无硬编码供应商列表）。"""

    @classmethod
    def create_client(cls, provider: str, config: Optional[Dict[str, Any]] = None) -> Any:
        """根据提供商名称创建对应的 AI 客户端。

        Args:
            provider: AI 模型提供商名称
            config: 客户端配置参数（供应商子字典），None 时按 env + 默认值解析

        Returns:
            配置好的 AI 客户端实例（OpenAI 兼容格式）

        Raises:
            ValueError: 当提供商未注册时
        """
        spec = LLMProviderRegistry.get(provider)
        cfg = resolve_provider_config(provider, config)
        return spec.client_cls.create_client(
            {"api_key": cfg.api_key, "base_url": cfg.base_url, "model": cfg.model}
        )

    @classmethod
    def get_supported_providers(cls) -> list:
        """获取已注册的 AI 模型提供商列表。"""
        return LLMProviderRegistry.names()

    @classmethod
    def get_provider_client_class(cls, provider: str) -> Any:
        """获取指定提供商的客户端类。"""
        return LLMProviderRegistry.get(provider).client_cls


# 创建全局工厂实例
ai_client_factory = AIClientFactory()


def get_ai_client(provider: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> Any:
    """获取 AI 客户端的便捷函数。

    Args:
        provider: AI 模型提供商名称，None 时取 AI_PROVIDER env 或配置默认值
        config: 客户端配置参数

    Returns:
        配置好的 AI 客户端实例
    """
    if provider is None:
        provider = os.environ.get("AI_PROVIDER") or get_settings_config().get("ai_model", {}).get(
            "provider", "qwen"
        )

    return ai_client_factory.create_client(provider, config)


def convert_response(provider: str, response: Any) -> str:
    """
    转换特定提供商的响应格式为文本，增强格式兼容性和错误处理

    Args:
        provider: AI模型提供商名称
        response: API响应对象或字典

    Returns:
        提取的文本内容
    """
    try:
        # 空响应检查
        if response is None:
            debug(f"收到空响应，提供商: {provider}")
            return ''

        # 对于特定提供商，仅对原始字典响应使用其专用的转换方法
        # （OpenAI 兼容对象如 BaseOpenAIResponse 统一走下方通用 .choices 分支）
        if provider in ['qwen', 'deepseek', 'ollama'] and isinstance(response, dict):
            try:
                client_class = ai_client_factory.get_provider_client_class(provider)
                result = client_class.convert_response(response)
                # 验证结果非空
                if result:
                    return result
                debug(f"提供商{provider}的转换方法返回空结果")
            except Exception as e:
                error(f"调用{provider}的转换方法失败: {str(e)}")
                # 继续尝试通用转换方法

        # OpenAI和通用响应格式处理
        # 1. 处理对象类型响应
        if hasattr(response, 'choices') and response.choices:
            first_choice = response.choices[0]
            if hasattr(first_choice, 'message'):
                message = first_choice.message
                if hasattr(message, 'content'):
                    return message.content
                elif hasattr(message, 'text'):
                    return message.text

        # 2. 处理字典类型响应
        elif isinstance(response, dict):
            # 标准OpenAI格式
            choices = response.get('choices', [])
            if choices and isinstance(choices, list):
                first_choice = choices[0]
                if isinstance(first_choice, dict):
                    message = first_choice.get('message', {})
                    if isinstance(message, dict):
                        return message.get('content', '') or message.get('text', '')
                    elif hasattr(message, 'content'):
                        return message.content

            # 其他常见格式
            # 直接输出格式
            if 'content' in response:
                return response['content']

            # 输出对象格式
            output = response.get('output')
            if output:
                if isinstance(output, dict):
                    return output.get('text', '') or output.get('content', '')
                elif hasattr(output, 'text'):
                    return output.text
                elif hasattr(output, 'content'):
                    return output.content

        # 3. 直接文本响应
        elif isinstance(response, str):
            return response

        # 4. 处理其他可能的格式
        # 检查是否有直接的文本属性
        if hasattr(response, 'text'):
            return response.text
        elif hasattr(response, 'content'):
            return response.content

        # 未知格式，记录详细信息以便调试
        error(f"无法识别的响应格式，提供商: {provider}, 类型: {type(response).__name__}, 内容: {str(response)[:200]}...")

        # 最后的备选方案：返回响应的字符串表示
        return str(response) if response else ''

    except Exception as e:
        error(f"转换响应时发生异常，提供商: {provider}, 错误: {str(e)}")
        # 安全地返回响应的字符串表示
        try:
            return str(response) if response else ''
        except:
            return ''
