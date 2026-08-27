# -*- coding: utf-8 -*-
"""
@FileName: requirement_analyzer.py
@Description: 用户需求分析服务模块
@Author: neopen
"""
from typing import Dict, Any

from penclip.config.config import get_settings_config
from penclip.client.ai_client import global_ai_client
from penclip.logger import info, error


class RequirementAnalyzer:
    """用户需求分析器"""

    def __init__(self):
        """初始化需求分析器"""
        self.ai_client = global_ai_client
        self.config = get_settings_config().get('ai_model', {})

    def analyze(self, user_input: str) -> Dict[str, Any]:
        """分析用户需求
        
        Args:
            user_input: 用户输入的需求描述
            
        Returns:
            包含分析结果的字典
        """
        if not user_input or not user_input.strip():
            return {
                'success': False,
                'error': '输入不能为空',
                'result': None
            }

        try:
            # 首先使用AI模型分析用户需求
            ai_result = self.ai_client.analyze_user_requirement(user_input)

            if not ai_result:
                return {
                    'success': False,
                    'error': 'AI分析失败，请检查配置',
                    'result': None
                }

            # 生成视频处理配置
            video_config = self.ai_client.generate_video_config(user_input)

            return {
                'success': True,
                'analysis': ai_result,
                'video_config': video_config,
                'provider': self.config.get('provider'),
                'result': {
                    'processed_input': user_input,
                    'ai_analysis': ai_result,
                    'config': video_config
                }
            }

        except Exception as e:
            error(f"需求分析失败: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'result': None
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

    def validate_requirement(self, user_input: str) -> Dict[str, Any]:
        """验证用户需求的有效性
        
        Args:
            user_input: 用户输入的需求描述
            
        Returns:
            验证结果
        """
        if not user_input or not user_input.strip():
            return {
                'valid': False,
                'reason': '需求描述不能为空'
            }

        # 检查需求长度
        if len(user_input) < 5:
            return {
                'valid': False,
                'reason': '需求描述太短，请提供更详细的信息'
            }

        # 检查是否包含视频处理相关关键词
        keywords = ['视频', '剪辑', '合并', '转场', '特效', '分辨率', '时长']
        if not any(keyword in user_input for keyword in keywords):
            return {
                'valid': True,
                'warning': '未检测到明显的视频处理关键词，可能需要更清晰的描述'
            }

        return {
            'valid': True,
            'reason': '需求描述有效'
        }


# 创建全局需求分析器实例
global_analyzer = RequirementAnalyzer()


def get_requirement_analyzer() -> RequirementAnalyzer:
    """获取全局需求分析器实例
    
    Returns:
        RequirementAnalyzer实例
    """
    return global_analyzer
