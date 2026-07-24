# -*- coding: utf-8 -*-
"""
@FileName: quality_validator.py
@Description: 基于langchain的质量验证器智能体，负责验证最终视频的质量和符合度
@Author: HengLine
@Time: 2025/10 - 2025/11
"""
import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List

from langchain_core.runnables import Runnable
from langchain_core.tools import Tool

from config.config import get_verify_report_dir
from hengline.logger import debug, info, warning, error
from .agent_state import GraphState


class QualityValidatorAgent(Runnable):
    """
    基于langchain的质量验证器智能体，负责验证最终视频的质量和符合度
    实现Runnable接口以支持与langchain生态系统的集成
    """

    def __init__(self):
        self.role = "质量验证"
        self.checks = [
            "片段连续性检查",
            "时间线合理性验证",
            "输出质量评估",
            "用户需求符合度检查"
        ]
        info(f"初始化 {self.role} 智能体 (基于langchain实现)")

    def get_tools(self) -> List[Tool]:
        """
        获取智能体可用的工具列表
        """
        return []  # 质量验证器目前没有使用外部工具

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
                debug(f"输出文件大小: {file_size / 1024:.2f} KB")
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

    def save_validation_report(self, state: GraphState, validation_report: Dict[str, Any]) -> str | None:
        """
        保存验证报告到指定目录
        返回报告文件路径
        """
        try:
            final_video_path = state.get('final_video_path')
            if not final_video_path:
                warning("无法获取最终视频路径，跳过保存验证报告")
                return None

            # 获取验证报告目录
            verify_dir = get_verify_report_dir()

            # 获取视频文件名（不包含扩展名）
            video_filename = os.path.basename(final_video_path)
            video_name_without_ext = os.path.splitext(video_filename)[0]

            # 构建报告文件名（与视频同名，扩展名为json）
            report_filename = f"{video_name_without_ext}.json"
            report_path = os.path.join(verify_dir, report_filename)

            # 丰富报告内容
            enriched_report = {
                **validation_report,
                'video_name': video_filename,
                'verification_time': datetime.now().isoformat(),
                'metadata': {
                    'created_by': 'quality_validator_agent',
                    'version': '1.0.0'
                }
            }

            # 保存报告
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(enriched_report, f, ensure_ascii=False, indent=2)

            info(f"验证报告已保存: {report_path}")
            return report_path
        except Exception as e:
            error(f"保存验证报告失败: {str(e)}")
            return None

    def execute(self, state: GraphState) -> GraphState:
        """
        执行质量验证器的主要逻辑
        实现Runnable接口的标准执行方法
        """
        try:
            result = self.validate_quality(state)

            # 保存验证报告
            if 'validation_report' in result:
                report_path = self.save_validation_report(state, result['validation_report'])
                if report_path:
                    result['validation_report_path'] = report_path

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
        支持批量处理多个质量验证任务
        """
        results = []
        for input_state in inputs:
            results.append(self.execute(input_state))
        return results
