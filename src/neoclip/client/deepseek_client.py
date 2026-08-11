# -*- coding: utf-8 -*-
"""
@FileName: deepseek_client.py
@Description: DeepSeek模型客户端模块
@Author: neopen
@Time: 2025/10/6
"""
from typing import Dict, Any, Optional, Callable

from neoclip.client.base_client import BaseAIClient
from neoclip.client.openai_compat import OpenAICompatibleWrapper, BaseOpenAIResponse
from neoclip.logger import debug, error


class DeepSeekClient(BaseAIClient):
    """DeepSeek模型客户端类"""

    # DeepSeek特定配置
    PROVIDER_NAME = "deepseek"
    DEFAULT_BASE_URL = "https://api.deepseek.com/v1"
    DEFAULT_MODEL = "deepseek-chat"
    API_KEY_ENV_VAR = "DEEPSEEK_API_KEY"

    @classmethod
    def _get_client_implementation(cls, api_key: str, base_url: str, config: Dict[str, Any]) -> OpenAICompatibleWrapper:
        """
        获取DeepSeek客户端实现
        
        Args:
            api_key: API密钥
            base_url: 基础URL
            config: 配置字典
            
        Returns:
            OpenAI兼容的客户端实例
        """
        # 创建completion处理函数，并传递config参数
        handler = cls.create_completion_handler(api_key, base_url, config)

        # 创建并返回OpenAI兼容的包装器
        return cls.create_openai_compatible_wrapper(handler)

    @classmethod
    def create_completion_handler(cls, api_key: str, base_url: str, config: Dict[str, Any]) -> Callable:
        """
        创建DeepSeek的completion处理函数
        
        Args:
            api_key: API密钥
            base_url: 基础URL
            
        Returns:
            completion处理函数
        """

        def deepseek_completion_handler(model: str = None, messages: list = None,
                                        temperature: Optional[float] = None,
                                        max_tokens: Optional[int] = None,
                                        response_format: Optional[Dict] = None,
                                        **kwargs) -> BaseOpenAIResponse:
            """
            DeepSeek模型调用处理函数
            
            Args:
                model: 模型名称
                messages: 消息列表
                temperature: 温度参数
                max_tokens: 最大生成字数
                response_format: 响应格式要求
                **kwargs: 其他参数
                
            Returns:
                BaseOpenAIResponse对象
            """
            try:
                # 构建DeepSeek API请求参数
                payload = cls._build_deepseek_payload(model, messages, temperature, max_tokens)

                # 构建请求头
                headers = cls._build_deepseek_headers(api_key)

                # 发送请求
                debug(f"向DeepSeek发送请求: model={model}, temperature={temperature}")
                response = cls.make_request(f"{base_url}/chat/completions", headers, payload)

                # 解析响应
                response_data = response.json()

                # 转换为OpenAI格式
                content = cls.convert_response(response_data)

                # 创建并返回响应对象
                return cls.create_response_from_content(content)

            except Exception as e:
                error(f"DeepSeek API调用失败: {str(e)}")
                raise

        return deepseek_completion_handler

    @classmethod
    def _build_deepseek_payload(cls, model: Optional[str], messages: list,
                                temperature: Optional[float] = None,
                                max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        构建DeepSeek特定的请求参数
        
        Args:
            model: 模型名称
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大生成字数
            
        Returns:
            DeepSeek请求参数字典
        """
        return {
            "model": model or cls.DEFAULT_MODEL,
            "messages": messages,
            "temperature": temperature if temperature is not None else 0.2,
            "max_tokens": max_tokens if max_tokens is not None else 2000,
            "stream": False
        }

    @classmethod
    def _build_deepseek_headers(cls, api_key: str) -> Dict[str, str]:
        """
        构建DeepSeek特定的请求头
        
        Args:
            api_key: API密钥
            
        Returns:
            DeepSeek请求头字典
        """
        return {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }

    @staticmethod
    def convert_response(response: Any) -> str:
        """
        转换DeepSeek的响应格式，支持多种响应格式和错误处理
        
        Args:
            response: DeepSeek API返回的响应对象或字典
            
        Returns:
            提取的文本内容
        """
        try:
            # 处理字典类型响应
            if isinstance(response, dict):
                choices = response.get('choices', [])
                if choices and isinstance(choices, list):
                    first_choice = choices[0]
                    if isinstance(first_choice, dict):
                        message = first_choice.get('message', {})
                        if message:
                            return message.get('content', '')
                    # 也处理对象类型的choice
                    elif hasattr(first_choice, 'message') and hasattr(first_choice.message, 'content'):
                        return first_choice.message.content
            
            # 处理对象类型响应
            elif hasattr(response, 'choices') and response.choices:
                first_choice = response.choices[0]
                if hasattr(first_choice, 'message') and hasattr(first_choice.message, 'content'):
                    return first_choice.message.content
            
            # 处理直接的文本响应
            elif isinstance(response, str):
                return response
            
            # 未知格式，记录更详细的日志
            error(f"DeepSeek响应格式无法识别: {type(response).__name__} - {str(response)[:200]}...")
            return ''
        except Exception as e:
            error(f"转换DeepSeek响应失败: {str(e)}")
            # 尝试返回响应的字符串表示作为最后的备选
            try:
                return str(response) if response else ''
            except:
                return ''
