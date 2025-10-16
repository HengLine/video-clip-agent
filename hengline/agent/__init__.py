# -*- coding: utf-8 -*-
"""
@FileName: __init__.py
@Description: 基于langchain的智能体模块初始化文件
@Author: HengLine
@Time: 2025/10 - 2025/11
"""
from .orchestrator_agent import OrchestratorAgent
from .content_analyzer_agent import ContentAnalyzerAgent
from .video_editor_agent import VideoEditorAgent
from .quality_validator_agent import QualityValidatorAgent
from .agent_state import GraphState

__all__ = [
    'OrchestratorAgent',
    'ContentAnalyzerAgent',
    'VideoEditorAgent',
    'QualityValidatorAgent',
    'GraphState'
]

# 版本信息 - 所有智能体现已迁移到langchain生态系统
__version__ = "1.1.0"  # 1.0.0: 原始版本, 1.1.0: langchain重构版本