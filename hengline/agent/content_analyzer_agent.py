# -*- coding: utf-8 -*-
"""
@FileName: content_analyzer.py
@Description: 基于langchain的内容分析器智能体，负责视频内容分析和剪切点识别
@Author: HengLine
@Time: 2025/10 - 2025/11
"""
import os
from typing import Dict, List, Tuple, Any, Optional
from langchain_core.runnables import Runnable, chain
from langchain_core.tools import Tool, BaseTool
from langchain.tools import tool
from hengline.logger import debug, info, warning, error
from hengline.tool.requirement_analyzer import RequirementAnalyzer, get_requirement_analyzer
from .agent_state import GraphState

# 使用langchain的tool装饰器定义工具函数
@tool
def detect_scenes(video_path: str) -> List[Tuple[float, float]]:
    """检测视频中的场景切换点"""
    # 这里是示例实现，实际需要调用视频分析库
    debug(f"执行场景检测: {video_path}")
    # 模拟返回一些场景切换点
    return [(0.0, 5.0), (5.0, 10.0), (10.0, 15.0)]

@tool
def detect_objects(video_path: str, objects: List[str]) -> Dict[str, List[Tuple[float, float]]]:
    """检测视频中的物体出现时间段"""
    debug(f"执行物体检测: {video_path}, 检测物体: {objects}")
    # 模拟返回物体检测结果
    results = {obj: [(2.0, 7.0), (12.0, 18.0)] for obj in objects}
    return results

@tool
def analyze_emotions(video_path: str) -> Dict[str, List[Tuple[float, float]]]:
    """分析视频中的情绪"""
    debug(f"执行情绪分析: {video_path}")
    # 模拟返回情绪分析结果
    return {
        'happy': [(1.0, 4.0), (8.0, 11.0)],
        'sad': [(15.0, 18.0)],
        'neutral': [(0.0, 1.0), (4.0, 8.0), (11.0, 15.0), (18.0, 20.0)]
    }

@tool
def transcribe_speech(video_path: str) -> List[Dict[str, Any]]:
    """提取视频中的语音并转文字"""
    debug(f"执行语音转文字: {video_path}")
    # 模拟返回语音转文字结果
    return [
        {'text': '你好', 'start_time': 0.5, 'end_time': 1.5},
        {'text': '这是一段测试视频', 'start_time': 2.0, 'end_time': 4.0}
    ]

@tool
def read_video_metadata(video_path: str) -> Dict[str, Any]:
    """读取视频元数据"""
    debug(f"读取视频元数据: {video_path}")
    # 模拟返回元数据
    return {
        'duration': 20.0,
        'width': 1920,
        'height': 1080,
        'fps': 30
    }

