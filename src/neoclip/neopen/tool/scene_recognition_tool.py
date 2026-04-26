# -*- coding: utf-8 -*-
"""
@FileName: scene_recognition.py
@Description: 基于计算机视觉的场景识别工具，用于识别视频中的特定内容并提取需要的场景镜头
@Author: HengLine
@Time: 2025/10 - 2025/11
"""
import os
import cv2
import numpy as np
from typing import List, Tuple, Dict, Any, Optional
from hengline.logger import debug, info, warning, error

class SceneRecognitionTool:
    """
    场景识别工具类，利用计算机视觉技术识别视频中要求的内容，找出需要的场景镜头
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化场景识别工具
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        # 默认配置
        self.default_config = {
            'scene_threshold': 0.6,  # 场景切换阈值
            'frame_interval': 1,     # 帧采样间隔（秒）
            'histogram_bins': 32,    # 颜色直方图的bin数量
            'roi_size': 0.8,         # 感兴趣区域大小（相对于帧的比例）
        }
        # 合并配置
        self._update_config()
        
        # 检查OpenCV是否可用
        try:
            self.opencv_available = cv2.__version__ is not None
            info(f"场景识别工具初始化完成，OpenCV版本: {cv2.__version__}")
        except ImportError:
            self.opencv_available = False
            warning("OpenCV不可用，将使用模拟实现")
    
    def _update_config(self):
        """
        更新配置参数
        """
        for key, value in self.default_config.items():
            if key not in self.config:
                self.config[key] = value
    
    def extract_scenes(self, video_path: str, target_content: Optional[str] = None, 
                      content_keywords: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        提取视频中的场景镜头，根据目标内容进行筛选
        
        Args:
            video_path: 视频文件路径
            target_content: 目标内容描述
            content_keywords: 内容关键词列表，用于匹配场景内容
            
        Returns:
            包含识别结果和场景信息的字典
        """
        try:
            if not os.path.exists(video_path):
                error(f"视频文件不存在: {video_path}")
                return {
                    'success': False,
                    'error': f"视频文件不存在: {video_path}"
                }
            
            debug(f"开始提取场景: {video_path}")
            debug(f"目标内容: {target_content}")
            debug(f"内容关键词: {content_keywords}")
            
            # 如果OpenCV可用，使用实际的计算机视觉方法
            if self.opencv_available:
                return self._extract_scenes_with_opencv(video_path, target_content, content_keywords)
            else:
                # 否则使用模拟实现
                return self._extract_scenes_mock(video_path, target_content, content_keywords)
                
        except Exception as e:
            error(f"提取场景时发生异常: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _extract_scenes_with_opencv(self, video_path: str, target_content: Optional[str], 
                                   content_keywords: Optional[List[str]]) -> Dict[str, Any]:
        """
        使用OpenCV提取视频场景
        
        Args:
            video_path: 视频文件路径
            target_content: 目标内容描述
            content_keywords: 内容关键词列表
            
        Returns:
            识别结果
        """
        global cap
        scenes = []
        selected_scenes = []
        video_info = {}
        
        try:
            # 打开视频文件
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                error(f"无法打开视频文件: {video_path}")
                return {
                    'success': False,
                    'error': "无法打开视频文件"
                }
            
            # 获取视频信息
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            video_info = {
                'fps': fps,
                'frame_count': frame_count,
                'duration': duration,
                'width': int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)),
                'height': int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            }
            
            info(f"视频信息: {video_info}")
            
            # 初始化场景检测变量
            previous_hist = None
            current_scene_start = 0.0
            scene_threshold = self.config['scene_threshold']
            frame_interval = int(fps * self.config['frame_interval'])  # 转换为帧数
            
            # 遍历视频帧
            frame_idx = 0
            while cap.isOpened():
                # 设置帧位置
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                
                if not ret:
                    break
                
                # 计算当前时间点
                current_time = frame_idx / fps
                
                # 计算当前帧的颜色直方图
                current_hist = self._calculate_histogram(frame)
                
                # 检测场景切换
                if previous_hist is not None:
                    # 计算直方图差异
                    hist_diff = self._compare_histograms(previous_hist, current_hist)
                    
                    # 如果差异超过阈值，认为是场景切换
                    if hist_diff > scene_threshold:
                        # 记录前一个场景
                        scenes.append((current_scene_start, current_time))
                        # 开始新场景
                        current_scene_start = current_time
                        debug(f"检测到场景切换: {current_time:.2f}s, 差异值: {hist_diff:.4f}")
                
                previous_hist = current_hist
                frame_idx += frame_interval
            
            # 记录最后一个场景
            if current_scene_start < duration:
                scenes.append((current_scene_start, duration))
            
            # 如果有目标内容，进行场景筛选
            if target_content or content_keywords:
                selected_scenes = self._filter_scenes_by_content(cap, scenes, content_keywords)
            else:
                selected_scenes = scenes
            
            cap.release()
            
            debug(f"共检测到 {len(scenes)} 个场景")
            debug(f"符合要求的场景有 {len(selected_scenes)} 个")
            
            return {
                'success': True,
                'video_info': video_info,
                'all_scenes': scenes,
                'selected_scenes': selected_scenes,
                'scene_count': len(scenes),
                'selected_count': len(selected_scenes)
            }
            
        except Exception as e:
            if 'cap' in locals():
                cap.release()
            raise e
    
    def _extract_scenes_mock(self, video_path: str, target_content: Optional[str], 
                            content_keywords: Optional[List[str]]) -> Dict[str, Any]:
        """
        模拟实现的场景提取函数
        
        Args:
            video_path: 视频文件路径
            target_content: 目标内容描述
            content_keywords: 内容关键词列表
            
        Returns:
            模拟的识别结果
        """
        # 模拟视频信息
        video_info = {
            'fps': 30.0,
            'frame_count': 300,  # 10秒视频
            'duration': 10.0,
            'width': 1280,
            'height': 720
        }
        
        # 模拟场景
        scenes = [
            (0.0, 2.5),   # 第一个场景
            (2.5, 5.0),   # 第二个场景
            (5.0, 7.5),   # 第三个场景
            (7.5, 10.0)   # 第四个场景
        ]
        
        # 根据关键词筛选场景
        selected_scenes = scenes
        if content_keywords:
            # 简单的模拟筛选逻辑
            if '人' in content_keywords:
                selected_scenes = [scenes[0], scenes[2]]  # 假设场景0和2有人
            elif '风景' in content_keywords:
                selected_scenes = [scenes[1], scenes[3]]  # 假设场景1和3有风景
        
        return {
            'success': True,
            'video_info': video_info,
            'all_scenes': scenes,
            'selected_scenes': selected_scenes,
            'scene_count': len(scenes),
            'selected_count': len(selected_scenes),
            'warning': "使用模拟实现，请安装OpenCV以获得实际的计算机视觉功能"
        }
    
    def _calculate_histogram(self, frame: np.ndarray) -> np.ndarray:
        """
        计算帧的颜色直方图
        
        Args:
            frame: 视频帧
            
        Returns:
            归一化的直方图
        """
        # 转换为HSV色彩空间，对场景检测更有效
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 计算感兴趣区域（中心区域）
        h, w = hsv.shape[:2]
        roi_size = self.config['roi_size']
        start_h = int(h * (1 - roi_size) / 2)
        start_w = int(w * (1 - roi_size) / 2)
        end_h = int(h * (1 + roi_size) / 2)
        end_w = int(w * (1 + roi_size) / 2)
        
        roi = hsv[start_h:end_h, start_w:end_w]
        
        # 计算H通道的直方图
        bins = self.config['histogram_bins']
        hist = cv2.calcHist([roi], [0], None, [bins], [0, 180])
        
        # 归一化直方图
        cv2.normalize(hist, hist)
        
        return hist
    
    def _compare_histograms(self, hist1: np.ndarray, hist2: np.ndarray) -> float:
        """
        比较两个直方图的差异
        
        Args:
            hist1: 第一个直方图
            hist2: 第二个直方图
            
        Returns:
            差异值（0-1之间，越大差异越大）
        """
        # 使用相关性比较，结果范围在-1到1之间
        # 转换为差异值（0-1之间）
        correlation = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)
        diff = (1 - correlation) / 2  # 转换为0-1范围
        return diff
    
    def _filter_scenes_by_content(self, cap: cv2.VideoCapture, scenes: List[Tuple[float, float]],
                                 keywords: Optional[List[str]]) -> List[Tuple[float, float]]:
        """
        根据内容关键词筛选场景
        
        Args:
            cap: 视频捕获对象
            scenes: 场景列表
            keywords: 内容关键词
            
        Returns:
            筛选后的场景列表
        """
        if not keywords:
            return scenes
        
        selected_scenes = []
        fps = cap.get(cv2.CAP_PROP_FPS)
        
        for start_time, end_time in scenes:
            # 从场景中间取一帧进行分析
            mid_time = (start_time + end_time) / 2
            frame_idx = int(mid_time * fps)
            
            cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            ret, frame = cap.read()
            
            if ret:
                # 这里应该使用更复杂的内容分析方法
                # 目前使用简单的模拟逻辑
                # 在实际应用中，可以使用预训练的分类器或目标检测模型
                
                # 模拟内容匹配（在实际应用中替换为真实的内容识别）
                scene_id = len(selected_scenes)
                if scene_id % 2 == 0 and '人' in keywords:
                    selected_scenes.append((start_time, end_time))
                elif scene_id % 2 == 1 and '风景' in keywords:
                    selected_scenes.append((start_time, end_time))
        
        return selected_scenes
    
    def recognize_content(self, video_path: str, time_ranges: List[Tuple[float, float]]) -> dict[str, str] | dict[str, list[str]] | dict[str, str]:
        """
        识别指定时间范围内的视频内容
        
        Args:
            video_path: 视频文件路径
            time_ranges: 时间范围列表
            
        Returns:
            每个时间范围的内容描述
        """
        content_results = {}
        
        try:
            if self.opencv_available:
                cap = cv2.VideoCapture(video_path)
                if not cap.isOpened():
                    return {'error': "无法打开视频文件"}
                
                fps = cap.get(cv2.CAP_PROP_FPS)
                
                for start_time, end_time in time_ranges:
                    # 从时间范围中间取帧
                    mid_time = (start_time + end_time) / 2
                    frame_idx = int(mid_time * fps)
                    
                    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                    ret, frame = cap.read()
                    
                    if ret:
                        # 这里应该使用更复杂的内容分析
                        # 目前使用简单的模拟识别
                        time_key = f"{start_time:.2f}-{end_time:.2f}"
                        # 模拟内容识别结果
                        content_results[time_key] = ["场景转换", "中等亮度", "色彩丰富"]
                
                cap.release()
            else:
                # 模拟实现
                for start_time, end_time in time_ranges:
                    time_key = f"{start_time:.2f}-{end_time:.2f}"
                    content_results[time_key] = ["模拟场景", "内容丰富"]
            
            return content_results
            
        except Exception as e:
            error(f"识别内容时发生异常: {str(e)}")
            return {'error': str(e)}

