#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
物体检测功能测试脚本

本脚本测试视频物体检测功能，包括：
1. 检测视频中的物体出现时间段
2. 获取支持的物体类型列表
3. 测试OpenCV可用性和备用实现
"""

import os
import sys
import unittest
import tempfile
from typing import Dict, List, Tuple

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from hengline.tool.object_detection import ObjectDetector, detect_objects, get_supported_object_types


class TestObjectDetection(unittest.TestCase):
    """测试物体检测功能"""
    
    def setUp(self):
        """测试前的准备工作"""
        self.detector = ObjectDetector()
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
    
    def test_get_supported_object_types(self):
        """测试获取支持的物体类型列表"""
        print("\n测试获取支持的物体类型列表...")
        try:
            supported_objects = get_supported_object_types()
            print(f"支持的物体类型: {supported_objects}")
            self.assertIsInstance(supported_objects, list)
            self.assertTrue(len(supported_objects) > 0)
        except Exception as e:
            print(f"测试失败: {str(e)}")
            self.fail(f"获取支持的物体类型失败: {str(e)}")
    
    def test_detect_objects_function(self):
        """测试detect_objects函数接口"""
        print("\n测试detect_objects函数接口...")
        try:
            # 测试一些常见物体
            test_objects = ["person", "car", "bicycle"]
            results = detect_objects(self.temp_video_path, test_objects)
            print(f"物体检测结果: {results}")
            
            # 验证结果格式
            self.assertIsInstance(results, dict)
            for obj in test_objects:
                self.assertIn(obj, results)
                self.assertIsInstance(results[obj], list)
        except Exception as e:
            print(f"测试失败: {str(e)}")
            self.fail(f"detect_objects函数测试失败: {str(e)}")
    
    def test_object_detector_class(self):
        """测试ObjectDetector类的基本功能"""
        print("\n测试ObjectDetector类的基本功能...")
        try:
            # 测试检测器初始化
            self.assertTrue(hasattr(self.detector, 'detect'))
            self.assertTrue(hasattr(self.detector, '_is_opencv_available'))
            
            # 测试OpenCV可用性检查
            print(f"OpenCV是否可用: {self.detector._is_opencv_available()}")
            
            # 测试物体检测方法
            test_objects = ["dog", "cat"]
            results = self.detector.detect(self.temp_video_path, test_objects)
            print(f"ObjectDetector类检测结果: {results}")
            self.assertIsInstance(results, dict)
        except Exception as e:
            print(f"测试失败: {str(e)}")
            self.fail(f"ObjectDetector类测试失败: {str(e)}")
    
    def test_edge_cases(self):
        """测试边缘情况"""
        print("\n测试边缘情况...")
        try:
            # 测试空物体列表
            results = detect_objects(self.temp_video_path, [])
            self.assertEqual(results, {})
            
            # 测试不存在的视频文件
            with self.assertRaises(Exception):
                detect_objects("non_existent_video.mp4", ["person"])
            
            print("边缘情况测试通过")
        except Exception as e:
            print(f"边缘情况测试失败: {str(e)}")
            self.fail(f"边缘情况测试失败: {str(e)}")


def run_tests():
    """运行所有测试"""
    print("开始测试物体检测功能...")
    unittest.main(argv=['first-arg-is-ignored'], exit=False)
    print("\n物体检测功能测试完成！")


if __name__ == "__main__":
    run_tests()