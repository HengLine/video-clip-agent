# -*- coding: utf-8 -*-
"""
@FileName: graph.py
@Description: 智能体协作流程图定义和管理
@Author: HengLine
@Time: 2025/08 - 2025/11
"""
from typing import Dict, Callable
from hengline.logger import debug, info, warning, error
from .state import GraphState
from .orchestrator import OrchestratorAgent
from .content_analyzer import ContentAnalyzerAgent
from .video_editor import VideoEditorAgent
from .quality_validator import QualityValidatorAgent

class AgentGraph:
    """
    智能体协作流程图
    """
    def __init__(self):
        self.graph_type = "有向无环图"
        self.agents = {
            "orchestrator": OrchestratorAgent(),
            "content_analyzer": ContentAnalyzerAgent(),
            "video_editor": VideoEditorAgent(),
            "quality_validator": QualityValidatorAgent()
        }
        self.edges = {
            "orchestrator": ["content_analyzer"],
            "content_analyzer": ["video_editor"],
            "video_editor": ["quality_validator"],
            "quality_validator": ["output", "error_handler"]
        }
        self.node_callbacks: Dict[str, Callable] = {
            "orchestrator": self.agents["orchestrator"].execute,
            "content_analyzer": self.agents["content_analyzer"].execute,
            "video_editor": self.agents["video_editor"].execute,
            "quality_validator": self.agents["quality_validator"].execute
        }
        info("初始化智能体协作流程图")
    
    def add_node(self, node_id: str, callback: Callable) -> None:
        """
        添加节点到流程图
        """
        if node_id in self.node_callbacks:
            warning(f"节点 {node_id} 已存在，将被覆盖")
        self.node_callbacks[node_id] = callback
        debug(f"添加节点: {node_id}")
    
    def add_edge(self, from_node: str, to_node: str) -> None:
        """
        添加边到流程图
        """
        if from_node not in self.edges:
            self.edges[from_node] = []
        if to_node not in self.edges[from_node]:
            self.edges[from_node].append(to_node)
        debug(f"添加边: {from_node} -> {to_node}")
    
    def get_next_nodes(self, node_id: str) -> list:
        """
        获取指定节点的下一个节点
        """
        return self.edges.get(node_id, [])
    
    def validate_graph(self) -> bool:
        """
        验证流程图的有效性
        """
        # 检查所有节点的回调函数是否存在
        for node_id in self.node_callbacks:
            if not callable(self.node_callbacks[node_id]):
                error(f"节点 {node_id} 的回调函数无效")
                return False
        
        # 检查所有边的有效性
        for from_node in self.edges:
            if from_node not in self.node_callbacks:
                warning(f"边源节点 {from_node} 不存在于节点列表中")
        
        return True
    
    def run(self, initial_state: GraphState) -> GraphState:
        """
        执行流程图
        """
        try:
            # 验证流程图
            if not self.validate_graph():
                raise ValueError("流程图验证失败")
            
            state = initial_state.copy()
            
            # 从编排器开始执行
            current_node = "orchestrator"
            state['current_agent'] = current_node
            
            while current_node in self.node_callbacks:
                info(f"执行节点: {current_node}")
                
                # 执行当前节点的回调函数
                state = self.node_callbacks[current_node](state)
                
                # 检查是否有错误
                if state.get('error'):
                    current_node = "error_handler"
                    break
                
                # 获取下一个节点
                next_node = state.get('current_agent')
                
                # 如果没有指定下一个节点，尝试从edges中查找默认的下一个节点
                if not next_node:
                    debug(f"未指定下一个节点，尝试从edges中查找默认路径")
                    next_nodes = self.get_next_nodes(current_node)
                    if next_nodes:
                        # 选择第一个可用的下一个节点
                        next_node = next_nodes[0]
                        debug(f"使用默认路径: {current_node} -> {next_node}")
                
                # 检查下一个节点是否在流程图中
                if not next_node or next_node not in self.node_callbacks and next_node not in ["output", "error_handler"]:
                    warning(f"无效的下一个节点: {next_node}")
                    # 尝试从edges中查找默认的下一个节点
                    next_nodes = self.get_next_nodes(current_node)
                    if next_nodes:
                        for node in next_nodes:
                            if node in self.node_callbacks or node in ["output", "error_handler"]:
                                next_node = node
                                debug(f"使用备用路径: {current_node} -> {next_node}")
                                break
                    # 如果仍然没有有效的下一个节点，结束流程
                    if not next_node or next_node not in self.node_callbacks and next_node not in ["output", "error_handler"]:
                        break
                
                current_node = next_node
                
                # 检查是否到达终点
                if current_node in ["output", "error_handler"]:
                    break
            
            # 处理错误情况
            if current_node == "error_handler":
                error(f"执行出错: {state.get('error')}")
                # 这里可以添加错误恢复逻辑
                state['processing_status'] = "failed"
            elif current_node == "output":
                info("流程执行成功，输出结果")
                state['processing_status'] = "completed"
            else:
                warning("流程执行中断")
                state['processing_status'] = "interrupted"
            
            return state
        except Exception as e:
            error(f"执行流程图出错: {str(e)}")
            state = initial_state.copy()
            state['error'] = f"流程图执行错误: {str(e)}"
            state['processing_status'] = "failed"
            return state

# 全局流程图实例
def create_agent_graph() -> AgentGraph:
    """
    创建智能体协作流程图实例
    """
    return AgentGraph()