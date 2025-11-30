"""
@FileName: agent_models.py
@Description: 定义视频混剪系统中各阶段的标准数据结构。
    所有模型均可通过 .model_dump() 转为字典，用于 JSON 序列化或 LangGraph State 传递。
@Author: HengLine
@Time: 2025/11/28 22:13
"""
from enum import Enum
from typing import List, Optional, Dict, Any

from pydantic import BaseModel, Field


class TransitionType(str, Enum):
    """支持的转场类型"""
    FADE = "fade"  # 淡入淡出
    CUT = "cut"  # 硬切
    SLIDE = "slide"  # 滑动


class BGMMood(str, Enum):
    """支持的背景音乐情绪"""
    RELAXED = "relaxed"
    UPBEAT = "upbeat"
    DRAMATIC = "dramatic"
    ROMANTIC = "romantic"
    SUSPENSE = "suspense"


# =============== 1. 用户指令解析结果 ===============

class TransitionConfig(BaseModel):
    """转场配置"""
    type: TransitionType = Field(
        default=TransitionType.FADE,
        description="转场类型：fade（淡入淡出）、cut（硬切）、slide（滑动）"
    )
    duration_sec: float = Field(
        default=0.6,
        ge=0.1, le=3.0,
        description="转场持续时间，单位：秒，范围 0.1 ~ 3.0"
    )


class BGMConfig(BaseModel):
    """背景音乐配置"""
    mood: BGMMood = Field(
        default=BGMMood.RELAXED,
        description="音乐情绪类型"
    )
    instrument: Optional[str] = Field(
        default="piano",
        description="乐器类型，如 'piano', 'guitar', 'strings'，可为空"
    )
    volume_db: int = Field(
        default=-15,
        ge=-30, le=0,
        description="背景音乐音量（dB），-30（极静）到 0（原始音量）"
    )


class ConstraintConfig(BaseModel):
    """剪辑约束条件"""
    min_clip_duration: float = Field(
        default=0.8,
        ge=0.1,
        description="单个片段最短时长（秒），低于此值将被丢弃"
    )
    max_clip_duration: float = Field(
        default=5.0,
        ge=1.0,
        description="单个片段最长时长（秒），超过将被截断"
    )
    per_video: bool = Field(
        default=True,
        description="是否要求每段输入视频至少输出一个有效片段"
    )
    max_total_clips: int = Field(
        default=10,
        ge=1,
        description="最终输出片段总数上限"
    )


class StructuredIntent(BaseModel):
    """
    用户自然语言指令解析后的结构化意图
    由 InstructionParserAgent 生成，供后续模块使用
    """
    content_keywords: List[str] = Field(
        default_factory=lambda: ["person"],
        description="需要提取的视觉/语义关键词列表，使用英文小写，如 ['smile', 'running', 'sunset']"
    )
    subject: str = Field(
        default="person",
        description="主体类型，如 'person', 'pet', 'car', 'building'"
    )
    action: str = Field(
        default="extract",
        description="剪辑动作，目前支持 'extract'（提取）"
    )
    transition: TransitionConfig = Field(
        default_factory=TransitionConfig,
        description="转场效果配置"
    )
    bgm: BGMConfig = Field(
        default_factory=BGMConfig,
        description="背景音乐配置"
    )
    constraints: ConstraintConfig = Field(
        default_factory=ConstraintConfig,
        description="剪辑约束参数"
    )


# =============== 2. 视频分析结果 ===============

class ClipCandidate(BaseModel):
    """
    视频分析智能体输出的候选片段
    每个片段代表一个可能符合用户意图的时间区间
    """
    video_path: str = Field(
        ...,
        description="原始视频文件路径"
    )
    start_sec: float = Field(
        ...,
        description="片段开始时间（秒），精确到小数点后1位"
    )
    end_sec: float = Field(
        ...,
        description="片段结束时间（秒）"
    )
    confidence: float = Field(
        ...,
        ge=0.0, le=1.0,
        description="该片段匹配用户意图的置信度（0.0~1.0）"
    )
    features: List[str] = Field(
        default_factory=list,
        description="检测到的语义特征，如 ['smile', 'eye_crinkle', 'frontal_face']"
    )
    frame_quality: Optional[float] = Field(
        default=1.0,
        ge=0.0, le=1.0,
        description="画面质量分数（模糊/遮挡等），1.0 为最佳"
    )


class VideoAnalysisResult(BaseModel):
    """
    VideoAnalysisAgent 的完整输出
    包含每段输入视频的候选片段列表
    """
    video_clips: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="按输入视频分组的候选片段。每个元素为：{'video_path': str, 'candidates': List[ClipCandidate]}"
    )


# =============== 3. 剪辑规划结果 ===============