class ContentAnalyzerAgent(Runnable):
    """
    基于langchain的内容分析器智能体，负责视频内容分析和剪切点识别
    实现Runnable接口以支持与langchain生态系统的集成
    """
    def __init__(self):
        self.role = "视频内容分析"
        self.capabilities = ["场景检测", "物体识别", "情绪分析", "语音转文字", "元数据读取"]
        # 初始化需求分析器
        self.requirement_analyzer = get_requirement_analyzer()
        info(f"初始化 {self.role} 智能体 (基于langchain实现)，集成需求分析功能")
    
    def get_tools(self) -> list[BaseTool]:
        """
        获取智能体可用的工具列表
        用于与langchain agent和其他组件集成
        """
        return [
            detect_scenes,
            detect_objects,
            analyze_emotions,
            transcribe_speech,
            read_video_metadata
        ]
    
    def analyze_requirement(self, user_query: str) -> Dict[str, Any]:
        """
        分析用户的视频裁剪需求描述
        
        Args:
            user_query: 用户输入的需求描述
            
        Returns:
            包含需求分析结果和建议的字典
        """
        try:
            # 使用需求分析器分析用户输入
            analysis_result = self.requirement_analyzer.analyze(user_query)
            
            # 确保analysis_result是字典类型
            if not isinstance(analysis_result, dict):
                warning(f"需求分析器返回非字典类型结果")
                return {
                    'success': False,
                    'error': '需求分析器返回格式错误'
                }
            
            if analysis_result.get('success'):
                info(f"成功分析用户需求，提供商: {analysis_result.get('provider')}")
                
                # 从分析结果中提取关键信息
                requirement_type = None
                processing_focus = None
                video_config = analysis_result.get('video_config', {})
                
                # 确保video_config是字典类型
                if isinstance(video_config, dict) and 'analysis' in video_config:
                    analysis = video_config['analysis']
                    # 确保analysis是字典类型
                    if isinstance(analysis, dict):
                        requirement_type = analysis.get('需求类型')
                        processing_focus = analysis.get('处理重点')
                
                # 返回结构化的分析结果
                return {
                    'success': True,
                    'requirement_type': requirement_type,
                    'processing_focus': processing_focus,
                    'video_config': video_config,
                    'analysis': analysis_result.get('analysis'),
                    'provider': analysis_result.get('provider')
                }
            else:
                warning(f"需求分析失败: {analysis_result.get('error', '未知错误')}")
                return {
                    'success': False,
                    'error': analysis_result.get('error', '需求分析失败')
                }
                
        except Exception as e:
            error(f"分析用户需求时发生异常: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_videos(self, state: GraphState) -> Dict[str, Any]:
        """
        分析所有视频的内容
        使用langchain的chain装饰器增强功能和错误处理
        """
        try:
            videos = state.get('videos', [])
            user_query = state.get('user_query', '')
            
            # 首先分析用户需求
            requirement_analysis = self.analyze_requirement(user_query)
            
            # 根据需求分析结果调整分析策略
            analysis_strategy = self._determine_analysis_strategy(requirement_analysis)
            # 确保analysis_strategy是字典类型
            if not isinstance(analysis_strategy, dict):
                debug(f"分析策略类型错误，使用默认策略")
                analysis_strategy = {
                    'use_default': True,
                    'focus_areas': ['scene_detection', 'emotion_analysis']
                }
            debug(f"确定的分析策略: {analysis_strategy}")
            
            analysis_results = {}
            clip_points = {}
            
            for video_path in videos:
                if not os.path.exists(video_path):
                    warning(f"视频文件不存在: {video_path}")
                    continue
                    
                # 读取视频元数据
                metadata = read_video_metadata(video_path)
                
                # 根据分析策略执行相应的分析
                video_analysis = {
                    'metadata': metadata,
                    'scenes': [],
                    'objects': {},
                    'emotions': {},
                    'transcriptions': []
                }
                
                # 获取focus_areas，确保它是可迭代的
                focus_areas = analysis_strategy.get('focus_areas', [])
                if not isinstance(focus_areas, list):
                    focus_areas = []
                
                # 场景检测 - 通常总是需要的
                if 'scene_detection' in focus_areas:
                    try:
                        video_analysis['scenes'] = detect_scenes(video_path)
                        clip_points[video_path] = video_analysis['scenes']
                    except Exception as e:
                        warning(f"场景检测失败: {str(e)}")
                        video_analysis['scenes'] = []
                
                # 物体检测
                if 'object_detection' in focus_areas:
                    try:
                        # 从用户需求中提取需要检测的物体
                        objects_to_detect = self._extract_objects_from_query(user_query)
                        if objects_to_detect:
                            video_analysis['objects'] = detect_objects(video_path, objects_to_detect)
                    except Exception as e:
                        warning(f"物体检测失败: {str(e)}")
                        video_analysis['objects'] = {}
                
                # 情绪分析
                if 'emotion_analysis' in focus_areas:
                    try:
                        video_analysis['emotions'] = analyze_emotions(video_path)
                    except Exception as e:
                        warning(f"情绪分析失败: {str(e)}")
                        video_analysis['emotions'] = {}
                
                # 语音转文字
                if 'speech_transcription' in focus_areas:
                    try:
                        video_analysis['transcriptions'] = transcribe_speech(video_path)
                    except Exception as e:
                        warning(f"语音转文字失败: {str(e)}")
                        video_analysis['transcriptions'] = []
                
                analysis_results[video_path] = video_analysis
            
            # 根据需求分析结果优化剪切点
            try:
                optimized_clip_points = self._optimize_clip_points(clip_points, requirement_analysis)
            except Exception as e:
                warning(f"优化剪切点失败: {str(e)}")
                optimized_clip_points = clip_points
            
            # 添加next_agent信息
            return {
                'analysis_results': analysis_results,
                'clip_points': optimized_clip_points,
                'requirement_analysis': requirement_analysis,
                'analysis_strategy': analysis_strategy,
                'next_agent': 'video_editor'
            }
            
        except Exception as e:
            error(f"分析视频内容时发生异常: {str(e)}")
            return {
                'error': str(e),
                'analysis_results': {},
                'clip_points': {},
                'next_agent': 'error_handler'
            }
            
    def _extract_objects_from_query(self, user_query: str) -> List[str]:
        """
        从用户查询中提取需要检测的物体
        
        Args:
            user_query: 用户查询文本
            
        Returns:
            物体名称列表
        """
        # 这里可以使用NLP技术提取物体名称
        # 目前使用简单的关键词匹配
        common_objects = ['人', '车', '猫', '狗', '建筑', '风景', '文字', '屏幕']
        detected_objects = []
        
        for obj in common_objects:
            if obj in user_query:
                detected_objects.append(obj)
        
        return detected_objects
        
    def _optimize_clip_points(self, clip_points: Dict[str, List[Tuple[float, float]]], 
                            requirement_analysis: Dict[str, Any]) -> Dict[str, List[Tuple[float, float]]]:
        """
        根据需求分析结果优化剪切点
        
        Args:
            clip_points: 原始剪切点
            requirement_analysis: 需求分析结果
            
        Returns:
            优化后的剪切点
        """
        # 如果需求分析成功，可以根据需求类型进一步优化剪切点
        if requirement_analysis.get('success'):
            # 这里可以添加更复杂的优化逻辑
            debug(f"根据需求分析结果优化剪切点")
        
        return clip_points
        
    def _determine_analysis_strategy(self, requirement_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        根据需求分析结果确定分析策略
        
        Args:
            requirement_analysis: 需求分析结果
            
        Returns:
            分析策略配置
        """
        # 确保requirement_analysis是字典类型
        if requirement_analysis is None or not isinstance(requirement_analysis, dict):
            debug(f"需求分析结果为None或类型错误，使用默认策略")
            return {
                'use_default': True,
                'focus_areas': ['scene_detection', 'emotion_analysis']
            }
            
        if not requirement_analysis.get('success'):
            debug(f"需求分析未成功，使用默认策略")
            return {
                'use_default': True,
                'focus_areas': ['scene_detection', 'emotion_analysis']
            }
        
        try:
            # 根据需求类型确定分析重点
            requirement_type = requirement_analysis.get('requirement_type', '')
            # 确保requirement_type是字符串
            if not isinstance(requirement_type, str):
                requirement_type = str(requirement_type)
                
            focus_areas = []
            
            if '场景' in requirement_type or '切换' in requirement_type:
                focus_areas.append('scene_detection')
            
            if '物体' in requirement_type or '识别' in requirement_type:
                focus_areas.append('object_detection')
            
            if '情绪' in requirement_type or '情感' in requirement_type:
                focus_areas.append('emotion_analysis')
            
            if '语音' in requirement_type or '对话' in requirement_type:
                focus_areas.append('speech_transcription')
            
            # 确保focus_areas是列表类型
            if not isinstance(focus_areas, list):
                focus_areas = ['scene_detection', 'emotion_analysis']
            elif not focus_areas:
                focus_areas = ['scene_detection', 'emotion_analysis']
            
            return {
                'use_default': False,
                'focus_areas': focus_areas,
                'requirement_type': requirement_type
            }
        except Exception as e:
            warning(f"确定分析策略时发生异常: {str(e)}")
            # 返回默认策略
            return {
                'use_default': True,
                'focus_areas': ['scene_detection', 'emotion_analysis']
            }
    
    def generate_clip_points(self, analysis_data: Dict[str, Any], user_query: str) -> List[Tuple[float, float]]:
        """
        根据分析结果和用户查询生成剪切点
        使用chain装饰器增强功能
        """
        clip_points = []
        user_query_lower = user_query.lower() if isinstance(user_query, str) else ''
        
        # 确保analysis_data是字典类型
        if not isinstance(analysis_data, dict):
            debug(f"分析数据类型错误，返回空剪切点列表")
            return []
        
        try:
            # 基于情绪的剪切点
            emotions = analysis_data.get('emotions', {})
            # 确保emotions是字典类型
            if isinstance(emotions, dict):
                if ('微笑' in user_query or '高兴' in user_query or '开心' in user_query_lower) and 'happy' in emotions:
                    happy_points = emotions.get('happy', [])
                    # 确保happy_points是可迭代的
                    if isinstance(happy_points, list):
                        clip_points.extend(happy_points)
            
            # 基于物体的剪切点
            objects = analysis_data.get('objects', {})
            # 确保objects是字典类型
            if isinstance(objects, dict):
                # 检查person
                person_points = objects.get('person', [])
                if isinstance(person_points, list):
                    clip_points.extend(person_points)
                
                # 检查cat
                if ('猫咪' in user_query or '猫' in user_query):
                    cat_points = objects.get('cat', [])
                    if isinstance(cat_points, list):
                        clip_points.extend(cat_points)
                
                # 检查sunset
                if '日落' in user_query:
                    sunset_points = objects.get('sunset', [])
                    if isinstance(sunset_points, list):
                        clip_points.extend(sunset_points)
            
            # 如果没有找到符合条件的剪切点，使用场景检测结果
            if not clip_points:
                scenes = analysis_data.get('scenes', [])
                # 确保scenes是列表类型
                if isinstance(scenes, list):
                    clip_points = scenes
            
            # 去重和排序
            try:
                clip_points = self._deduplicate_and_sort(clip_points)
            except Exception as e:
                warning(f"剪切点去重和排序失败: {str(e)}")
            
            # 过滤短片段
            try:
                clip_points = [(start, end) for start, end in clip_points if isinstance(start, (int, float)) and isinstance(end, (int, float)) and end - start >= 1.0]  # 至少1秒
            except Exception as e:
                warning(f"过滤短片段失败: {str(e)}")
                clip_points = []
            
        except Exception as e:
            warning(f"生成剪切点时发生异常: {str(e)}")
            clip_points = []
        
        return clip_points
    
    @staticmethod
    def _deduplicate_and_sort(intervals: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
        """
        对时间间隔进行去重和合并
        """
        if not intervals:
            return []
        
        # 按开始时间排序
        sorted_intervals = sorted(intervals, key=lambda x: x[0])
        merged = [sorted_intervals[0]]
        
        for current in sorted_intervals[1:]:
            last = merged[-1]
            if current[0] <= last[1]:
                # 有重叠，合并
                new_start = last[0]
                new_end = max(last[1], current[1])
                merged[-1] = (new_start, new_end)
            else:
                merged.append(current)
        
        return merged
    
    def execute(self, state: GraphState) -> GraphState:
        """
        执行内容分析器的主要逻辑
        实现Runnable接口的标准执行方法
        """
        try:
            result = self.analyze_videos(state)
            
            # 更新状态
            updated_state = state.copy()
            updated_state.update(result)
            updated_state['current_agent'] = result.get('next_agent')
            
            return updated_state
        except Exception as e:
            error(f"内容分析器执行出错: {str(e)}")
            updated_state = state.copy()
            updated_state['error'] = f"内容分析器错误: {str(e)}"
            updated_state['current_agent'] = 'error_handler'
            return updated_state
    
    # 实现Runnable接口的invoke方法
    def invoke(self, input_state: Dict[str, Any], config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        实现langchain的Runnable接口
        支持标准的invoke调用模式
        """
        return self.execute(input_state)
    
    # 实现Runnable接口的batch方法，支持批量处理
    def batch(self, inputs: List[Dict[str, Any]], config: Optional[Dict] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        支持批量处理多个视频分析任务
        """
        results = []
        for input_state in inputs:
            results.append(self.execute(input_state))
        return results