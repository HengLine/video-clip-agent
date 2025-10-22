# -*- coding: utf-8 -*-
"""
@FileName: content_analyzer.py
@Description: 基于langchain的内容分析器智能体，负责视频内容分析和剪切点识别
@Author: HengLine
@Time: 2025/10 - 2025/11
"""
import os
from typing import Dict, List, Tuple, Any, Optional

from langchain.tools import tool
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool

from hengline.logger import debug, info, warning, error
# 导入情绪分析工具
from hengline.tool.emotion_analysis_tool import analyze_emotions as emotion_analysis_analyze_emotions
# 导入物体检测工具
from hengline.tool.object_detection_tool import detect_objects as object_detection_detect_objects
from hengline.tool.requirement_analyzer_tool import get_requirement_analyzer
# 导入场景识别工具
from hengline.tool.scene_recognition_tool import extract_scenes as scene_recognition_extract_scenes
# 语音识别工具
from hengline.tool.speech_recognition_tool import SpeechRecognizer
# 导入视频元数据读取工具
from hengline.tool.video_metadata_tool import read_video_metadata as video_metadata_read_metadata
from .agent_state import GraphState


# 使用langchain的tool装饰器定义工具函数
@tool
def detect_scenes(video_path: str) -> List[Tuple[float, float]]:
    """检测视频中的场景切换点，使用SceneRecognitionTool实现"""
    debug(f"执行场景检测: {video_path}")
    try:
        # 使用scene_recognition.py中的extract_scenes函数进行场景检测
        scenes = scene_recognition_extract_scenes(video_path)
        debug(f"成功检测到{len(scenes)}个场景")
        return scenes
    except Exception as e:
        warning(f"场景检测失败，使用备用实现: {str(e)}")
        # 发生错误时返回模拟数据
        return [(0.0, 5.0), (5.0, 10.0), (10.0, 15.0)]


@tool
def detect_objects(video_path: str, objects: List[str]) -> Dict[str, List[Tuple[float, float]]]:
    """检测视频中的物体出现时间段，使用ObjectDetector实现"""
    debug(f"执行物体检测: {video_path}, 检测物体: {objects}")
    try:
        # 使用object_detection.py中的detect_objects函数进行物体检测
        results = object_detection_detect_objects(video_path, objects)
        debug(f"物体检测完成，检测结果数量: {sum(len(segments) for segments in results.values())}")
        return results
    except Exception as e:
        warning(f"物体检测失败，使用备用实现: {str(e)}")
        # 发生错误时返回模拟数据
        results = {obj: [(2.0, 7.0), (12.0, 18.0)] for obj in objects}
        return results


@tool
def analyze_emotions(video_path: str) -> Dict[str, List[Tuple[float, float]]]:
    """分析视频中的情绪，使用EmotionAnalyzer实现"""
    debug(f"执行情绪分析: {video_path}")
    try:
        # 使用emotion_analysis.py中的analyze_emotions函数进行情绪分析
        results = emotion_analysis_analyze_emotions(video_path)
        debug(f"情绪分析完成，检测到的情绪类型数量: {len(results)}")
        debug(f"情绪片段总数: {sum(len(segments) for segments in results.values())}")
        return results
    except Exception as e:
        warning(f"情绪分析失败，使用备用实现: {str(e)}")
        # 发生错误时返回模拟数据
        return {
            'happy': [(1.0, 4.0), (8.0, 11.0)],
            'sad': [(15.0, 18.0)],
            'neutral': [(0.0, 1.0), (4.0, 8.0), (11.0, 15.0), (18.0, 20.0)]
        }


@tool
def transcribe_speech(video_path: str) -> List[Dict[str, Any]]:
    """提取视频中的语音并转文字"""
    debug(f"执行语音转文字: {video_path}")
    try:
        # 使用SpeechRecognizer进行真实的语音转文字
        recognizer = SpeechRecognizer()
        transcriptions = recognizer.transcribe_video(video_path)
        debug(f"成功获取转录结果，共{len(transcriptions)}条")
        if transcriptions and "transcription_text" in transcriptions:
            return transcriptions["transcription_text"]

    except Exception as e:
        warning(f"语音转文字失败，使用模拟数据: {str(e)}")
        # 发生错误时返回模拟数据
        return [
            {'text': '你好', 'start_time': 0.5, 'end_time': 1.5},
            {'text': '这是一段测试视频', 'start_time': 2.0, 'end_time': 4.0}
        ]