class FinalClip(BaseModel):
    """
    最终确定用于合成的片段
    由 EditPlanningAgent 输出
    """
    source: str = Field(
        ...,
        description="来源视频路径"
    )
    in_sec: float = Field(
        ...,
        description="入点时间（秒），通常比原始检测 start_sec 略早（如 -0.2s）以保证动作完整性"
    )
    out_sec: float = Field(
        ...,
        description="出点时间（秒），通常比原始检测 end_sec 略晚"
    )


class EditPlan(BaseModel):
    """
    最终剪辑时间轴计划
    供 VideoComposerAgent 执行
    """
    final_sequence: List[FinalClip] = Field(
        default_factory=list,
        description="按播放顺序排列的最终片段列表"
    )
    transition: TransitionConfig = Field(
        ...,
        description="转场配置（与 StructuredIntent 中一致）"
    )
    bgm_path: str = Field(
        ...,
        description="选定的背景音乐文件绝对路径"
    )
    bgm_volume_db: int = Field(
        ...,
        description="BGM 音量（dB）"
    )
    output_resolution: str = Field(
        default="1920x1080",
        description="输出视频分辨率，如 '1920x1080', '1080x1920'（竖屏）"
    )

# =============== 4. 视频片段处理 ===============
class ClipStyleConfig(BaseModel):
    """
    单个视频片段的视觉样式处理配置
    由 ClipStylingAgent 为每个 FinalClip 生成
    """
    # 画幅处理
    target_aspect_ratio: str = Field(
        default="16:9",
        pattern=r"^\d+:\d+$",
        description="目标宽高比，如 '16:9', '9:16', '1:1'"
    )
    resize_mode: str = Field(
        default="pad",
        examples=["crop", "pad", "stretch"],
        description="crop（裁剪中心）, pad（填充）, stretch（拉伸）"
    )
    pad_color: Optional[str] = Field(
        default=None,
        description="填充颜色（HEX），如 '#000000'；若为 None 且 resize_mode='pad'，则用模糊背景"
    )

    # 色彩处理
    brightness: float = Field(
        default=1.0,
        ge=0.0, le=2.0,
        description="亮度增益（1.0=原始）"
    )
    contrast: float = Field(
        default=1.0,
        ge=0.0, le=2.0,
        description="对比度增益"
    )
    saturation: float = Field(
        default=1.0,
        ge=0.0, le=2.0,
        description="饱和度增益"
    )
    temperature: int = Field(
        default=0,
        ge=-100, le=100,
        description="色温偏移（-100=冷，+100=暖）"
    )

    # 风格化
    filter_preset: Optional[str] = Field(
        default=None,
        description="预设滤镜名称，如 'vintage', 'cinematic', 'monochrome'"
    )
    grain_strength: float = Field(
        default=0.0,
        ge=0.0, le=1.0,
        description="胶片颗粒强度（0.0=无）"
    )

    # 输出
    processed_clip_path: str = Field(
        ...,
        description="处理后的片段临时文件路径"
    )


class StyledClipSequence(BaseModel):
    """
    ClipStylingAgent 的完整输出
    包含每个片段的样式配置和处理后路径
    """
    styled_clips: List[ClipStyleConfig] = Field(
        default_factory=list,
        description="与 EditPlan.final_sequence 一一对应的样式配置列表"
    )
    global_style: Dict[str, Any] = Field(
        default_factory=dict,
        description="全局样式（如统一 LUT），供 Composer 使用"
    )

# =============== 5. 合成结果 ===============

class ComposedResult(BaseModel):
    """视频合成完成后的结果"""
    output_video_path: str = Field(
        ...,
        description="最终输出视频的完整文件路径"
    )
    duration_sec: float = Field(
        ...,
        description="输出视频总时长（秒）"
    )
    resolution: str = Field(
        ...,
        description="实际输出分辨率"
    )
    has_audio: bool = Field(
        default=True,
        description="是否包含音频轨道"
    )
    codec: str = Field(
        default="h264",
        description="视频编码格式"
    )


# =============== 5. 质量验证报告 ===============

class QualityCheckResult(BaseModel):
    """各项质量检查的结果"""
    smile_presence: bool = Field(default=False, description="是否检测到微笑（若用户要求）")
    transition_smooth: bool = Field(default=True, description="转场是否平滑无跳帧")
    bgm_correct: bool = Field(default=True, description="BGM风格是否匹配要求")
    no_black_frames: bool = Field(default=True, description="是否包含黑屏/异常帧")
    audio_sync: bool = Field(default=True, description="音画是否同步")


class QualityReport(BaseModel):
    """最终质量验证报告"""
    job_id: str = Field(..., description="任务ID")
    status: str = Field(..., examples=["PASS", "FAIL", "REVIEW"], description="整体状态")
    checks: QualityCheckResult = Field(default_factory=QualityCheckResult, description="详细检查项")
    suggestions: List[str] = Field(default_factory=list, description="改进建议（如 '微笑片段过短'）")
    confidence_score: float = Field(0.0, ge=0.0, le=1.0, description="系统对结果的总体置信度")
