# -*- coding: utf-8 -*-
"""
@FileName: video_editor_agent.py
@Description: 基于langchain的视频编辑器智能体，负责视频片段提取、编排和合成
@Author: HengLine
@Time: 2025/10 - 2025/11
"""
import os
import uuid
from typing import List, Dict, Tuple, Any, Optional

from langchain.tools import tool
from langchain_core.runnables import Runnable
from langchain_core.tools import BaseTool

from config.config import get_video_rendering_config, get_output_dir
from hengline.logger import debug, info, warning, error
from utils.ffmpeg_env_utils import find_ffmpeg
from utils.ffmpeg_utils import FFmpegUtils
from utils.log_utils import print_log_exception
from .agent_state import GraphState


# 原始功能实现，不使用@tool装饰器
def _extract_video_clip(video_path: str, start_time: float, end_time: float, output_path: str, clip_index: int = 0) -> bool:
    """使用FFmpegUtils从视频中提取片段"""
    # 为片段添加顺序索引到文件名
    base_name, ext = os.path.splitext(output_path)
    indexed_output_path = f"{base_name}_clip_{clip_index:03d}{ext}"
    success = FFmpegUtils.extract_video_clip(video_path, indexed_output_path, start_time, end_time)
    
    # 如果提取成功，更新output_path为实际生成的文件路径
    if success:
        # 将实际生成的文件路径复制回原始output_path位置
        if os.path.exists(indexed_output_path) and os.path.exists(output_path):
            os.remove(output_path)  # 删除原文件（如果存在）
        if os.path.exists(indexed_output_path):
            # 将文件重命名为原始期望的路径
            import shutil
            shutil.move(indexed_output_path, output_path)
    
    return success


def _plan_sequential_sequence(clip_points: Dict[str, List[Tuple[float, float]]]) -> List[Dict[str, Any]]:
    """按顺序规划片段序列"""
    sequence = []
    global_clip_index = 0
    
    for video_path, points in clip_points.items():
        for i, (start, end) in enumerate(points):
            # 生成唯一标识符，包含视频路径和片段索引
            unique_id = f"{os.path.basename(video_path)}_segment_{i:03d}"
            sequence.append({
                'video_path': video_path,
                'start_time': start,
                'end_time': end,
                'index': i,
                'global_index': global_clip_index,
                'unique_id': unique_id
            })
            global_clip_index += 1
    return sequence


def _plan_interleaving_sequence(clip_points: Dict[str, List[Tuple[float, float]]]) -> List[Dict[str, Any]]:
    """穿插规划片段序列"""
    sequence = []
    # 获取所有视频的片段
    all_clips = []
    global_clip_index = 0
    
    for video_path, points in clip_points.items():
        for i, (start, end) in enumerate(points):
            # 生成唯一标识符
            unique_id = f"{os.path.basename(video_path)}_segment_{i:03d}"
            all_clips.append({
                'video_path': video_path,
                'start_time': start,
                'end_time': end,
                'index': i,
                'global_index': global_clip_index,
                'unique_id': unique_id
            })
            global_clip_index += 1

    # 按视频路径和索引排序
    all_clips.sort(key=lambda x: (x['video_path'], x['index']))

    # 模拟穿插效果
    # 实际实现可能需要更复杂的算法
    video_groups = {}
    for clip in all_clips:
        if clip['video_path'] not in video_groups:
            video_groups[clip['video_path']] = []
        video_groups[clip['video_path']].append(clip)

    # 按视频交替选取片段
    max_len = max(len(clips) for clips in video_groups.values())
    for i in range(max_len):
        for video_path in video_groups:
            if i < len(video_groups[video_path]):
                sequence.append(video_groups[video_path][i])

    return sequence


