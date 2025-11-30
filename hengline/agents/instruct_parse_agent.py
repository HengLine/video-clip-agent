"""
@FileName: instruct_parse_agent.py
@Description: 用户指令解析智能体，将自然语言指令转换为结构化任务配置
@Author: HengLine
@Time: 2025/11/28 17:22
"""
import json
import os
from typing import Dict, Any, Optional, List, Union

from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.runnables import Runnable, RunnableConfig
from tenacity import retry, stop_after_attempt, wait_exponential

from hengline.agents.agent_models import StructuredIntent, TransitionConfig, BGMConfig, ConstraintConfig
from hengline.logger import debug, info, warning, error
from hengline.tool.requirement_analyzer_tool import get_requirement_analyzer
from hengline.client.ai_client import global_ai_client

class InstructParseAgent(Runnable):

    def __init__(self):
        """
        初始化需求分析agent
        设置基本信息和初始化需求分析器
        """
        self.role = "需求分析"
        self.capabilities = [
            "用户需求解析",
            "需求验证",
            "提取结构化信息"
        ]
        # 初始化需求分析器
        self.requirement_analyzer = get_requirement_analyzer()
        # 初始化AI客户端
        self.ai_client = global_ai_client
        # 输出解析器
        self.output_parser = PydanticOutputParser(pydantic_object=StructuredIntent)
        info(f"初始化 {self.role} agent (基于langchain实现)")

    def analyze_user_requirement(self, user_input: str) -> Dict[str, Any]:
        """
        分析用户需求

        Args:
            user_input: 用户输入的需求描述

        Returns:
            包含分析结果的字典，包含成功状态、分析内容和可能的错误信息
        """
        try:
            # 分析用户需求
            analysis_result = self.requirement_analyzer.analyze(user_input)
            
            # 处理分析结果
            if analysis_result and analysis_result.get('success'):
                info(f"成功分析用户需求: {user_input}")
                return {
                    'success': True,
                    'analysis': analysis_result.get('analysis'),
                    'video_config': analysis_result.get('video_config'),
                    'provider': analysis_result.get('provider'),
                    'user_input': user_input
                }
            else:
                error_msg = analysis_result.get('error', '需求分析失败') if analysis_result else '需求分析失败'
                warning(f"需求分析失败: {error_msg}")
                return {
                    'success': False,
                    'error': error_msg,
                    'user_input': user_input
                }

        except Exception as e:
            error(f"分析用户需求时发生异常: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'user_input': user_input
            }
    
    def _convert_config_to_structured_intent(self, config: Dict[str, Any]) -> StructuredIntent:
        """
        将AI生成的配置转换为StructuredIntent对象
        
        Args:
            config: AI生成的配置字典
            
        Returns:
            StructuredIntent对象
        """
        # 提取转场配置
        transition_data = config.get('transition', {})
        transition = TransitionConfig(
            type=transition_data.get('type', 'fade'),
            duration_sec=transition_data.get('duration_sec', 0.6)
        )
        
        # 提取BGM配置
        bgm_data = config.get('bgm', {})
        bgm = BGMConfig(
            mood=bgm_data.get('mood', 'relaxed'),
            instrument=bgm_data.get('instrument', 'piano'),
            volume_db=bgm_data.get('volume_db', -15)
        )
        
        # 提取约束配置
        constraints_data = config.get('constraints', {})
        constraints = ConstraintConfig(
            min_clip_duration=constraints_data.get('min_clip_duration', 0.8),
            max_clip_duration=constraints_data.get('max_clip_duration', 5.0),
            per_video=constraints_data.get('per_video', True),
            max_total_clips=constraints_data.get('max_total_clips', 10)
        )
        
        # 创建并返回StructuredIntent对象
        return StructuredIntent(
            content_keywords=config.get('content_keywords', ['person']),
            subject=config.get('subject', 'person'),
            action=config.get('action', 'extract'),
            transition=transition,
            bgm=bgm,
            constraints=constraints
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
    def _parse_with_retry(self, user_input: str) -> StructuredIntent:
        """
        使用LLM解析用户指令，并支持重试机制
        
        Args:
            user_input: 用户输入的指令
            
        Returns:
            StructuredIntent对象
        """
        try:
            # 获取AI生成的视频配置
            video_config = self.ai_client.generate_video_config(user_input)
            
            if not video_config:
                error("无法获取有效的视频配置")
                raise ValueError("AI模型未能生成有效的视频配置")
                
            # 转换为StructuredIntent对象
            result = self._convert_config_to_structured_intent(video_config)
            info(f"成功解析指令: {result.model_dump_json(indent=2)}")
            return result
            
        except Exception as e:
            warning(f"解析失败（重试中）: {e}")
            raise e  # 触发重试
    
    def invoke(self, input: Dict[str, Any], config: Optional[RunnableConfig] = None) -> Dict[str, Any]:
        """
        实现Runnable接口，处理输入并返回结构化的输出
        
        Args:
            input: 输入字典，应包含'instruction'键
            config: 可选的Runnable配置
            
        Returns:
            包含结构化意图的字典
        """
        try:
            # 从输入中提取用户指令
            user_instruction = input.get('instruction', '')
            if not user_instruction:
                raise ValueError("输入中缺少'instruction'字段")
            
            # 分析用户需求
            analysis_result = self.analyze_user_requirement(user_instruction)
            
            if not analysis_result.get('success'):
                # 如果分析失败，返回错误信息
                return {
                    'error': analysis_result.get('error', '需求分析失败'),
                    'message': analysis_result.get('message', '无法解析用户指令'),
                    'structured_intent': None
                }
            
            # 尝试解析为结构化意图
            try:
                structured_intent = self._parse_with_retry(user_instruction)
                return {
                    'structured_intent': structured_intent.model_dump(),
                    'analysis': analysis_result.get('analysis'),
                    'success': True
                }
            except Exception as e:
                error(f"结构化意图解析失败: {str(e)}")
                # 如果解析失败但有video_config，尝试直接使用
                if analysis_result.get('video_config'):
                    try:
                        structured_intent = self._convert_config_to_structured_intent(analysis_result['video_config'])
                        return {
                            'structured_intent': structured_intent.model_dump(),
                            'analysis': analysis_result.get('analysis'),
                            'success': True
                        }
                    except Exception as inner_e:
                        error(f"从配置转换为结构化意图失败: {str(inner_e)}")
                
                # 如果所有尝试都失败，返回错误
                return {
                    'error': f"解析结构化意图失败: {str(e)}",
                    'analysis': analysis_result.get('analysis'),
                    'structured_intent': None,
                    'success': False
                }
                
        except Exception as e:
            error(f"执行指令解析时发生异常: {str(e)}")
            return {
                'error': str(e),
                'structured_intent': None,
                'success': False
            }

# 创建全局实例供其他模块使用
global_instruct_parse_agent = InstructParseAgent()

def get_instruct_parse_agent() -> InstructParseAgent:
    """
    获取全局指令解析智能体实例
    
    Returns:
        InstructParseAgent实例
    """
    return global_instruct_parse_agent

