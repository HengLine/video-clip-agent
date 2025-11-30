"""
@FileName: agent_orchestrator.py
@Description: Agent 节点模块，定义各个节点的处理逻辑，通过 LangGraph 进行任务流编排
@Author: HengLine
@Time: 2025/11/28 17:30
"""
import os
from typing import Literal

from langchain_core.runnables import RunnableConfig

from hengline.logger import info, warning, error
from .agent_state import GraphState
from .agent_tools import *


def instruction_parser_node(graph_state: GraphState, config: RunnableConfig) -> dict:
    try:
        raw_dict = parse_instruction_tool.invoke({"instruction": graph_state["user_instruction"]})
        validated = StructuredIntent(**raw_dict)
    except Exception as e:
        return {"error": f"解析结果不符合Schema: {e}", "current_step": "error"}

    return {
        "structured_intent": validated.model_dump(),  # 转回 dict 存入 State
        "current_step": "analyze"
    }


def video_analysis_node(graph_state: GraphState, config: RunnableConfig) -> dict:
    intent = graph_state["structured_intent"]
    result = analyze_video_tool.invoke({
        "video_paths": graph_state["input_videos"],
        "keywords": intent["content_keywords"]
    })
    return {"analyzed_clips": result["video_clips"], "current_step": "plan"}


def video_plan_node(graph_state: GraphState, config: RunnableConfig) -> dict:
    plan = plan_video_tool.invoke({
        "candidates": graph_state["analyzed_clips"],
        "constraints": graph_state["structured_intent"]["constraints"],
        "transition": graph_state["structured_intent"]["transition"],
        "bgm": graph_state["structured_intent"]["bgm"]
    })
    return {"edit_plan": plan, "current_step": "edit"}


def video_edit_node(graph_state: GraphState, config: RunnableConfig) -> dict:
    style = edit_video_tool.invoke({
        "edit_plan": graph_state["edit_plan"],
        "output_dir": graph_state["output_dir"]
    })

    return {
        "styled_clips": style,
        "current_step": "compose"
    }


def video_edit_decider(graph_state: GraphState) -> Literal["quality_validator", "error_handler"]:
    """
    视频编辑器的条件决策函数
    """
    if graph_state.get('error') or not graph_state.get('final_video_path'):
        warning("视频编辑器决定进入错误处理流程")
        return "error_handler"
    return "quality_validator"


def video_composer_node(graph_state: GraphState, config: RunnableConfig) -> dict:
    output_path = f"{graph_state['output_dir']}/final.mp4"
    result = compose_video_tool.invoke({
        "edit_plan": graph_state["edit_plan"],
        "output_path": output_path
    })
    return {"composed_result": result, "current_step": "validate"}


def quality_validator_node(graph_state: GraphState, config: RunnableConfig) -> dict:
    report = validate_quality_tool.invoke({
        "video_path": graph_state["composed_result"]["output_video_path"],
        "intent": graph_state["structured_intent"]
    })
    return {"quality_report": report, "current_step": "done"}


def error_handler_node(graph_state: GraphState) -> GraphState:
    """
    错误处理节点 - 使用langgraph的错误处理机制
    """
    error_msg = graph_state.get('error', '未知错误')
    current_agent = graph_state.get('current_agent', 'unknown')

    info(f"执行错误处理 - 智能体: {current_agent}, 错误: {error_msg}")

    # 更新状态
    graph_state['current_agent'] = "error"
    graph_state['current_step'] = "error"

    try:
        # 添加详细的错误信息
        graph_state['error_details'] = {
            'error_message': error_msg,
            'current_agent': current_agent,
            'timestamp': os.popen('echo %time%').read().strip(),  # Windows时间获取
            'attempted_action': graph_state.get('current_step', 'error')
        }

        return graph_state

    except Exception as e:
        error(f"错误处理异常: {str(e)}")
        graph_state['error'] = f"错误处理异常: {str(e)}"
        return graph_state
