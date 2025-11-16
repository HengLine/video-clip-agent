# -*- coding: utf-8 -*-
"""
@FileName: test_scene_recognition.py
@Description: 测试场景识别工具的功能
@Author: HengLine
@Time: 2025/10 - 2025/11
"""
import os
import sys
import unittest
from typing import List, Dict, Any, Tuple

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hengline.tool.scene_recognition import (
    SceneRecognitionTool, 
    get_scene_recognition_tool, 
    extract_scenes, 
    recognize_content
)

class TestSceneRecognition(unittest.TestCase):
    """
    场景识别工具测试类
    """
    
    def setUp(self):
        """
        测试前的设置
        """
        # 初始化场景识别工具
        self.scene_tool = SceneRecognitionTool()
        # 使用模拟视频路径进行测试
        self.test_video_path = "test_video.mp4"
        
        # 模拟一个简单的视频文件用于测试
        # 如果文件不存在，创建一个空文件
        if not os.path.exists(self.test_video_path):
            with open(self.test_video_path, 'w') as f:
                f.write("This is a test video file")
    
    def tearDown(self):
        """
        测试后的清理
        """
        # 移除测试文件
        if os.path.exists(self.test_video_path):
            try:
                os.remove(self.test_video_path)
            except:
                pass
    
    def test_init(self):
        """
        测试工具初始化
        """
        # 测试默认初始化
        tool1 = SceneRecognitionTool()
        self.assertIsInstance(tool1, SceneRecognitionTool)
        self.assertIn('scene_threshold', tool1.config)
        self.assertEqual(tool1.config['scene_threshold'], 0.6)
        
        # 测试带配置初始化
        custom_config = {
            'scene_threshold': 0.7,
            'frame_interval': 2
        }
        tool2 = SceneRecognitionTool(custom_config)
        self.assertEqual(tool2.config['scene_threshold'], 0.7)
        self.assertEqual(tool2.config['frame_interval'], 2)
        # 确保其他默认配置项仍然存在
        self.assertIn('histogram_bins', tool2.config)
    
    def test_get_instance(self):
        """
        测试获取全局实例
        """
        tool1 = get_scene_recognition_tool()
        tool2 = get_scene_recognition_tool()
        # 验证返回的是同一个实例
        self.assertIs(tool1, tool2)
        
        # 测试使用新配置获取实例
        custom_config = {'scene_threshold': 0.8}
        tool3 = get_scene_recognition_tool(custom_config)
        self.assertEqual(tool3.config['scene_threshold'], 0.8)
    
    def test_extract_scenes_function(self):
        """
        测试extract_scenes函数接口
        """
        # 使用函数接口
        result = extract_scenes(self.test_video_path)
        
        # 验证返回结果格式
        self.assertIn('success', result)
        self.assertIn('video_info', result)
        self.assertIn('all_scenes', result)
        self.assertIn('selected_scenes', result)
    
    def test_extract_scenes_with_keywords(self):
        """
        测试使用关键词提取场景
        """
        # 使用人物关键词
        result = extract_scenes(self.test_video_path, content_keywords=['人'])
        self.assertIn('selected_scenes', result)
        
        # 使用风景关键词
        result = extract_scenes(self.test_video_path, content_keywords=['风景'])
        self.assertIn('selected_scenes', result)
    
    def test_recognize_content(self):
        """
        测试内容识别功能
        """
        # 定义一些时间范围
        time_ranges = [(0.0, 2.0), (2.0, 4.0)]
        
        # 测试内容识别
        result = recognize_content(self.test_video_path, time_ranges)
        
        # 验证返回结果
        self.assertIsInstance(result, dict)
        # 检查每个时间范围是否有结果
        for start, end in time_ranges:
            time_key = f"{start:.2f}-{end:.2f}"
            self.assertIn(time_key, result)
            self.assertIsInstance(result[time_key], list)
    
    def test_nonexistent_video(self):
        """
        测试处理不存在的视频文件
        """
        nonexistent_path = "nonexistent_video.mp4"
        result = extract_scenes(nonexistent_path)
        
        # 验证错误处理
        self.assertFalse(result['success'])
        self.assertIn('error', result)
    
    def test_tool_class_methods(self):
        """
        测试工具类的主要方法
        """
        # 测试extract_scenes方法
        result = self.scene_tool.extract_scenes(self.test_video_path)
        self.assertIn('success', result)
        
        # 测试recognize_content方法
        time_ranges = [(0.0, 1.0)]
        content_result = self.scene_tool.recognize_content(self.test_video_path, time_ranges)
        self.assertIsInstance(content_result, dict)

if __name__ == '__main__':
    unittest.main()