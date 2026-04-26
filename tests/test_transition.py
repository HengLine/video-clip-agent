#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试视频转场效果
"""
import os
import sys
import time

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.ffmpeg_utils import FFmpegUtils

def test_transition_effect():
    """
    测试视频转场效果
    """
    # 示例视频路径（需要确保这些文件存在）
    # 你可以修改为实际存在的视频文件路径
    video_paths = [
        # 请替换为实际的视频文件路径
        "path_to_video1.mp4",
        "path_to_video2.mp4"
    ]
    
    # 检查视频文件是否存在
    valid_videos = []
    for path in video_paths:
        if os.path.exists(path):
            valid_videos.append(path)
        else:
            print(f"警告：视频文件不存在: {path}")
    
    # 如果没有有效的视频文件，尝试查找output目录中的视频
    if len(valid_videos) < 2:
        print("正在寻找可用的测试视频...")
        output_dir = "output"
        if os.path.exists(output_dir):
            for file in os.listdir(output_dir):
                if file.endswith(".mp4"):
                    file_path = os.path.join(output_dir, file)
                    valid_videos.append(file_path)
                    print(f"找到测试视频: {file_path}")
                    if len(valid_videos) >= 2:
                        break
    
    if len(valid_videos) < 2:
        print("错误：找不到足够的视频文件进行转场测试")
        print("请确保至少有两个视频文件用于测试")
        return False
    
    # 使用前两个找到的视频
    valid_videos = valid_videos[:2]
    print(f"\n使用以下视频进行测试:")
    for i, path in enumerate(valid_videos):
        print(f"{i+1}. {path}")
    
    # 生成输出文件名
    timestamp = int(time.time())
    output_path = f"test_transition_{timestamp}.mp4"
    
    # 配置转场参数
    config = {
        'transition': {
            'enabled': True,
            'type': 'fade',
            'duration': 1.0
        },
        'width': 1280,
        'height': 720,
        'resize_mode': 'fit',
        'codec': 'libx264',
        'preset': 'medium',
        'crf': 23,
        'framerate': 30,
        'audio_bitrate': '192k'
    }
    
    print(f"\n开始测试转场效果...")
    print(f"输出文件: {output_path}")
    print(f"转场配置: {config['transition']}")
    
    # 执行转场测试
    try:
        result = FFmpegUtils.render_video(valid_videos, output_path, config)
        
        if os.path.exists(result) and os.path.getsize(result) > 0:
            print(f"\n✓ 转场测试成功完成!")
            print(f"输出文件: {result}")
            print(f"文件大小: {os.path.getsize(result) / (1024*1024):.2f} MB")
            return True
        else:
            print(f"\n✗ 转场测试失败: 输出文件不存在或为空")
            return False
    except Exception as e:
        print(f"\n✗ 转场测试异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """
    主函数
    """
    print("=" * 60)
    print("视频转场效果测试工具")
    print("=" * 60)
    
    # 运行测试
    success = test_transition_effect()
    
    if success:
        print("\n测试完成，转场效果已应用。请检查输出文件验证效果。")
    else:
        print("\n测试失败，请检查日志和配置。")
    
    print("\n提示：")
    print("1. 如果测试失败，请检查FFmpeg是否支持xfade滤镜")
    print("2. 尝试更新到最新版本的FFmpeg")
    print("3. 检查视频文件格式是否兼容")

if __name__ == "__main__":
    main()