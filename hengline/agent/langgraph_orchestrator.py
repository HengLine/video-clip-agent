# -*- coding: utf-8 -*-
"""
@FileName: langgraph_orchestrator.py
@Description: 基于langchain+langgraph的智能体编排实现
@Author: HengLine
@Time: 2025/10/15 22:40
"""
import os
from typing import Dict, Any, Optional, List, Literal

from langchain_core.runnables import Runnable
from langchain_core.tools import Tool
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, END

from config.config import get_settings_config
from hengline.logger import debug, info, warning, error
from .agent_state import GraphState
from .content_analyzer_agent import ContentAnalyzerAgent
from .orchestrator_agent import OrchestratorAgent
from .quality_validator_agent import QualityValidatorAgent
from .video_editor_agent import VideoEditorAgent


class LangGraphOrchestrator(Runnable):
    """
    基于langchain+langgraph的智能体编排器
    完全使用langchain和langgraph框架实现，支持Runnable接口和高级状态管理
    """

    def __init__(self):
        # 初始化所有智能体
        self.agents = {
            "orchestrator": OrchestratorAgent(),
            "content_analyzer": ContentAnalyzerAgent(),
            "video_editor": VideoEditorAgent(),
            "quality_validator": QualityValidatorAgent()
        }

        # 使用langgraph的检查点机制支持状态持久化和断点恢复
        self.checkpointer = MemorySaver()

        # 构建并编译流程图
        self.graph = self._build_graph()

        info("初始化基于langchain+langgraph的智能体编排器")
        info(f"可用智能体节点: {', '.join(self.get_available_agents())}")

    def _build_graph(self) -> Any:
        """
        构建langgraph智能体流程图
        完全利用langgraph的高级功能构建规范的智能体协作图
        """
        # 创建状态图，使用TypedDict作为状态类型
        workflow = StateGraph(GraphState)

        # 添加节点 - 使用lambda函数确保正确传递self和state参数
        workflow.add_node("orchestrator", lambda state: self._orchestrator_node(state))
        workflow.add_node("content_analyzer", lambda state: self._content_analyzer_node(state))
        workflow.add_node("video_editor", lambda state: self._video_editor_node(state))
        workflow.add_node("quality_validator", lambda state: self._quality_validator_node(state))
        workflow.add_node("error_handler", lambda state: self._error_handler_node(state))

        # 设置入口点
        workflow.set_entry_point("orchestrator")

        # 添加条件边 - 基于状态的智能流转
        workflow.add_conditional_edges(
            "orchestrator",
            self._orchestrator_decider
        )

        workflow.add_conditional_edges(
            "content_analyzer",
            self._content_analyzer_decider
        )

        workflow.add_conditional_edges(
            "video_editor",
            self._video_editor_decider
        )

        workflow.add_conditional_edges(
            "quality_validator",
            self._quality_validator_decider
        )

        # 错误处理边
        workflow.add_edge("error_handler", END)

        # 编译图 - 启用检查点以支持状态恢复和异步执行
        return workflow.compile(checkpointer=self.checkpointer)

    def _orchestrator_node(self, state: GraphState) -> GraphState:
        """
        编排器节点 - 使用langchain的chain装饰器增强功能
        """
        info("🔄 执行编排器智能体 - 解析用户需求")

        # 更新状态
        state['current_agent'] = "orchestrator"
        state['processing_status'] = "in_progress"

        try:
            # 调用编排器智能体
            result = self.agents["orchestrator"].parse_user_request(state)

            # 合并结果到状态
            state.update(result)

            # 日志记录
            if 'task_description' in result:
                debug(f"✓ 任务描述: {result['task_description']}")
            if 'required_steps' in result:
                debug(f"✓ 识别步骤: {len(result['required_steps'])}个")

            return state

        except Exception as e:
            error(f"❌ 编排器执行异常: {str(e)}")
            state['error'] = f"编排器异常: {str(e)}"
            state['processing_status'] = "failed"
            return state

    def _content_analyzer_node(self, state: GraphState) -> GraphState:
        """
        内容分析节点 - 寻找剪切点和关键内容
        """
        info("🔍 执行内容分析智能体 - 分析视频内容")

        # 更新状态
        state['current_agent'] = "content_analyzer"
        state['processing_status'] = "analyzing"

        try:
            # 调用内容分析智能体
            result = self.agents["content_analyzer"].execute(state)

            # 合并结果到状态
            state.update(result)

            # 日志记录和状态验证
            if 'analysis_results' in result:
                debug(f"📊 分析完成，处理视频数: {len(result['analysis_results'])}")
            if 'clip_points' in result:
                debug(f"✂️  识别剪切点: {sum(len(points) for points in result['clip_points'].values())}个")

            return state

        except Exception as e:
            error(f"❌ 内容分析异常: {str(e)}")
            state['error'] = f"内容分析异常: {str(e)}"
            state['processing_status'] = "failed"
            return state

    def _video_editor_node(self, state: GraphState) -> GraphState:
        """
        视频编辑节点 - 裁剪、排序、合并、调整视频
        """
        info("🎬 执行视频编辑智能体 - 处理视频内容")

        # 更新状态
        state['current_agent'] = "video_editor"
        state['processing_status'] = "editing"

        try:
            # 调用视频编辑智能体
            result = self.agents["video_editor"].execute(state)

            # 合并结果到状态
            state.update(result)

            # 日志记录
            if 'editing_actions' in result:
                debug(f"⚡ 执行编辑动作: {len(result['editing_actions'])}")
            if 'final_video_path' in result:
                info(f"✅ 生成最终视频: {result['final_video_path']}")

            return state

        except Exception as e:
            error(f"❌ 视频编辑异常: {str(e)}")
            state['error'] = f"视频编辑异常: {str(e)}"
            state['processing_status'] = "failed"
            return state

    def _quality_validator_node(self, state: GraphState) -> GraphState:
        """
        质量验证节点 - 验证最终视频质量
        """
        info("✅ 执行质量验证智能体 - 检查视频质量")

        # 更新状态
        state['current_agent'] = "quality_validator"
        state['processing_status'] = "validating"

        try:
            # 调用质量验证智能体
            result = self.agents["quality_validator"].execute(state)

            # 合并结果到状态
            state.update(result)

            # 设置验证结果状态
            state['validation_passed'] = result.get('validation_passed', False)

            # 日志记录
            if 'validation_report' in result:
                debug(f"📋 验证报告: {result['validation_report']}")

            return state

        except Exception as e:
            error(f"❌ 质量验证异常: {str(e)}")
            state['error'] = f"质量验证异常: {str(e)}"
            state['processing_status'] = "failed"
            state['validation_passed'] = False
            return state

    def _error_handler_node(self, state: GraphState) -> GraphState:
        """
        错误处理节点 - 使用langgraph的错误处理机制
        """
        error_msg = state.get('error', '未知错误')
        current_agent = state.get('current_agent', 'unknown')

        info(f"❌ 执行错误处理 - 智能体: {current_agent}, 错误: {error_msg}")

        # 更新状态
        state['current_agent'] = "error_handler"
        state['processing_status'] = "failed"

        try:
            # 调用编排器的错误处理方法
            result = self.agents["orchestrator"].handle_error(state)

            # 合并结果到状态
            state.update(result)

            # 添加详细的错误信息
            state['error_details'] = {
                'error_message': error_msg,
                'current_agent': current_agent,
                'timestamp': os.popen('echo %time%').read().strip(),  # Windows时间获取
                'attempted_action': state.get('processing_status', 'unknown')
            }

            return state

        except Exception as e:
            error(f"❌ 错误处理异常: {str(e)}")
            state['error'] = f"错误处理异常: {str(e)}"
            return state

    # 条件决策函数 - 完全基于状态决定下一步
    def _orchestrator_decider(self, state: GraphState) -> Literal["content_analyzer", "error_handler"]:
        """
        编排器的条件决策函数
        """
        if state.get('error') or not state.get('videos'):
            warning("编排器决定进入错误处理流程")
            return "error_handler"
        return "content_analyzer"

    def _content_analyzer_decider(self, state: GraphState) -> Literal["video_editor", "error_handler"]:
        """
        内容分析器的条件决策函数
        """
        if state.get('error') or not state.get('clip_points'):
            warning("内容分析器决定进入错误处理流程")
            return "error_handler"
        return "video_editor"

    def _video_editor_decider(self, state: GraphState) -> Literal["quality_validator", "error_handler"]:
        """
        视频编辑器的条件决策函数
        """
        if state.get('error') or not state.get('final_video_path'):
            warning("视频编辑器决定进入错误处理流程")
            return "error_handler"
        return "quality_validator"

    def _quality_validator_decider(self, state: GraphState) -> Literal[END, "error_handler"]:
        """
        质量验证器的条件决策函数
        """
        if state.get('error') or not state.get('validation_passed', False):
            if not state.get('error') and not state.get('validation_passed', False):
                state['error'] = "质量验证未通过"
            warning("质量验证器决定进入错误处理流程")
            return "error_handler"

        # 验证通过，设置完成状态
        # 确保状态正确更新并被langgraph捕获
        state['processing_status'] = "completed"
        # 额外添加状态确认
        state['validation_passed'] = True
        state['current_agent'] = "quality_validator"
        state['next_agent'] = None

        info("🎉 质量验证通过，流程执行成功完成")
        return END

    # 实现Runnable接口的invoke方法
    def invoke(self, input_state: Dict[str, Any], config: Optional[Dict] = None) -> Dict[str, Any]:
        """
        实现langchain的Runnable接口
        支持标准的invoke调用模式
        确保正确处理状态参数并与langgraph框架兼容
        """
        # 确保config参数存在并正确设置
        if config is None:
            config = {}

        # 准备初始状态
        prepared_state = self._prepare_initial_state(input_state)

        # 生成唯一的thread_id用于跟踪
        thread_id = f"video_processing_{os.urandom(8).hex()}"
        debug(f"🔍 创建新的流程实例，thread_id={thread_id}")

        # 配置langgraph的执行参数
        graph_config = {
            "configurable": {
                "thread_id": thread_id
            }
        }

        try:
            # 使用langgraph的invoke方法运行图
            result = self.graph.invoke(prepared_state, config=graph_config)
            return result
        except Exception as e:
            error(f"❌ 运行智能体流程时发生异常: {str(e)}")
            # 确保返回有效的错误状态
            return {
                'error': f"流程执行异常: {str(e)}",
                'processing_status': "failed",
                'current_agent': "orchestrator"
            }

    # 实现Runnable接口的batch方法
    def batch(self, inputs: List[Dict[str, Any]], config: Optional[Dict] = None, **kwargs) -> List[Dict[str, Any]]:
        """
        支持批量处理多个视频任务
        使用invoke方法确保与Runnable接口一致
        """
        results = []
        for input_state in inputs:
            results.append(self.invoke(input_state, config=config, **kwargs))
        return results

    def run(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        运行智能体流程
        完全利用langgraph的高级功能
        """
        try:
            info("🚀 开始运行基于langchain+langgraph的智能体流程")

            # 准备初始状态 - 确保所有必要字段都有默认值
            prepared_state = self._prepare_initial_state(initial_state)

            # 生成唯一的thread_id用于跟踪
            thread_id = f"video_processing_{os.urandom(8).hex()}"
            debug(f"🔍 创建新的流程实例，thread_id={thread_id}")

            # 配置langgraph的执行参数
            graph_config = {
                "configurable": {
                    "thread_id": thread_id
                }
            }

            # 使用langgraph的invoke方法运行图
            result = self.graph.invoke(prepared_state, config=graph_config)

            # 改进状态检测逻辑：如果验证通过且没有错误，视为完成
            processing_status = result.get('processing_status')
            validation_passed = result.get('validation_passed', False)
            has_error = result.get('error') is not None
            final_video_exists = result.get('final_video_path') is not None

            # 综合判断流程是否成功完成
            if (processing_status == "completed" or
                    (validation_passed and not has_error and final_video_exists)):
                # 确保状态一致性
                if processing_status != "completed":
                    result['processing_status'] = "completed"
                    debug("状态修正：验证通过且有输出视频，将状态更新为completed")

                info(f"🎉 智能体流程执行成功完成，thread_id={thread_id}")
                # 添加执行摘要
                result['execution_summary'] = {
                    'status': 'success',
                    'thread_id': thread_id,
                    'processed_videos': len(prepared_state.get('videos', [])),
                    'output_video': result.get('final_video_path')
                }
            else:
                warning(f"❌ 智能体流程执行未完成，状态: {processing_status}, 验证通过: {validation_passed}, 有错误: {has_error}")

            return result

        except Exception as e:
            error(f"❌ 运行智能体流程时发生异常: {str(e)}")
            return {
                'error': f"流程执行异常: {str(e)}",
                'processing_status': "failed"
            }

    def _prepare_initial_state(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """
        准备初始状态，确保符合GraphState的规范
        这是langgraph推荐的状态准备模式
        """
        # 从config.py获取应用配置
        app_config = get_settings_config()
        debug(f"从config.py获取配置: {app_config.keys()}")

        # 构建config字段，从应用配置中提取相关配置
        config_from_app = {
            # 基础路径配置
            'output_dir': app_config.get('video_processing', {}).get('output_dir', 'data/output'),
            'temp_dir': app_config.get('video_processing', {}).get('temp_dir', 'data/temp'),
            'upload_dir': app_config.get('video_processing', {}).get('upload_dir', 'uploads'),

            # 视频处理配置
            'merge_mode': 'sequential',  # 默认合并模式
            'use_transition': app_config.get('video_rendering', {}).get('transition', {}).get('enabled', False),
            'transition_duration': app_config.get('video_rendering', {}).get('transition', {}).get('duration', 0.5),
            'transition_type': app_config.get('video_rendering', {}).get('transition', {}).get('type', 'crossfade'),

            # 视频渲染配置
            'width': app_config.get('video_rendering', {}).get('width', 1920),
            'height': app_config.get('video_rendering', {}).get('height', 1080),
            'resize_mode': app_config.get('video_rendering', {}).get('resize_mode', 'fit'),
            'codec': app_config.get('video_rendering', {}).get('codec', 'libx264'),
            'preset': app_config.get('video_rendering', {}).get('preset', 'medium'),
            'crf': app_config.get('video_rendering', {}).get('crf', 23),
            'framerate': app_config.get('video_rendering', {}).get('framerate', 30),
            'audio_bitrate': app_config.get('video_rendering', {}).get('audio_bitrate', '128k'),
            'transcode_params': app_config.get('video_rendering', {}).get('transcode_params', {})
        }

        # 使用符合langgraph最佳实践的默认值
        defaults = {
            'videos': [],
            'user_query': '',
            'current_agent': None,
            'next_agent': None,
            'error': None,
            'validation_passed': False,
            'processing_status': 'initializing',
            'analysis_results': {},
            'clip_points': {},
            'sequence_plan': [],
            'editing_actions': [],
            'final_video_path': None,
            'config': config_from_app
        }

        # 创建新状态，先应用默认值，再合并初始状态
        prepared_state = defaults.copy()
        prepared_state.update(initial_state)

        # 确保必要目录存在
        if 'config' in prepared_state and 'output_dir' in prepared_state['config']:
            os.makedirs(prepared_state['config']['output_dir'], exist_ok=True)
        if 'config' in prepared_state and 'temp_dir' in prepared_state['config']:
            os.makedirs(prepared_state['config']['temp_dir'], exist_ok=True)

        # 验证必要字段
        required_fields = ['videos', 'user_query']
        for field in required_fields:
            if not prepared_state[field]:
                warning(f"⚠️  初始状态缺少必要字段或值为空: {field}")

        return prepared_state

    def get_available_agents(self) -> List[str]:
        """
        获取可用的智能体列表
        实现langchain的Runnable接口要求
        """
        return list(self.agents.keys())

    def get_agent_info(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """
        获取智能体详细信息
        用于调试和监控
        """
        agent = self.agents.get(agent_name)
        if agent:
            return {
                "name": agent_name,
                "role": getattr(agent, 'role', "未知角色"),
                "capabilities": getattr(agent, 'capabilities', []),
                "class_name": agent.__class__.__name__
            }
        return None

    def get_graph_configuration(self) -> Dict[str, Any]:
        """
        获取当前流程图的配置信息
        用于可视化和调试
        """
        return {
            "available_agents": self.get_available_agents(),
            "agent_details": {name: self.get_agent_info(name) for name in self.get_available_agents()},
            "graph_type": "langgraph StateGraph",
            "supports_checkpointing": True,
            "checkpointer_type": "MemorySaver",
            "entry_point": "orchestrator",
            "exit_point": "END",
            "error_handling": "dedicated error_handler node"
        }

    # 创建工具函数，支持通过tools接口使用
    def create_tools(self) -> List[Tool]:
        """
        创建可供langchain agents使用的工具列表
        支持与其他langchain组件集成
        """
        tools = []

        # 视频处理工具 - 仅保留核心功能
        process_video_tool = Tool(
            name="process_video",
            func=lambda inputs: self.invoke(inputs),
            description="处理视频文件，根据用户查询执行编辑操作"
        )
        tools.append(process_video_tool)

        return tools
