#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试视频合并功能，特别是不同比例视频的处理
"""

import os
import sys
import time
from utils.ffmpeg_utils import FFmpegUtils

def test_video_merge():
    """
    测试视频合并功能
    """
    # 获取当前目录
    current_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 用户需要修改的部分：指定两个不同比例的视频文件
    # 请将下面的路径替换为实际的视频文件路径
    video1 = os.path.join(current_dir, "video1.mp4")  # 第一个视频
    video2 = os.path.join(current_dir, "video2.mp4")  # 第二个视频
    
    # 检查视频文件是否存在
    if not os.path.exists(video1):
        print(f"错误: 找不到视频文件 {video1}")
        print("请修改脚本中的视频文件路径")
        return
    
    if not os.path.exists(video2):
        print(f"错误: 找不到视频文件 {video2}")
        print("请修改脚本中的视频文件路径")
        return
    
    # 输出目录
    output_dir = os.path.join(current_dir, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    print("开始测试视频合并功能...")
    print(f"视频1: {video1}")
    print(f"视频2: {video2}")
    
    # 测试不同的缩放模式
    modes = [
        {'name': 'fit', 'desc': '保持原始比例，添加黑边'},  # 默认模式
        {'name': 'fill', 'desc': '保持原始比例，裁剪以填充'}, 
        {'name': 'stretch', 'desc': '拉伸到目标尺寸'}
    ]
    
    for mode_info in modes:
        mode = mode_info['name']
        desc = mode_info['desc']
        
        print(f"\n测试缩放模式: {mode} ({desc})")
        
        # 生成输出文件名
        timestamp = int(time.time())
        output_file = os.path.join(output_dir, f"merged_{mode}_{timestamp}.mp4")
        
        # 配置参数
        config = {
            'width': 1920,         # 输出视频宽度
            'height': 1080,        # 输出视频高度
            'resize_mode': mode,   # 缩放模式
            'codec': 'libx264',    # 编码器
            'preset': 'medium',    # 编码预设
            'crf': 23,             # 质量因子
            'framerate': 30        # 帧率
        }
        
        print(f"配置: {config}")
        print(f"输出文件: {output_file}")
        
        try:
            # 执行合并
            start_time = time.time()
            result = FFmpegUtils.render_video([video1, video2], output_file, config)
            end_time = time.time()
            
            print(f"✓ 合并成功! 耗时: {end_time - start_time:.2f} 秒")
            print(f"结果文件: {result}")
            
            # 验证输出文件是否存在
            if os.path.exists(result) and os.path.getsize(result) > 0:
                print(f"✓ 输出文件验证成功，大小: {os.path.getsize(result) / (1024 * 1024):.2f} MB")
            else:
                print("✗ 输出文件验证失败")
                
        except Exception as e:
            print(f"✗ 合并失败: {str(e)}")
    
    print("\n测试完成! 请检查 output 目录中的合并结果。")
    print("提示: 你可以调整测试脚本中的配置参数来尝试不同的输出效果。")

if __name__ == "__main__":
    test_video_merge()