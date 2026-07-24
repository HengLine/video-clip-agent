"""
@FileName: ffmpeg_env_utils.py
@Description: FFmpeg环境工具类，用于封装所有FFmpeg相关的功能。提供查找FFmpeg可执行文件路径等功能的统一接口
@Author: neopen
@Time: 2025/10/17 16:14
"""
import os
import subprocess

from neopen.logger import debug, error


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
    error("没有找到可用的 FFmpeg 可执行文件，请检查系统 PATH 是否配置正确，或者手动指定 FFmpeg 路径")
    raise FileNotFoundError("FFmpeg 不可用，请检查是否安装并配置了正确的 PATH")



def check_xfade_support(ffmpeg_path: str = "ffmpeg") -> bool:
    """
    检查FFmpeg是否支持xfade滤镜
    
    Args:
        ffmpeg_path: ffmpeg可执行文件路径
        
    Returns:
        bool: 是否支持
    """
    try:
        check_cmd = [ffmpeg_path, '-filters']
        check_result = subprocess.run(check_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        return 'xfade' in check_result.stdout
    except Exception as e:
        debug(f"检查FFmpeg功能时出错: {str(e)}")
        return False

        