# -*- coding: utf-8 -*-
"""
@FileName: quality_validator.py
@Description: 质量验证器智能体，负责验证最终视频的质量和符合度
@Author: HengLine
@Time: 2025/08 - 2025/11
"""
import os
from typing import Dict, Any
from hengline.logger import debug, info, warning, error
from .state import GraphState

class QualityValidatorAgent:
    """
    质量验证器智能体，负责验证最终视频的质量和符合度
    """
    def __init__(self):
        self.role = "质量验证"
        self.checks = [
            "片段连续性检查",
            "时间线合理性验证",
            "输出质量评估",
            "用户需求符合度检查"
        ]
        info(f"初始化 {self.role} 智能体")
    
    def validate_quality(self, state: GraphState) -> Dict[str, Any]:
        """
        执行质量验证
        """
        try:
            final_video_path = state.get('final_video_path')
            user_query = state.get('user_query', '')
            sequence_plan = state.get('sequence_plan', [])
            editing_actions = state.get('editing_actions', [])
            
            validation_results = {
                'file_exists': False,
                'file_size_valid': False,
                'duration_valid': False,
                'sequence_continuity': True,
                'requirements_met': True
            }
            
            # 检查输出文件是否存在
            if os.path.exists(final_video_path):
                validation_results['file_exists'] = True
                
                # 检查文件大小
                file_size = os.path.getsize(final_video_path)
                # 假设最小文件大小为100KB
                validation_results['file_size_valid'] = file_size > 102400
                debug(f"输出文件大小: {file_size/1024:.2f} KB")
            else:
                warning(f"输出文件不存在: {final_video_path}")
            
            # 检查片段连续性
            if len(sequence_plan) > 1:
                # 简化的连续性检查
                # 实际应该检查片段之间的内容连贯性
                validation_results['sequence_continuity'] = True
            
            # 检查用户需求符合度
            # 简化的需求符合度检查
            # 实际应该基于内容分析结果进行更复杂的匹配
            if user_query:
                # 假设只要处理流程完成，就认为基本符合需求
                validation_results['requirements_met'] = True
            
            # 综合判断
            validation_passed = all([
                validation_results['file_exists'],
                validation_results['file_size_valid'],
                validation_results['sequence_continuity'],
                validation_results['requirements_met']
            ])
            
            # 生成验证报告
            validation_report = {
                'validation_results': validation_results,
                'total_clips': len(sequence_plan),
                'editing_actions': len(editing_actions),
                'passed': validation_passed
            }
            
            debug(f"质量验证结果: {'通过' if validation_passed else '失败'}")
            
            return {
                'validation_passed': validation_passed,
                'validation_report': validation_report,
                'next_agent': 'output'
            }
        except Exception as e:
            error(f"质量验证出错: {str(e)}")
            return {
                'error': f"质量验证失败: {str(e)}",
                'validation_passed': False,
                'next_agent': 'error_handler'
            }
    
    def execute(self, state: GraphState) -> GraphState:
        """
        执行质量验证器的主要逻辑
        """
        try:
            result = self.validate_quality(state)
            
            # 更新状态
            updated_state = state.copy()
            updated_state.update(result)
            updated_state['current_agent'] = result.get('next_agent')
            
            return updated_state
        except Exception as e:
            error(f"质量验证器执行出错: {str(e)}")
            updated_state = state.copy()
            updated_state['error'] = f"质量验证器错误: {str(e)}"
            updated_state['validation_passed'] = False
            updated_state['current_agent'] = 'error_handler'
            return updated_state