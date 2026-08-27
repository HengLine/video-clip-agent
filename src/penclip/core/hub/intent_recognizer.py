"""IntentRecognizer — V0.1 keyword matching, V0.2 LLM semantic understanding."""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from penclip.domain.value_objects.intent import IntentType
from penclip.logger import debug


@dataclass
class IntentResult:
    intent: IntentType
    confidence: float = 1.0
    params: Dict[str, Any] = field(default_factory=dict)
    needs_clarification: bool = False
    clarification: str = ""


_URL_PATTERN = re.compile(r"^https?://\S+", re.IGNORECASE)
_VIDEO_EXTENSIONS = (".mp4", ".mov", ".avi", ".mkv", ".webm", ".flv", ".m4v", ".mpg", ".mpeg")


def is_asset_url(text: str) -> bool:
    """判断输入是否为资源 URL 或视频文件路径。"""
    stripped = text.strip()
    if _URL_PATTERN.match(stripped):
        return True
    lower = stripped.lower()
    return any(ext in lower for ext in _VIDEO_EXTENSIONS)


# V0.1 keyword → intent mappings
_KEYWORD_INTENT_MAP: Dict[str, IntentType] = {
    "创建": IntentType.PLAN_CREATE, "生成": IntentType.PLAN_CREATE,
    "做": IntentType.PLAN_CREATE, "制作": IntentType.PLAN_CREATE,
    "追加": IntentType.PLAN_APPEND, "添加": IntentType.PLAN_APPEND,
    "插入": IntentType.PLAN_INSERT,
    "删除": IntentType.PLAN_DELETE, "移除": IntentType.PLAN_DELETE,
    "排序": IntentType.PLAN_REORDER, "调换": IntentType.PLAN_REORDER,
    "复制": IntentType.PLAN_DUPLICATE, "拷贝": IntentType.PLAN_DUPLICATE,
    "分析": IntentType.ANALYZE_FULL,
    "优先分析": IntentType.ANALYZE_PRIORITY,
    "剪": IntentType.CLIP_TRIM, "裁剪": IntentType.CLIP_TRIM,
    "替换": IntentType.CLIP_REPLACE, "换": IntentType.CLIP_REPLACE,
    "预览": IntentType.CLIP_PREVIEW,
    "转场": IntentType.EFFECT_ADD_TRANSITION,
    "滤镜": IntentType.EFFECT_ADD_FILTER,
    "音量": IntentType.AUDIO_ADJUST_VOLUME, "声音": IntentType.AUDIO_ADJUST_VOLUME,
    "背景音乐": IntentType.AUDIO_ADD_BGM, "配乐": IntentType.AUDIO_ADD_BGM,
    "进度": IntentType.STATE_QUERY_PROGRESS, "在哪": IntentType.STATE_QUERY_PROGRESS,
    "能做什么": IntentType.STATE_QUERY_CAPABILITIES, "功能": IntentType.STATE_QUERY_CAPABILITIES,
    "撤销": IntentType.STATE_UNDO,
    "重做": IntentType.STATE_REDO,
    "合成": IntentType.STATE_RENDER, "渲染": IntentType.STATE_RENDER, "导出": IntentType.STATE_RENDER,
    "交换": IntentType.CLIP_SWAP, "对调": IntentType.CLIP_SWAP,
}


class IntentRecognizer:
    """V0.1: keyword matching. V0.2+: LLM-based semantic understanding."""

    def __init__(self):
        self._examples: List[Dict] = []
        debug("IntentRecognizer initialized (keyword mode)")

    def recognize(self, text: str, context: Optional[Dict] = None) -> IntentResult:
        if is_asset_url(text):
            return IntentResult(
                intent=IntentType.ASSET_ADD,
                params={"url": text.strip(), "raw_text": text},
            )
        for keyword, intent in _KEYWORD_INTENT_MAP.items():
            if keyword in text:
                return IntentResult(intent=intent, params={"raw_text": text})
        # 语义完整的自然语言指令默认视为"创建规划"，交由 PlannerAgent 结合 LLM 解读
        return IntentResult(
            intent=IntentType.PLAN_CREATE,
            confidence=1.0,
            params={"raw_text": text},
        )

    def extract_params(self, text: str, intent: IntentType) -> Dict[str, Any]:
        return {"raw_text": text}

    def needs_clarification(self, text: str) -> bool:
        return len(text.strip()) < 2

    def generate_clarification(self, text: str) -> str:
        return f"请详细描述您的需求，例如'把自我介绍放开头，活动放中间，风景放结尾'"
