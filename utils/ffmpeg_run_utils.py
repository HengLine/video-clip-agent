"""
@FileName: ffmpeg_video_utils.py
@Description: 
@Author: HengLine
@Time: 2025/10/17 15:54
"""

import json
import os
import subprocess
import uuid
from typing import Dict, Any

from hengline.logger import error, debug, warning
from utils.log_utils import print_log_exception


def get_video_duration(video_path, ffmpeg_path: str = "ffprobe", default_duration: float = 3) -> float:
    """
    获取视频文件的时长
    Args:
        video_path: 视频文件路径
        ffmpeg_path: ffprobe可执行文件路径，默认为"ffprobe"
        default_duration: 如果无法获取时长，返回的默认时长，单位为秒，默认为3秒
    Returns:
        float: 视频时长，单位为秒
    """
    try:
        # 获取以秒为单位的时长  ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 input.mp4
        cmd = [ffmpeg_path, '-v', 'error', '-show_entries', 'format=duration', '-of', 'default=noprint_wrappers=1:nokey=1', video_path]

        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode == 0 and result.stderr:
            # 解析JSON输出
            data = json.loads(result.stdout)
            return float(data)
        else:
            cmd = [
                'ffprobe', '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                video_path
            ]

            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            data = json.loads(result.stdout)
            return float(data['format']['duration'])

    except Exception as e:
        print_log_exception()
        error(f"无法获取视频 {video_path} 的时长，使用默认值{default_duration}秒")
        return default_duration


def has_audio_info(video_path) -> bool:
    """检测视频是否有音频流"""
    try:
        # 使用ffprobe获取流信息
        cmd = [
            'ffprobe', '-v', 'quiet',
            '-print_format', 'json',
            '-show_streams',
            video_path
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        data = json.loads(result.stdout)

        # 检查是否有音频流
        audio_streams = [stream for stream in data['streams'] if stream['codec_type'] == 'audio']

        if audio_streams:
            debug(f"{video_path} 找到 {len(audio_streams)} 个音频流")
            for i, audio in enumerate(audio_streams):
                debug(f"音频流 {i + 1}:")
                debug(f"  编码器: {audio.get('codec_name', '未知')}")
                debug(f"  声道数: {audio.get('channels', '未知')}")
                debug(f"  采样率: {audio.get('sample_rate', '未知')} Hz")
                debug(f"  比特率: {audio.get('bit_rate', '未知')}")
            return True
        else:
            # warning("没有找到音频流")
            return False

    except Exception as e:
        error(f"错误: {e}")
        return True


def get_audio_from_video(video_path: str, output_audio_path: str, ffmpeg_path: str = "ffmpeg") -> bool:
    """
    获取视频文件的音频信息

    Args:
        video_path: 视频文件路径
        output_audio_path: 输出音频文件路径
        ffmpeg_path: ffmpeg可执行文件路径，默认为"ffmpeg"

    Returns:
        dict: 包含音频信息的字典，如果没有音频返回空字典
    """
    try:
        # 使用FFmpeg提取音频
        cmd = [
            ffmpeg_path, '-i', video_path,
            '-vn',  # 不包含视频
            '-acodec', 'pcm_s16le',  # 无损PCM格式
            '-ar', '16000',  # 16kHz采样率
            '-ac', '1',  # 单声道
            '-y',  # 覆盖输出文件
            output_audio_path
        ]
        debug(f"从视频提取音频: {video_path} -> {output_audio_path}")
        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )

        return result.returncode == 0
    except Exception as e:
        error(f"获取音频信息失败: {str(e)}")
        return False


def get_video_info(video_path: str, ffmpeg_path: str = "ffprobe") -> dict:
    """
    获取视频文件信息

    Args:
        video_path: 视频文件路径

    Returns:
        dict: 包含视频信息的字典，如果获取失败返回空字典
    """
    try:
        # 使用ffprobe获取视频信息
        cmd = [
            ffmpeg_path,
            "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height,duration,r_frame_rate",
            "-of", "json",
            video_path
        ]

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )

        if result.returncode == 0:
            info_data = json.loads(result.stdout)
            if 'streams' in info_data and len(info_data['streams']) > 0:
                stream = info_data['streams'][0]
                return {
                    'width': stream.get('width'),
                    'height': stream.get('height'),
                    'duration': float(stream.get('duration', 0)),
                    'frame_rate': stream.get('r_frame_rate')
                }
    except Exception as e:
        error(f"获取视频信息失败: {str(e)}")

    return {}


