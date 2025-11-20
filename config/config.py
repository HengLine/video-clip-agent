# -*- coding: utf-8 -*-
"""
@FileName: config_utils.py
@Description: 配置工具模块，负责读取和管理应用配置
@Author: HengLine
@Time: 2025/08 - 2025/11
"""
import os
import json
from typing import Dict, Any
from dotenv import load_dotenv

from hengline.logger import debug, info, error

# 加载.env文件中的环境变量
load_dotenv()

# 默认配置
DEFAULT_CONFIG = {
    'logging': {
        'level': 'DEBUG',
        'console_level': 'DEBUG',
        'file_level': 'INFO',
        'disable_unnecessary_logs': True
    },
    'flask': {
        'host': '0.0.0.0',
        'port': 8000,
        'debug': True
    },
    'video_processing': {
        'upload_dir': 'uploads',
        'temp_dir': 'data/temp',
        'output_dir': 'data/output',
        'default_transition_duration': 0.5,
        'max_concurrent_processes': 2,
        'allowed_extensions': {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'ts'}
    },
    'video_rendering': {
        'width': 1920,
        'height': 1080,
        'resize_mode': 'fit',  # fit: 保持比例适应, fill: 保持比例填充, stretch: 拉伸填充
        'codec': 'libx264',
        'preset': 'medium',
        'crf': 23,
        'framerate': 30,
        'audio_bitrate': '128k',
        'transcode_params': {
            'enable': True,  # 是否启用统一转码
            'ignore_dts': True,  # 是否忽略DTS时间戳问题
            'force_key_frames': True,  # 是否强制关键帧
            'movflags': '+faststart'  # 输出文件格式标志
        },
        'transition': {
            'enabled': False,  # 是否启用转场效果
            'type': 'crossfade',  # 转场类型: crossfade, fade, slide_left, slide_right, random
            'duration': 1.0  # 转场时长（秒）
        }
    },
    'ai_model': {
        'provider': 'qwen',  # 默认AI模型提供商: openai, qwen, deepseek
        'model': 'qwen-turbo',  # 默认模型
        'temperature': 0.1,
        'max_tokens': 2000,
        'timeout': 30,
        'qwen': {
            'api_key': '',
            'base_url': 'https://dashscope.aliyuncs.com/compatible-mode/v1',
            'model': 'qwen-turbo'
        },
    }
}

def get_config_path() -> str:
    """
    获取配置文件路径
    """
    # 获取当前文件所在路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 向上两级到达项目根目录
    # project_root = os.path.dirname(os.path.dirname(current_dir))
    # 配置文件路径
    config_path = os.path.join(current_dir, 'config.json')
    return config_path

def get_settings_config() -> Dict[str, Any]:
    """
    获取应用设置配置
    """
    try:
        config_path = get_config_path()
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                # 合并默认配置和用户配置
                merged_config = DEFAULT_CONFIG.copy()
                merged_config.update(config)
                # 从环境变量更新AI模型配置
                _update_ai_config_from_env(merged_config)
                return merged_config
        else:
            # 如果配置文件不存在，返回默认配置
            default_config = DEFAULT_CONFIG.copy()
            _update_ai_config_from_env(default_config)
            return default_config
    except Exception as e:
        # 如果读取配置文件出错，返回默认配置
        error(f"读取配置文件失败: {str(e)}")
        default_config = DEFAULT_CONFIG.copy()
        _update_ai_config_from_env(default_config)
        return default_config

