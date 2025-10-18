# -*- coding: utf-8 -*-
"""
@FileName: state.py
@Description: 智能体图状态定义
@Author: HengLine
@Time: 2025/08 - 2025/11
"""
from typing import List, Dict, Optional, Any
from typing_extensions import TypedDict

class GraphState(TypedDict):
    """
    智能体协作图的状态定义
    """
    # 输入
    videos: List[str]                    # 输入视频路径列表
    user_query: str                     # 用户描述
    config: dict                        # 处理配置
    
    # 处理中间状态
    analysis_results: dict              # 视频分析结果
    clip_points: dict                   # 剪切点规划
    sequence_plan: List                 # 片段序列计划
    editing_actions: List               # 编辑动作序列
    
    # 输出和控制
    final_video_path: str               # 最终输出路径
    current_agent: str                  # 当前执行智能体
    next_agent: str | None              # 下一个智能体
    error: str                          # 错误信息
    error_details: Optional[Dict[str, Any]]  # 错误详情
    processing_status: str              # 处理状态（如：待处理、处理中、已完成）
    validation_passed: bool             # 验证结果
    validation_report: Optional[Dict[str, Any]]  # 验证报告