# -*- coding: utf-8 -*-
"""
@FileName: video_metadata.py
@Description: 视频元数据读取功能模块，用于提取视频文件的基本信息
@Author: HengLine
@Time: 2025/11
"""

import os
from typing import Dict, Any, Optional

from hengline.logger import debug, warning, error
from utils.ffmpeg_run_utils import get_video_metadata

# 视频元数据读取器的默认配置
DEFAULT_CONFIG = {
    'timeout': 30,  # 命令执行超时时间（秒）
    'probe_format': 'json',  # 探测输出格式
    'probe_show_entries': 'format:stream'  # 探测显示的条目
}


class VideoMetadataReader:
    """视频元数据读取器类"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化视频元数据读取器
        
        Args:
            config: 配置参数，可选
        """
        self.config = DEFAULT_CONFIG.copy()
        if config:
            self.config.update(config)

        debug("视频元数据读取器初始化完成")

    def read_metadata(self, video_path: str) -> Dict[str, Any]:
        """
        读取视频文件的元数据
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            Dict[str, Any]: 视频元数据信息
        """
        if not os.path.exists(video_path):
            error(f"视频文件不存在: {video_path}")
            raise FileNotFoundError(f"视频文件不存在: {video_path}")

        if not os.path.isfile(video_path):
            error(f"指定路径不是文件: {video_path}")
            raise IsADirectoryError(f"指定路径不是文件: {video_path}")

        debug(f"开始读取视频元数据: {video_path}")

        try:
            # 使用ffprobe读取视频元数据
            metadata = get_video_metadata(video_path
                                          , self.config.get("probe_show_entries")
                                          , self.config.get("probe_format"))

            # 提取和整理关键元数据
            return self._extract_key_metadata(metadata)
        except Exception as e:
            error(f"读取视频元数据失败: {str(e)}")
            # 发生错误时返回基本模拟数据
            return self._get_default_metadata()

    def _extract_key_metadata(self, raw_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        从原始元数据中提取关键信息
        
        Args:
            raw_metadata: 原始元数据
            
        Returns:
            Dict[str, Any]: 提取后的关键元数据
        """
        # 初始化结果字典
        metadata = {
            'duration': 0.0,
            'width': 0,
            'height': 0,
            'fps': 0.0,
            'bitrate': 0,
            'codec_name': '',
            'format_name': '',
            'frame_count': 0,
            'has_audio': False,
            'has_video': False,
            'audio_codec': '',
            'audio_sample_rate': 0
        }

        # 提取格式信息
        if 'format' in raw_metadata:
            format_info = raw_metadata['format']

            # 提取持续时间
            if 'duration' in format_info:
                try:
                    metadata['duration'] = float(format_info['duration'])
                except ValueError:
                    warning("无法解析持续时间")

            # 提取比特率
            if 'bit_rate' in format_info:
                try:
                    metadata['bitrate'] = int(format_info['bit_rate'])
                except ValueError:
                    warning("无法解析比特率")

            # 提取格式名称
            if 'format_name' in format_info:
                metadata['format_name'] = format_info['format_name']

        # 提取流信息
        if 'streams' in raw_metadata:
            for stream in raw_metadata['streams']:
                # 视频流信息
                if stream.get('codec_type') == 'video':
                    metadata['has_video'] = True

                    # 提取分辨率
                    if 'width' in stream and 'height' in stream:
                        metadata['width'] = stream['width']
                        metadata['height'] = stream['height']

                    # 提取帧率
                    if 'r_frame_rate' in stream:
                        try:
                            # r_frame_rate格式通常为 '30/1' 或 '29.97/1'
                            num, den = stream['r_frame_rate'].split('/')
                            metadata['fps'] = float(num) / float(den)
                        except (ValueError, ZeroDivisionError):
                            warning("无法解析帧率")

                    # 提取编解码器
                    if 'codec_name' in stream:
                        metadata['codec_name'] = stream['codec_name']

                    # 提取帧数
                    if 'nb_frames' in stream:
                        try:
                            metadata['frame_count'] = int(stream['nb_frames'])
                        except ValueError:
                            warning("无法解析帧数")

                # 音频流信息
                elif stream.get('codec_type') == 'audio':
                    metadata['has_audio'] = True

                    # 提取音频编解码器
                    if 'codec_name' in stream:
                        metadata['audio_codec'] = stream['codec_name']

                    # 提取音频采样率
                    if 'sample_rate' in stream:
                        try:
                            metadata['audio_sample_rate'] = int(stream['sample_rate'])
                        except ValueError:
                            warning("无法解析音频采样率")

        debug(f"提取的视频元数据: {metadata}")
        return metadata

    def _get_default_metadata(self) -> Dict[str, Any]:
        """
        获取默认的元数据（当读取失败时使用）
        
        Returns:
            Dict[str, Any]: 默认元数据
        """
        return {
            'duration': 0.0,
            'width': 0,
            'height': 0,
            'fps': 0.0,
            'bitrate': 0,
            'codec_name': '',
            'format_name': '',
            'frame_count': 0,
            'has_audio': False,
            'has_video': False,
            'audio_codec': '',
            'audio_sample_rate': 0
        }

    def validate_video(self, video_path: str) -> Dict[str, Any]:
        """
        验证视频文件的有效性并返回基本信息
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            Dict[str, Any]: 验证结果，包含是否有效及基本信息
        """
        try:
            metadata = self.read_metadata(video_path)

            # 根据元数据判断视频是否有效
            is_valid = (
                    metadata['has_video'] and
                    metadata['duration'] > 0 and
                    metadata['width'] > 0 and
                    metadata['height'] > 0 and
                    metadata['fps'] > 0
            )

            return {
                'is_valid': is_valid,
                'metadata': metadata,
                'error': None
            }
        except Exception as e:
            return {
                'is_valid': False,
                'metadata': self._get_default_metadata(),
                'error': str(e)
            }

    def get_video_resolution(self, video_path: str) -> Dict[str, int]:
        """
        获取视频分辨率
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            Dict[str, int]: 包含宽度和高度的字典
        """
        metadata = self.read_metadata(video_path)
        return {
            'width': metadata['width'],
            'height': metadata['height']
        }

    def get_video_duration(self, video_path: str) -> float:
        """
        获取视频时长
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            float: 视频时长（秒）
        """
        metadata = self.read_metadata(video_path)
        return metadata['duration']

    def get_video_fps(self, video_path: str) -> float:
        """
        获取视频帧率
        
        Args:
            video_path: 视频文件路径
            
        Returns:
            float: 视频帧率
        """
        metadata = self.read_metadata(video_path)
        return metadata['fps']


# 全局视频元数据读取器实例
_video_metadata_reader_instance = None


def get_video_metadata_reader() -> VideoMetadataReader:
    """
    获取全局视频元数据读取器实例
    
    Returns:
        VideoMetadataReader: 视频元数据读取器实例
    """
    global _video_metadata_reader_instance
    if _video_metadata_reader_instance is None:
        _video_metadata_reader_instance = VideoMetadataReader()
    return _video_metadata_reader_instance


def read_video_metadata(video_path: str) -> Dict[str, Any]:
    """
    读取视频文件的元数据
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        Dict[str, Any]: 视频元数据信息
    """
    reader = get_video_metadata_reader()
    return reader.read_metadata(video_path)


def validate_video_file(video_path: str) -> Dict[str, Any]:
    """
    验证视频文件的有效性
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        Dict[str, Any]: 验证结果
    """
    reader = get_video_metadata_reader()
    return reader.validate_video(video_path)


def get_video_resolution(video_path: str) -> Dict[str, int]:
    """
    获取视频分辨率
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        Dict[str, int]: 包含宽度和高度的字典
    """
    reader = get_video_metadata_reader()
    return reader.get_video_resolution(video_path)


def get_video_duration(video_path: str) -> float:
    """
    获取视频时长
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        float: 视频时长（秒）
    """
    reader = get_video_metadata_reader()
    return reader.get_video_duration(video_path)


def get_video_fps(video_path: str) -> float:
    """
    获取视频帧率
    
    Args:
        video_path: 视频文件路径
        
    Returns:
        float: 视频帧率
    """
    reader = get_video_metadata_reader()
    return reader.get_video_fps(video_path)
