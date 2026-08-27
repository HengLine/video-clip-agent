#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import random
import subprocess
from penclip.utils.ffmpeg_env_utils import find_ffmpeg
from penclip.utils.ffmpeg_run_utils import has_audio_info, get_video_duration
from penclip.logger import error, debug, warning, info

def get_random_background_audio():
    """从source/audio目录随机选择一个背景音频文件"""
    audio_dir = "source/audio"
    
    # 检查音频目录是否存在
    if not os.path.exists(audio_dir):
        error(f"音频目录不存在: {audio_dir}")
        return None
    
    # 获取所有音频文件
    audio_files = []
    for file in os.listdir(audio_dir):
        if file.lower().endswith(('.mp3', '.wav', '.aac', '.m4a')):
            audio_files.append(os.path.join(audio_dir, file))
    
    if not audio_files:
        error(f"音频目录中没有找到音频文件: {audio_dir}")
        return None
    
    # 随机选择一个音频文件
    selected_audio = random.choice(audio_files)
    info(f"随机选择背景音频: {os.path.basename(selected_audio)}")
    return selected_audio

def add_background_audio_to_video(video_path, output_path, background_audio_path=None):
    """
    为无音频的视频添加背景音乐
    
    Args:
        video_path: 输入视频路径
        output_path: 输出视频路径
        background_audio_path: 背景音频路径，如果为None则随机选择
    
    Returns:
        tuple: (success, error_message)
    """
    try:
        ffmpeg_path = find_ffmpeg()
        
        # 如果没有指定背景音频，随机选择一个
        if background_audio_path is None:
            background_audio_path = get_random_background_audio()
            if background_audio_path is None:
                return False, "无法找到背景音频文件"
        
        # 获取视频时长
        video_duration = get_video_duration(video_path)
        if video_duration <= 0:
            return False, "无法获取视频时长"
        
        debug(f"为视频 {os.path.basename(video_path)} 添加背景音频，时长: {video_duration}秒")
        
        # 构建添加背景音频的命令
        # 使用amerge滤镜将背景音频与视频时长匹配
        cmd = [
            ffmpeg_path, "-y",
            "-i", video_path,  # 输入视频
            "-stream_loop", "-1",  # 无限循环背景音频
            "-i", background_audio_path,  # 输入背景音频
            "-filter_complex", f"[1:a]atrim=duration={video_duration}[bg_audio];[bg_audio]volume=0.3[audio_out]",  # 截取音频时长并调整音量
            "-map", "0:v",  # 使用原始视频流
            "-map", "[audio_out]",  # 使用处理后的音频流
            "-c:v", "copy",  # 复制视频流
            "-c:a", "aac",  # 音频编码器
            "-ar", "44100",  # 采样率
            "-ac", "2",  # 立体声
            "-b:a", "128k",  # 音频比特率
            "-shortest",  # 以最短流为准
            output_path
        ]
        
        debug(f"执行添加背景音频命令: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        
        if result.returncode == 0 and os.path.exists(output_path):
            info(f"成功为视频添加背景音频: {os.path.basename(output_path)}")
            return True, None
        else:
            error(f"添加背景音频失败: {result.stderr}")
            return False, result.stderr
            
    except Exception as e:
        error(f"添加背景音频异常: {str(e)}")
        return False, str(e)

def ensure_audio_duration_match(video_path, output_path):
    """
    确保视频的音频时长与视频时长匹配
    如果音频时长不足，则添加静音或循环音频到视频时长
    
    Args:
        video_path: 输入视频路径
        output_path: 输出视频路径
    
    Returns:
        tuple: (success, error_message)
    """
    try:
        ffmpeg_path = find_ffmpeg()
        
        # 获取视频时长
        video_duration = get_video_duration(video_path)
        if video_duration <= 0:
            return False, "无法获取视频时长"
        
        # 检查是否有音频
        has_audio = has_audio_info(video_path)
        
        if not has_audio:
            # 无音频，添加背景音乐
            return add_background_audio_to_video(video_path, output_path)
        
        # 有音频，检查音频时长
        import subprocess
        # 使用ffprobe获取音频时长
        cmd = [ffmpeg_path.replace("ffmpeg", "ffprobe"), "-v", "quiet", "-show_entries", "stream=duration", "-select_streams", "a:0", "-of", "default=noprint_wrappers=1:nokey=1", video_path]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        if result.returncode != 0 or not result.stdout.strip():
            # 无法获取音频时长，尝试重新编码并添加静音
            warning(f"无法获取音频时长，尝试重新编码并添加静音: {video_path}")
            cmd = [
                ffmpeg_path, "-y",
                "-i", video_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-ar", "44100",
                "-ac", "2",
                "-b:a", "128k",
                "-af", f"aresample=async=1:first_pts=0,apad=pad_dur={video_duration}",
                output_path
            ]
        else:
            try:
                audio_duration = float(result.stdout.strip())
                debug(f"视频时长: {video_duration}秒, 音频时长: {audio_duration}秒")
                
                if abs(audio_duration - video_duration) < 0.1:  # 允许0.1秒误差
                    # 音频时长匹配，直接复制
                    debug(f"音频时长匹配，直接复制")
                    import shutil
                    shutil.copy2(video_path, output_path)
                    return True, None
                elif audio_duration < video_duration:
                    # 音频时长不足，添加静音补齐
                    silence_duration = video_duration - audio_duration
                    debug(f"音频时长不足，添加{silence_duration}秒静音")
                    cmd = [
                        ffmpeg_path, "-y",
                        "-i", video_path,
                        "-af", f"apad=pad_dur={silence_duration}",
                        "-c:v", "copy",
                        "-c:a", "aac",
                        "-ar", "44100",
                        "-ac", "2",
                        "-b:a", "128k",
                        output_path
                    ]
                else:
                    # 音频时长超过视频，截取
                    debug(f"音频时长超过，截取到{video_duration}秒")
                    cmd = [
                        ffmpeg_path, "-y",
                        "-i", video_path,
                        "-af", f"atrim=duration={video_duration}",
                        "-c:v", "copy",
                        "-c:a", "aac",
                        "-ar", "44100",
                        "-ac", "2",
                        "-b:a", "128k",
                        output_path
                    ]
            except ValueError:
                # 解析失败，重新编码并添加静音
                warning(f"解析音频时长失败，重新编码并添加静音: {video_path}")
                cmd = [
                    ffmpeg_path, "-y",
                    "-i", video_path,
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-ar", "44100",
                    "-ac", "2",
                    "-b:a", "128k",
                    "-af", f"aresample=async=1:first_pts=0,apad=pad_dur={video_duration}",
                    output_path
                ]
        
        debug(f"执行音频时长匹配命令: {' '.join(cmd)}")
        
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )
        
        if result.returncode == 0 and os.path.exists(output_path):
            info(f"成功匹配音频时长: {os.path.basename(output_path)}")
            return True, None
        else:
            error(f"匹配音频时长失败: {result.stderr}")
            return False, result.stderr
            
    except Exception as e:
        error(f"匹配音频时长异常: {str(e)}")
        return False, str(e)

