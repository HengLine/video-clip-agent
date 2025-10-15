# -*- coding: utf-8 -*-
"""
@FileName: orchestrator.py
@Description: 智能体编排协调器
@Author: HengLine
@Time: 2025/08 - 2025/11
"""
from typing import Dict, Any, Optional
from hengline.logger import debug, info, warning, error
from .state import GraphState

class OrchestratorAgent:
    """
    智能体编排协调器，负责解析用户需求、制定处理策略和协调其他智能体工作
    """
    def __init__(self):
        self.role = "流程编排和任务分发"
        self.capabilities = [
            "解析用户复杂需求",
            "制定处理策略", 
            "协调其他智能体工作",
            "错误处理和重试机制"
        ]
        info(f"初始化 {self.role} 智能体")
    
    def parse_user_request(self, state: GraphState) -> Dict[str, Any]:
        """
        解析用户请求，提取关键信息
        """
        try:
            user_query = state.get('user_query', '')
            videos = state.get('videos', [])
            
            debug(f"解析用户请求: {user_query}")
            debug(f"输入视频列表: {videos}")
            
            # 提取需求类型（示例实现，实际可能需要更复杂的NLP解析）
            needs_interleaving = any(keyword in user_query.lower() for keyword in ['穿插', '交替', '轮流'])
            needs_transition = any(keyword in user_query.lower() for keyword in ['转场', '过渡', '效果'])
            
            # 制定处理策略
            strategy = {
                'merge_mode': 'interleaving' if needs_interleaving else 'sequential',
                'use_transition': needs_transition,
                'transition_duration': 0.5,  # 默认转场时长
                'priority_videos': []  # 优先级视频列表
            }
            
            # 更新配置
            config = state.get('config', {})
            config.update(strategy)
            
            return {
                'config': config,
                'next_agent': 'content_analyzer'
            }
        except Exception as e:
            error(f"解析用户请求时出错: {str(e)}")
            return {
                'error': f"解析请求失败: {str(e)}",
                'next_agent': None
            }
    
    def handle_error(self, state: GraphState) -> Dict[str, Any]:
        """
        处理错误情况
        """
        error_msg = state.get('error', '未知错误')
        warning(f"处理错误: {error_msg}")
        
        # 根据错误类型决定下一步操作
        # 这里可以实现更复杂的错误恢复策略
        return {
            'error': error_msg,
            'next_agent': None  # 终止处理流程
        }
    
    def decide_next_step(self, state: GraphState) -> str:
        """
        根据当前状态决定下一步操作
        """
        current_agent = state.get('current_agent')
        next_agent = state.get('next_agent')
        
        if next_agent:
            return next_agent
        
        # 根据当前状态决定下一步
        if current_agent == 'quality_validator':
            validation_passed = state.get('validation_passed', False)
            if validation_passed:
                return 'output'
            else:
                return 'error_handler'
        
        # 默认流程
        agent_flow = {
            None: 'parse_request',
            'parse_request': 'content_analyzer',
            'orchestrator': 'content_analyzer',  # 添加编排器的默认流转路径
            'content_analyzer': 'video_editor',
            'video_editor': 'quality_validator',
            'error_handler': None
        }
        
        return agent_flow.get(current_agent, None)
    
    def execute(self, state: GraphState) -> GraphState:
        """
        执行编排器的主要逻辑
        """
        try:
            current_agent = state.get('current_agent')
            debug(f"编排器执行当前步骤: {current_agent}")
            
            if current_agent == 'orchestrator':
                # 对于orchestrator节点，直接解析用户请求
                result = self.parse_user_request(state)
            elif current_agent == 'parse_request' or current_agent is None:
                # 解析用户请求
                result = self.parse_user_request(state)
            elif current_agent == 'error_handler':
                # 处理错误
                result = self.handle_error(state)
            else:
                # 决定下一步
                next_agent = self.decide_next_step(state)
                result = {'next_agent': next_agent}
            
            # 确保result包含next_agent
            if 'next_agent' not in result or not result['next_agent']:
                debug(f"未设置next_agent，使用默认流转路径")
                # 对于orchestrator节点，默认流转到content_analyzer
                if current_agent == 'orchestrator':
                    result['next_agent'] = 'content_analyzer'
                else:
                    # 使用decide_next_step获取默认路径
                    default_next = self.decide_next_step(state)
                    result['next_agent'] = default_next
            
            # 更新状态
            updated_state = state.copy()
            updated_state.update(result)
            updated_state['current_agent'] = result.get('next_agent')
            
            debug(f"编排器更新状态: next_agent={result.get('next_agent')}")
            return updated_state
        except Exception as e:
            error(f"编排器执行出错: {str(e)}")
            updated_state = state.copy()
            updated_state['error'] = f"编排器错误: {str(e)}"
            updated_state['current_agent'] = 'error_handler'
            return updated_state