def _update_ai_config_from_env(config: Dict[str, Any]) -> None:
    """
    从环境变量更新AI模型配置
    
    Args:
        config: 配置字典
    """
    if 'ai_model' not in config:
        config['ai_model'] = DEFAULT_CONFIG['ai_model']

    # 更新通用AI模型配置
    if os.environ.get('AI_PROVIDER'):
        config['ai_model']['provider'] = os.environ.get('AI_PROVIDER')

    # 更新OpenAI配置
    if os.environ.get('OPENAI_API_KEY'):
        config['ai_model']['openai']['api_key'] = os.environ.get('OPENAI_API_KEY')
    if os.environ.get('OPENAI_BASE_URL'):
        config['ai_model']['openai']['base_url'] = os.environ.get('OPENAI_BASE_URL')
    if os.environ.get('OPENAI_MODEL'):
        config['ai_model']['openai']['model'] = os.environ.get('OPENAI_MODEL')
    
    # 更新Qwen配置
    if os.environ.get('QWEN_API_KEY'):
        config['ai_model']['qwen']['api_key'] = os.environ.get('QWEN_API_KEY')
    if os.environ.get('QWEN_BASE_URL'):
        config['ai_model']['qwen']['base_url'] = os.environ.get('QWEN_BASE_URL')
    if os.environ.get('QWEN_MODEL'):
        config['ai_model']['qwen']['model'] = os.environ.get('QWEN_MODEL')
    
    # 更新DeepSeek配置
    if os.environ.get('DEEPSEEK_API_KEY'):
        config['ai_model']['deepseek']['api_key'] = os.environ.get('DEEPSEEK_API_KEY')
    if os.environ.get('DEEPSEEK_BASE_URL'):
        config['ai_model']['deepseek']['base_url'] = os.environ.get('DEEPSEEK_BASE_URL')
    if os.environ.get('DEEPSEEK_MODEL'):
        config['ai_model']['deepseek']['model'] = os.environ.get('DEEPSEEK_MODEL')

    # 更新 ollama 配置
    if os.environ.get('OLLAMA_MODEL'):
        config['ai_model']['ollama']['model'] = os.environ.get('OLLAMA_MODEL')
    if os.environ.get('OLLAMA_BASE_URL'):
        config['ai_model']['ollama']['base_url'] = os.environ.get('OLLAMA_BASE_URL')
    
    # 更新Flask配置
    if os.environ.get('FLASK_HOST'):
        config['flask']['host'] = os.environ.get('FLASK_HOST')
    if os.environ.get('FLASK_PORT'):
        try:
            config['flask']['port'] = int(os.environ.get('FLASK_PORT'))
        except ValueError:
            pass
    if os.environ.get('FLASK_DEBUG'):
        config['flask']['debug'] = os.environ.get('FLASK_DEBUG').lower() == 'true'

def save_config(config: Dict[str, Any]) -> bool:
    """
    保存配置到文件
    """
    try:
        config_path = get_config_path()
        # 确保配置目录存在
        os.makedirs(os.path.dirname(config_path), exist_ok=True)
        # 保存配置
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        return True
    except Exception as e:
        print(f"保存配置文件失败: {str(e)}")
        return False

def get_flask_host() -> dict:
    """
    获取Flask应用的主机地址
    """
    # 从环境变量获取，如果没有则使用默认值
    config = get_settings_config()
    return config['flask']

def get_app_root() -> str:
    """
    获取应用根目录的绝对路径
    """
    # 获取当前文件所在路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 对于 tool-video-agent 项目，应用根目录是包含 config 文件夹的父目录
    app_root = os.path.dirname(current_dir)  # 上一级目录就是应用根目录
    return app_root

def get_upload_dir() -> str:
    """
    获取上传目录的绝对路径
    """
    config = get_settings_config()
    upload_dir = os.path.join(get_app_root(), config['video_processing']['upload_dir'])
    # 确保目录存在
    os.makedirs(upload_dir, exist_ok=True)
    return upload_dir

def get_output_dir() -> str:
    """
    获取输出目录的绝对路径
    """
    config = get_settings_config()
    output_dir = os.path.join(get_app_root(), config.get('video_processing', {}).get('output_dir', 'data/output'))
    # 确保目录存在
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def get_model_dir() -> str:
    """
    获取模型目录的绝对路径
    """
    config = get_settings_config()
    model_dir = os.path.join(get_app_root(), config.get('video_processing', {}).get('model_dir', 'data/models'))
    # 确保目录存在
    os.makedirs(model_dir, exist_ok=True)
    return model_dir

def get_temp_dir() -> str:
    """
    获取临时目录的绝对路径
    """
    config = get_settings_config()
    temp_dir = os.path.join(get_app_root(), config.get('video_processing', {}).get('temp_dir', 'data/temp'))
    # 确保目录存在
    os.makedirs(temp_dir, exist_ok=True)
    return temp_dir

def get_allowed_extensions() -> set:
    """
    获取允许的文件扩展名集合
    """
    return get_settings_config().get('video_processing', {}).get('allowed_extensions', set())

def get_video_rendering_config() -> Dict[str, Any]:
    """
    获取视频渲染配置
    """
    return get_settings_config().get('video_rendering', {})

def get_verify_report_dir() -> str:
    """
    获取验证报告目录的绝对路径
    """
    # 使用固定路径 data/verify 存储验证报告
    # verify_dir = os.path.join(get_app_root(), 'data', 'verify')
    config = get_settings_config()
    verify_dir = os.path.join(get_app_root(), config.get('video_processing', {}).get('verify_dir', 'data/verify'))

    # 确保目录存在
    os.makedirs(verify_dir, exist_ok=True)
    return verify_dir