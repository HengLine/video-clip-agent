#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试语音识别模块的功能
"""

import os
import sys
import time
from typing import List, Dict, Any, Tuple

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hengline.logger import debug, info, warning, error
from hengline.tool.speech_recognition import SpeechRecognizer
from hengline.tool.scene_recognition import extract_scenes

def test_transcribe_video():
    """
    测试从视频中提取音频并转文字
    """
    print("=== 测试1: 视频音频转文字 ===")
    
    # 这里需要一个测试视频文件
    # 如果没有提供，使用示例路径
    video_path = sys.argv[1] if len(sys.argv) > 1 else "test_video.mp4"
    
    if not os.path.exists(video_path):
        print(f"警告: 测试视频文件不存在: {video_path}")
        print("请提供一个视频文件路径作为命令行参数")
        return None
    
    try:
        recognizer = SpeechRecognizer()
        start_time = time.time()
        transcriptions = recognizer.transcribe_video(video_path)
        end_time = time.time()
        
        print(f"成功识别视频语音，耗时: {end_time - start_time:.2f}秒")
        print(f"识别到 {len(transcriptions)} 条转录结果")
        
        # 打印前5条转录结果
        for i, trans in enumerate(transcriptions[:5], 1):
            print(f"[{i}] {trans['start_time']:.2f}s - {trans['end_time']:.2f}s: {trans['text']}")
        
        if len(transcriptions) > 5:
            print(f"... 以及 {len(transcriptions) - 5} 条更多结果")
        
        return transcriptions
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return None

def test_keyword_matching(transcriptions: List[Dict[str, Any]]):
    """
    测试关键词匹配功能
    """
    if not transcriptions:
        print("无法测试关键词匹配，转录结果为空")
        return None
    
    print("\n=== 测试2: 关键词匹配 ===")
    
    # 测试关键词
    test_keywords = ["测试", "视频", "分析"]
    print(f"测试关键词: {', '.join(test_keywords)}")
    
    try:
        recognizer = SpeechRecognizer()
        matches = recognizer.find_keywords_in_transcript(transcriptions, test_keywords)
        
        print(f"找到 {len(matches)} 个关键词匹配")
        
        for i, match in enumerate(matches, 1):
            print(f"[{i}] 关键词 '{match['keyword']}' 在 {match['start_time']:.2f}s - {match['end_time']:.2f}s 匹配: '{match['text']}'")
        
        return matches
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return None

def test_scene_recognition_with_audio():
    """
    测试集成了语音识别的场景识别功能
    """
    print("\n=== 测试3: 集成语音识别的场景识别 ===")
    
    # 使用与之前相同的视频文件
    video_path = sys.argv[1] if len(sys.argv) > 1 else "test_video.mp4"
    
    if not os.path.exists(video_path):
        print(f"警告: 测试视频文件不存在: {video_path}")
        return None
    
    # 测试关键词
    audio_keywords = ["测试", "视频", "分析"]
    print(f"音频关键词: {', '.join(audio_keywords)}")
    
    try:
        start_time = time.time()
        scenes = extract_scenes(
            video_path=video_path,
            audio_keywords=audio_keywords,
            use_audio=True
        )
        end_time = time.time()
        
        print(f"场景识别完成，耗时: {end_time - start_time:.2f}秒")
        print(f"识别到 {len(scenes)} 个场景")
        
        for i, (start, end) in enumerate(scenes, 1):
            duration = end - start
            print(f"[{i}] {start:.2f}s - {end:.2f}s (持续 {duration:.2f}s)")
        
        return scenes
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return None

def test_subtitle_generation():
    """
    测试字幕文件生成功能
    """
    print("\n=== 测试4: 字幕文件生成 ===")
    
    # 使用与之前相同的视频文件
    video_path = sys.argv[1] if len(sys.argv) > 1 else "test_video.mp4"
    
    if not os.path.exists(video_path):
        print(f"警告: 测试视频文件不存在: {video_path}")
        return False
    
    try:
        recognizer = SpeechRecognizer()
        
        # 生成SRT字幕
        srt_path = "test_subtitles.srt"
        recognizer.generate_subtitle_file(video_path, srt_path, format="srt")
        print(f"成功生成SRT字幕: {srt_path}")
        
        # 生成VTT字幕
        vtt_path = "test_subtitles.vtt"
        recognizer.generate_subtitle_file(video_path, vtt_path, format="vtt")
        print(f"成功生成VTT字幕: {vtt_path}")
        
        return True
    except Exception as e:
        print(f"测试失败: {str(e)}")
        return False

def main():
    """
    主测试函数
    """
    print("开始语音识别模块测试...")
    
    # 测试1: 视频音频转文字
    transcriptions = test_transcribe_video()
    
    # 测试2: 关键词匹配
    if transcriptions:
        test_keyword_matching(transcriptions)
    
    # 测试3: 集成语音识别的场景识别
    test_scene_recognition_with_audio()
    
    # 测试4: 字幕文件生成
    test_subtitle_generation()
    
    print("\n测试完成!")

if __name__ == "__main__":
    main()