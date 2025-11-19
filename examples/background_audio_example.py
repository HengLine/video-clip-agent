#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
背景音频功能使用示例
演示如何为无音频的视频添加背景音乐
"""

import os
import sys
from utils.background_audio_utils import add_background_audio_to_video, process_video_audio_with_background
from utils.ffmpeg_run_utils import merge_videos, has_audio_info

def example_single_video():
    """示例：为单个无音频视频添加背景音乐"""
    print("=== 示例1：为单个视频添加背景音乐 ===")
    
    # 假设你有一个无音频的视频文件
    input_video = "path/to/your/silent_video.mp4"
    output_video = "path/to/your/video_with_background.mp4"
    
    if not os.path.exists(input_video):
        print(f"❌ 输入视频不存在: {input_video}")
        print("请将 input_video 替换为实际的视频文件路径")
        return False
    
    # 检查视频是否有音频
    if has_audio_info(input_video):
        print(f"⚠️  {input_video} 已经有音频，无需添加背景音乐")
        return True
    
    # 添加背景音乐
    try:
        success = add_background_audio_to_video(input_video, output_video)
        if success and os.path.exists(output_video):
            print(f"✅ 成功为视频添加背景音乐: {output_video}")
            
            # 验证输出视频是否有音频
            if has_audio_info(output_video):
                print(f"✅ 输出视频现在有音频了")
            else:
                print(f"❌ 输出视频仍然没有音频")
            return True
        else:
            print(f"❌ 添加背景音乐失败")
            return False
    except Exception as e:
        print(f"❌ 处理过程中出错: {str(e)}")
        return False

def example_video_list():
    """示例：处理视频列表，为无音频的视频添加背景音乐"""
    print("\n=== 示例2：处理视频列表 ===")
    
    # 假设你有多个视频文件
    video_list = [
        "path/to/video1.mp4",  # 可能有音频
        "path/to/video2.mp4",  # 可能无音频
        "path/to/video3.mp4",  # 可能无音频
    ]
    
    # 检查视频文件是否存在
    existing_videos = []
    for video in video_list:
        if os.path.exists(video):
            existing_videos.append(video)
        else:
            print(f"⚠️  视频文件不存在，跳过: {video}")
    
    if not existing_videos:
        print("❌ 没有找到可用的视频文件")
        print("请将 video_list 替换为实际的视频文件路径")
        return False
    
    try:
        # 创建临时目录
        temp_dir = "temp_example_processing"
        os.makedirs(temp_dir, exist_ok=True)
        
        # 处理视频列表
        processed_videos, audio_mapping = process_video_audio_with_background(existing_videos, temp_dir)
        
        print(f"📊 处理结果:")
        for i, original in enumerate(existing_videos):
            processed = processed_videos[i]
            original_has_audio = has_audio_info(original)
            processed_has_audio = has_audio_info(processed)
            
            status = "✅" if processed_has_audio else "❌"
            change = "保持原样" if original_has_audio == processed_has_audio else "添加了背景音频"
            
            print(f"  {status} {os.path.basename(original)} -> {os.path.basename(processed)} ({change})")
        
        # 清理临时文件
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"🧹 已清理临时目录")
        
        return True
        
    except Exception as e:
        print(f"❌ 处理过程中出错: {str(e)}")
        return False

def example_merge_videos():
    """示例：合并多个视频，自动为无音频视频添加背景音乐"""
    print("\n=== 示例3：合并视频（自动处理音频） ===")
    
    # 假设你要合并多个视频
    video_list = [
        "path/to/video1.mp4",
        "path/to/video2.mp4", 
        "path/to/video3.mp4",
    ]
    
    # 检查视频文件是否存在
    existing_videos = []
    for video in video_list:
        if os.path.exists(video):
            existing_videos.append(video)
        else:
            print(f"⚠️  视频文件不存在，跳过: {video}")
    
    if len(existing_videos) < 2:
        print("❌ 需要至少2个视频文件进行合并")
        print("请将 video_list 替换为实际的视频文件路径")
        return False
    
    try:
        # 创建合并列表文件
        merge_list_file = "temp_merge_example.txt"
        with open(merge_list_file, 'w', encoding='utf-8') as f:
            for video in existing_videos:
                f.write(f"file '{video}'\n")
        
        # 输出文件
        output_video = "output/merged_video_with_background.mp4"
        os.makedirs(os.path.dirname(output_video), exist_ok=True)
        
        # 合并视频（会自动为无音频视频添加背景音乐）
        success = merge_videos(merge_list_file, output_video)
        
        if success and os.path.exists(output_video):
            print(f"✅ 视频合并成功: {output_video}")
            
            # 检查合并后视频的音频状态
            if has_audio_info(output_video):
                print(f"✅ 合并后视频有音频")
            else:
                print(f"❌ 合并后视频没有音频")
            
            return True
        else:
            print(f"❌ 视频合并失败")
            return False
        
    except Exception as e:
        print(f"❌ 处理过程中出错: {str(e)}")
        return False
    
    finally:
        # 清理临时文件
        if os.path.exists(merge_list_file):
            os.remove(merge_list_file)
            print(f"🧹 已清理临时列表文件")

def main():
    """主函数 - 运行所有示例"""
    print("🎵 背景音频功能使用示例\n")
    
    print("📋 功能说明:")
    print("- 自动检测视频是否有音频")
    print("- 为无音频视频随机选择背景音乐（从 source/audio/ 目录）")
    print("- 有音频的视频保持原样")
    print("- 支持单个视频处理、批量处理和视频合并")
    print()
    
    # 检查背景音频目录
    audio_dir = "source/audio"
    if not os.path.exists(audio_dir):
        print(f"❌ 背景音频目录不存在: {audio_dir}")
        print("请确保在 source/audio/ 目录下有音频文件（.mp3, .wav, .m4a）")
        return
    
    audio_files = [f for f in os.listdir(audio_dir) if f.endswith(('.mp3', '.wav', '.m4a'))]
    if not audio_files:
        print(f"❌ 背景音频目录中没有音频文件: {audio_dir}")
        print("请在 source/audio/ 目录下添加音频文件")
        return
    
    print(f"✅ 找到背景音频文件: {audio_files}")
    print()
    
    # 运行示例（注释掉实际执行，因为路径是示例）
    print("🔧 使用示例代码（请修改路径后使用）:\n")
    
    print("1. 单个视频处理:")
    print("   add_background_audio_to_video('input.mp4', 'output_with_bg.mp4')")
    print()
    
    print("2. 批量处理:")
    print("   videos = ['video1.mp4', 'video2.mp4', 'video3.mp4']")
    print("   processed = process_video_audio_with_background(videos, 'temp_dir')")
    print()
    
    print("3. 视频合并:")
    print("   # 创建列表文件")
    print("   with open('list.txt', 'w') as f:")
    print("       for video in videos:")
    print("           f.write(f\"file '{video}'\\n\")")
    print("   merge_videos('list.txt', 'merged_output.mp4')")
    print()
    
    print("📖 详细使用方法请参考示例函数中的代码")
    print("🎉 背景音频功能已准备就绪！")

if __name__ == "__main__":
    main()