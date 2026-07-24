#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import subprocess
import os
from utils.ffmpeg_env_utils import find_ffmpeg

def test_direct_xfade():
    """直接测试xfade命令"""
    
    ffmpeg_path = find_ffmpeg()
    if not ffmpeg_path:
        print("❌ FFmpeg未找到")
        return
    
    video1 = 'data/output/output_0fa7828d.mp4'
    video2 = 'data/output/output_6de22725.mp4'
    
    if not os.path.exists(video1) or not os.path.exists(video2):
        print("❌ 测试视频不存在")
        return
    
    output_path = 'test_xfade_output.mp4'
    
    # 构建简单的xfade命令
    cmd = [
        ffmpeg_path,
        "-y",
        "-i", video1,
        "-i", video2,
        "-filter_complex", "[0:v]settb=AVTB,fps=30[v1];[1:v]settb=AVTB,fps=30[v2];[v1][v2]xfade=transition=fade:duration=1:offset=15[v]",
        "-map", "[v]",
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "23",
        "-an",  # 暂时禁用音频
        output_path
    ]
    
    print(f"执行命令: {' '.join(cmd)}")
    
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False
    )
    
    print(f"返回码: {result.returncode}")
    print(f"标准输出: {result.stdout}")
    print(f"标准错误: {result.stderr}")
    print(f"输出文件存在: {os.path.exists(output_path)}")
    
    if os.path.exists(output_path):
        os.remove(output_path)

if __name__ == "__main__":
    test_direct_xfade()