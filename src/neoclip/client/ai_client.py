# -*- coding: utf-8 -*-
"""
@FileName: ai_client.py
@Description: AI模型客户端模块，支持OpenAI、Qwen、DeepSeek等多种模型
@Author: neopen
"""
import json
import time
from typing import Dict, Any, Optional

from config.config import get_settings_config
from neopen.prompt.prompt import get_generate_video_prompt, get_user_requirement_prompt
from neopen.client.client_factory import get_ai_client, convert_response
from neopen.logger import debug, error


class AIClient:
    """AI模型客户端，支持多种AI模型提供商"""

    def __init__(self):
        """初始化AI客户端"""
        self.config = get_settings_config().get('ai_model', {})
        self.client = None
        self.provider = self.config.get('provider', 'openai')
        # 加载提示词配置
        self._init_client()

    def _init_client(self):
        """根据配置初始化对应的AI客户端"""
        try:
            # 获取当前提供商的配置
            provider_config = self.config.get(self.provider, {})
            # 使用客户端工厂创建对应的AI客户端，并传入配置
            # 工厂会确保返回OpenAI兼容格式的客户端
            self.client = get_ai_client(self.provider, provider_config)
        except Exception as e:
            error(f"初始化{self.provider} AI客户端失败: {str(e)}")
            self.client = None

    def set_provider(self, provider: str):
        """切换AI模型提供商
        
        Args:
            provider: 提供商名称，支持 'openai', 'qwen', 'deepseek'
        """
        if provider in ['openai', 'qwen', 'deepseek', 'ollama']:
            self.provider = provider
            self._init_client()
            return True
        else:
            error(f"不支持的AI模型提供商: {provider}")
            return False

    def analyze_user_requirement(self, user_input: str, max_tokens: Optional[int] = None) -> Optional[str]:
        """分析用户的描述需求
        
        Args:
            user_input: 用户输入的需求描述
            max_tokens: 最大生成token数
            
        Returns:
            模型生成的响应内容（字符串）
        """
        if not self.client:
            error("AI客户端未初始化或配置错误")
            return None

        # 获取当前提供商的模型配置
        provider_config = self.config.get(self.provider, {})
        model = provider_config.get('model', 'qwen-plus')
        temperature = self.config.get('temperature', 0.1)
        max_tokens = max_tokens or self.config.get('max_tokens', 2000)

        try:
            # 调用AI模型
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=model,
                messages=get_user_requirement_prompt(user_input),
                temperature=temperature,
                max_tokens=max_tokens
            )

            end_time = time.time()
            debug(f"AI模型调用耗时: {end_time - start_time:.2f}秒")

            # 使用统一的响应转换函数返回内容
            result = convert_response(self.provider, response)
            debug(f"用户需求分析 AI模型响应: {result}")

            # 确保返回的是字符串类型，处理可能的对象
            if isinstance(result, str):
                return result
            elif hasattr(result, 'content'):
                return str(result.content) if result.content else ""
            else:
                # 最后的备选方案
                return str(result) if result else ""

        except Exception as e:
            error(f"AI模型调用失败: {str(e)}")
            return None

    def generate_video_config(self, user_requirement: str, max_tokens: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """根据用户需求生成视频处理配置
        
        Args:
            user_requirement: 用户的视频处理需求描述
            max_tokens: 最大生成token数
            
        Returns:
            包含视频处理配置的字典
        """
        if not self.client:
            error("AI客户端未初始化或配置错误")
            return None

        # 获取当前提供商的模型配置
        provider_config = self.config.get(self.provider, {})
        model = provider_config.get('model', 'qwen-plus')
        temperature = self.config.get('video_config_temperature', 0.3)
        max_tokens = max_tokens or self.config.get('max_tokens', 2000)

        try:
            # 调用AI模型
            start_time = time.time()
            response = self.client.chat.completions.create(
                model=model,
                messages=get_generate_video_prompt(user_requirement),
                temperature=temperature,
                max_tokens=max_tokens
            )

            end_time = time.time()
            debug(f"AI模型调用耗时: {end_time - start_time:.2f}秒")

            # 使用统一的响应转换函数返回内容
            result = convert_response(self.provider, response)
            debug(f"生成视频处理配置 AI模型响应: {result}")

            # 确保content是字符串
            content = ""
            if isinstance(result, str):
                content = result
            elif hasattr(result, 'content'):
                content = str(result.content) if result.content else ""
            else:
                content = str(result) if result else ""

            # 清理可能的Markdown代码块标记
            if content.startswith('```'):
                content = '\n'.join(content.split('\n')[1:])
            if content.endswith('```'):
                content = '\n'.join(content.split('\n')[:-1])

            # 去除首尾空白
            content = content.strip()

            # 尝试解析JSON
            if content:
                try:
                    config = json.loads(content)
                    debug(f"成功解析配置: {config}")
                    return config
                except json.JSONDecodeError as e:
                    error(f"解析AI返回的配置失败: {str(e)}")
                    # 尝试查找JSON内容
                    if '{' in content and '}' in content:
                        try:
                            # 尝试提取JSON部分
                            start_idx = content.find('{')
                            end_idx = content.rfind('}') + 1
                            json_content = content[start_idx:end_idx]
                            config = json.loads(json_content)
                            debug(f"成功从内容中提取并解析配置")
                            return config
                        except Exception as inner_e:
                            error(f"提取JSON并解析失败: {str(inner_e)}")
            else:
                error("AI返回的内容为空")

            return None
        except Exception as e:
            error(f"AI模型调用失败: {str(e)}")
            return None


# 创建全局AI客户端实例
global_ai_client = AIClient()
