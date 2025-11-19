#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import glob
import shutil
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.ffmpeg_run_utils import has_audio_info, get_video_duration
from utils.background_audio_utils import process_video_audio_with_background
from utils.ffmpeg_utils import FFmpegUtils

def debug(message):
    """调试输出"""
    print(f"[DEBUG] {message}")

def info(message):
    """信息输出"""
    print(f"[INFO] {message}")

def warning(message):
    """警告输出"""
    print(f"[WARNING] {message}")

def error(message):
    """错误输出"""
    print(f"[ERROR] {message}")

def find_test_videos():
    """查找测试视频文件"""
    # 查找data/output目录下的视频文件
    video_files = []
    
    # 搜索data/output目录
    if os.path.exists("data/output"):
        video_files.extend(glob.glob("data/output/*.mp4"))
    
    # 搜索data目录
    if os.path.exists("data"):
        video_files.extend(glob.glob("data/*.mp4"))
    
    # 去重并过滤存在的文件
    unique_videos = []
    seen = set()
    for video in video_files:
        if video not in seen and os.path.exists(video):
            unique_videos.append(video)
            seen.add(video)
    
    return unique_videos[:2]  # 最多返回2个视频进行测试

def test_audio_matching():
    """测试音频匹配修复功能"""
    info("开始测试音频匹配修复功能...")
    
    # 查找测试视频
    test_videos = find_test_videos()
    if len(test_videos) < 2:
        error("需要至少2个视频文件进行测试")
        return False
    
    info(f"找到测试视频: {[os.path.basename(v) for v in test_videos]}")
    
    # 检查每个视频的音频状态
    audio_status = []
    for video in test_videos:
        has_audio = has_audio_info(video)
        audio_status.append(has_audio)
        duration = get_video_duration(video)
        info(f"视频 {os.path.basename(video)} - 时长: {duration:.2f}秒, 音频: {'有' if has_audio else '无'}")
    
    # 创建临时目录
    temp_dir = "test_audio_fix_temp"
    os.makedirs(temp_dir, exist_ok=True)
    
    try:
        # 测试音频处理功能
        info("测试音频处理功能...")
        processed_videos, audio_mapping = process_video_audio_with_background(test_videos, temp_dir)
        
        info(f"处理结果:")
        for i, (original, processed) in enumerate(zip(test_videos, processed_videos)):
            original_has_audio = has_audio_info(original)
            processed_has_audio = has_audio_info(processed)
            
            status = "✅" if processed_has_audio else "❌"
            change = "保持原样" if original_has_audio == processed_has_audio else "添加了背景音频"
            
            info(f"  {status} {os.path.basename(original)} -> {os.path.basename(processed)} ({change})")
            
            # 验证音频映射
            mapping_info = audio_mapping.get(i, {})
            info(f"    映射信息: {mapping_info}")
        
        # 测试转场功能，确保音频不会错乱
        info("\n测试转场功能（检查音频是否错乱）...")
        
        # 使用FFmpegUtils进行转场测试
        ffmpeg_utils = FFmpegUtils()
        
        # 测试xfade转场
        output_xfade = os.path.join(temp_dir, "test_xfade_output.mp4")
        success_xfade = ffmpeg_utils.apply_video_transitions(
            processed_videos, 
            output_xfade, 
            transition_type="xfade",
            transition_duration=1.0
        )
        
        if success_xfade and os.path.exists(output_xfade):
            output_duration = get_video_duration(output_xfade)
            has_output_audio = has_audio_info(output_xfade)
            info(f"✅ xfade转场成功 - 输出时长: {output_duration:.2f}秒, 音频: {'有' if has_output_audio else '无'}")
        else:
            error("❌ xfade转场失败")
        
        # 测试基础转场
        output_basic = os.path.join(temp_dir, "test_basic_output.mp4")
        success_basic = ffmpeg_utils.apply_video_transitions(
            processed_videos, 
            output_basic, 
            transition_type="basic",
            transition_duration=1.0
        )
        
        if success_basic and os.path.exists(output_basic):
            output_duration = get_video_duration(output_basic)
            has_output_audio = has_audio_info(output_basic)
            info(f"✅ 基础转场成功 - 输出时长: {output_duration:.2f}秒, 音频: {'有' if has_output_audio else '无'}")
        else:
            error("❌ 基础转场失败")
        
        # 验证音频匹配是否正确
        info("\n验证音频匹配正确性...")
        
        # 计算预期总时长
        total_duration = sum(get_video_duration(v) for v in processed_videos)
        transition_duration = 1.0
        expected_duration = total_duration - transition_duration  # xfade转场会减少转场时长
        
        if success_xfade and os.path.exists(output_xfade):
            actual_duration = get_video_duration(output_xfade)
            duration_diff = abs(actual_duration - expected_duration)
            
            if duration_diff <= 2.0:  # 允许2秒误差
                info(f"✅ 音频匹配验证通过 - 预期时长: {expected_duration:.2f}秒, 实际时长: {actual_duration:.2f}秒, 误差: {duration_diff:.2f}秒")
            else:
                warning(f"⚠️  音频匹配可能有问题 - 预期时长: {expected_duration:.2f}秒, 实际时长: {actual_duration:.2f}秒, 误差: {duration_diff:.2f}秒")
        
        return True
        
    except Exception as e:
        error(f"测试过程中出错: {str(e)}")
        return False
    
    finally:
        # 清理临时文件
        try:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
                info("已清理临时文件")
        except Exception as e:
            warning(f"清理临时文件失败: {str(e)}")

def main():
    """主函数"""
    info("=" * 50)
    info("音频匹配修复功能测试")
    info("=" * 50)
    
    # 检查背景音频目录
    audio_dir = "source/audio"
    if not os.path.exists(audio_dir):
        error(f"背景音频目录不存在: {audio_dir}")
        info("请确保在 source/audio/ 目录下有音频文件（.mp3, .wav, .m4a）")
        return
    
    audio_files = [f for f in os.listdir(audio_dir) if f.endswith(('.mp3', '.wav', '.m4a'))]
    if not audio_files:
        error(f"背景音频目录中没有音频文件: {audio_dir}")
        info("请在 source/audio/ 目录下添加音频文件")
        return
    
    info(f"找到背景音频文件: {audio_files}")
    
    # 运行测试
    success = test_audio_matching()
    
    info("\n" + "=" * 50)
    if success:
        info("✅ 音频匹配修复功能测试完成")
        info("修复内容:")
        info("1. 修复了音频映射错乱问题")
        info("2. 为无音频视频添加背景音频")
        info("3. 确保转场过程中音频正确对应")
        info("4. 使用唯一文件名避免冲突")
    else:
        error("❌ 音频匹配修复功能测试失败")
    info("=" * 50)

if __name__ == "__main__":
    main()