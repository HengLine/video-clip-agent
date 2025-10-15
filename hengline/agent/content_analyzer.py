# -*- coding: utf-8 -*-
"""
@FileName: content_analyzer.py
@Description: 内容分析器智能体，负责视频内容分析和剪切点识别
@Author: HengLine
@Time: 2025/08 - 2025/11
"""
import os
from typing import Dict, List, Tuple, Any
from hengline.logger import debug, info, warning, error
from .state import GraphState

# 工具类定义
class SceneDetectionTool:
    """场景检测工具"""
    def detect(self, video_path: str) -> List[Tuple[float, float]]:
        """检测视频中的场景切换点"""
        # 这里是示例实现，实际需要调用视频分析库
        debug(f"执行场景检测: {video_path}")
        # 模拟返回一些场景切换点
        return [(0.0, 5.0), (5.0, 10.0), (10.0, 15.0)]

class ObjectDetectionTool:
    """物体检测工具"""
    def detect(self, video_path: str, objects: List[str]) -> Dict[str, List[Tuple[float, float]]]:
        """检测视频中的物体出现时间段"""
        debug(f"执行物体检测: {video_path}, 检测物体: {objects}")
        # 模拟返回物体检测结果
        results = {obj: [(2.0, 7.0), (12.0, 18.0)] for obj in objects}
        return results

class EmotionAnalysisTool:
    """情绪分析工具"""
    def analyze(self, video_path: str) -> Dict[str, List[Tuple[float, float]]]:
        """分析视频中的情绪"""
        debug(f"执行情绪分析: {video_path}")
        # 模拟返回情绪分析结果
        return {
            'happy': [(1.0, 4.0), (8.0, 11.0)],
            'sad': [(15.0, 18.0)],
            'neutral': [(0.0, 1.0), (4.0, 8.0), (11.0, 15.0), (18.0, 20.0)]
        }

class SpeechToTextTool:
    """语音转文字工具"""
    def transcribe(self, video_path: str) -> List[Dict[str, Any]]:
        """提取视频中的语音并转文字"""
        debug(f"执行语音转文字: {video_path}")
        # 模拟返回语音转文字结果
        return [
            {'text': '你好', 'start_time': 0.5, 'end_time': 1.5},
            {'text': '这是一段测试视频', 'start_time': 2.0, 'end_time': 4.0}
        ]

class MetadataReaderTool:
    """元数据读取工具"""
    def read(self, video_path: str) -> Dict[str, Any]:
        """读取视频元数据"""
        debug(f"读取视频元数据: {video_path}")
        # 模拟返回元数据
        return {
            'duration': 20.0,
            'width': 1920,
            'height': 1080,
            'fps': 30
        }

class ContentAnalyzerAgent:
    """
    内容分析器智能体，负责视频内容分析和剪切点识别
    """
    def __init__(self):
        self.role = "视频内容分析"
        self.tools = {
            "scene_detection": SceneDetectionTool(),
            "object_detection": ObjectDetectionTool(),
            "emotion_analysis": EmotionAnalysisTool(),
            "speech_to_text": SpeechToTextTool(),
            "metadata_reader": MetadataReaderTool()
        }
        info(f"初始化 {self.role} 智能体")
    
    def analyze_videos(self, state: GraphState) -> Dict[str, Any]:
        """
        分析所有视频的内容
        """
        try:
            videos = state.get('videos', [])
            user_query = state.get('user_query', '')
            
            analysis_results = {}
            clip_points = {}
            
            for video_path in videos:
                if not os.path.exists(video_path):
                    warning(f"视频文件不存在: {video_path}")
                    continue
                
                debug(f"开始分析视频: {video_path}")
                
                # 读取视频元数据
                metadata = self.tools['metadata_reader'].read(video_path)
                
                # 执行场景检测
                scenes = self.tools['scene_detection'].detect(video_path)
                
                # 根据用户查询决定是否需要其他分析
                detected_objects = []
                if '人物' in user_query or '人' in user_query:
                    detected_objects.append('person')
                if '猫咪' in user_query or '猫' in user_query:
                    detected_objects.append('cat')
                if '日落' in user_query:
                    detected_objects.append('sunset')
                
                object_results = {}
                if detected_objects:
                    object_results = self.tools['object_detection'].detect(video_path, detected_objects)
                
                # 情绪分析
                emotion_results = self.tools['emotion_analysis'].analyze(video_path)
                
                # 语音转文字
                speech_results = self.tools['speech_to_text'].transcribe(video_path)
                
                # 存储分析结果
                analysis_results[video_path] = {
                    'metadata': metadata,
                    'scenes': scenes,
                    'objects': object_results,
                    'emotions': emotion_results,
                    'speech': speech_results
                }
                
                # 生成剪切点（这里是基于简单规则的示例）
                video_clip_points = self.generate_clip_points(analysis_results[video_path], user_query)
                clip_points[video_path] = video_clip_points
            
            return {
                'analysis_results': analysis_results,
                'clip_points': clip_points,
                'next_agent': 'video_editor'
            }
        except Exception as e:
            error(f"视频分析出错: {str(e)}")
            return {
                'error': f"视频分析失败: {str(e)}",
                'next_agent': 'error_handler'
            }
    
    def generate_clip_points(self, analysis_data: Dict[str, Any], user_query: str) -> List[Tuple[float, float]]:
        """
        根据分析结果和用户查询生成剪切点
        """
        clip_points = []
        user_query_lower = user_query.lower()
        
        # 基于情绪的剪切点
        emotions = analysis_data.get('emotions', {})
        if '微笑' in user_query or '高兴' in user_query or '开心' in user_query_lower:
            if 'happy' in emotions:
                clip_points.extend(emotions['happy'])
        
        # 基于物体的剪切点
        objects = analysis_data.get('objects', {})
        if 'person' in objects:
            clip_points.extend(objects['person'])
        if 'cat' in objects and ('猫咪' in user_query or '猫' in user_query):
            clip_points.extend(objects['cat'])
        if 'sunset' in objects and '日落' in user_query:
            clip_points.extend(objects['sunset'])
        
        # 如果没有找到符合条件的剪切点，使用场景检测结果
        if not clip_points:
            scenes = analysis_data.get('scenes', [])
            clip_points = scenes
        
        # 去重和排序
        clip_points = self._deduplicate_and_sort(clip_points)
        
        # 过滤短片段
        clip_points = [(start, end) for start, end in clip_points if end - start >= 1.0]  # 至少1秒
        
        return clip_points
    
    def _deduplicate_and_sort(self, intervals: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
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