def _apply_transitions(clip_paths: List[str], transition_type: str, duration: float, output_dir: str, width: int = 1920, height: int = 1080, resize_mode: str = 'fit') -> List[str]:
    """应用转场效果 - 使用独立的转场函数处理"""
    # 如果只有一个片段，不需要转场
    if len(clip_paths) <= 1:
        debug("视频片段数量少于2，不需要应用转场")
        return clip_paths

    # 创建临时输出文件路径
    temp_transition_path = os.path.join(output_dir, f"transition_{str(uuid.uuid4())[:8]}.mp4")

    debug(f"开始应用转场效果: 片段数={len(clip_paths)}, 类型={transition_type}, 时长={duration}秒")

    # 应用转场效果
    transition_result = FFmpegUtils.apply_video_transitions(
        clip_paths=clip_paths,
        output_path=temp_transition_path,
        transition_type=transition_type,
        transition_duration=duration,
        width=width,
        height=height,
        resize_mode=resize_mode
    )

    # 检查转场是否成功
    if transition_result and isinstance(transition_result, str) and os.path.exists(transition_result):
        debug(f"转场效果应用成功: {transition_result}")
        # 转场后的文件作为单个片段返回
        return [transition_result]
    else:
        debug("转场效果应用失败，返回过滤后的原始片段")
        # 转场失败时返回过滤后的原始片段，确保不包含None或无效路径
        valid_clips = []
        for clip in clip_paths:
            if clip and isinstance(clip, str) and os.path.exists(clip):
                valid_clips.append(clip)
        return valid_clips


# 使用@tool装饰器的版本，用于langchain agent集成
@tool
def extract_video_clip(video_path: str, start_time: float, end_time: float, output_path: str) -> bool:
    """使用FFmpegUtils从视频中提取片段"""
    return _extract_video_clip(video_path, start_time, end_time, output_path)


@tool
def plan_sequential_sequence(clip_points: Dict[str, List[Tuple[float, float]]]) -> List[Dict[str, Any]]:
    """按顺序规划片段序列"""
    return _plan_sequential_sequence(clip_points)


@tool
def plan_interleaving_sequence(clip_points: Dict[str, List[Tuple[float, float]]]) -> List[Dict[str, Any]]:
    """穿插规划片段序列"""
    return _plan_interleaving_sequence(clip_points)


@tool
def apply_transitions(clip_paths: List[str], transition_type: str, duration: float, output_dir: str, width: int = 1920, height: int = 1080, resize_mode: str = 'fit') -> List[str]:
    """在片段之间应用转场效果"""
    return _apply_transitions(clip_paths, transition_type, duration, output_dir, width, height, resize_mode)


def render_video(clip_paths: List[str], output_path: str, config: Dict[str, Any], clip_mapping: List[Dict[str, Any]] = None) -> str:
    """渲染最终视频"""
    # 将clip_mapping添加到config中，以便FFmpegUtils可以使用
    if clip_mapping:
        config['clip_mapping'] = clip_mapping
        debug(f"传递片段映射到渲染器: {len(clip_mapping)} 个片段")
    return FFmpegUtils.render_video(clip_paths, output_path, config)


