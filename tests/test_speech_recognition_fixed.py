#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
语音识别功能测试脚本
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from hengline.tool.speech_recognition_tool import SpeechRecognizer, get_speech_recognizer
from hengline.logger import info, debug, warning, error

def test_speech_recognition_init():
    """测试语音识别器初始化"""
    print("=" * 50)
    print("测试语音识别器初始化")
    print("=" * 50)
    
    try:
        recognizer = get_speech_recognizer()
        info(f"语音识别器初始化成功")
        info(f"可用引擎: {', '.join(recognizer.available_engines)}")
        return True
    except Exception as e:
        error(f"语音识别器初始化失败: {e}")
        return False

def test_audio_file_check():
    """测试音频文件检查"""
    print("\n" + "=" * 50)
    print("测试音频文件检查")
    print("=" * 50)
    
    # 检查是否有测试音频文件
    test_audio_files = [
        "source/audio/1.mp3",
        "source/audio/2.mp3", 
        "source/audio/3.mp3"
    ]
    
    available_files = []
    for file_path in test_audio_files:
        if os.path.exists(file_path):
            available_files.append(file_path)
            info(f"找到测试音频文件: {file_path}")
        else:
            warning(f"测试音频文件不存在: {file_path}")
    
    return available_files

def test_speech_recognition():
    """测试语音识别功能"""
    print("\n" + "=" * 50)
    print("测试语音识别功能")
    print("=" * 50)
    
    recognizer = get_speech_recognizer()
    available_files = test_audio_file_check()
    
    if not available_files:
        warning("没有找到可用的音频文件，跳过语音识别测试")
        return True
    
    # 测试第一个可用的音频文件
    test_file = available_files[0]
    info(f"使用测试文件: {test_file}")
    
    try:
        # 测试音频转录
        result = recognizer.transcribe_audio(test_file, language='zh-CN')
        
        if result:
            info(f"转录成功，识别到 {len(result)} 个片段")
            for i, segment in enumerate(result[:3]):  # 只显示前3个片段
                info(f"片段 {i+1}: {segment.get('text', 'N/A')}")
                info(f"时间: {segment.get('start_time', 0):.2f}s - {segment.get('end_time', 0):.2f}s")
            return True
        else:
            warning("转录结果为空")
            return False
            
    except Exception as e:
        error(f"语音识别测试失败: {e}")
        return False

def test_video_speech_recognition():
    """测试视频语音识别"""
    print("\n" + "=" * 50)
    print("测试视频语音识别")
    print("=" * 50)
    
    # 检查是否有测试视频文件
    test_video_files = [
        "output/test_merge_with_bg_audio.mp4"
    ]
    
    available_video = None
    for file_path in test_video_files:
        if os.path.exists(file_path):
            available_video = file_path
            info(f"找到测试视频文件: {file_path}")
            break
        else:
            warning(f"测试视频文件不存在: {file_path}")
    
    if not available_video:
        warning("没有找到可用的视频文件，跳过视频语音识别测试")
        return True
    
    try:
        recognizer = get_speech_recognizer()
        result = recognizer.transcribe_video(available_video, language='zh-CN')
        
        if result.get('success', False):
            info(f"视频语音转录成功")
            info(f"识别到 {result.get('total_segments', 0)} 个片段")
            info(f"转录文本: {result.get('transcription_text', 'N/A')[:100]}...")
            return True
        else:
            warning(f"视频语音转录失败: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        error(f"视频语音识别测试失败: {e}")
        return False

def main():
    """主测试函数"""
    print("语音识别功能测试")
    print("=" * 50)
    
    test_results = []
    
    # 测试1: 初始化
    test_results.append(("语音识别器初始化", test_speech_recognition_init()))
    
    # 测试2: 音频文件检查
    available_files = test_audio_file_check()
    test_results.append(("音频文件检查", len(available_files) > 0))
    
    # 测试3: 语音识别
    test_results.append(("语音识别功能", test_speech_recognition()))
    
    # 测试4: 视频语音识别
    test_results.append(("视频语音识别", test_video_speech_recognition()))
    
    # 输出测试结果
    print("\n" + "=" * 50)
    print("测试结果汇总")
    print("=" * 50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\n总计: {passed}/{total} 测试通过")
    
    if passed == total:
        info("所有测试通过！语音识别功能正常工作。")
        return True
    else:
        warning(f"部分测试失败，请检查配置和依赖。")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)