def get_video_metadata(video_path: str, probe_show_entries: str = "format:stream", probe_format: str = "json"
                       , ffmpeg_path: str = "ffprobe") -> Any | None:
    """
    使用ffprobe工具读取视频元数据

    Args:
        video_path: 视频文件路径

    Returns:
        Dict[str, Any]: 原始元数据信息
    """
    # 构建ffprobe命令
    cmd = [
        ffmpeg_path,
        '-v', 'error',
        '-show_entries', probe_show_entries,
        '-of', probe_format,
        video_path
    ]

    # 执行命令
    result = subprocess.run(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False
    )

    # 解析JSON输出
    try:
        if result.returncode == 0:
            info_data = json.loads(result.stdout)
            if 'streams' in info_data and len(info_data['streams']) > 0:
                return info_data['streams'][0]
    except json.JSONDecodeError as e:
        raise Exception(f"解析ffprobe输出失败: {str(e)}")


def codec_video(temp_list_file: str, output_path: str, config, ffmpeg_path: str = "ffmpeg") -> bool | tuple[bool, str]:
    """
    使用ffmpeg对视频进行转码，确保所有视频参数一致
    Args:
        temp_list_file: 输入视频文件路径
        output_path: 输出视频文件路径
        ffmpeg_path: ffmpeg可执行文件路径，默认为"ffmpeg"
        config: 转码配置字典，包含以下可选参数：
            - width: 目标视频宽度，默认为1920
            - height: 目标视频高度，默认为1080
            - resize_mode: 尺寸调整模式，'fit'（适应）或
                            'fill'（填充），默认为'fit'
            - codec: 视频编码器，默认为'libx264'
            - preset: 编码预设，默认为'medium'
            - crf: 质量因子，默认为23
            - framerate: 帧率，默认为30
            - audio_bitrate: 音频比特率，默认为'128k'
    Returns:
        bool: 转码是否成功
    """

    try:
        width = config.get('width', 1920)
        height = config.get('height', 1080)
        resize_mode = config.get('resize_mode', 'fit')
        codec = config.get('codec', 'libx264')
        preset = config.get('preset', 'medium')
        crf = config.get('crf', 23)
        framerate = config.get('framerate', 30)
        audio_bitrate = config.get('audio_bitrate', '128k')

        # 基于缩放模式构建视频滤镜
        if resize_mode == 'fit':
            filter_complex = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black"
        elif resize_mode == 'fill':
            filter_complex = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"
        else:  # stretch
            filter_complex = f"scale={width}:{height}"

        # 构建增强型命令，添加更健壮的参数和统一尺寸处理
        cmd = [
            ffmpeg_path,
            # 全局参数
            "-y",  # 覆盖输出文件
            # 输入参数 - 添加时间戳处理
            "-fflags", "+igndts",  # 忽略可能有问题的时间戳
            "-f", "concat",  # 指定输入格式为concat
            "-safe", "0",  # 允许绝对路径
            "-i", temp_list_file,  # 输入文件列表
            # 视频滤镜 - 统一所有片段的尺寸
            "-vf", filter_complex,
            # 输出参数 - 强制统一所有参数
            "-c:v", codec,  # 使用配置的编码器
            "-preset", preset,  # 使用配置的预设
            "-crf", str(crf),  # 使用配置的质量因子
            "-r", str(framerate),  # 使用配置的帧率
            "-video_track_timescale", str(framerate * 1000),  # 时间基准
            # 强制关键帧，确保正确连接
            "-force_key_frames", "expr:gte(t,n_forced*1)",
            # 音频参数 - 确保音频正确处理
            "-c:a", "aac",  # 音频编码器
            "-b:a", audio_bitrate,  # 使用配置的音频比特率
            # 确保文件兼容性
            "-movflags", "+faststart",
            # 输出文件路径
            output_path
        ]

        debug(f"策略1命令: {' '.join(cmd)}")

        result = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,
            shell=False  # 显式设置为不使用shell
        )

        return result.returncode == 0, result.stderr

    except Exception as e:
        error(f"视频转码失败: {str(e)}")
        return False, str(e)


