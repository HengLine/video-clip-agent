# -*- coding: utf-8 -*-
"""
@FileName: requirement_analyzer.py
@Description: 用户需求分析服务模块
@Author: HengLine
"""
import time
from typing import Dict, Any

from config.config import get_settings_config
from hengline.client.ai_client import global_ai_client
from hengline.logger import info, error


class RequirementAnalyzer:
    """用户需求分析器"""

    def __init__(self):
        """初始化需求分析器"""
        self.ai_client = global_ai_client
        self.config = get_settings_config().get('ai_model', {})

    def analyze(self, user_input: str) -> Dict[str, Any]:
        """分析用户需求并生成视频处理配置
        
        Args:
            user_input: 用户输入的需求描述
            
        Returns:
            包含分析结果和视频配置的结构化字典
        """
        try:
            # 先验证需求有效性
            is_valid, message = self.validate_requirement(user_input)
            if not is_valid:
                return {
                    'success': False,
                    'error': message,
                    'data': None
                }

            # 直接生成视频处理配置（一步到位，减少API调用）
            video_config = self.ai_client.generate_video_config(user_input)
            
            if not video_config:
                return {
                    'success': False,
                    'error': '无法生成有效的视频配置，请提供更详细的需求描述',
                    'data': None
                }
            
            # 结构化返回结果，更清晰的格式
            return {
                'success': True,
                'data': {
                    'user_input': user_input,
                    'video_config': video_config,
                    'metadata': {
                        'provider': self.config.get('provider'),
                        'timestamp': time.time(),
                        'validation_result': message
                    }
                }
            }

        except Exception as e:
            error(f"需求分析失败: {str(e)}")
            return {
                'success': False,
                'error': f'处理过程中发生错误: {str(e)}',
                'data': None
            }

    def get_supported_providers(self) -> list:
        """获取支持的AI模型提供商列表
        
        Returns:
            支持的提供商名称列表
        """
        return ['openai', 'qwen', 'deepseek']

    def switch_provider(self, provider: str) -> bool:
        """切换AI模型提供商
        
        Args:
            provider: 提供商名称
            
        Returns:
            是否切换成功
        """
        success = self.ai_client.set_provider(provider)
        if success:
            info(f"成功切换AI模型提供商为: {provider}")
        return success

    def get_current_provider(self) -> str:
        """获取当前使用的AI模型提供商
        
        Returns:
            当前提供商名称
        """
        return self.config.get('provider', 'openai')

    def validate_requirement(self, user_input: str):
        """验证用户需求的有效性
        
        Args:
            user_input: 用户输入的需求描述
            
        Returns:
            验证结果
        """
        if not user_input or not user_input.strip():
            return False, '需求描述不能为空'

        # 检查需求长度
        if len(user_input) < 5:
            return False, '需求描述太短，请提供更详细的信息'

        # 检查是否包含视频处理相关关键词
        keywords = ['视频', '剪辑', '合并', '转场', '特效', '分辨率', '时长']
        if not any(keyword in user_input for keyword in keywords):
            return True, '未检测到明显的视频处理关键词，可能需要更清晰的描述'

        return True, '需求描述有效'


# 创建全局需求分析器实例
global_analyzer = RequirementAnalyzer()


def get_requirement_analyzer() -> RequirementAnalyzer:
    """获取全局需求分析器实例
    
    Returns:
        RequirementAnalyzer实例
    """
    return global_analyzer
