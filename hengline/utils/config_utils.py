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
        'temp_dir': 'data/temp',
        'output_dir': 'data/output',
        'default_transition_duration': 0.5,
        'max_concurrent_processes': 2
    }
}

def get_config_path() -> str:
    """
    获取配置文件路径
    """
    # 获取当前文件所在路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # 向上两级到达项目根目录
    project_root = os.path.dirname(os.path.dirname(current_dir))
    # 配置文件路径
    config_path = os.path.join(project_root, 'config', 'config.json')
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
                return merged_config
        else:
            # 如果配置文件不存在，返回默认配置
            return DEFAULT_CONFIG
    except Exception as e:
        # 如果读取配置文件出错，返回默认配置
        print(f"读取配置文件失败: {str(e)}")
        return DEFAULT_CONFIG

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

def get_flask_secret_key() -> str:
    """
    获取Flask应用的密钥
    """
    # 从环境变量获取，如果没有则使用默认值
    return os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')