"""
@FileName: agent_state.py
@Description: LangGraph 工作流的全局状态定义。
        必须使用 TypedDict（非 Pydantic），因为 LangGraph 内部依赖字典操作。
        所有字段可为 None，表示该阶段尚未执行。
@Author: HengLine
@Time: 2025/11/28 17:16
"""

from typing import List, Optional, Dict, Any, TypedDict

from typing_extensions import NotRequired


class GraphState(TypedDict):
    """
    视频混剪多智能体系统的全局状态。
    每个 LangGraph 节点读取并更新此状态。
    """

    # === 任务元信息 ===
    job_id: str  # 任务唯一ID，如 "job_20251128_001"
    user_instruction: str  # 原始用户自然语言指令
    input_videos: List[str]  # 用户上传的视频文件路径列表
    output_dir: str  # 输出目录路径

    # === 各阶段输出（按执行顺序）===
    structured_intent: NotRequired[Optional[Dict[str, Any]]]  # InstructionParserAgent 输出
    analyzed_clips: NotRequired[Optional[List[Dict[str, Any]]]]  # VideoAnalysisAgent 输出
    edit_plan: NotRequired[Optional[Dict[str, Any]]]  # EditPlanningAgent 输出
    composed_result: NotRequired[Optional[Dict[str, Any]]]  # VideoComposerAgent 输出
    quality_report: NotRequired[Optional[Dict[str, Any]]]  # QualityValidatorAgent 输出

    # === 控制流与错误处理 ===
    current_step: NotRequired[str]  # 当前执行到哪一步，如 "parse", "analyze", "plan","edit", "compose", "validate", "done", "error"
    error: NotRequired[Optional[str]]  # 若发生错误，记录错误信息
    error_details: Optional[Dict[str, Any]]  # 错误详情
    retry_count: NotRequired[int]  # 重试次数（用于自动恢复）

    # 输出和控制
    final_video_path: str               # 最终输出路径
    current_agent: str                  # 当前执行智能体
    current_agent_status: bool          # 当前执行智能体状态
    next_agent: str | None              # 下一个智能体
    validation_passed: bool             # 验证结果
    validation_report: Optional[Dict[str, Any]]  # 验证报告