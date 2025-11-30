"""
@FileName: agent_orchestrator.py
@Description: Agent编排器模块，定义各个节点的处理逻辑，通过LangGraph进行任务流编排
@Author: HengLine
@Time: 2025/11/28 17:30
"""
from typing import Any

from langchain_core.runnables import Runnable
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END

from hengline.logger import debug
from .agent_nodes import *


class AgentOrchestrator(Runnable):
    """
    基于langchain+langgraph的智能体编排器
    完全使用langchain和langgraph框架实现，支持Runnable接口和高级状态管理
    """
    def __init__(self):
        # 初始化所有智能体
        self.agents = {
        }
        # 使用langgraph的检查点机制支持状态持久化和断点恢复
        self.checkpointer = MemorySaver()

        # 构建并编译流程图
        self.graph = self._build_graph()

        debug("初始化基于langchain+langgraph的智能体编排器")

    def _build_graph(self) -> Any:
        """
        构建langgraph智能体流程图
        完全利用langgraph的高级功能构建规范的智能体协作图
        """
        # 创建状态图，使用TypedDict作为状态类型
        workflow = StateGraph[GraphState, None, GraphState, GraphState](GraphState)

        # 添加节点 - 使用lambda函数确保正确传递self和state参数
        workflow.add_node("parse", lambda graph_state: instruction_parser_node)
        workflow.add_node("analyze", lambda graph_state: video_analysis_node)
        workflow.add_node("plan", lambda graph_state: video_plan_node)
        workflow.add_node("edit", lambda graph_state: video_edit_node)
        workflow.add_node("compose", lambda graph_state: video_composer_node)
        workflow.add_node("validate", lambda graph_state: quality_validator_node)
        workflow.add_node("error", lambda graph_state: error_handler_node)

        # 设置入口
        workflow.set_entry_point("parse")

        # 定义边（条件路由可选，此处线性）
        workflow.add_edge("parse", "analyze")
        workflow.add_edge("analyze", "plan")
        workflow.add_edge("plan", "edit")
        workflow.add_edge("edit", "compose")
        workflow.add_edge("compose", "validate")
        workflow.add_edge("validate", END)
        # 错误处理边
        workflow.add_edge("error", END)

        # 编译图 - 启用检查点以支持状态恢复和异步执行
        return workflow.compile(checkpointer=self.checkpointer)