def process_video_audio_with_background(video_paths, output_dir, clip_mapping=None):
    """
    处理视频列表的音频：有音频的保持原样，无音频的添加背景音乐
    确保所有视频的音频时长都与视频时长匹配，并保持原始顺序
    
    Args:
        video_paths: 视频路径列表
        output_dir: 输出目录
        clip_mapping: 片段映射信息，用于保持顺序一致性
    
    Returns:
        tuple: (processed_videos, audio_mapping) - 处理后的视频路径列表和音频映射信息
    """
    processed_videos = []
    audio_mapping = {}  # 记录原始视频到处理后视频的映射
    
    debug(f"开始处理{len(video_paths)}个视频的音频，保持原始顺序")
    if clip_mapping:
        debug(f"使用片段映射信息保持顺序一致性: {len(clip_mapping)}个片段")
    
    for i, video_path in enumerate(video_paths):
        if not os.path.exists(video_path):
            warning(f"视频文件不存在，跳过: {video_path}")
            continue
        
        # 获取片段的唯一标识符（如果有映射信息）
        unique_id = None
        original_index = i
        if clip_mapping:
            # 在映射中查找当前视频路径对应的片段信息
            for mapping in clip_mapping:
                if mapping.get('clip_path') == video_path:
                    unique_id = mapping.get('unique_id')
                    original_index = mapping.get('original_index', i)
                    break
        
        # 检查视频是否有音频
        has_audio = has_audio_info(video_path)
        
        # 创建输出文件路径，使用唯一ID或索引确保顺序
        if unique_id:
            if has_audio:
                output_path = os.path.join(output_dir, f"{unique_id}_original_audio.mp4")
            else:
                output_path = os.path.join(output_dir, f"{unique_id}_bg_audio.mp4")
        else:
            base_name = os.path.splitext(os.path.basename(video_path))[0]
            if has_audio:
                output_path = os.path.join(output_dir, f"{base_name}_original_audio_{i:03d}.mp4")
            else:
                output_path = os.path.join(output_dir, f"{base_name}_bg_audio_{i:03d}.mp4")
        
        if has_audio:
            # 有音频的视频，确保音频时长匹配
            debug(f"[{i+1}/{len(video_paths)}] 视频 {os.path.basename(video_path)} 有音频，检查时长匹配")
            
            # 确保音频时长匹配
            success, error_msg = ensure_audio_duration_match(video_path, output_path)
            
            if success:
                processed_videos.append(output_path)
                audio_mapping[i] = {
                    "original": video_path, 
                    "processed": output_path, 
                    "has_audio": True, 
                    "index": i,
                    "unique_id": unique_id
                }
                info(f"成功处理 {os.path.basename(video_path)} 的音频时长")
            else:
                warning(f"处理 {os.path.basename(video_path)} 音频时长失败: {error_msg}")
                # 失败时使用原视频
                processed_videos.append(video_path)
                audio_mapping[i] = {
                    "original": video_path, 
                    "processed": video_path, 
                    "has_audio": True, 
                    "index": i,
                    "unique_id": unique_id
                }
        else:
            # 无音频的视频，添加背景音乐
            debug(f"[{i+1}/{len(video_paths)}] 视频 {os.path.basename(video_path)} 无音频，添加背景音乐")
            
            # 添加背景音频
            success, error_msg = add_background_audio_to_video(video_path, output_path)
            
            if success:
                processed_videos.append(output_path)
                audio_mapping[i] = {
                    "original": video_path, 
                    "processed": output_path, 
                    "has_audio": False, 
                    "index": i,
                    "unique_id": unique_id
                }
                info(f"成功为 {os.path.basename(video_path)} 添加背景音频")
            else:
                warning(f"为 {os.path.basename(video_path)} 添加背景音频失败: {error_msg}")
                # 失败时使用原视频
                processed_videos.append(video_path)
                audio_mapping[i] = {
                    "original": video_path, 
                    "processed": video_path, 
                    "has_audio": False, 
                    "index": i,
                    "unique_id": unique_id
                }
    
    # 验证输出顺序 - 确保processed_videos的顺序与原始video_paths完全一致
    debug(f"音频处理完成，处理了{len(processed_videos)}个视频")
    debug("验证音频映射顺序:")
    for i in range(len(video_paths)):
        if i in audio_mapping:
            mapping = audio_mapping[i]
            debug(f"  索引[{i}]: {os.path.basename(mapping['original'])} -> {os.path.basename(mapping['processed'])} (音频: {'有' if mapping['has_audio'] else '无'})")
        else:
            debug(f"  索引[{i}]: 未找到映射信息")
    
    return processed_videos, audio_mapping

if __name__ == "__main__":
    # 测试代码
    test_video = "data/output/output_0fa7828d.mp4"
    test_output = "test_bg_audio.mp4"
    
    if os.path.exists(test_video):
        success, error = add_background_audio_to_video(test_video, test_output)
        if success:
            print(f"测试成功，输出文件: {test_output}")
        else:
            print(f"测试失败: {error}")
    else:
        print(f"测试视频不存在: {test_video}")