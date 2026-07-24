# -*- coding: utf-8 -*-
"""
@FileName: orchestrator_agent.py
@Description: 需求分析agent，负责解析用户输入需求，为视频内容分析做输入和准备
@Author: HengLine
@Time: 2025/10 - 2025/11
"""
import os
from typing import Dict, Any, Optional, List

from langchain_core.runnables import Runnable

from hengline.logger import debug, info, warning, error
from hengline.tool.requirement_analyzer_tool import get_requirement_analyzer
from .agent_state import GraphState


class RequirementAnalyzerAgent(Runnable):
    """
    需求分析agent
    负责解析用户输入需求，提取关键信息，并为视频内容分析做准备工作
    实现Runnable接口以支持与langchain生态系统的集成
    """

    def __init__(self):
        """
        初始化需求分析agent
        设置基本信息和初始化需求分析器
        """
        self.role = "需求分析"
        self.capabilities = [
            "用户需求解析",
            "需求验证",
            "分析策略生成",
            "内容提取",
            "处理建议"
        ]
        # 初始化需求分析器
        self.requirement_analyzer = get_requirement_analyzer()
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
            # 验证需求有效性
            validation_result = self.requirement_analyzer.validate_requirement(user_input)

            if not validation_result.get('valid', False):
                warning(f"用户需求无效: {validation_result.get('reason')}")
                return {
                    'success': False,
                    'error': validation_result.get('reason', '需求无效'),
                    'user_input': user_input
                }

            # 分析用户需求
            analysis_result = self.requirement_analyzer.analyze(user_input)

            # 确保analysis_result是字典类型
            if not isinstance(analysis_result, dict):
                error(f"需求分析器返回非字典类型结果")
                return {
                    'success': False,
                    'error': '需求分析器返回格式错误',
                    'user_input': user_input
                }

            if analysis_result.get('success'):
                info(f"成功分析用户需求")
                # 提取并处理分析结果
                processed_result = self._process_analysis_result(analysis_result, user_input)
                return processed_result
            else:
                error(f"需求分析失败: {analysis_result.get('error', '未知错误')}")
                return {
                    'success': False,
                    'error': analysis_result.get('error', '需求分析失败'),
                    'user_input': user_input
                }

        except Exception as e:
            error(f"分析用户需求时发生异常: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'user_input': user_input
            }

    def _process_analysis_result(self, analysis_result: Dict[str, Any], user_input: str) -> Dict[str, Any]:
        """
        处理需求分析结果，提取关键信息
        
        Args:
            analysis_result: 需求分析结果
            user_input: 原始用户输入
            
        Returns:
            处理后的分析结果
        """
        # 从分析结果中提取关键信息
        analysis = analysis_result.get('analysis', {})
        video_config = analysis_result.get('video_config', {})
        provider = analysis_result.get('provider')

        # 确保必要字段是字典类型
        if not isinstance(analysis, dict):
            analysis = {}
        if not isinstance(video_config, dict):
            video_config = {}

        # 提取需求类型和处理重点
        requirement_type = analysis.get('需求类型', '通用视频处理')
        processing_focus = analysis.get('处理重点', [])

        # 生成内容分析策略
        analysis_strategy = self._generate_analysis_strategy(requirement_type, processing_focus, user_input)

        # 提取关键内容（如物体、情绪、关键词等）
        key_content = self._extract_key_content(user_input, analysis)

        return {
            'success': True,
            'user_input': user_input,
            'analysis': analysis,
            'video_config': video_config,
            'provider': provider,
            'requirement_type': requirement_type,
            'processing_focus': processing_focus,
            'analysis_strategy': analysis_strategy,
            'key_content': key_content,
            'content_analysis_input': self._prepare_content_analysis_input(
                analysis_strategy, key_content, video_config
            )
        }

    def _generate_analysis_strategy(self, requirement_type: str, processing_focus: List[str],
                                    user_input: str) -> Dict[str, Any]:
        """
        生成内容分析策略
        
        Args:
            requirement_type: 需求类型
            processing_focus: 处理重点
            user_input: 用户输入
            
        Returns:
            分析策略字典
        """
        # 基础分析策略
        strategy = {
            'focus_areas': ['scene_detection'],  # 场景检测通常是基础需求
            'priority': [],
            'special_instructions': []
        }

        # 根据需求类型调整策略
        if requirement_type == '内容摘要':
            strategy['focus_areas'].extend(['emotion_analysis', 'speech_transcription'])
            strategy['priority'].append('emotional_highlights')
        elif requirement_type == '物体追踪':
            strategy['focus_areas'].append('object_detection')
            strategy['priority'].append('object_presence')
        elif requirement_type == '情绪分析':
            strategy['focus_areas'].append('emotion_analysis')
            strategy['priority'].append('emotion_changes')
        elif requirement_type == '语音转写':
            strategy['focus_areas'].append('speech_transcription')
            strategy['priority'].append('transcription_quality')
        else:
            # 通用处理，添加所有分析
            strategy['focus_areas'].extend(['emotion_analysis', 'object_detection', 'speech_transcription'])

        # 根据处理重点调整策略
        if isinstance(processing_focus, list):
            for focus in processing_focus:
                if '情绪' in focus and 'emotion_analysis' not in strategy['focus_areas']:
                    strategy['focus_areas'].append('emotion_analysis')
                elif '物体' in focus and 'object_detection' not in strategy['focus_areas']:
                    strategy['focus_areas'].append('object_detection')
                elif '语音' in focus and 'speech_transcription' not in strategy['focus_areas']:
                    strategy['focus_areas'].append('speech_transcription')
                elif '场景' in focus and 'scene_detection' not in strategy['focus_areas']:
                    strategy['focus_areas'].append('scene_detection')

        # 添加特殊指令
        if '高质量' in user_input or '高清' in user_input:
            strategy['special_instructions'].append('优先保留高质量视频片段')
        if '关键' in user_input or '重要' in user_input:
            strategy['special_instructions'].append('重点识别关键内容')

        return strategy

    def _extract_key_content(self, user_input: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        从用户输入和分析结果中提取关键内容
        
        Args:
            user_input: 用户输入
            analysis: 分析结果
            
        Returns:
            关键内容字典
        """
        key_content = {
            'objects': [],
            'emotions': [],
            'keywords': [],
            'time_points': []
        }

        # 从分析结果中提取
        if analysis:
            # 提取物体
            if '检测物体' in analysis:
                detected_objects = analysis['检测物体']
                if isinstance(detected_objects, list):
                    key_content['objects'] = detected_objects
                elif isinstance(detected_objects, str):
                    key_content['objects'] = [detected_objects]

            # 提取情绪
            if '目标情绪' in analysis:
                target_emotions = analysis['目标情绪']
                if isinstance(target_emotions, list):
                    key_content['emotions'] = target_emotions
                elif isinstance(target_emotions, str):
                    key_content['emotions'] = [target_emotions]

            # 提取关键词
            if '关键词' in analysis:
                keywords = analysis['关键词']
                if isinstance(keywords, list):
                    key_content['keywords'] = keywords
                elif isinstance(keywords, str):
                    key_content['keywords'] = [keywords]

            # 提取时间点
            if '时间点' in analysis:
                time_points = analysis['时间点']
                if isinstance(time_points, list):
                    key_content['time_points'] = time_points

        # 备用：从用户输入中简单提取
        if not key_content['objects']:
            common_objects = ['人', '车', '猫', '狗', '建筑', '风景', '文字', '屏幕']
            for obj in common_objects:
                if obj in user_input:
                    key_content['objects'].append(obj)

        return key_content

    def _prepare_content_analysis_input(self, analysis_strategy: Dict[str, Any],
                                        key_content: Dict[str, Any],
                                        video_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备内容分析的输入数据
        
        Args:
            analysis_strategy: 分析策略
            key_content: 关键内容
            video_config: 视频配置
            
        Returns:
            内容分析输入字典
        """
        # 准备内容分析的输入数据
        content_analysis_input = {
            'analysis_strategy': analysis_strategy,
            'detect_objects': key_content['objects'],
            'target_emotions': key_content['emotions'],
            'audio_keywords': key_content['keywords'],
            'specific_time_points': key_content['time_points'],
            'crop_preferences': video_config.get('crop_preferences', {}),
            'output_format': video_config.get('output_format', {}),
            'quality_settings': video_config.get('quality_settings', {})
        }

        return content_analysis_input

    def validate_video_files(self, videos: List[str]) -> Dict[str, Any]:
        """
        验证视频文件
        
        Args:
            videos: 视频文件路径列表
            
        Returns:
            验证结果，包含有效视频列表和可能的错误信息
        """
        if not videos:
            return {
                'valid': False,
                'error': '没有找到视频文件',
                'valid_videos': [],
                'missing_videos': []
            }

        valid_videos = []
        missing_videos = []

        for video_path in videos:
            if os.path.exists(video_path):
                valid_videos.append(video_path)
            else:
                warning(f"视频文件不存在: {video_path}")
                missing_videos.append(video_path)

        if not valid_videos:
            return {
                'valid': False,
                'error': '所有视频文件都不存在',
                'valid_videos': [],
                'missing_videos': missing_videos
            }

        return {
            'valid': True,
            'valid_videos': valid_videos,
            'missing_videos': missing_videos,
            'total_valid': len(valid_videos)
        }

    def execute(self, state: GraphState) -> GraphState:
        """
        执行需求分析逻辑
        实现Runnable接口的标准执行方法
        """
        try:
            # 从状态中获取用户查询和视频信息
            user_query = state.get('user_query', '')
            videos = state.get('videos', [])

            debug(f"执行需求分析: 用户查询={user_query}")
            debug(f"输入视频列表: {videos}")

            if not user_query or not user_query.strip():
                # 处理空输入
                updated_state = state.copy()
                updated_state['error'] = '用户输入为空'
                updated_state['next_agent'] = 'error_handler'
                updated_state['suggestions'] = ['请输入视频处理需求']
                updated_state['current_agent'] = 'error_handler'
                return updated_state

            # 分析用户需求
            requirement_analysis = self.analyze_user_requirement(user_query)

            if not requirement_analysis.get('success'):
                # 处理需求分析失败
                updated_state = state.copy()
                updated_state['error'] = requirement_analysis.get('error', '需求分析失败')
                updated_state['next_agent'] = 'error_handler'
                updated_state['suggestions'] = [
                    '请提供更清晰的视频处理需求',
                    '确保需求中包含视频相关的关键词',
                    '尝试使用更详细的描述'
                ]
                updated_state['current_agent'] = 'error_handler'
                return updated_state

            # 验证视频文件
            video_validation = self.validate_video_files(videos)

            if not video_validation.get('valid'):
                # 处理视频文件验证失败
                updated_state = state.copy()
                updated_state['error'] = video_validation.get('error', '视频文件验证失败')
                updated_state['next_agent'] = 'file_handler'
                updated_state['suggestions'] = ['请上传有效的视频文件']
                updated_state['current_agent'] = 'file_handler'
                return updated_state

            # 准备完整的输出结果
            result = {
                'success': True,
                'requirement_analysis': requirement_analysis,
                'video_validation': video_validation,
                'valid_videos': video_validation.get('valid_videos', []),
                'content_analysis_input': requirement_analysis.get('content_analysis_input', {}),
                'next_agent': 'content_analyzer',
                'message': f"成功分析需求并准备内容分析数据，将处理{len(video_validation.get('valid_videos', []))}个视频文件"
            }

            # 更新状态
            updated_state = state.copy()
            updated_state.update(result)
            updated_state['current_agent'] = 'content_analyzer'

            debug(f"需求分析完成，下一步: {updated_state['current_agent']}")
            return updated_state

        except Exception as e:
            error(f"执行需求分析逻辑时发生异常: {str(e)}")
            updated_state = state.copy()
            updated_state['error'] = f"需求分析错误: {str(e)}"
            updated_state['current_agent'] = 'error_handler'
            updated_state['next_agent'] = 'error_handler'
            return updated_state

    def invoke(self, input_state: Dict[str, Any], config: Optional[Dict] = None, **kwargs: Any) -> Dict[str, Any]:
        """
        实现langchain的Runnable接口
        支持标准的invoke调用模式
        """
        return self.execute(input_state)

    def batch(self, inputs: List[Dict[str, Any]], config: Optional[Dict] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        支持批量处理多个需求分析任务
        """
        results = []
        for input_state in inputs:
            results.append(self.execute(input_state))
        return results

    def stream(self, input_state: Dict[str, Any], config: Optional[Dict] = None, **kwargs: Optional[Any]):
        """
        实现Runnable接口的stream方法
        
        Args:
            input_state: 输入数据
            config: 配置
            
        Yields:
            流式输出结果
        """
        # 由于是简单实现，这里直接返回invoke的结果
        yield self.invoke(input_state, config)
