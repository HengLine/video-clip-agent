# -*- coding: utf-8 -*-
"""
@FileName: ollama_client.py
@Description: Ollama本地模型客户端
@Author: neopen
@Time: 2025/10/6
"""

from typing import Dict, Any, Optional, Callable

from neoclip.client.base_client import BaseAIClient
from neoclip.client.openai_compat import OpenAICompatibleWrapper, BaseOpenAIResponse
from neoclip.logger import debug, error


class OllamaClient(BaseAIClient):
    """
    Ollama本地模型客户端
    提供Ollama本地模型的访问和响应处理
    """

    # Ollama特定配置
    PROVIDER_NAME = "ollama"
    DEFAULT_BASE_URL = "http://localhost:11434"
    DEFAULT_MODEL = "llama3"
    API_KEY_ENV_VAR = "OLLAMA_API_KEY"  # Ollama通常不需要API密钥，但为了接口一致性保留

    @classmethod
    def _get_client_implementation(cls, api_key: str, base_url: str, config: Dict[str, Any]) -> OpenAICompatibleWrapper:
        """
        获取Ollama客户端实现
        
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
        创建Ollama的completion处理函数
        
        Args:
            api_key: API密钥（Ollama通常不需要）
            base_url: 基础URL
            
        Returns:
            completion处理函数
        """

        def ollama_completion_handler(model: str = None, messages: list = None,
                                      temperature: Optional[float] = None,
                                      max_tokens: Optional[int] = None,
                                      response_format: Optional[Dict] = None,
                                      **kwargs) -> BaseOpenAIResponse:
            """
            Ollama模型调用处理函数
            
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
                # 构建Ollama API请求参数
                payload = cls._build_ollama_payload(model, messages, temperature, max_tokens)

                # 构建请求头（Ollama通常不需要Authorization）
                headers = cls._build_ollama_headers(api_key)

                # 发送请求
                debug(f"向Ollama发送请求: model={model}, temperature={temperature}")
                response = cls.make_request(f"{base_url}/api/chat", headers, payload)

                # 解析响应
                response_data = response.json()

                # 转换为OpenAI格式
                content = cls.convert_response(response_data)

                # 创建并返回响应对象
                return cls.create_response_from_content(content)

            except Exception as e:
                error(f"Ollama调用失败: {str(e)}")
                raise

        return ollama_completion_handler

    @classmethod
    def _build_ollama_payload(cls, model: Optional[str], messages: list,
                              temperature: Optional[float] = None,
                              max_tokens: Optional[int] = None) -> Dict[str, Any]:
        """
        构建Ollama特定的请求参数
        
        Args:
            model: 模型名称
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大生成字数
            
        Returns:
            Ollama请求参数字典
        """
        payload = {
            "model": model or cls.DEFAULT_MODEL,
            "messages": messages,
            "stream": False
        }

        if temperature is not None:
            payload['temperature'] = temperature
        if max_tokens is not None:
            payload['max_tokens'] = max_tokens

        return payload

    @classmethod
    def _build_ollama_headers(cls, api_key: str) -> Dict[str, str]:
        """
        构建Ollama特定的请求头
        
        Args:
            api_key: API密钥（Ollama通常不需要）
            
        Returns:
            Ollama请求头字典
        """
        headers = {
            "Content-Type": "application/json"
        }

        # 如果提供了API密钥，则添加Authorization头
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

        return headers

    @staticmethod
    def convert_response(response: Dict) -> str:
        """
        转换Ollama的响应格式
        
        Args:
            response: Ollama API返回的响应字典
            
        Returns:
            提取的文本内容
        """
        return response.get('message', {}).get('content', '')
