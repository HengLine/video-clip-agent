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
from langchain_core.runnables import Runnable, chain
from langchain_core.tools import Tool, BaseTool
from langchain.tools import tool
from hengline.logger import debug, info, warning, error
from .agent_state import GraphState
from utils.ffmpeg_utils import FFmpegUtils
from config.config import get_video_rendering_config

# @tool
def extract_video_clip(video_path: str, start_time: float, end_time: float, output_path: str) -> bool:
    """使用FFmpegUtils从视频中提取片段"""
    return FFmpegUtils.extract_video_clip(video_path, output_path, start_time, end_time)

# @tool
def plan_sequential_sequence(clip_points: Dict[str, List[Tuple[float, float]]]) -> List[Dict[str, Any]]:
    """按顺序规划片段序列"""
    sequence = []
    for video_path, points in clip_points.items():
        for i, (start, end) in enumerate(points):
            sequence.append({
                'video_path': video_path,
                'start_time': start,
                'end_time': end,
                'index': i
            })
    return sequence

# @tool
def plan_interleaving_sequence(clip_points: Dict[str, List[Tuple[float, float]]]) -> List[Dict[str, Any]]:
    """穿插规划片段序列"""
    sequence = []
    # 获取所有视频的片段
    all_clips = []
    for video_path, points in clip_points.items():
        for i, (start, end) in enumerate(points):
            all_clips.append({
                'video_path': video_path,
                'start_time': start,
                'end_time': end,
                'index': i
            })
    
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

# @tool
def apply_transitions(clip_paths: List[str], transition_type: str, duration: float, output_dir: str) -> List[str]:
    """在片段之间应用转场效果"""
    debug(f"应用转场效果: 类型={transition_type}, 时长={duration}秒")
    # 这里是示例实现，实际需要调用视频处理库
    # 模拟返回添加转场后的片段路径
    return clip_paths  # 简化处理，实际应该返回带转场的新片段

def render_video(clip_paths: List[str], output_path: str, config: Dict[str, Any]) -> str:
    """渲染最终视频"""
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
        FFmpegUtils.find_ffmpeg()
        info(f"初始化 {self.role} 智能体 (基于langchain实现)")
    
    def get_tools(self) -> list[BaseTool]:
        """
        获取智能体可用的工具列表
        用于与langchain agent和其他组件集成
        """
        return [
            extract_video_clip,
            plan_sequential_sequence,
            plan_interleaving_sequence,
            apply_transitions,
            render_video
        ]

    def edit_videos(self, state: GraphState) -> Dict[str, Any]:
        """
        执行视频编辑流程
        使用langchain的chain装饰器增强功能和错误处理
        """
        try:
            clip_points = state.get('clip_points', {})
            config = state.get('config', {})
            merge_mode = config.get('merge_mode', 'sequential')
            use_transition = config.get('use_transition', False)
            transition_duration = config.get('transition_duration', 0.5)
            
            # 创建临时目录
            temp_dir = config.get('temp_dir', 'data/temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            # 规划片段序列
            if merge_mode == 'interleaving':
                sequence_plan = plan_interleaving_sequence(clip_points=clip_points)
            else:
                sequence_plan = plan_sequential_sequence(clip_points=clip_points)
            
            debug(f"规划的片段序列: {len(sequence_plan)} 个片段")
            
            # 提取片段
            extracted_clips = []
            for clip_info in sequence_plan:
                video_path = clip_info['video_path']
                start_time = clip_info['start_time']
                end_time = clip_info['end_time']
                
                # 生成临时文件名
                clip_id = str(uuid.uuid4())[:8]
                output_path = os.path.join(temp_dir, f"clip_{clip_id}.mp4")
                
                # 提取片段
                success = extract_video_clip(video_path, start_time, end_time, output_path)
                if success:
                    extracted_clips.append(output_path)
                else:
                    warning(f"提取片段失败: {video_path} ({start_time}-{end_time})")
            
            # 应用转场效果
            if use_transition and len(extracted_clips) > 1:
                transition_type = 'fade'
                extracted_clips = apply_transitions(
                    extracted_clips, transition_type, transition_duration, temp_dir
                )
            
            # 直接使用配置模块中的辅助方法获取输出目录
            from config.config import get_output_dir
            
            # 获取输出目录绝对路径
            output_dir = get_output_dir()
            
            output_filename = f"output_{str(uuid.uuid4())[:8]}.mp4"
            output_path = os.path.join(output_dir, output_filename)
            
            # 记录输出路径信息
            debug(f"使用输出目录: {output_dir}")
            debug(f"将生成输出文件: {output_path}")
            
            # 从配置文件获取渲染配置
            render_config = get_video_rendering_config()
            
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
            
            final_video_path = render_video(extracted_clips, output_path, render_config)
            
            # 记录编辑动作
            editing_actions = [
                {'type': 'extract_clips', 'count': len(extracted_clips)},
                {'type': 'merge_mode', 'mode': merge_mode},
                {'type': 'transition', 'applied': use_transition, 'duration': transition_duration},
                {'type': 'render', 'path': final_video_path}
            ]
            
            return {
                'sequence_plan': sequence_plan,
                'editing_actions': editing_actions,
                'final_video_path': final_video_path,
                'next_agent': 'quality_validator'
            }
        except Exception as e:
            error(f"视频编辑出错: {str(e)}")
            return {
                'error': f"视频编辑失败: {str(e)}",
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