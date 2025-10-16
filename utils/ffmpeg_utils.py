"""
FFmpeg工具类，用于封装所有FFmpeg相关的功能
提供视频片段提取、视频合并、转码等功能的统一接口
https://ffmpeg.org/ffmpeg.html
"""
import os
import subprocess
import uuid
from hengline.logger import debug, info, error, warning
from config.config import get_video_rendering_config

class FFmpegUtils:
    """
    FFmpeg工具类，封装所有FFmpeg相关操作
    """
    
    @staticmethod
    def find_ffmpeg() -> str:
        """
        查找系统中的FFmpeg可执行文件路径
        
        Returns:
            str: FFmpeg可执行文件的绝对路径
        
        Raises:
            FileNotFoundError: 当找不到FFmpeg时抛出
        """
        # 首先尝试直接使用'ffmpeg'命令（系统PATH中）
        try:
            # 使用subprocess的check_output来获取ffmpeg版本信息
            # 如果成功执行，说明ffmpeg在系统PATH中
            result = subprocess.run(
                ['ffmpeg', '-version'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            if result.returncode == 0:
                debug("FFmpeg found in system PATH")
                return 'ffmpeg'
        except (subprocess.SubprocessError, FileNotFoundError):
            # 如果直接调用失败，尝试查找常见安装路径
            pass
        
        # 定义常见的FFmpeg安装路径
        # Windows常见路径
        windows_paths = [
            os.path.join(os.environ.get('PROGRAMFILES', 'C:\Program Files'), 'ffmpeg', 'bin', 'ffmpeg.exe'),
            os.path.join(os.environ.get('PROGRAMFILES(X86)', 'C:\Program Files (x86)'), 'ffmpeg', 'bin', 'ffmpeg.exe'),
            os.path.join(os.environ.get('LOCALAPPDATA', os.path.expanduser('~\AppData\Local')), 'ffmpeg', 'bin', 'ffmpeg.exe'),
            # 检查PATH中的目录
            *[os.path.join(path, 'ffmpeg.exe') for path in os.environ.get('PATH', '').split(os.pathsep)]
        ]
        
        # Linux/macOS常见路径
        unix_paths = [
            '/usr/bin/ffmpeg',
            '/usr/local/bin/ffmpeg',
            '/opt/homebrew/bin/ffmpeg',
            # 检查PATH中的目录
            *[os.path.join(path, 'ffmpeg') for path in os.environ.get('PATH', '').split(os.pathsep)]
        ]
        
        # 组合所有可能的路径
        all_paths = windows_paths + unix_paths
        
        # 去重并检查每个路径
        for path in set(all_paths):
            if os.path.isfile(path) and os.access(path, os.X_OK):
                debug(f"FFmpeg found at: {path}")
                return path
        
        # 如果所有路径都检查失败，抛出异常
        error("FFmpeg not found. Please install FFmpeg and add it to your system PATH.")
        raise FileNotFoundError("FFmpeg not found. Please install FFmpeg and add it to your system PATH.")
    
    @staticmethod
    def extract_video_clip(input_path: str, output_path: str, start_time: float, end_time: float = None) -> bool:
        """
        从视频中提取指定时间段的片段
        
        Args:
            input_path: 输入视频路径
            output_path: 输出视频片段路径
            start_time: 开始时间（秒）
            end_time: 结束时间（秒），如果为None则提取到视频结束
            
        Returns:
            bool: 成功返回True，失败返回False
        """
        debug(f"提取视频片段: 输入={input_path}, 输出={output_path}, 开始={start_time}, 结束={end_time}")
        
        # 确保输入文件存在
        if not os.path.exists(input_path):
            error(f"输入文件不存在: {input_path}")
            return False
        
        # 验证时间参数
        if start_time < 0:
            error(f"无效的开始时间: {start_time}，必须大于等于0")
            return False
        
        # 检查时间范围有效性（只有当end_time不为None时）
        if end_time is not None:
            if end_time <= start_time:
                error(f"无效的时间范围: 开始时间({start_time})必须小于结束时间({end_time})")
                return False
        
        # 获取FFmpeg路径
        try:
            ffmpeg_path = FFmpegUtils.find_ffmpeg()
        except FileNotFoundError:
            return False
        
        # 构建FFmpeg命令
        cmd = [
            ffmpeg_path,
            # 全局参数
            "-y",  # 覆盖输出文件
            # 输入参数
            "-ss", str(start_time),  # 开始时间
            "-i", input_path,       # 输入文件
        ]
        
        # 只有当end_time不为None时才添加-to参数
        if end_time is not None:
            cmd.extend(["-to", str(end_time)])
        
        # 添加输出参数
        cmd.extend([
            "-c", "copy",          # 复制流（无损快速）
            "-map", "0",           # 映射所有流
            output_path             # 输出文件
        ])
        
        debug(f"执行FFmpeg提取命令: {' '.join(cmd)}")
        
        try:
            # 执行命令
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            # 检查执行结果
            if result.returncode != 0:
                error(f"FFmpeg执行失败: {result.stderr}")
                return False
            
            # 检查输出文件是否生成
            if not os.path.exists(output_path):
                error(f"输出文件未生成: {output_path}")
                return False
            
            # 检查输出文件大小
            if os.path.getsize(output_path) == 0:
                error(f"输出文件为空: {output_path}")
                return False
            
            debug(f"片段提取成功，输出文件大小: {os.path.getsize(output_path)} 字节")
            return True
            
        except subprocess.SubprocessError as e:
            error(f"执行FFmpeg时出错: {str(e)}")
            return False
        except Exception as e:
            error(f"片段提取过程中出错: {str(e)}")
            return False
    
    @staticmethod
    def render_video(clip_paths: list[str], output_path: str, config: dict = None) -> str:
        """
        渲染最终视频，使用统一编码方式确保不同类型视频可以合并
        
        Args:
            clip_paths: 视频片段路径列表
            output_path: 输出视频路径
            config: 渲染配置参数，支持以下选项：
                - width: 输出视频宽度
                - height: 输出视频高度
                - resize_mode: 缩放模式 ('fit', 'fill', 'stretch')
                - codec: 视频编码器
                - preset: 编码预设
                - crf: 质量因子
                - framerate: 帧率
                - audio_bitrate: 音频比特率
                - transcode_params: 转码参数配置，包含以下选项：
                    - enable: 是否启用统一转码
                    - ignore_dts: 是否忽略DTS时间戳问题
                    - force_key_frames: 是否强制关键帧
                    - movflags: 输出文件格式标志
        
        Returns:
            str: 输出视频路径
        """
        import uuid
        import subprocess
        import os
        
        # 从配置文件获取默认配置
        default_config = get_video_rendering_config()
        
        # 如果没有提供配置，使用默认配置
        if config is None:
            config = default_config.copy()
        else:
            # 合并用户配置和默认配置
            for key, value in default_config.items():
                if key == 'transcode_params' and key in config:
                    # 深度合并转码参数配置
                    if isinstance(config[key], dict):
                        for param_key, param_value in value.items():
                            if param_key not in config[key]:
                                config[key][param_key] = param_value
                    else:
                        config[key] = value.copy()
                elif key not in config:
                    config[key] = value
        
        debug(f"渲染最终视频: 输出={output_path}")
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_path)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        # 如果只有一个视频，直接复制
        if len(clip_paths) == 1:
            debug("只有一个视频，直接复制")
            try:
                # 复制文件
                import shutil
                shutil.copy2(clip_paths[0], output_path)
                debug(f"复制成功，输出文件: {output_path}")
                return output_path
            except Exception as e:
                error(f"复制失败: {str(e)}")
                return output_path
        
        # 对于多个视频，先进行统一编码，然后再合并（用户要求）
        debug("处理多个视频，先统一编码再合并")
        debug(f"输入文件数量: {len(clip_paths)}")
        
        # 创建临时目录
        temp_dir = os.path.join(output_dir, 'temp')
        os.makedirs(temp_dir, exist_ok=True)
        
        # 获取配置参数
        width = config.get('width', 1920)
        height = config.get('height', 1080)
        resize_mode = config.get('resize_mode', 'fit')
        codec = config.get('codec', 'libx264')
        preset = config.get('preset', 'medium')
        crf = config.get('crf', 23)
        framerate = config.get('framerate', 30)
        audio_bitrate = config.get('audio_bitrate', '128k')
        
        # 获取FFmpeg路径
        ffmpeg_path = FFmpegUtils.find_ffmpeg()
        
        # 检查是否启用转场效果
        transition_enabled = config.get('transition', {}).get('enabled', False)
        
        # 首先对所有视频进行统一编码
        transcoded_clips = []
        try:
            debug("开始对所有视频进行统一编码")
            
            # 处理每个视频片段
            for i, clip_path in enumerate(clip_paths):
                debug(f"正在转码视频片段 {i+1}/{len(clip_paths)}: {clip_path}")
                
                # 创建临时转码输出文件
                transcode_output = os.path.join(temp_dir, f"transcoded_{i}_{str(uuid.uuid4())[:8]}.mp4")
                
                # 根据缩放模式构建视频滤镜
                if resize_mode == 'fit':
                    filter_complex = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black"
                elif resize_mode == 'fill':
                    filter_complex = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"
                else:  # stretch
                    filter_complex = f"scale={width}:{height}"
                
                # 获取转码参数配置
                transcode_params = config.get('transcode_params', {})
                enable_transcode = transcode_params.get('enable', True) or transition_enabled
                ignore_dts = transcode_params.get('ignore_dts', True)
                force_key_frames = transcode_params.get('force_key_frames', True)
                movflags = transcode_params.get('movflags', '+faststart')
                
                # 构建转码命令
                transcode_cmd = [
                    ffmpeg_path,
                    # 全局参数
                    "-y",  # 覆盖输出文件
                    # 输入参数
                    "-i", clip_path
                ]
                
                # 添加忽略DTS参数
                if ignore_dts:
                    transcode_cmd.insert(2, "-fflags")
                    transcode_cmd.insert(3, "+igndts")
                
                # 添加视频滤镜
                transcode_cmd.extend([
                    "-vf", filter_complex,
                    # 视频编码参数
                    "-c:v", codec,
                    "-preset", preset,
                    "-crf", str(crf),
                    "-r", str(framerate),
                    "-video_track_timescale", str(framerate * 1000)
                ])
                
                # 添加强制关键帧参数
                if force_key_frames:
                    transcode_cmd.extend([
                        "-force_key_frames", "expr:gte(t,n_forced*1)"
                    ])
                
                # 添加音频参数
                transcode_cmd.extend([
                    "-c:a", "aac",
                    "-b:a", audio_bitrate
                ])
                
                # 添加movflags参数
                if movflags:
                    transcode_cmd.extend([
                        "-movflags", movflags
                    ])
                
                # 添加输出文件
                transcode_cmd.append(transcode_output)
                
                debug(f"执行转码命令: {' '.join(transcode_cmd)}")
                
                # 执行转码命令
                transcode_result = subprocess.run(
                    transcode_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False
                )
                
                # 检查转码结果
                if transcode_result.returncode == 0 and os.path.exists(transcode_output):
                    file_size = os.path.getsize(transcode_output)
                    debug(f"视频片段 {i+1} 转码成功，输出文件大小: {file_size / (1024*1024):.2f} MB")
                    transcoded_clips.append(transcode_output)
                else:
                    error(f"视频片段 {i+1} 转码失败: {transcode_result.stderr}")
                    # 即使有片段转码失败，也继续尝试其他片段
            
            # 检查是否有成功转码的片段
            if not transcoded_clips:
                error("所有视频片段转码失败")
                return output_path
            
            debug(f"成功转码 {len(transcoded_clips)} 个视频片段，开始合并")
            
            # 初始化转场启用标志
            transition_enabled = config.get('transition', {}).get('enabled', True)
            debug(f"【转场调试】transition_enabled = {transition_enabled}")
            
            # 检查FFmpeg是否支持xfade滤镜
            has_xfade = False
            try:
                check_cmd = [ffmpeg_path, "-filters"]
                check_result = subprocess.run(
                    check_cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False
                )
                if "xfade" in check_result.stdout:
                    has_xfade = True
                    debug("【转场调试】FFmpeg支持xfade滤镜")
                else:
                    debug("【转场调试】FFmpeg不支持xfade滤镜")
            except Exception as e:
                debug(f"【转场调试】检查FFmpeg滤镜失败: {str(e)}")
            
            # 关键修改：如果启用了转场效果且FFmpeg支持xfade，使用带有转场的complex filtergraph
            if transition_enabled and has_xfade and len(transcoded_clips) > 1:
                debug("【转场调试】启用转场效果，直接使用complex filtergraph进行合并")
                
                # 构建带有转场效果的complex filtergraph合并命令
                cmd = [
                    ffmpeg_path,
                    "-y",  # 覆盖输出文件
                    "-fflags", "+igndts"  # 忽略可能有问题的时间戳
                ]
                
                # 添加所有转码后的视频作为输入
                for clip in transcoded_clips:
                    cmd.extend(["-i", clip])
                    debug(f"添加输入文件: {clip}")
                
                # 构建complex filtergraph
                filter_complex_parts = []
                
                # 添加音频标记
                for i in range(len(transcoded_clips)):
                    filter_complex_parts.append(f"[{i}:a]asetpts=PTS-STARTPTS[a{i}];")
                
                # 直接使用视频流（已经在转码阶段统一了尺寸）
                for i in range(len(transcoded_clips)):
                    filter_complex_parts.append(f"[{i}:v]setpts=PTS-STARTPTS[v{i}];")
                
                # 构建filter_complex
                filter_complex = "".join(filter_complex_parts)
                
                # 使用固定的简单转场参数
                debug("【转场调试】使用固定的简单转场参数")
                
                # 对于两个视频，使用最简单的转场实现
                if len(transcoded_clips) == 2:
                    debug("【转场调试】两视频简单转场处理")
                    # 完全简化的参数配置，使用固定时长1秒
                    filter_complex = "[0:v][1:v]xfade=transition=fade:duration=1[outv];[0:a][1:a]acrossfade=d=1[outa]"
                else:
                    # 对于多个视频，使用简化的处理方式
                    debug("【转场调试】多视频简单转场处理")
                    filter_complex = "[0:v][1:v]xfade=transition=fade:duration=1[merged_v];"
                    filter_complex += "[0:a][1:a]acrossfade=d=1[merged_a];"
                    
                    # 依次添加剩余视频
                    for i in range(2, len(transcoded_clips)):
                        filter_complex += f"[merged_v][{i}:v]xfade=transition=fade:duration=1[merged_v];"
                        filter_complex += f"[merged_a][{i}:a]acrossfade=d=1[merged_a];"
                    
                    # 最终输出
                    filter_complex += "[merged_v]setpts=PTS-STARTPTS[outv];[merged_a]asetpts=PTS-STARTPTS[outa]"
                
                debug(f"【转场调试】最终filtergraph: {filter_complex}")
                
                # 完成命令构建，使用更简单的参数
                cmd.extend([
                    "-filter_complex", filter_complex,
                    "-map", "[outv]",
                    "-map", "[outa]",
                    "-c:v", "libx264",  # 使用固定编码器
                    "-preset", "ultrafast",  # 使用更快的预设
                    "-crf", "28",  # 降低质量要求以提高兼容性
                    "-c:a", "aac",
                    "-b:a", "128k",  # 降低音频比特率
                    output_path
                ])
                
                debug(f"执行转场合并命令: {' '.join(cmd)}")
                
                # 执行命令
                merge_result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False
                )
                
                # 检查结果
                if merge_result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    file_size = os.path.getsize(output_path)
                    debug(f"转场合并成功，输出文件大小: {file_size} 字节")
                    return output_path
                else:
                    error(f"转场合并失败: {merge_result.stderr}")
                    # 转场合并失败，继续尝试常规合并
            
            # 常规合并（没有转场效果或转场合并失败时使用）
            debug("使用常规concat方式合并视频片段")
            
            # 创建合并文件列表
            merge_list_file = os.path.join(temp_dir, f"merge_list_{str(uuid.uuid4())[:8]}.txt")
            
            # 写入文件列表
            with open(merge_list_file, 'w', encoding='utf-8') as f:
                for transcode_path in transcoded_clips:
                    # 转换为绝对路径并处理Windows路径格式
                    abs_path = os.path.abspath(transcode_path).replace('\\', '/')
                    f.write(f"file '{abs_path}'\n")
                    debug(f"添加到合并列表: {abs_path}")
            
            # 构建合并命令
            merge_cmd = [
                ffmpeg_path,
                "-y",
                "-f", "concat",
                "-safe", "0",
                "-i", merge_list_file,
                "-c", "copy",  # 由于已经统一编码，可以直接copy
                output_path
            ]
            
            debug(f"执行合并命令: {' '.join(merge_cmd)}")
            
            # 执行合并命令
            merge_result = subprocess.run(
                merge_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False
            )
            
            # 检查合并结果
            if merge_result.returncode == 0 and os.path.exists(output_path):
                file_size = os.path.getsize(output_path)
                debug(f"视频合并成功，输出文件大小: {file_size / (1024*1024):.2f} MB")
                
                # 计算输入文件总大小
                total_input_size = sum([os.path.getsize(v) for v in transcoded_clips])
                
                # 验证文件大小
                if file_size > total_input_size * 0.8:  # 应该接近输入文件总和
                    debug("✓ 视频合并成功，输出文件大小合理")
                    return output_path
                else:
                    debug("合并输出文件大小异常，尝试转码模式合并")
                    
                    # 如果直接copy合并失败，尝试转码合并
                    # 获取转码参数配置
                    transcode_params = config.get('transcode_params', {})
                    movflags = transcode_params.get('movflags', '+faststart')
                    
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
                    
                    if transcode_merge_result.returncode == 0 and os.path.exists(output_path):
                        file_size = os.path.getsize(output_path)
                        debug(f"转码合并成功，输出文件大小: {file_size / (1024*1024):.2f} MB")
                        return output_path
                    else:
                        error(f"转码合并失败: {transcode_merge_result.stderr}")
                        return output_path
            else:
                error(f"合并失败: {merge_result.stderr}")
                return output_path
                
        except Exception as e:
            error(f"视频处理出错: {str(e)}")
            import traceback
            error(f"异常详情: {traceback.format_exc()}")
            return output_path
        finally:
            # 清理临时文件
            # 删除合并列表文件
            if 'merge_list_file' in locals() and os.path.exists(merge_list_file):
                try:
                    os.remove(merge_list_file)
                    debug(f"已删除临时列表文件: {merge_list_file}")
                except:
                    pass
            
            # 删除转码后的临时文件
            for clip in transcoded_clips:
                if os.path.exists(clip):
                    try:
                        os.remove(clip)
                        debug(f"已删除临时转码文件: {clip}")
                    except:
                        pass
    
    @staticmethod
    def _generate_transition_filter(video_index1: int, video_index2: int, transition_type: str, duration: float, width: int, height: int) -> tuple:
        """
        生成转场滤镜
        
        Args:
            video_index1: 第一个视频索引
            video_index2: 第二个视频索引
            transition_type: 转场类型
            duration: 转场时长（秒）
            width: 视频宽度
            height: 视频高度
            
        Returns:
            tuple: (视频滤镜部分, 音频滤镜部分)
        """
        import random
        
        # 使用固定的淡入淡出转场，这是最可靠的转场类型
        transition_type = 'fade'
        debug(f"使用固定转场类型: {transition_type}, 时长: {duration}秒")
        
        # 为了确保转场效果正确应用，我们使用一种更简单的方法
        # 对于第一个视频对，直接连接
        if video_index1 == 0:
            # 第一个转场直接连接两个视频，使用简单的淡入淡出效果
            video_filter = f"[v{video_index1}][v{video_index2}]xfade=transition={transition_type}:duration={duration}:offset=0[vt];"
            audio_filter = f"[a{video_index1}][a{video_index2}]acrossfade=d={duration}[at];"
        else:
            # 对于后续视频，连接到前一个转场的输出
            video_filter = f"[vt][v{video_index2}]xfade=transition={transition_type}:duration={duration}:offset=0[vt];"
            audio_filter = f"[at][a{video_index2}]acrossfade=d={duration}[at];"
        
        debug(f"生成的视频滤镜: {video_filter}")
        debug(f"生成的音频滤镜: {audio_filter}")
        
        return video_filter, audio_filter
    
    @staticmethod
    def _render_with_transcoding(clip_paths: list[str], output_path: str, config: dict) -> str:
        """
        使用转码方式渲染视频（当直接合并失败时使用）
        
        Args:
            clip_paths: 视频片段路径列表
            output_path: 输出视频路径
            config: 渲染配置参数
            
        Returns:
            str: 输出视频路径
        """
        debug(f"使用转码方式渲染视频，基于FFmpeg官方文档优化")
        
        try:
            # 获取FFmpeg路径
            ffmpeg_path = FFmpegUtils.find_ffmpeg()
            
            # 根据FFmpeg官方文档，确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)
            
            # 确保临时目录存在
            temp_dir = os.path.join(output_dir, "temp")
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir, exist_ok=True)
            
            # 策略1：使用concat协议（符合FFmpeg官方文档 3.2 Transcoding）
            debug("策略1 - 使用concat协议进行转码合并")
            
            # 获取配置参数
            width = config.get('width', 1920)
            height = config.get('height', 1080)
            resize_mode = config.get('resize_mode', 'fit')
            codec = config.get('codec', 'libx264')
            preset = config.get('preset', 'medium')
            crf = config.get('crf', 23)
            framerate = config.get('framerate', 30)
            audio_bitrate = config.get('audio_bitrate', '128k')
            
            # 打印输入文件信息和大小
            total_input_size = 0
            for i, clip in enumerate(clip_paths):
                clip_size = os.path.getsize(clip)
                total_input_size += clip_size
                debug(f"输入文件 {i+1}: {clip}, 大小: {clip_size} 字节")
            debug(f"输入文件总大小: {total_input_size} 字节")
            
            # 根据缩放模式添加视频滤镜
            if resize_mode == 'fit':
                filter_complex = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black"
            elif resize_mode == 'fill':
                filter_complex = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"
            else:  # stretch
                filter_complex = f"scale={width}:{height}"
            
            # 创建临时文件列表（符合FFmpeg文档中的concat demuxer用法）
            temp_list_file = os.path.join(temp_dir, f"ffmpeg_list_{str(uuid.uuid4())[:8]}.txt")
            try:
                # 写入临时文件列表，改进路径处理
                with open(temp_list_file, 'w', encoding='utf-8') as f:
                    for i, clip in enumerate(clip_paths):
                        # 确保使用正确的路径 - 转换为正斜杠以避免Windows路径问题
                        abs_clip_path = os.path.abspath(clip).replace('\\', '/')
                        f.write(f"file '{abs_clip_path}'\n")
                        debug(f"添加到策略1合并列表: {abs_clip_path}")
                
                # 构建增强型命令，添加更健壮的参数和统一尺寸处理
                cmd = [
                    ffmpeg_path,
                    # 全局参数
                    "-y",  # 覆盖输出文件
                    # 输入参数 - 添加时间戳处理
                    "-fflags", "+igndts",  # 忽略可能有问题的时间戳
                    "-f", "concat",  # 指定输入格式为concat
                    "-safe", "0",     # 允许绝对路径
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
                
                # 检查执行结果 - 更严格的验证
                if result.returncode == 0 and os.path.exists(output_path):
                    output_size = os.path.getsize(output_path)
                    debug(f"策略1转码完成，输出文件大小: {output_size} 字节")
                    
                    # 检查文件大小是否合理（至少应该大于单个文件的一小部分）
                    min_input_size = min([os.path.getsize(clip) for clip in clip_paths])
                    if output_size > min_input_size * 0.1:  # 至少应该大于最小输入文件的10%
                        debug(f"策略1转码成功，输出文件大小合理")
                        return output_path
                    else:
                        warning(f"策略1输出文件大小异常小: {output_size} 字节（预期应接近输入文件总大小: {total_input_size} 字节），尝试其他策略")
                        # 删除异常小的输出文件
                        if os.path.exists(output_path):
                            os.remove(output_path)
                else:
                    error(f"策略1转码失败: {result.stderr}")
            finally:
                # 清理临时文件
                if os.path.exists(temp_list_file):
                    try:
                        os.remove(temp_list_file)
                        debug(f"已删除临时列表文件: {temp_list_file}")
                    except Exception as e:
                        warning(f"删除临时文件失败: {str(e)}")
            
            # 策略2：使用concat协议（更可靠的方法，替换原来的complex filtergraph）
            debug("策略2 - 使用concat协议合并视频")
            debug("创建文件列表进行concat合并")
            
            # 获取配置参数
            width = config.get('width', 1920)
            height = config.get('height', 1080)
            resize_mode = config.get('resize_mode', 'fit')
            codec = config.get('codec', 'libx264')
            preset = config.get('preset', 'medium')
            crf = config.get('crf', 23)
            framerate = config.get('framerate', 30)
            audio_bitrate = config.get('audio_bitrate', '128k')
            
            # 创建文件列表
            list_file = os.path.join(temp_dir, f"ffmpeg_list_{str(uuid.uuid4())[:8]}.txt")
            try:
                # Windows路径需要特殊处理
                with open(list_file, 'w', encoding='utf-8') as f:
                    for video_path in clip_paths:
                        # 转换为绝对路径并处理Windows路径格式
                        abs_path = os.path.abspath(video_path).replace('\\', '/')
                        f.write(f"file '{abs_path}'\n")
                        debug(f"添加到列表: {abs_path}")
                
                debug(f"文件列表创建完成: {list_file}")
                
                # 基于缩放模式构建视频滤镜
                if resize_mode == 'fit':
                    filter_complex = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black"
                elif resize_mode == 'fill':
                    filter_complex = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"
                else:  # stretch
                    filter_complex = f"scale={width}:{height}"
                
                # 构建命令 - 使用concat协议并进行转码确保兼容性
                cmd = [
                    ffmpeg_path,
                    # 全局参数
                    "-y",  # 覆盖输出文件
                    # 添加时间戳处理参数
                    "-fflags", "+igndts",
                    # 使用concat格式
                    "-f", "concat",
                    "-safe", "0",
                    "-i", list_file,
                    # 视频滤镜统一尺寸
                    "-vf", filter_complex,
                    # 视频编码参数
                    "-c:v", codec,
                    "-preset", preset,
                    "-crf", str(crf),
                    "-r", str(framerate),
                    "-video_track_timescale", str(framerate * 1000),
                    # 强制关键帧
                    "-force_key_frames", "expr:gte(t,n_forced*1)",
                    # 音频参数
                    "-c:a", "aac",
                    "-b:a", audio_bitrate,
                    # 确保文件兼容性
                    "-movflags", "+faststart",
                    # 输出文件
                    output_path
                ]
                
                debug(f"策略2命令: {' '.join(cmd)}")
                
                result = subprocess.run(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    check=False,
                    shell=False
                )
                
                # 验证输出文件
                if result.returncode == 0 and os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    debug(f"策略2转码完成，输出文件大小: {file_size} 字节")
                    
                    # 检查文件大小是否合理
                    total_input_size = sum([os.path.getsize(v) for v in clip_paths])
                    debug(f"输入文件总大小: {total_input_size} 字节")
                    debug(f"输出文件大小: {file_size} 字节")
                    
                    # 对于转码模式，输出文件大小可能会有所不同，但应该合理
                    if file_size > min(total_input_size * 0.5, 1024 * 1024):  # 至少应该大于输入文件总和的50%或1MB
                        debug(f"策略2转码成功，输出文件大小合理")
                        return output_path
                    else:
                        warning(f"策略2输出文件大小异常: {file_size} 字节，尝试策略3")
                        # 删除异常小的输出文件
                        if os.path.exists(output_path):
                            os.remove(output_path)
                else:
                    error(f"策略2转码失败: {result.stderr}")
            except Exception as e:
                error(f"策略2执行异常: {str(e)}")
            finally:
                # 清理文件列表
                if os.path.exists(list_file):
                    try:
                        os.remove(list_file)
                        debug(f"已删除临时列表文件: {list_file}")
                    except Exception as e:
                        warning(f"删除临时文件失败: {str(e)}")
            
            # 如果策略2失败，尝试使用complex filtergraph作为备选
            debug("策略2备选 - 使用complex filtergraph进行转码合并")
            
            # 构建增强型命令
            cmd = [
                ffmpeg_path,
                # 全局参数
                "-y",  # 覆盖输出文件
                # 添加时间戳处理参数
                "-fflags", "+igndts"
            ]
            
            # 添加所有输入文件并记录路径
            for i, clip in enumerate(clip_paths):
                cmd.extend(["-i", clip])
                debug(f"策略2备选添加输入文件 {i+1}: {clip}")
            
            # 构建complex filtergraph，包含尺寸统一处理
            filter_complex_parts = []
            
            # 检查是否启用转场效果
            transition_enabled = config.get('transition', {}).get('enabled', False)
            transition_type = config.get('transition', {}).get('type', 'crossfade')
            transition_duration = config.get('transition', {}).get('duration', 1.0)
            
            # 为每个视频流添加尺寸调整滤镜
            for i in range(len(clip_paths)):
                # 为每个视频流添加尺寸调整
                if resize_mode == 'fit':
                    scale_filter = f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black[v{i}];"
                elif resize_mode == 'fill':
                    scale_filter = f"[{i}:v]scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}[v{i}];"
                else:  # stretch
                    scale_filter = f"[{i}:v]scale={width}:{height}[v{i}];"
                
                filter_complex_parts.append(scale_filter)
            
            # 添加音频标记
            for i in range(len(clip_paths)):
                filter_complex_parts.append(f"[{i}:a]asetpts=PTS-STARTPTS[a{i}];")
            
            # 根据是否启用转场构建不同的filtergraph
            if transition_enabled and len(clip_paths) > 1:
                debug(f"【转场调试】启用转场效果: {transition_type}, 时长: {transition_duration}秒")
                debug(f"【转场调试】视频数量: {len(clip_paths)}")
                
                # 使用最简单的转场实现，只处理视频尺寸调整和基本转场
                filter_complex = "".join(filter_complex_parts)
                
                # 对于两个视频，使用最基本的转场语法
                if len(clip_paths) == 2:
                    debug("【转场调试】使用两视频极简转场方案")
                    # 最简单的xfade语法，确保使用fade类型（兼容性最好）
                    # 这里使用明确的参数格式
                    filter_complex += f"[v0][v1]xfade=transition=fade:duration={transition_duration}:offset=0[outv];"
                    filter_complex += f"[a0][a1]acrossfade=d={transition_duration}[outa]"
                else:
                    # 对于多个视频，我们使用分步处理的方法
                    debug("【转场调试】使用多视频分步转场方案")
                    
                    # 先处理前两个视频的转场
                    filter_complex += f"[v0][v1]xfade=transition=fade:duration={transition_duration}:offset=0[merged_v];"
                    filter_complex += f"[a0][a1]acrossfade=d={transition_duration}[merged_a];"
                    
                    # 然后依次添加剩余视频
                    for i in range(2, len(clip_paths)):
                        # 对每个新视频应用转场
                        filter_complex += f"[merged_v][v{i}]xfade=transition=fade:duration={transition_duration}:offset=0[merged_v];"
                        filter_complex += f"[merged_a][a{i}]acrossfade=d={transition_duration}[merged_a];"
                    
                    # 最终输出
                    filter_complex += "[merged_v]setpts=PTS-STARTPTS[outv];[merged_a]asetpts=PTS-STARTPTS[outa]"
                
                debug(f"【转场调试】最终filtergraph: {filter_complex}")
            else:
                debug(f"【转场调试】转场未启用或视频数量不足: transition_enabled={transition_enabled}, video_count={len(clip_paths)}")
                # 常规合并，不使用转场
                # 构建concat部分
                concat_inputs = []
                for i in range(len(clip_paths)):
                    concat_inputs.extend([f"[v{i}]", f"[a{i}]"])
                
                filter_complex = "".join(filter_complex_parts)
                filter_complex += "".join(concat_inputs)
                filter_complex += f"concat=n={len(clip_paths)}:v=1:a=1[outv][outa]"
            
            debug(f"构建的filtergraph: {filter_complex}")
            
            # 添加filter_complex和增强型输出参数
            cmd.extend([
                # Filtergraph参数
                "-filter_complex", filter_complex,
                # Stream mapping
                "-map", "[outv]",  # 映射视频输出
                "-map", "[outa]",  # 映射音频输出
                # 视频编码参数 - 使用配置的值
                "-c:v", codec,
                "-preset", preset,
                "-crf", str(crf),
                "-r", str(framerate),
                "-video_track_timescale", str(framerate * 1000),
                # 强制关键帧
                "-force_key_frames", "expr:gte(t,n_forced*1)",
                # 音频编码参数
                "-c:a", "aac",
                "-b:a", audio_bitrate,
                # 确保文件兼容性
                "-movflags", "+faststart",
                # 输出文件
                output_path
            ])
            
            debug(f"策略2备选命令: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
                shell=False
            )
            
            # 检查执行结果
            if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                file_size = os.path.getsize(output_path)
                debug(f"策略2备选转码成功，输出文件大小: {file_size} 字节")
                
                # 检查文件大小是否合理
                total_input_size = sum([os.path.getsize(v) for v in clip_paths])
                if file_size > min(total_input_size * 0.5, 1024 * 1024):  # 至少应该大于输入文件总和的50%或1MB
                    debug(f"策略2备选转码成功，输出文件大小合理")
                    return output_path
                else:
                    warning(f"策略2备选输出文件大小异常: {file_size} 字节")
                    # 删除异常小的输出文件
                    if os.path.exists(output_path):
                        os.remove(output_path)
            else:
                error(f"策略2备选转码失败: {result.stderr}")
            
            # 策略3：逐个转码后再合并（最通用的降级方案）
            debug("策略3 - 逐个转码后再合并")
            
            # 为每个片段创建转码后的临时文件
            transcoded_clips = []
            try:
                # 获取配置参数
                width = config.get('width', 1920)
                height = config.get('height', 1080)
                resize_mode = config.get('resize_mode', 'fit')
                codec = config.get('codec', 'libx264')
                preset = config.get('preset', 'medium')
                crf = config.get('crf', 23)
                framerate = config.get('framerate', 30)
                audio_bitrate = config.get('audio_bitrate', '128k')
                
                debug(f"使用配置: 尺寸={width}x{height}, 缩放模式={resize_mode}, 编码器={codec}")
                
                # 处理每个片段，统一尺寸和编码
                for i, clip in enumerate(clip_paths):
                    debug(f"处理片段 {i+1}/{len(clip_paths)}: {clip}")
                    # 使用统一的临时目录
                    transcode_output = os.path.join(temp_dir, f"transcoded_{i}_{str(uuid.uuid4())[:8]}.mp4")
                    
                    # 构建转码命令
                    transcode_cmd = [
                        ffmpeg_path,
                        # 全局参数
                        "-y",
                        # 输入文件参数
                        "-fflags", "+igndts",  # 忽略可能有问题的时间戳
                        "-i", clip,
                    ]
                    
                    # 根据缩放模式添加视频滤镜
                    # 这是处理不同比例视频的关键
                    if resize_mode == 'fit':
                        # 保持原始比例，添加黑边以适应目标尺寸
                        filter_complex = f"scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2:black"
                    elif resize_mode == 'fill':
                        # 保持原始比例，裁剪以填充目标尺寸
                        filter_complex = f"scale={width}:{height}:force_original_aspect_ratio=increase,crop={width}:{height}"
                    else:  # stretch
                        # 直接拉伸到目标尺寸
                        filter_complex = f"scale={width}:{height}"
                    
                    transcode_cmd.extend([
                        # 视频滤镜
                        "-vf", filter_complex,
                        # 转码参数
                        "-c:v", codec,
                        "-preset", preset,
                        "-crf", str(crf),
                        "-r", str(framerate),
                        "-video_track_timescale", str(framerate * 1000),
                        # 音频参数
                        "-c:a", "aac",
                        "-b:a", audio_bitrate,
                        # 强制关键帧
                        "-force_key_frames", "expr:gte(t,n_forced*1)",
                        # 确保文件兼容性
                        "-movflags", "+faststart",
                        # 输出文件
                        transcode_output
                    ])
                    
                    debug(f"转码单个片段 {i+1}/{len(clip_paths)}: {clip}")
                    
                    transcode_result = subprocess.run(
                        transcode_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=False,
                        shell=False
                    )
                    
                    if transcode_result.returncode == 0 and os.path.exists(transcode_output) and os.path.getsize(transcode_output) > 0:
                        debug(f"片段 {i+1} 转码成功，大小: {os.path.getsize(transcode_output)} 字节")
                        transcoded_clips.append(transcode_output)
                    else:
                        error(f"片段 {i+1} 转码失败: {transcode_result.stderr}")
                        all_transcoded = False
                        # 即使有片段失败，也继续尝试其他片段
                
                # 检查是否有成功转码的片段
                if not transcoded_clips:
                    error("没有成功转码的片段")
                    # 所有片段都转码失败，返回空结果
                    
                # 如果有成功转码的片段，尝试合并它们
                debug(f"成功转码 {len(transcoded_clips)} 个片段，开始合并")
                
                # 使用concat协议合并转码后的片段
                merge_list_file = os.path.join(temp_dir, f"merge_list_{str(uuid.uuid4())[:8]}.txt")
                try:
                    with open(merge_list_file, 'w', encoding='utf-8') as f:
                        for i, clip in enumerate(transcoded_clips):
                            # 更安全的路径处理
                            abs_clip_path = os.path.abspath(clip)
                            # Windows路径处理 - 避免双重转义问题
                            if '\\' in abs_clip_path:
                                # 在ffmpeg concat文件中，路径不需要额外转义
                                # 只需要确保使用单引号包裹
                                abs_clip_path = abs_clip_path.replace('\\', '/')
                            f.write(f"file '{abs_clip_path}'\n")
                            debug(f"添加到合并列表: {abs_clip_path}")
                        
                    # 使用配置的参数进行合并
                    debug("使用转码方式合并片段以确保兼容性")
                    transcode_merge_cmd = [
                        ffmpeg_path,
                        "-y",
                        "-f", "concat",
                        "-safe", "0",
                        "-i", merge_list_file,
                        # 输入参数
                        "-fflags", "+igndts",  # 忽略时间戳
                        # 输出参数
                        "-c:v", codec,
                        "-preset", preset,
                        "-crf", str(crf),
                        "-r", str(framerate),
                        "-video_track_timescale", str(framerate * 1000),
                        "-c:a", "aac",
                        "-b:a", audio_bitrate,
                        # 强制关键帧，确保正确连接
                        "-force_key_frames", "expr:gte(t,n_forced*1)",
                        # 确保文件兼容性
                        "-movflags", "+faststart",
                        output_path
                    ]
                    
                    debug(f"合并命令: {' '.join(transcode_merge_cmd)}")
                    
                    transcode_merge_result = subprocess.run(
                        transcode_merge_cmd,
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        check=False,
                        shell=False
                    )
                    
                    if transcode_merge_result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                        debug(f"合并成功，输出文件大小: {os.path.getsize(output_path)} 字节")
                        return output_path
                    else:
                        error(f"合并失败: {transcode_merge_result.stderr}")
                finally:
                    if os.path.exists(merge_list_file):
                        try:
                            os.remove(merge_list_file)
                            debug(f"已删除合并列表文件: {merge_list_file}")
                        except Exception as e:
                            warning(f"删除合并列表文件失败: {str(e)}")
            finally:
                # 清理临时转码文件
                for clip in transcoded_clips:
                    if os.path.exists(clip):
                        try:
                            os.remove(clip)
                            debug(f"已删除临时转码文件: {clip}")
                        except Exception as e:
                            warning(f"删除临时转码文件失败: {str(e)}")
            
            # 所有策略都失败
            error(f"所有FFmpeg转码策略都失败")
            return output_path
            
        except Exception as e:
            error(f"转码渲染过程中出错: {str(e)}")
            import traceback
            error(f"错误堆栈: {traceback.format_exc()}")
            return output_path
    
    @staticmethod
    def get_video_info(video_path: str) -> dict:
        """
        获取视频文件信息
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            dict: 包含视频信息的字典，如果获取失败返回空字典
        """
        try:
            # 获取FFmpeg路径
            ffmpeg_path = FFmpegUtils.find_ffmpeg()
            
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
                import json
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