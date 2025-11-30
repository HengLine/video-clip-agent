"""
@FileName: agent_tools.py
@Description: 
@Author: HengLine
@Time: 2025/11/28 17:40
"""
from typing import List

from langchain_core.tools import tool
from langgraph.graph import state
from pydantic import BaseModel, Field

from hengline.agents.agent_models import StructuredIntent, StyledClipSequence
from hengline.agents.instruct_parse_agent import InstructParseAgent
from hengline.agents.video_edit_agent import video_edit

@tool(args_schema=InstructParseAgent)
def parse_instruction_tool(instruction: str) -> dict:
    """将用户指令解析为结构化任务配置"""
    # 实际可调用 LLM + Pydantic Output Parser
    # 此处简化为规则+模拟
    if "微笑" in instruction or "smile" in instruction.lower():
        return {
            "content_keywords": ["smile", "facial expression"],
            "subject": "person",
            "transition": {"type": "fade", "duration_sec": 0.6},
            "bgm": {"mood": "relaxed", "instrument": "piano", "volume_db": -15},
            "constraints": {"min_clip_duration": 0.8, "max_clip_duration": 4.0, "per_video": True}
        }
    else:
        raise ValueError("无法解析指令")


@tool
def analyze_video_tool(video_paths: List[str], keywords: List[str]) -> dict:
    """对视频进行语义分析，返回候选片段"""
    # 模拟：实际调用 MediaPipe + 微笑检测模型
    candidates = []
    for vid in video_paths:
        # 模拟每段视频找到1-2个微笑片段
        candidates.append({
            "video_path": vid,
            "candidates": [
                {"start_sec": 12.1, "end_sec": 14.2, "confidence": 0.89, "features": ["smile", "eye_crinkle"]},
                {"start_sec": 5.6, "end_sec": 7.0, "confidence": 0.92, "features": ["smile"]}
            ]
        })
    return {"video_clips": candidates}


@tool
def plan_video_tool(candidates: list, constraints: dict, transition: dict, bgm: dict) -> dict:
    """筛选并优化片段，生成剪辑计划"""
    final_seq = []
    for item in candidates:
        # 简单策略：取最高置信度片段
        best = max(item["candidates"], key=lambda x: x["confidence"])
        final_seq.append({
            "source": item["video_path"],
            "in_sec": best["start_sec"] - 0.2,  # 提前0.2s入点
            "out_sec": best["end_sec"] + 0.2
        })

    return {
        "final_sequence": final_seq,
        "transition": transition,
        "bgm_path": "./assets/bgm/relaxed_piano.mp3",
        "bgm_volume_db": bgm["volume_db"]
    }


@tool
def edit_video_tool(plan_video: dict, output_path: str) -> dict:
    edit_plan = plan_video["edit_plan"]
    intent = StructuredIntent(**state["structured_intent"])

    styled_clips = []
    for i, clip in enumerate(edit_plan.final_sequence):
        video_edit.determine_style(i, clip, intent, styled_clips)

    return {
        "styled_clips": StyledClipSequence(styled_clips=styled_clips).model_dump(),
    }



@tool
def compose_video_tool(edit_plan: dict, output_path: str) -> dict:
    """执行视频合成"""
    # 实际调用 MoviePy
    # 此处模拟
    return {
        "output_video_path": output_path,
        "duration_sec": 10.2,
        "resolution": "1920x1080"
    }

@tool
def validate_quality_tool(video_path: str, intent: dict) -> dict:
    """验证输出质量"""
    return {
        "status": "PASS",
        "checks": {
            "smile_presence": True,
            "transition_smooth": True,
            "bgm_correct": True
        }
    }
