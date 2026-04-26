#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
情绪分析功能测试脚本

本脚本测试视频情绪分析功能，包括：
1. 分析视频中的情绪变化
2. 获取支持的情绪类型列表
3. 测试OpenCV可用性和备用实现
"""

import os
import sys
import unittest
import tempfile
from typing import Dict, List, Tuple

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from hengline.tool.emotion_analysis import EmotionAnalyzer, analyze_emotions, get_supported_emotions, get_emotion_display_name


class TestEmotionAnalysis(unittest.TestCase):
    """测试情绪分析功能"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.analyzer = EmotionAnalyzer()
        self.test_video_path = "test_video.mp4"  # 假设的测试视频路径
        
        # 创建临时视频文件用于测试
        self.temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
        self.temp_video.close()
        self.temp_video_path = self.temp_video.name
        
        # 创建一个空文件作为测试视频
        with open(self.temp_video_path, 'wb') as f:
            f.write(b'')  # 空视频文件，仅用于测试接口
    
    def tearDown(self):
        """测试后的清理工作"""
        # 删除临时文件
        if os.path.exists(self.temp_video_path):
            os.unlink(self.temp_video_path)
    
    def test_get_supported_emotions(self):
        """测试获取支持的情绪类型列表"""
        print("\n测试获取支持的情绪类型列表...")
        try:
            supported_emotions = get_supported_emotions()
            print(f"支持的情绪类型: {supported_emotions}")
            self.assertIsInstance(supported_emotions, list)
            self.assertTrue(len(supported_emotions) > 0)
            
            # 检查基本情绪是否都在列表中
            basic_emotions = ['happy', 'sad', 'angry', 'fear', 'surprise', 'disgust', 'neutral']
            for emotion in basic_emotions:
                self.assertIn(emotion, supported_emotions)
        except Exception as e:
            print(f"测试失败: {str(e)}")
            self.fail(f"获取支持的情绪类型失败: {str(e)}")
    
    def test_get_emotion_display_name(self):
        """测试获取情绪类型的中文显示名称"""
        print("\n测试获取情绪类型的中文显示名称...")
        try:
            # 测试基本情绪的中文名称
            test_cases = {
                'happy': '开心',
                'sad': '悲伤',
                'angry': '愤怒',
                'fear': '恐惧',
                'surprise': '惊讶',
                'disgust': '厌恶',
                'neutral': '中性'
            }
            
            for emotion, expected_name in test_cases.items():
                display_name = get_emotion_display_name(emotion)
                print(f"{emotion} -> {display_name}")
                self.assertEqual(display_name, expected_name)
            
            # 测试不存在的情绪类型
            unknown_emotion = 'unknown_emotion'
            self.assertEqual(get_emotion_display_name(unknown_emotion), unknown_emotion)
        except Exception as e:
            print(f"测试失败: {str(e)}")
            self.fail(f"获取情绪显示名称失败: {str(e)}")
    
    def test_analyze_emotions_function(self):
        """测试analyze_emotions函数接口"""
        print("\n测试analyze_emotions函数接口...")
        try:
            results = analyze_emotions(self.temp_video_path)
            print(f"情绪分析结果: {results}")
            
            # 验证结果格式
            self.assertIsInstance(results, dict)
            
            # 检查结果中的情绪类型是否都是字符串
            for emotion, segments in results.items():
                self.assertIsInstance(emotion, str)
                self.assertIsInstance(segments, list)
                
                # 检查时间段格式
                for start, end in segments:
                    self.assertIsInstance(start, (int, float))
                    self.assertIsInstance(end, (int, float))
                    self.assertTrue(end > start)  # 结束时间应该大于开始时间
        except Exception as e:
            print(f"测试失败: {str(e)}")
            self.fail(f"analyze_emotions函数测试失败: {str(e)}")
    
    def test_emotion_analyzer_class(self):
        """测试EmotionAnalyzer类的基本功能"""
        print("\n测试EmotionAnalyzer类的基本功能...")
        try:
            # 测试分析器初始化
            self.assertTrue(hasattr(self.analyzer, 'analyze'))
            self.assertTrue(hasattr(self.analyzer, '_is_opencv_available'))
            
            # 测试OpenCV可用性检查
            print(f"OpenCV是否可用: {self.analyzer._is_opencv_available()}")
            
            # 测试情绪分析方法
            results = self.analyzer.analyze(self.temp_video_path)
            print(f"EmotionAnalyzer类分析结果: {results}")
            self.assertIsInstance(results, dict)
        except Exception as e:
            print(f"测试失败: {str(e)}")
            self.fail(f"EmotionAnalyzer类测试失败: {str(e)}")
    
    def test_edge_cases(self):
        """测试边缘情况"""
        print("\n测试边缘情况...")
        try:
            # 测试不存在的视频文件
            with self.assertRaises(Exception):
                analyze_emotions("non_existent_video.mp4")
            
            print("边缘情况测试通过")
        except Exception as e:
            print(f"边缘情况测试失败: {str(e)}")
            self.fail(f"边缘情况测试失败: {str(e)}")
    
    def test_custom_config(self):
        """测试自定义配置参数"""
        print("\n测试自定义配置参数...")
        try:
            # 使用自定义配置创建分析器
            custom_config = {
                'frame_sample_rate': 2,
                'confidence_threshold': 0.6,
                'emotion_hold_time': 1.0
            }
            
            custom_analyzer = EmotionAnalyzer(config=custom_config)
            
            # 验证配置是否生效
            self.assertEqual(custom_analyzer.config['frame_sample_rate'], 2)
            self.assertEqual(custom_analyzer.config['confidence_threshold'], 0.6)
            self.assertEqual(custom_analyzer.config['emotion_hold_time'], 1.0)
            
            print("自定义配置测试通过")
        except Exception as e:
            print(f"自定义配置测试失败: {str(e)}")
            self.fail(f"自定义配置测试失败: {str(e)}")


def run_tests():
    """运行所有测试"""
    print("开始测试情绪分析功能...")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    print("\n情绪分析功能测试完成！")


if __name__ == "__main__":
    run_tests()