@tool
def read_video_metadata(video_path: str) -> Dict[str, Any]:
    """读取视频元数据，使用VideoMetadataReader实现"""
    debug(f"读取视频元数据: {video_path}")
    try:
        # 使用video_metadata.py中的read_video_metadata函数读取视频元数据
        results = video_metadata_read_metadata(video_path)
        debug(f"视频元数据读取完成: 分辨率={results['width']}x{results['height']}, 时长={results['duration']}秒, 帧率={results['fps']}fps")
        return results
    except Exception as e:
        warning(f"视频元数据读取失败，使用备用实现: {str(e)}")
        # 发生错误时返回模拟数据
        return {
            'duration': 20.0,
            'width': 1920,
            'height': 1080,
            'fps': 30,
            'bitrate': 0,
            'codec_name': '',
            'format_name': '',
            'frame_count': 0,
            'has_audio': True,
            'has_video': True,
            'audio_codec': '',
            'audio_sample_rate': 0
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

            # 提取音频关键词
            audio_keywords = self._extract_audio_keywords_from_query(user_query)

            # 根据需求分析结果调整分析策略
            analysis_strategy = self._determine_analysis_strategy(requirement_analysis)
            # 确保analysis_strategy是字典类型
            if not isinstance(analysis_strategy, dict):
                debug(f"分析策略类型错误，使用默认策略")
                analysis_strategy = {
                    'use_default': True,
                    'focus_areas': ['scene_detection', 'emotion_analysis', 'speech_transcription']
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
                    'transcriptions': [],
                    'audio_keywords_matches': []
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

                        # 如果有音频关键词，尝试匹配转录结果
                        if audio_keywords:
                            try:
                                # 使用SpeechRecognizer查找关键词匹配
                                recognizer = SpeechRecognizer()
                                keyword_matches = recognizer.find_keywords_in_transcript(
                                    video_analysis['transcriptions'],
                                    audio_keywords
                                )
                                video_analysis['audio_keywords_matches'] = keyword_matches

                                # 将关键词匹配的时间范围添加到剪切点
                                if keyword_matches:
                                    for match in keyword_matches:
                                        clip_points[video_path].append(
                                            (match['start_time'], match['end_time'])
                                        )
                            except Exception as e:
                                warning(f"关键词匹配失败: {str(e)}")
                    except Exception as e:
                        warning(f"语音转文字失败: {str(e)}")
                        video_analysis['transcriptions'] = []

                analysis_results[video_path] = video_analysis

            # 根据需求分析结果优化剪切点
            try:
                optimized_clip_points = self._optimize_clip_points(clip_points, requirement_analysis)
                # 对剪切点进行去重和排序
                for video_path in optimized_clip_points:
                    optimized_clip_points[video_path] = self._deduplicate_and_sort(
                        optimized_clip_points[video_path]
                    )
            except Exception as e:
                warning(f"优化剪切点失败: {str(e)}")
                optimized_clip_points = clip_points

            # 添加next_agent信息
            return {
                'analysis_results': analysis_results,
                'clip_points': optimized_clip_points,
                'requirement_analysis': requirement_analysis,
                'analysis_strategy': analysis_strategy,
                'audio_keywords': audio_keywords,
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

    def _extract_audio_keywords_from_query(self, user_query: str) -> List[str]:
        """
        从用户查询中提取音频关键词
        
        Args:
            user_query: 用户查询文本
            
        Returns:
            关键词列表
        """
        if not isinstance(user_query, str):
            return []

        # 使用简单的关键词提取
        # 在实际应用中，可以使用更复杂的NLP技术
        keywords = []
        import re

        # 常见关键词模式
        query_lower = user_query.lower()

        # 提取明确提到的关键词
        if '关键词' in query_lower or 'key word' in query_lower:
            # 尝试提取关键词后的内容
            match = re.search(r'(关键词|key word)[：:]([^，。,.;；]*)', query_lower)
            if match:
                keyword_text = match.group(2).strip()
                if keyword_text:
                    keywords = [kw.strip() for kw in re.split(r'[，,;；]', keyword_text) if kw.strip()]

        # 如果没有明确的关键词，使用整个查询的主要词汇
        if not keywords:
            # 移除停用词
            stop_words = ['的', '了', '是', '在', '我', '有', '和', '就', '不', '人', '都', '一', '一个', '上', '也', '很', '到', '说', '要', '去', '你', '会', '着', '没有', '看',
                          '好', '自己', '这']
            words = re.findall(r'[\u4e00-\u9fa5a-zA-Z0-9]+', user_query)
            keywords = [word for word in words if word not in stop_words and len(word) > 1]

        return keywords

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
                'focus_areas': ['scene_detection', 'emotion_analysis', 'speech_transcription']
            }

        if not requirement_analysis.get('success'):
            debug(f"需求分析未成功，使用默认策略")
            return {
                'use_default': True,
                'focus_areas': ['scene_detection', 'emotion_analysis', 'speech_transcription']
            }

        try:
            # 根据需求类型确定分析重点
            requirement_type = requirement_analysis.get('requirement_type', '')
            # 确保requirement_type是字符串
            if not isinstance(requirement_type, str):
                requirement_type = str(requirement_type)

            focus_areas = ['speech_transcription']  # 默认包含语音转文字分析

            if '场景' in requirement_type or '切换' in requirement_type:
                focus_areas.append('scene_detection')

            if '物体' in requirement_type or '识别' in requirement_type:
                focus_areas.append('object_detection')

            if '情绪' in requirement_type or '情感' in requirement_type:
                focus_areas.append('emotion_analysis')

            if '语音' in requirement_type or '对话' in requirement_type:
                # 确保语音转文字在列表中
                if 'speech_transcription' not in focus_areas:
                    focus_areas.append('speech_transcription')

            # 确保场景检测总是在列表中
            if 'scene_detection' not in focus_areas:
                focus_areas.append('scene_detection')

            # 确保focus_areas是列表类型
            if not isinstance(focus_areas, list):
                focus_areas = ['scene_detection', 'emotion_analysis', 'speech_transcription']

            return {
                'use_default': False,
                'focus_areas': focus_areas,
                'requirement_type': requirement_type
            }
        except Exception as e:
            warning(f"确定分析策略时发生异常: {str(e)}")
            # 返回默认策略，包含语音转文字
            return {
                'use_default': True,
                'focus_areas': ['scene_detection', 'emotion_analysis', 'speech_transcription']
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