class VideoEditorAgent(Runnable):
    """
    基于langchain的视频编辑器智能体,负责视频片段提取、编排和合成
    实现Runnable接口以支持与langchain生态系统的集成
    """

    def __init__(self):
        self.role = "视频编辑处理"
        self.capabilities = ["片段提取", "序列规划", "转场应用", "视频渲染"]
        # 预查找FFmpeg
        find_ffmpeg()
        info(f"初始化 {self.role} 智能体 (基于langchain实现)")

    def get_tools(self) -> list[BaseTool]:
        """
        获取智能体可用的工具列表
        用于与langchain agent和其他组件集成
        """
        # render_video函数不需要@tool装饰器，因为它没有被直接调用
        return [
            extract_video_clip,
            plan_sequential_sequence,
            plan_interleaving_sequence,
            apply_transitions
        ]

    def edit_videos(self, state: GraphState) -> Dict[str, Any]:
        """
        执行视频编辑流程
        使用langchain的chain装饰器增强功能和错误处理
        """
        # 初始化编辑动作列表，确保在所有返回路径中都有定义
        editing_actions = []

        try:
            clip_points = state.get('clip_points', {})
            config = state.get('config', {})
            merge_mode = config.get('merge_mode', 'sequential')
            use_transition = config.get('use_transition', False)
            transition_duration = config.get('transition_duration', 0.5)

            # 创建临时目录
            temp_dir = config.get('temp_dir', 'data/temp')

            # 规划片段序列
            if merge_mode == 'interleaving':
                sequence_plan = _plan_interleaving_sequence(clip_points=clip_points)
            else:
                sequence_plan = _plan_sequential_sequence(clip_points=clip_points)

            debug(f"规划的片段序列: {len(sequence_plan)} 个片段")

            # 提取片段
            extracted_clips = []
            clip_mapping = []  # 记录片段映射关系
            
            for clip_info in sequence_plan:
                video_path = clip_info['video_path']
                start_time = clip_info['start_time']
                end_time = clip_info['end_time']
                global_index = clip_info.get('global_index', 0)
                unique_id = clip_info.get('unique_id', f'clip_{global_index}')

                # 确保视频路径有效
                if not video_path or not isinstance(video_path, str) or not os.path.exists(video_path):
                    error(f"无效的视频路径: {video_path}")
                    continue

                # 使用唯一ID和全局索引生成文件名
                output_path = os.path.join(temp_dir, f"{unique_id}.mp4")

                # 提取片段，传入全局索引
                success = _extract_video_clip(video_path, start_time, end_time, output_path, global_index)
                if success and os.path.exists(output_path):
                    debug(f"成功提取片段: {output_path} (索引: {global_index})")
                    extracted_clips.append(output_path)
                    # 记录映射关系
                    clip_mapping.append({
                        'original_index': global_index,
                        'unique_id': unique_id,
                        'video_path': video_path,
                        'clip_path': output_path,
                        'start_time': start_time,
                        'end_time': end_time
                    })
                else:
                    warning(f"提取片段失败: {video_path}")

            debug(f"片段映射关系: {clip_mapping}")

            # 从配置文件获取渲染配置
            render_config = get_video_rendering_config()

            # 应用转场效果 - 调用_apply_transitions函数
            if use_transition and len(extracted_clips) > 1:
                transition_type = 'fade'
                debug(f"启用转场效果: {transition_type}, 时长={transition_duration}秒")

                # 获取视频分辨率设置
                width = render_config.get('width', 1920)
                height = render_config.get('height', 1080)
                resize_mode = render_config.get('resize_mode', 'fit')

                # 直接调用_apply_transitions函数处理转场
                extracted_clips = _apply_transitions(
                    clip_paths=extracted_clips,
                    transition_type=transition_type,
                    duration=transition_duration,
                    output_dir=temp_dir,
                    width=width,
                    height=height,
                    resize_mode=resize_mode
                )
            else:
                debug("转场效果已禁用")

            # 获取输出目录绝对路径
            try:
                output_dir = get_output_dir()
                # 确保output_dir是字符串类型
                if not output_dir or not isinstance(output_dir, str):
                    error("无效的输出目录")
                    return {
                        'error': "无效的输出目录配置",
                        'editing_actions': editing_actions,
                        'next_agent': 'error_handler'
                    }
                # 确保输出目录存在
                os.makedirs(output_dir, exist_ok=True)
            except Exception as e:
                error(f"创建输出目录失败: {str(e)}")
                return {
                    'error': f"创建输出目录失败: {str(e)}",
                    'editing_actions': editing_actions,
                    'next_agent': 'error_handler'
                }

            # 生成输出文件名和路径
            try:
                output_filename = f"hengline_output_{str(uuid.uuid4())[:8]}.mp4"
                output_path = os.path.join(output_dir, output_filename)

                # 记录输出路径信息
                debug(f"使用输出目录: {output_dir}")
                debug(f"将生成输出文件: {output_path}")
            except Exception as e:
                error(f"生成输出路径失败: {str(e)}")
                return {
                    'error': f"生成输出路径失败: {str(e)}",
                    'editing_actions': editing_actions,
                    'next_agent': 'error_handler'
                }

            # 获取用户配置
            user_render_config = config.get('render_config', {})

            # 处理resolution配置（向后兼容）
            if 'resolution' in user_render_config:
                resolution = user_render_config.pop('resolution')
                try:
                    width, height = map(int, resolution.split('x'))
                    render_config['width'] = width
                    render_config['height'] = height
                except ValueError:
                    warning(f"无效的分辨率格式: {resolution}，使用默认值")

            # 处理fps配置（向后兼容）
            if 'fps' in user_render_config:
                render_config['framerate'] = user_render_config.pop('fps')

            # 处理codec配置（向后兼容）
            if 'codec' in user_render_config:
                codec = user_render_config.pop('codec')
                # 映射常见的编解码器名称
                codec_map = {
                    'h264': 'libx264',
                    'hevc': 'libx265'
                }
                render_config['codec'] = codec_map.get(codec, codec)

            # 更新其他配置
            render_config.update(user_render_config)

            debug(f"使用的渲染配置: {render_config}")

            # 检查是否有有效片段可供渲染
            if not extracted_clips:
                error("没有可用的视频片段进行渲染")
                return {
                    'error': "没有可用的视频片段进行渲染",
                    'editing_actions': editing_actions,
                    'next_agent': 'error_handler'
                }

            # 确保所有提取的片段都有效
            valid_extracted_clips = []
            for clip in extracted_clips:
                if clip and isinstance(clip, str) and os.path.exists(clip):
                    valid_extracted_clips.append(clip)

            if not valid_extracted_clips:
                error("所有提取的视频片段都是无效的")
                return {
                    'error': "所有提取的视频片段都是无效的",
                    'editing_actions': editing_actions,
                    'next_agent': 'error_handler'
                }

            # 渲染最终视频，传递片段映射信息
            final_video_path = render_video(valid_extracted_clips, output_path, render_config, clip_mapping)

            # 验证渲染结果
            if not final_video_path or not isinstance(final_video_path, str) or not os.path.exists(final_video_path):
                error(f"视频渲染失败，未生成有效的输出文件")
                return {
                    'error': "视频渲染失败，未生成有效的输出文件",
                    'editing_actions': editing_actions,
                    'next_agent': 'error_handler'
                }

            # 记录编辑动作
            editing_actions = [
                {'type': 'extract_clips', 'count': len(valid_extracted_clips)},
                {'type': 'merge_mode', 'mode': merge_mode},
                {'type': 'transition', 'applied': use_transition, 'duration': transition_duration},
                {'type': 'render', 'path': final_video_path}
            ]

            return {
                'sequence_plan': sequence_plan,
                'clip_mapping': clip_mapping,  # 添加片段映射关系
                'editing_actions': editing_actions,
                'final_video_path': final_video_path,
                'next_agent': 'quality_validator'
            }
        except Exception as e:
            error(f"视频编辑出错: {str(e)}")
            print_log_exception()
            return {
                'error': f"视频编辑失败: {str(e)}",
                'editing_actions': editing_actions,
                'next_agent': 'error_handler'
            }

    def execute(self, state: GraphState) -> GraphState:
        """
        执行视频编辑器的主要逻辑
        实现Runnable接口的标准执行方法
        """
        try:
            result = self.edit_videos(state)

            # 更新状态
            updated_state = state.copy()
            updated_state.update(result)
            updated_state['current_agent'] = result.get('next_agent')

            return updated_state
        except Exception as e:
            error(f"视频编辑器执行出错: {str(e)}")
            print_log_exception()
            updated_state = state.copy()
            updated_state['error'] = f"视频编辑器错误: {str(e)}"
            updated_state['current_agent'] = 'error_handler'
            return updated_state

    # 实现Runnable接口的invoke方法
    def invoke(self, input_state: Dict[str, Any], config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        实现langchain的Runnable接口
        支持标准的invoke调用模式
        """
        return self.execute(input_state)

    # 实现Runnable接口的batch方法，支持批量处理
    def batch(self, inputs: List[Dict[str, Any]], config: Optional[Dict] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        支持批量处理多个视频编辑任务
        """
        results = []
        for input_state in inputs:
            results.append(self.execute(input_state))
        return results
