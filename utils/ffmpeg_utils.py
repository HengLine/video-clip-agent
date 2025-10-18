"""
FFmpeg工具类，用于封装所有FFmpeg相关的功能
提供视频片段提取、视频合并、转码等功能的统一接口
https://ffmpeg.org/ffmpeg.html
"""
import os
import subprocess
import uuid

from config.config import get_video_rendering_config
from hengline.logger import debug, error, warning, info
from utils.ffmpeg_env_utils import find_ffmpeg, check_xfade_support
from utils.ffmpeg_run_utils import get_video_duration, merge_videos, transcode_merge_video, codec_video, \
    scale_video, apply_xfade_transition, apply_basic_transition
from utils.log_utils import print_log_exception


class FFmpegUtils:
    """
    FFmpeg工具类，封装所有FFmpeg相关操作
    """

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
            ffmpeg_path = find_ffmpeg()
        except FileNotFoundError:
            return False

        # 构建FFmpeg命令
        cmd = [
            ffmpeg_path,
            # 全局参数
            "-y",  # 覆盖输出文件
            # 输入参数
            "-ss", str(start_time),  # 开始时间
            "-i", input_path,  # 输入文件
        ]

        # 只有当end_time不为None时才添加-to参数
        if end_time is not None:
            cmd.extend(["-to", str(end_time)])

        # 添加输出参数
        cmd.extend([
            "-c", "copy",  # 复制流（无损快速）
            "-map", "0",  # 映射所有流
            output_path  # 输出文件
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
    def apply_video_transitions(clip_paths: list[str], output_path: str, transition_type: str = None,
                                transition_duration: float = None, width: int = 1920, height: int = 1080,
                                resize_mode: str = 'fit') -> str | None:
        """
        独立的视频转场功能，专门用于在视频片段之间添加转场效果
        使用分步合并的方式，每次只处理两个视频片段，避免复杂的滤镜组合
        当xfade滤镜不可用时，使用基础的淡入淡出效果作为备选方案
        
        参数:
        clip_paths: 视频片段路径列表
        output_path: 输出文件路径
        transition_type: 转场类型，默认'fade'
        transition_duration: 转场时长（秒），默认1.0秒
        width: 输出视频宽度
        height: 输出视频高度
        resize_mode: 缩放模式 ('fit', 'fill', 'stretch')
        
        返回:
        成功时返回输出文件路径，失败时返回None
        """
        try:
            # 确保FFmpeg可用
            ffmpeg_path = find_ffmpeg()

            # 路径参数验证
            if not output_path or not isinstance(output_path, str):
                error("输出路径必须是有效的字符串")
                return None

            if not clip_paths or len(clip_paths) < 2:
                error("至少需要两个视频片段才能应用转场效果")
                return None

            # 验证所有输入视频路径并过滤
            valid_clip_paths = []
            for i, clip_path in enumerate(clip_paths):
                if not clip_path or not isinstance(clip_path, str):
                    error(f"视频片段 {i + 1} 的路径无效或为None")
                    continue  # 跳过无效路径，继续检查其他路径
                if not os.path.exists(clip_path):
                    error(f"视频片段 {i + 1} 不存在: {clip_path}")
                    continue  # 跳过不存在的路径
                valid_clip_paths.append(clip_path)

            # 如果过滤后没有有效的视频片段，返回None
            if len(valid_clip_paths) < 2:
                error(f"有效视频片段数量不足，需要至少2个有效的视频片段，当前有: {len(valid_clip_paths)}")
                return None

            # 使用过滤后的有效路径列表
            clip_paths = valid_clip_paths

            # 从配置文件获取转场设置
            try:
                rendering_config = get_video_rendering_config()
                if rendering_config is None:
                    rendering_config = {}
                transition_config = rendering_config.get('transition', {})
                if transition_config is None:
                    transition_config = {}
            except Exception as e:
                error(f"获取配置时出错: {str(e)}")
                # 使用默认配置
                transition_config = {}

            # 如果未指定转场类型或时长，从配置中获取
            if transition_type is None:
                transition_type = transition_config.get('type', 'fade')
            elif transition_type.lower() == 'random':
                # 如果是随机模式，从支持的转场类型中随机选择
                import random
                transition_type = random.choice(
                    transition_config.get('types', ["fade", "wipeleft", "wiperight", "wipeup", "wipedown", "slideleft", "slideright", "slideup", "slidedown"]))
                debug(f"随机选择转场类型: {transition_type}")

            if transition_duration is None:
                transition_duration = transition_config.get('duration', 1.0)  # 使用配置文件中的默认值

            info(f"开始应用转场效果: 类型={transition_type}, 时长={transition_duration}秒")
            debug(f"处理 {len(clip_paths)} 个视频片段")

            # 创建临时目录
            try:
                output_dir = os.path.dirname(output_path)
                temp_dir = os.path.join(output_dir, "temp_transition")
                os.makedirs(temp_dir, exist_ok=True)
            except Exception as e:
                error(f"创建目录失败: {str(e)}")
                return None

            # 首先对所有视频进行统一尺寸处理
            scaled_files = []
            for i, clip_path in enumerate(clip_paths):
                scaled_output = os.path.join(temp_dir, f"scaled_{i}_{os.path.basename(clip_path)}")

                debug(f"调整视频尺寸: {clip_path} -> {scaled_output}")
                # 调用ffmpeg_run_utils中的scale_video函数
                success, stderr = scale_video(clip_path, scaled_output, width, height, resize_mode, ffmpeg_path)

                if success:
                    scaled_files.append(scaled_output)
                else:
                    error(f"调整视频尺寸失败: {stderr}")
                    # 清理已生成的临时文件
                    for f in scaled_files:
                        if os.path.exists(f):
                            os.remove(f)
                    return None

            # 检查FFmpeg是否支持xfade滤镜
            use_xfade = check_xfade_support(ffmpeg_path)
            debug(f"FFmpeg {'支持' if use_xfade else '不支持'} xfade滤镜")

            # 第二步：逐步合并视频
            current_merged = scaled_files[0]
            temp_files_to_clean = []

            for i in range(1, len(scaled_files)):
                next_video = scaled_files[i]
                temp_output = os.path.join(temp_dir, f"temp_merged_{i}.mp4")

                # 获取当前视频的时长
                current_duration = get_video_duration(current_merged, ffmpeg_path, 3.0)
                next_duration = get_video_duration(next_video, ffmpeg_path, 3.0)

                debug(f"合并 {os.path.basename(current_merged)} ({current_duration}秒) 和 {os.path.basename(next_video)} ({next_duration}秒)")

                if use_xfade:
                    # 尝试使用xfade滤镜，# 减掉 transition_duration 方式会减少时长（视频重叠部分直接剪掉）
                    offset = current_duration  # - transition_duration
                    debug("尝试使用xfade滤镜进行转场")
                    # 调用ffmpeg_run_utils中的apply_xfade_transition函数
                    success, stderr = apply_xfade_transition(
                        current_merged, next_video, temp_output, transition_type,
                        transition_duration, offset, ffmpeg_path
                    )

                    # 检查xfade是否成功
                    if not success:
                        warning(f"xfade转场失败，将回退到基础淡入淡出方案: {stderr}")
                        use_xfade = False
                    else:
                        # xfade成功，继续处理
                        info("xfade转场成功")

                if not use_xfade:
                    # 使用基础的淡入淡出方案
                    info("使用基础淡入淡出方案")
                    # 调用ffmpeg_run_utils中的apply_basic_transition函数
                    success, stderr = apply_basic_transition(
                        current_merged, next_video, temp_output, transition_duration,
                        temp_dir, ffmpeg_path
                    )

                    if not success:
                        error(f"应用基础转场失败: {stderr}")
                        # 清理临时文件
                        for f in temp_files_to_clean + scaled_files:
                            if os.path.exists(f):
                                os.remove(f)
                        if os.path.exists(current_merged) and current_merged != scaled_files[0]:
                            os.remove(current_merged)
                        return None

                # 记录需要清理的临时文件
                if i > 1:  # 保留第一个缩放文件直到完成
                    temp_files_to_clean.append(current_merged)

                # 更新当前合并结果
                current_merged = temp_output

            # 将最终合并结果移动到输出路径
            import shutil
            shutil.move(current_merged, output_path)

            # 清理所有临时文件
            for f in temp_files_to_clean + scaled_files:
                if os.path.exists(f):
                    os.remove(f)

            # 清理临时目录
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir, ignore_errors=True)

            debug(f"转场效果应用成功，输出文件: {output_path}")
            return output_path

        except Exception as e:
            error(f"应用转场效果时发生异常: {str(e)}")
            print_log_exception()
            # 清理失败的输出文件
            if os.path.exists(output_path):
                os.remove(output_path)
            return None

    @staticmethod
    def render_video(clip_paths: list[str], output_path: str, config: dict = None) -> str | None:
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

        Returns:
            str: 输出视频路径
        """
        # 路径参数验证
        if not output_path or not isinstance(output_path, str):
            error("输出路径必须是有效的字符串")
            return None

        if not clip_paths or not isinstance(clip_paths, list) or len(clip_paths) == 0:
            error("至少需要一个视频片段")
            return None

        # 验证所有输入视频路径
        valid_clip_paths = []
        for i, clip_path in enumerate(clip_paths):
            if not clip_path or not isinstance(clip_path, str):
                error(f"视频片段 {i + 1} 的路径无效")
                continue
            if not os.path.exists(clip_path):
                error(f"视频片段 {i + 1} 不存在: {clip_path}")
                continue
            valid_clip_paths.append(clip_path)

        if not valid_clip_paths:
            error("没有有效的视频片段可供处理")
            return None

        # 更新clip_paths为有效路径列表
        clip_paths = valid_clip_paths

        # 从配置文件获取默认配置
        merge_list_file = None
        try:
            default_config = get_video_rendering_config()
            if default_config is None:
                default_config = {}
        except Exception as e:
            error(f"获取默认配置失败: {str(e)}")
            default_config = {}

        # 如果没有提供配置，使用默认配置
        if config is None:
            config = default_config.copy()
        else:
            # 合并用户配置和默认配置
            try:
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
            except Exception as e:
                error(f"合并配置时出错: {str(e)}")
                config = default_config.copy()

        debug(f"渲染最终视频: 输出={output_path}")

        # 确保输出目录存在
        try:
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
        except Exception as e:
            error(f"创建输出目录失败: {str(e)}")
            return None

        # 如果只有一个视频，直接复制
        if len(clip_paths) == 1:
            debug("只有一个视频，直接复制")
            try:
                # 复制文件
                import shutil
                if os.path.exists(clip_paths[0]):  # 再次检查文件是否存在
                    shutil.copy2(clip_paths[0], output_path)
                    debug(f"复制成功，输出文件: {output_path}")
                    return output_path
                else:
                    error(f"源文件不存在: {clip_paths[0]}")
                    return None
            except Exception as e:
                error(f"复制失败: {str(e)}")
                return None

        # 对于多个视频，先进行统一编码，然后再合并（用户要求）
        debug("处理多个视频，先统一编码再合并")
        debug(f"输入文件数量: {len(clip_paths)}")

        # 创建临时目录
        try:
            temp_dir = os.path.join(output_dir, 'temp')
            os.makedirs(temp_dir, exist_ok=True)
        except Exception as e:
            error(f"创建临时目录失败: {str(e)}")
            return None

        # 获取FFmpeg路径
        ffmpeg_path = find_ffmpeg()

        # 检查是否启用转场效果
        transition_enabled = config.get('transition', {}).get('enabled', False)

        # 获取转码参数配置，包含enable_transcode变量
        transcode_params = config.get('transcode_params', {})
        enable_transcode = transcode_params.get('enable', False) or transition_enabled

        # 首先对所有视频进行统一编码
        transcoded_clips = []
        try:
            debug("开始对所有视频进行统一编码")

            # 处理每个视频片段
            for i, clip_path in enumerate(clip_paths):
                debug(f"正在转码视频片段 {i + 1}/{len(clip_paths)}: {clip_path}")

                # 创建临时转码输出文件
                transcode_output = os.path.join(temp_dir, f"transcoded_{i}_{str(uuid.uuid4())[:8]}.mp4")

                # 直接调用ffmpeg_run_utils中的方法进行单个视频转码
                # 为单个视频创建临时文件列表
                temp_list_file = os.path.join(temp_dir, f"single_clip_{i}_{str(uuid.uuid4())[:8]}.txt")
                with open(temp_list_file, 'w', encoding='utf-8') as f:
                    abs_path = os.path.abspath(clip_path).replace('\\', '/')
                    f.write(f"file '{abs_path}'\n")

                # 调用codec_video方法进行转码
                transcode_result, transcode_stderr = codec_video(temp_list_file, transcode_output, config, ffmpeg_path)

                # 清理临时列表文件
                if os.path.exists(temp_list_file):
                    try:
                        os.remove(temp_list_file)
                    except:
                        pass

                # 检查转码结果
                if transcode_result and os.path.exists(transcode_output):
                    file_size = os.path.getsize(transcode_output)
                    debug(f"视频片段 {i + 1} 转码成功，输出文件大小: {file_size / (1024 * 1024):.2f} MB")
                    transcoded_clips.append(transcode_output)
                else:
                    error(f"视频片段 {i + 1} 转码失败: {transcode_stderr}")
                    # 即使有片段转码失败，也继续尝试其他片段

            # 检查是否有成功转码的片段
            if not transcoded_clips:
                error("所有视频片段转码失败")
                return output_path

            debug(f"成功转码 {len(transcoded_clips)} 个视频片段，开始合并")

            # 如果启用了转场效果，调用专门的转场处理方法
            if enable_transcode and len(transcoded_clips) > 1:
                debug("启用转场效果，调用apply_video_transitions方法")
                # 使用apply_video_transitions方法处理转场
                try:
                    transition_config = config.get('transition', {})
                    transition_type = transition_config.get('type', 'fade')
                    transition_duration = transition_config.get('duration', 1.0)  # 使用配置文件中的默认值

                    # 调用apply_video_transitions方法
                    transition_result = FFmpegUtils.apply_video_transitions(
                        transcoded_clips,
                        output_path,
                        transition_type=transition_type,
                        transition_duration=transition_duration
                    )

                    # 先检查返回值是否为None，再检查文件是否存在
                    if transition_result is not None and isinstance(transition_result, str) and os.path.exists(transition_result) and os.path.getsize(transition_result) > 0:
                        debug("转场处理成功")
                        return output_path
                    else:
                        warning("转场处理失败或返回None，回退到常规合并")
                except Exception as e:
                    error(f"转场处理异常: {str(e)}")
                    debug("转场处理异常，回退到常规合并")

            # 如果转场效果未启用或转场处理失败，继续使用常规合并
            # 常规合并（没有转场效果或转场合并失败时使用）
            debug("使用常规concat方式合并视频片段")

            # 创建合并文件列表
            merge_list_file = os.path.join(temp_dir, f"merge_list_{str(uuid.uuid4())[:8]}.txt")

            # 写入文件列表
            with open(merge_list_file, 'w', encoding='utf-8') as f:
                for transcode_path in transcoded_clips:
                    # 确保路径有效且文件存在
                    if transcode_path and isinstance(transcode_path, str) and os.path.exists(transcode_path):
                        # 转换为绝对路径并处理Windows路径格式
                        abs_path = os.path.abspath(transcode_path).replace('\\', '/')
                        f.write(f"file '{abs_path}'\n")
                        debug(f"添加到合并列表: {abs_path}")
                    else:
                        debug(f"跳过无效或不存在的转码文件: {transcode_path}")

            # 执行合并命令 - 传入config参数
            merge_result, merge_stderr = merge_videos(merge_list_file, output_path, ffmpeg_path)

            # 检查合并结果
            if merge_result and os.path.exists(output_path):
                try:
                    file_size = os.path.getsize(output_path)
                    debug(f"视频合并成功，输出文件大小: {file_size / (1024 * 1024):.2f} MB")

                    # 计算输入文件总大小
                    total_input_size = 0
                    for v in transcoded_clips:
                        if v and isinstance(v, str) and os.path.exists(v):
                            total_input_size += os.path.getsize(v)
                except Exception as e:
                    error(f"检查文件大小出错: {str(e)}")
                    return output_path

                # 验证文件大小
                if file_size > total_input_size * 0.8:  # 应该接近输入文件总和
                    debug("✓ 视频合并成功，输出文件大小合理")
                    return output_path
                else:
                    debug("合并输出文件大小异常，尝试转码模式合并")

                    # 如果直接copy合并失败，尝试转码合并
                    transcode_merge_result, transcode_merge_stderr = transcode_merge_video(merge_list_file, output_path, config, ffmpeg_path)

                    if transcode_merge_result and os.path.exists(output_path):
                        file_size = os.path.getsize(output_path)
                        debug(f"转码合并成功，输出文件大小: {file_size / (1024 * 1024):.2f} MB")
                        return output_path
                    else:
                        error(f"转码合并失败: {transcode_merge_stderr}")
                        return output_path
            else:
                error(f"合并失败: {merge_stderr}")
                return output_path

        except Exception as e:
            error(f"视频处理出错: {str(e)}")
            import traceback
            error(f"异常详情: {traceback.format_exc()}")
            return output_path
        finally:
            # 清理临时文件：删除合并列表文件
            if merge_list_file and 'merge_list_file' in locals() and os.path.exists(merge_list_file):
                try:
                    os.remove(merge_list_file)
                    debug(f"已删除临时列表文件: {merge_list_file}")
                except:
                    pass

            if transcoded_clips:
                # 删除转码后的临时文件
                for clip in transcoded_clips:
                    if os.path.exists(clip):
                        try:
                            os.remove(clip)
                            debug(f"已删除临时转码文件: {clip}")
                        except:
                            pass

    @staticmethod
    def _render_with_transcoding(clip_paths: list[str], output_path: str, config: dict) -> str | None:
        """
        使用转码方式渲染视频（当直接合并失败时使用）
        
        Args:
            clip_paths: 视频片段路径列表
            output_path: 输出视频路径
            config: 渲染配置参数
            
        Returns:
            str: 输出视频路径
        """
        debug(f"使用转码方式渲染视频")

        # 验证输入参数
        if not isinstance(clip_paths, list):
            error("clip_paths必须是列表类型")
            return None

        if not output_path or not isinstance(output_path, str):
            error("无效的输出路径")
            return None

        # 过滤出有效的视频片段路径
        valid_clip_paths = []
        for clip in clip_paths:
            if clip and isinstance(clip, str) and os.path.exists(clip):
                valid_clip_paths.append(clip)
            else:
                debug(f"跳过无效的视频片段: {clip}")

        if not valid_clip_paths:
            error("没有有效的视频片段可供转码渲染")
            return None

        try:
            # 获取FFmpeg路径
            ffmpeg_path = find_ffmpeg()

            # 确保输出目录存在
            output_dir = os.path.dirname(output_path)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir, exist_ok=True)

            # 确保临时目录存在
            temp_dir = os.path.join(output_dir, "temp")
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir, exist_ok=True)

            # 打印输入文件信息
            for i, clip in enumerate(valid_clip_paths):
                try:
                    clip_size = os.path.getsize(clip)
                    debug(f"输入文件 {i + 1}: {clip}, 大小: {clip_size} 字节")
                except Exception as e:
                    error(f"获取文件 {clip} 大小失败: {str(e)}")

            # 创建临时文件列表
            temp_list_file = os.path.join(temp_dir, f"ffmpeg_list_{str(uuid.uuid4())[:8]}.txt")
            try:
                # 写入临时文件列表
                with open(temp_list_file, 'w', encoding='utf-8') as f:
                    for clip in valid_clip_paths:
                        try:
                            # 转换为正斜杠以避免Windows路径问题
                            abs_clip_path = os.path.abspath(clip).replace('\\', '/')
                            f.write(f"file '{abs_clip_path}'\n")
                            debug(f"添加到合并列表: {abs_clip_path}")
                        except Exception as e:
                            error(f"处理文件路径 {clip} 失败: {str(e)}")
                            continue

                # 检查生成的列表文件是否为空
                if os.path.exists(temp_list_file) and os.path.getsize(temp_list_file) == 0:
                    error("生成的文件列表为空，无法进行转码合并")
                    raise ValueError("文件列表为空")

                # 直接调用ffmpeg_run_utils中的codec_video方法进行转码合并
                # 这已经包含了所有必要的转码逻辑和参数处理
                codec_result, result_stderr = codec_video(temp_list_file, output_path, config, ffmpeg_path)

                # 检查执行结果
                if codec_result and output_path and isinstance(output_path, str) and os.path.exists(output_path):
                    try:
                        output_size = os.path.getsize(output_path)
                        debug(f"转码完成，输出文件大小: {output_size} 字节")
                    except Exception as e:
                        error(f"获取输出文件大小失败: {str(e)}")

                    # 检查文件大小是否合理
                    try:
                        # 使用已验证的视频片段路径列表，避免NoneType错误
                        min_input_size = min([os.path.getsize(clip) for clip in valid_clip_paths])
                        if output_size > min_input_size * 0.1:  # 至少应该大于最小输入文件的10%
                            debug(f"转码成功，输出文件大小合理")
                            return output_path
                        else:
                            warning(f"输出文件大小异常小: {output_size} 字节，尝试使用transcode_merge_video方法")
                            # 删除异常小的输出文件
                            if os.path.exists(output_path):
                                os.remove(output_path)
                    except Exception as e:
                        error(f"检查文件大小合理性失败: {str(e)}")
                        # 继续执行后续逻辑，不中断流程
                else:
                    error(f"转码失败: {result_stderr}")
            finally:
                # 清理临时文件
                if os.path.exists(temp_list_file):
                    try:
                        os.remove(temp_list_file)
                        debug(f"已删除临时列表文件: {temp_list_file}")
                    except Exception as e:
                        warning(f"删除临时文件失败: {str(e)}")

            # 如果codec_video失败，尝试使用transcode_merge_video方法
            debug("尝试使用transcode_merge_video方法进行转码合并")

            # 创建新的临时文件列表
            list_file = os.path.join(temp_dir, f"ffmpeg_list_{str(uuid.uuid4())[:8]}.txt")
            try:
                # 写入文件列表，使用已验证的视频片段路径列表，避免NoneType错误
                with open(list_file, 'w', encoding='utf-8') as f:
                    for video_path in valid_clip_paths:
                        abs_path = os.path.abspath(video_path).replace('\\', '/')
                        f.write(f"file '{abs_path}'\n")

                # 调用ffmpeg_run_utils中的transcode_merge_video方法
                transcode_result, transcode_stderr = transcode_merge_video(list_file, output_path, config, ffmpeg_path)

                # 验证输出文件
                if transcode_result and os.path.exists(output_path):
                    file_size = os.path.getsize(output_path)
                    debug(f"transcode_merge_video成功，输出文件大小: {file_size} 字节")
                    return output_path
                else:
                    error(f"transcode_merge_video失败: {transcode_stderr}")
                    # 清理失败的输出文件
                    if os.path.exists(output_path):
                        os.remove(output_path)
            finally:
                # 清理文件列表
                if os.path.exists(list_file):
                    try:
                        os.remove(list_file)
                    except:
                        pass

            # 所有策略都失败
            error(f"所有FFmpeg转码策略都失败")
            return output_path

        except Exception as e:
            error(f"转码渲染过程中出错: {str(e)}")
            import traceback
            error(f"错误堆栈: {traceback.format_exc()}")
            return output_path
