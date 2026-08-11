# -*- coding: utf-8 -*-
"""
OpenAI 模型客户端实现
"""

import os
from typing import Dict, Optional, Any, Callable
import httpx

from openai import OpenAI
from neoclip.logger import debug, info, error
from neoclip.client.base_client import BaseAIClient
from neoclip.client.openai_compat import OpenAICompatibleWrapper, BaseOpenAIResponse


class OpenAIClient(BaseAIClient):
    """
    OpenAI 客户端类
    提供 OpenAI 模型的访问功能
    """
    
    # OpenAI特定配置
    PROVIDER_NAME = "openai"
    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    DEFAULT_MODEL = "gpt-4"
    API_KEY_ENV_VAR = "OPENAI_API_KEY"
    
    @classmethod
    def _get_client_implementation(cls, api_key: str, base_url: str, config: Dict[str, Any]) -> OpenAICompatibleWrapper:
        """
        获取OpenAI客户端实现
        
        Args:
            api_key: API密钥
            base_url: 基础URL
            config: 配置字典
            
        Returns:
            OpenAI兼容的客户端实例
        """
        # 创建completion处理函数，确保传递config参数
        handler = cls.create_completion_handler(api_key, base_url, config)
        
        # 创建并返回OpenAI兼容的包装器
        return cls.create_openai_compatible_wrapper(handler)
    
    @classmethod
    def create_completion_handler(cls, api_key: str, base_url: str, config: Dict[str, Any]) -> Callable:
        """
        创建OpenAI的completion处理函数
        
        Args:
            api_key: API密钥
            base_url: 基础URL
            config: 配置字典
            
        Returns:
            completion处理函数
        """
        try:
            # 创建 HTTP 客户端，设置适当的超时和重试策略
            http_client = httpx.Client(
                timeout=30.0,
                follow_redirects=True
            )
            
            client = OpenAI(
                api_key=api_key,
                base_url=base_url,
                http_client=http_client
            )
            
            def openai_completion_handler(model: str = None, messages: list = None, 
                                        temperature: Optional[float] = None, 
                                        max_tokens: Optional[int] = None, 
                                        response_format: Optional[Dict] = None, 
                                        **kwargs) -> BaseOpenAIResponse:
                """
                OpenAI模型调用处理函数
                
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
                    # 构建请求参数
                    payload = {
                        "model": model or cls.DEFAULT_MODEL,
                        "messages": messages,
                        "temperature": temperature if temperature is not None else 0.7,
                        "max_tokens": max_tokens if max_tokens is not None else 2000,
                    }
                    
                    # 添加响应格式参数（如果提供）
                    if response_format:
                        payload["response_format"] = response_format
                    
                    # 添加其他可选参数
                    for key, value in kwargs.items():
                        if value is not None:
                            payload[key] = value
                    
                    # 发送请求
                    debug(f"向OpenAI发送请求: model={model}, temperature={temperature}")
                    response = client.chat.completions.create(**payload)
                    
                    # 转换为OpenAI格式（实际上已经是兼容的）
                    content = cls.convert_response(response)
                    
                    # 创建并返回响应对象
                    return cls.create_response_from_content(content)
                    
                except Exception as e:
                    error(f"OpenAI调用失败: {str(e)}")
                    raise
            
            return openai_completion_handler
            
        except Exception as e:
            error(f"创建 OpenAI 客户端失败: {str(e)}")
            raise
    
    @staticmethod
    def convert_response(response: Any) -> str:
        """
        转换OpenAI响应为文本内容
        
        Args:
            response: OpenAI API响应对象
            
        Returns:
            提取的文本内容
        """
        try:
            # 处理 OpenAI SDK 返回的对象
            if response and hasattr(response, 'choices') and response.choices:
                choice = response.choices[0]
                if hasattr(choice, 'message') and hasattr(choice.message, 'content'):
                    return choice.message.content
            
            # 处理字典格式的响应
            elif isinstance(response, dict):
                content = response.get('choices', [{}])[0].get('message', {}).get('content', '')
                if content:
                    return content
            
            error(f"OpenAI响应格式异常: {response}")
            return ""
            
        except Exception as e:
            error(f"转换OpenAI响应失败: {str(e)}")
            return ""
    
    @classmethod
    def get_default_model(cls) -> str:
        """
        获取默认模型名称
        
        Returns:
            默认模型名称
        """
        # 允许通过环境变量覆盖默认模型
        return os.environ.get('OPENAI_DEFAULT_MODEL', cls.DEFAULT_MODEL)


def get_openai_client(config: Optional[Dict[str, Any]] = None) -> OpenAICompatibleWrapper:
    """
    获取OpenAI客户端实例
    
    Args:
        config: 配置参数
        
    Returns:
        OpenAI兼容的客户端实例
    """
    return OpenAIClient.create_client(config)


# 缓存的客户端实例
_cached_client = None
_cached_config = None


def get_cached_openai_client(config: Optional[Dict[str, Any]] = None) -> OpenAICompatibleWrapper:
    """
    获取缓存的OpenAI客户端实例
    
    Args:
        config: 配置参数
        
    Returns:
        OpenAI兼容的客户端实例
    """
    global _cached_client, _cached_config
    
    # 如果没有缓存或配置发生变化，则创建新实例
    if _cached_client is None or _cached_config != config:
        _cached_client = OpenAIClient.create_client(config)
        _cached_config = config
    
    return _cached_client

def create_openai_client_with_retry(max_retries: int = 3, 
                                   retry_delay: float = 2.0, 
                                   config: Optional[Dict[str, Any]] = None) -> OpenAICompatibleWrapper:
    """
    创建带重试机制的OpenAI客户端
    
    Args:
        max_retries: 最大重试次数
        retry_delay: 重试间隔（秒）
        config: 配置参数
        
    Returns:
        OpenAI兼容的客户端实例
    """
    import time
    
    for attempt in range(max_retries):
        try:
            client = OpenAIClient.create_client(config)
            info("成功创建OpenAI客户端")
            return client
        except Exception as e:
            if attempt == max_retries - 1:
                error(f"创建OpenAI客户端失败，已达到最大重试次数: {str(e)}")
                raise
            error(f"创建OpenAI客户端失败，将在{retry_delay}秒后重试: {str(e)}")
            time.sleep(retry_delay)
            retry_delay *= 1.5  # 指数退避
    
    raise RuntimeError("创建OpenAI客户端失败")


def analyze_with_openai(self, audio_path, user_query):
    """使用OpenAI Whisper API进行语音识别"""
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                timestamp_granularities=["word"]
            )

        return transcript
    except ImportError:
        print("请安装openai: pip install openai")
        return None
    except Exception as e:
        print(f"OpenAI API错误: {e}")
        return None