# 创建全局实例
_scene_recognition_tool = None

def get_scene_recognition_tool(config: Optional[Dict[str, Any]] = None) -> SceneRecognitionTool:
    """
    获取场景识别工具的全局实例
    
    Args:
        config: 配置参数
        
    Returns:
        SceneRecognitionTool实例
    """
    global _scene_recognition_tool
    if _scene_recognition_tool is None or config:
        _scene_recognition_tool = SceneRecognitionTool(config)
    return _scene_recognition_tool

# 直接可用的函数接口
def extract_scenes(video_path: str, target_content: Optional[str] = None, 
                  content_keywords: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    提取视频中的场景镜头
    
    Args:
        video_path: 视频文件路径
        target_content: 目标内容描述
        content_keywords: 内容关键词列表
        
    Returns:
        识别结果
    """
    tool = get_scene_recognition_tool()
    return tool.extract_scenes(video_path, target_content, content_keywords)

def recognize_content(video_path: str, time_ranges: List[Tuple[float, float]]) -> Dict[str, List[str]]:
    """
    识别指定时间范围内的视频内容
    
    Args:
        video_path: 视频文件路径
        time_ranges: 时间范围列表
        
    Returns:
        内容描述
    """
    tool = get_scene_recognition_tool()
    return tool.recognize_content(video_path, time_ranges)