def merge_videos(merge_list_file, output_path: str, ffmpeg_path: str = "ffmpeg") -> bool | tuple[bool, str]:
    """
    合并多个视频文件为一个视频文件

    Args:
        merge_list_file: 视频文件路径列表
        output_path: 输出视频文件路径
        ffmpeg_path: ffmpeg可执行文件路径，默认为"ffmpeg"

    Returns:
        bool: 合并是否成功
    """
    try:
        # 从列表文件中读取视频路径
        video_paths = []
        try:
            with open(merge_list_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    # 解析文件路径（去除'file '前缀和单引号）
                    if line.strip().startswith('file '):
                        path = line.strip().replace('file ', '', 1).strip("'\"")
                        video_paths.append(path)
        except Exception as e:
            debug(f"读取合并列表文件失败: {str(e)}")

        # 检查是否有任何视频包含音频
        has_any_audio = False
        for video_path in video_paths:
            if os.path.exists(video_path):
                try:
                    probe_cmd = [
                        ffmpeg_path, '-v', 'error', '-show_streams', '-select_streams', 'a',
                        '-of', 'default=noprint_wrappers=1:nokey=1', video_path
                    ]
                    result = subprocess.run(probe_cmd, capture_output=True, text=True, check=False)
                    if len(result.stdout.strip()) > 0:
                        has_any_audio = True
                        debug(f"检测到音频: {video_path}")
                        break  # 只要有一个视频有音频就可以了
                except Exception as e:
                    debug(f"检查视频 {video_path} 音频流失败: {str(e)}")

        # 构建合并命令
        merge_cmd = [
            ffmpeg_path,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", merge_list_file,
        ]

        # 根据是否有音频设置不同的合并策略
        if has_any_audio:
            # 有音频时，分别指定视频和音频的编码方式
            merge_cmd.extend([
                "-c:v", "copy",  # 复制视频流
                "-c:a", "copy"  # 复制音频流
            ])
        else:
            # 没有音频时，直接复制所有流
            merge_cmd.extend(["-c", "copy"])

        merge_cmd.append(output_path)

        debug(f"执行合并命令: {' '.join(merge_cmd)}")

        # 执行合并命令
        merge_result = subprocess.run(
            merge_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )

        return merge_result.returncode == 0, merge_result.stderr

    except Exception as e:
        error(f"合并视频失败: {str(e)}")
        return False, str(e)


def transcode_merge_video(merge_list_file, output_path: str, config, ffmpeg_path: str = "ffmpeg") -> bool | tuple[bool, str]:
    """
    转码并合并视频文件为一个视频文件

    Args:
        merge_list_file: 输入视频文件路径
        output_path: 输出视频文件路径
        ffmpeg_path: ffmpeg可执行文件路径，默认为"ffmpeg"

    Returns:
        bool: 转码合并是否成功
    """
    try:
        codec = config.get('codec', 'libx264')
        preset = config.get('preset', 'medium')
        crf = config.get('crf', 23)
        framerate = config.get('framerate', 30)
        audio_bitrate = config.get('audio_bitrate', '128k')

        # 构建基本转码命令，使用合理的默认参数
        transcode_merge_cmd = [
            ffmpeg_path,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", merge_list_file,
            # 重新转码确保兼容性
            "-c:v", codec,
            "-preset", preset,
            "-crf", str(crf),
            "-r", str(framerate),
            "-c:a", "aac",
            "-b:a", audio_bitrate
        ]

        # 获取转码参数配置
        transcode_params = config.get('transcode_params', {})
        movflags = transcode_params.get('movflags', '+faststart')

        # 添加movflags参数
        if movflags:
            transcode_merge_cmd.extend([
                "-movflags", movflags
            ])

        transcode_merge_cmd.append(output_path)

        debug(f"执行转码合并命令: {' '.join(transcode_merge_cmd)}")

        transcode_merge_result = subprocess.run(
            transcode_merge_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )

        return transcode_merge_result.returncode == 0, transcode_merge_result.stderr
    except Exception as e:
        error(f"转码合并视频失败: {str(e)}")
        return False, str(e)


def scale_video(input_path: str, output_path: str, width: int, height: int, resize_mode: str = 'fit', ffmpeg_path: str = "ffmpeg") -> bool | tuple[bool, str]:
    """
    调整视频尺寸
    
    Args:
        input_path: 输入视频路径
        output_path: 输出视频路径
        width: 目标宽度
        height: 目标高度
        resize_mode: 缩放模式 ('fit', 'fill', 'stretch')
        ffmpeg_path: ffmpeg可执行文件路径
        
    Returns:
        bool: 是否成功
    """
    try:
        # 路径参数验证
        if not input_path or not isinstance(input_path, str):
            error("输入路径必须是有效的字符串")
            return False, "输入路径无效"

        if not output_path or not isinstance(output_path, str):
            error("输出路径必须是有效的字符串")
            return False, "输出路径无效"

        # 验证输入文件是否存在
        if not os.path.exists(input_path):
            error(f"输入文件不存在: {input_path}")
            return False, "输入文件不存在"

        # 确保输出目录存在
        try:
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            error(f"创建输出目录失败: {str(e)}")
            return False, f"创建输出目录失败: {str(e)}"

        # 检查视频是否有音频
        has_audio = has_audio_info(input_path)

        # 构建尺寸调整命令
        scale_cmd = [
            ffmpeg_path,
            "-y",
            "-i", input_path
        ]

        # 根据resize_mode添加相应的缩放滤镜
        if resize_mode == 'fit':
            scale_filter = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black"
        elif resize_mode == 'fill':
            scale_filter = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"
        else:  # stretch
            scale_filter = f"scale={width}:{height}"

        scale_cmd.extend([
            "-vf", scale_filter,
        ])

        # 根据音频存在情况设置音频参数
        if has_audio:
            # 复制音频流，确保不丢失
            scale_cmd.extend(["-c:a", "copy"])
        else:
            # 没有音频时禁用音频
            scale_cmd.append("-an")

        scale_cmd.append(output_path)

        scale_result = subprocess.run(
            scale_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )

        return scale_result.returncode == 0 and os.path.exists(output_path), scale_result.stderr
    except Exception as e:
        error(f"调整视频尺寸失败: {str(e)}")
        return False, str(e)


def apply_xfade_transition(video1_path: str, video2_path: str, output_path: str, transition_type: str,
                           transition_duration: float, offset: float, ffmpeg_path: str = "ffmpeg") -> bool | tuple[bool, str]:
    """
    使用xfade滤镜应用转场效果
    
    Args:
        video1_path: 第一个视频路径
        video2_path: 第二个视频路径
        output_path: 输出视频路径
        transition_type: 转场类型 (支持多种ffmpeg xfade转场效果，如fade, slideleft, slideright, circleopen等)
        transition_duration: 转场时长（秒）
        offset: 转场开始时间偏移（秒）
        ffmpeg_path: ffmpeg可执行文件路径
        
    Returns:
        bool: 是否成功
    """
    try:
        # 路径参数验证
        if not video1_path or not isinstance(video1_path, str):
            error("第一个视频路径必须是有效的字符串")
            return False, "第一个视频路径无效"

        if not video2_path or not isinstance(video2_path, str):
            error("第二个视频路径必须是有效的字符串")
            return False, "第二个视频路径无效"

        if not output_path or not isinstance(output_path, str):
            error("输出路径必须是有效的字符串")
            return False, "输出路径无效"

        # 验证视频文件是否存在
        if not os.path.exists(video1_path):
            error(f"第一个视频文件不存在: {video1_path}")
            return False, "第一个视频文件不存在"

        if not os.path.exists(video2_path):
            error(f"第二个视频文件不存在: {video2_path}")
            return False, "第二个视频文件不存在"

        # 确保输出目录存在
        try:
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            error(f"创建输出目录失败: {str(e)}")
            return False, f"创建输出目录失败: {str(e)}"
        # 检查每个视频是否有音频流
        has_audio1 = has_audio_info(video1_path)
        has_audio2 = has_audio_info(video2_path)

        # 构建命令
        merge_cmd = [
            ffmpeg_path,
            "-y",
            "-i", video1_path,
            "-i", video2_path
        ]

        # 根据音频存在情况构建滤镜
        filter_complex = []
        filter_complex.append(f"[0:v][1:v]xfade=transition={transition_type}:duration={transition_duration}:offset={offset}[v]")

        # 检查是否有至少一个视频有音频
        has_any_audio = has_audio1 or has_audio2

        # 根据音频存在情况构建音频处理
        if has_audio1 and has_audio2:
            # 两个视频都有音频，添加音频转场
            filter_complex.append(f"[0:a][1:a]acrossfade=d={transition_duration}[a]")
        elif has_audio1:
            # 只有第一个视频有音频，直接映射第一个音频
            filter_complex.append("[0:a]asetpts=PTS+offset/TB[a]")
        elif has_audio2:
            # 只有第二个视频有音频，直接映射第二个音频
            filter_complex.append("[1:a]asetpts=PTS[a]")

        merge_cmd.extend(["-filter_complex", ";".join(filter_complex)])
        merge_cmd.extend(["-map", "[v]"])

        # 如果有任何音频，映射音频输出
        if has_any_audio:
            merge_cmd.extend(["-map", "[a]"])
        else:
            # 否则禁用音频输出
            merge_cmd.append("-an")

        # 添加视频编码参数
        merge_cmd.extend([
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
            "-r", "30"
        ])

        # 如果有任何音频，添加音频编码参数
        if has_any_audio:
            merge_cmd.extend([
                "-c:a", "aac",
                "-b:a", "128k"
            ])

        merge_cmd.extend([
            "-movflags", "+faststart",
            output_path
        ])

        merge_result = subprocess.run(
            merge_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )

        return merge_result.returncode == 0 and os.path.exists(output_path), merge_result.stderr
    except Exception as e:
        error(f"应用xfade转场失败: {str(e)}")
        return False, str(e)


def apply_basic_transition(video1_path: str, video2_path: str, output_path: str, transition_duration: float,
                           temp_dir: str, ffmpeg_path: str = "ffmpeg") -> bool | tuple[bool, str]:
    """
    使用基础的淡入淡出方案应用转场效果
    
    Args:
        video1_path: 第一个视频路径
        video2_path: 第二个视频路径
        output_path: 输出视频路径
        transition_duration: 转场时长（秒）
        temp_dir: 临时文件目录
        ffmpeg_path: ffmpeg可执行文件路径
        
    Returns:
        bool: 是否成功
    """
    try:
        # 路径参数验证
        if not video1_path or not isinstance(video1_path, str):
            error("第一个视频路径必须是有效的字符串")
            return False, "第一个视频路径无效"

        if not video2_path or not isinstance(video2_path, str):
            error("第二个视频路径必须是有效的字符串")
            return False, "第二个视频路径无效"

        if not output_path or not isinstance(output_path, str):
            error("输出路径必须是有效的字符串")
            return False, "输出路径无效"

        if not temp_dir or not isinstance(temp_dir, str):
            error("临时目录路径必须是有效的字符串")
            return False, "临时目录路径无效"

        # 验证视频文件是否存在
        if not os.path.exists(video1_path):
            error(f"第一个视频文件不存在: {video1_path}")
            return False, "第一个视频文件不存在"

        if not os.path.exists(video2_path):
            error(f"第二个视频文件不存在: {video2_path}")
            return False, "第二个视频文件不存在"

        # 确保目录存在
        try:
            os.makedirs(temp_dir, exist_ok=True)
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            error(f"创建目录失败: {str(e)}")
            return False, f"创建目录失败: {str(e)}"

        # 检查视频是否有音频（使用JSON格式获取更准确的信息）
        has_audio1 = has_audio_info(video1_path)
        has_audio2 = has_audio_info(video2_path)

        # 检查是否有至少一个视频有音频
        has_any_audio = has_audio1 or has_audio2
        debug(f"基础转场 - 是否有任何音频需要保留: {has_any_audio}")

        # 1. 为第一个视频添加淡出效果
        first_fade_out = os.path.join(temp_dir, f"fadeout_{str(uuid.uuid4())[:8]}.mp4")
        current_duration = get_video_duration(video1_path, ffmpeg_path, 3.0)

        fadeout_cmd = [
            ffmpeg_path,
            "-y",
            "-i", video1_path,
            "-vf", f"fade=t=out:st={current_duration - transition_duration}:d={transition_duration}",
        ]

        # 只有当视频有音频时才添加音频滤镜
        if has_audio1:
            fadeout_cmd.extend([
                "-af", f"afade=t=out:st={current_duration - transition_duration}:d={transition_duration}",
            ])
        else:
            # 没有音频时禁用音频
            fadeout_cmd.append("-an")

        fadeout_cmd.extend([
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
        ])

        # 只有当视频有音频时才添加音频编码参数
        if has_audio1:
            fadeout_cmd.extend([
                "-c:a", "aac",
                "-b:a", "128k",
                # 确保音频同步
                "-async", "1"
            ])

        fadeout_cmd.append(first_fade_out)
        debug(f"执行淡出命令: {' '.join(fadeout_cmd)}")

        fadeout_result = subprocess.run(
            fadeout_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )

        if fadeout_result.returncode != 0 or not os.path.exists(first_fade_out):
            debug(f"淡出命令失败: {fadeout_result.stderr}")
            return False, fadeout_result.stderr

        # 2. 为第二个视频添加淡入效果
        second_fade_in = os.path.join(temp_dir, f"fadein_{str(uuid.uuid4())[:8]}.mp4")

        fadein_cmd = [
            ffmpeg_path,
            "-y",
            "-i", video2_path,
            "-vf", f"fade=t=in:st=0:d={transition_duration}",
        ]

        # 只有当视频有音频时才添加音频滤镜
        if has_audio2:
            fadein_cmd.extend([
                "-af", f"afade=t=in:st=0:d={transition_duration}",
            ])
        else:
            # 没有音频时禁用音频
            fadein_cmd.append("-an")

        fadein_cmd.extend([
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "23",
        ])

        # 只有当视频有音频时才添加音频编码参数
        if has_audio2:
            fadein_cmd.extend([
                "-c:a", "aac",
                "-b:a", "128k",
                # 确保音频同步
                "-async", "1"
            ])

        fadein_cmd.append(second_fade_in)
        debug(f"执行淡入命令: {' '.join(fadein_cmd)}")

        fadein_result = subprocess.run(
            fadein_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )

        if fadein_result.returncode != 0 or not os.path.exists(second_fade_in):
            # 清理
            if os.path.exists(first_fade_out):
                os.remove(first_fade_out)
            debug(f"淡入命令失败: {fadein_result.stderr}")
            return False, fadein_result.stderr

        # 3. 使用concat协议合并两个处理后的视频
        concat_list = os.path.join(temp_dir, f"concat_list_{str(uuid.uuid4())[:8]}.txt")
        with open(concat_list, 'w', encoding='utf-8') as f:
            f.write(f"file '{os.path.abspath(first_fade_out)}'\n")
            f.write(f"file '{os.path.abspath(second_fade_in)}'\n")

        # 构建合并命令
        concat_cmd = [
            ffmpeg_path,
            "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", concat_list
        ]

        # 根据是否有音频设置不同的合并策略
        if has_any_audio:
            # 如果有音频，分别指定视频和音频的复制方式，确保音频正确处理
            concat_cmd.extend([
                "-c:v", "copy",
                "-c:a", "copy"
            ])
        else:
            # 如果没有音频，直接复制所有流
            concat_cmd.extend(["-c", "copy"])

        concat_cmd.append(output_path)
        debug(f"执行合并命令: {' '.join(concat_cmd)}")

        concat_result = subprocess.run(
            concat_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False
        )

        # 如果直接copy失败，尝试重新编码
        if concat_result.returncode != 0 or not os.path.exists(output_path):
            debug(f"直接复制合并失败，尝试重新编码: {concat_result.stderr}")
            concat_cmd = [
                ffmpeg_path,
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", concat_list,
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "23",
            ]

            # 检查是否有任何音频需要保留
            if has_any_audio:
                concat_cmd.extend([
                    "-c:a", "aac",
                    "-b:a", "128k",
                    # 确保音频同步和质量
                    "-async", "1",
                    # 优化音频编码
                    "-ac", "2",
                    "-ar", "44100"
                ])
            else:
                concat_cmd.append("-an")

            concat_cmd.extend([
                "-movflags", "+faststart",
                output_path
            ])
            concat_result = subprocess.run(
                concat_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )

        # 清理临时文件
        if os.path.exists(first_fade_out):
            os.remove(first_fade_out)
        if os.path.exists(second_fade_in):
            os.remove(second_fade_in)
        if os.path.exists(concat_list):
            os.remove(concat_list)

        return concat_result.returncode == 0 and os.path.exists(output_path), concat_result.stderr
    except Exception as e:
        error(f"应用基础转场失败: {str(e)}")
        return False, str(e)


if __name__ == '__main__':

    # 使用示例
    duration = get_video_duration("E:\Projects\blogs\tool-video-agent\data/output\temp\transcoded_1_ba4feb95.mp4")
    print(duration)
    if duration:
        hours = int(duration // 3600)
        minutes = int((duration % 3600) // 60)
        seconds = duration % 60
        print(f"视频时长: {hours:02d}:{minutes:02d}:{seconds:06.3f}")
