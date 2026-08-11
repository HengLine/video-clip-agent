"""
@FileName: intent_recognizer.py
@Description: V0.1 意图识别器 — 基于关键字的意图分类
    扫描用户输入的文本，匹配预定义的关键词表，返回最佳匹配意图
    V0.2: 替换为 LLMIntentRecognizer（LLM 结构化输出），接口不变
@Author: HiPeng
@Time: 2026/08
"""
import re
from typing import Any, Dict, List, Optional

from neoclip.logger import debug
from neoclip.state.models import (
    CommandTier,
    ExtractedParams,
    IntentType,
    RecognizedIntent,
)


# ============================================================================
# V0.1 关键字 → 意图映射表（中英文双语）
# ============================================================================

DEFAULT_INTENT_KEYWORDS: Dict[IntentType, List[str]] = {
    # ── 规划类 ──
    IntentType.PLAN_CREATE: [
        "创建", "生成", "制作", "做个", "新建", "建一个", "生成时间线", "规划",
        "create", "make", "generate", "build", "new timeline", "plan",
    ],
    IntentType.PLAN_APPEND: [
        "追加", "添加片段", "加一段", "再加", "补充", "append", "add slot", "add clip",
    ],
    IntentType.PLAN_INSERT: [
        "插入", "中间加", "在.*之前插入", "insert", "add between",
    ],
    IntentType.PLAN_DELETE: [
        "删除", "移除片段", "去掉", "删除片段", "delete", "remove slot",
    ],
    IntentType.PLAN_REORDER: [
        "重新排序", "交换顺序", "移到", "移动到", "调整顺序", "对调",
        "reorder", "move", "swap order", "rearrange",
    ],
    IntentType.PLAN_DUPLICATE: [
        "复制", "拷贝片段", "复用", "duplicate", "copy slot", "clone",
    ],

    # ── 分析类 ──
    IntentType.ANALYZE_FULL: [
        "完整分析", "分析所有", "全部分析", "analyze full", "full analysis",
    ],
    IntentType.ANALYZE_INCREMENTAL: [
        "增量分析", "分析新增", "analyze new", "incremental analysis",
    ],
    IntentType.ANALYZE_PRIORITY: [
        "优先分析", "先分析", "重点分析", "priority analyze",
    ],
    IntentType.ANALYZE_CANCEL: [
        "取消分析", "停止分析", "cancel analyze", "stop analysis",
    ],

    # ── 素材操作类 ──
    IntentType.CLIP_TRIM: [
        "裁剪", "修剪", "剪短", "剪到", "截取", "trim", "cut", "crop",
    ],
    IntentType.CLIP_REPLACE: [
        "替换", "换掉", "换成", "更换", "replace", "swap in",
    ],
    IntentType.CLIP_SWAP: [
        "交换", "对调", "互换", "swap", "exchange",
    ],
    IntentType.CLIP_PREVIEW: [
        "预览", "播放", "查看", "preview", "play", "show clip",
    ],
    IntentType.CLIP_REMOVE: [
        "移除", "去掉片段", "去除", "remove clip",
    ],

    # ── 效果类 ──
    IntentType.EFFECT_ADD_TRANSITION: [
        "添加转场", "加转场", "增加转场", "add transition",
    ],
    IntentType.EFFECT_CHANGE_TRANSITION: [
        "更换转场", "转场换成", "修改转场", "change transition", "switch transition",
    ],
    IntentType.EFFECT_ADD_FILTER: [
        "添加滤镜", "加滤镜", "增加滤镜", "add filter",
    ],
    IntentType.EFFECT_REMOVE_FILTER: [
        "移除滤镜", "去掉滤镜", "删除滤镜", "remove filter",
    ],
    IntentType.AUDIO_ADJUST_VOLUME: [
        "调整音量", "声音", "调大", "调小", "音量", "静音",
        "volume", "louder", "quieter", "mute",
    ],
    IntentType.AUDIO_ADD_BGM: [
        "添加背景音乐", "加音乐", "配乐", "背景音乐", "bgm", "add music",
    ],
    IntentType.AUDIO_ADJUST_BGM_VOLUME: [
        "背景音乐音量", "bgm音量", "bgm volume", "音乐大小",
    ],

    # ── 状态类 ──
    IntentType.STATE_QUERY_PROGRESS: [
        "进度", "进行到哪", "状态", "到什么", "progress", "status", "how is it going",
    ],
    IntentType.STATE_QUERY_CAPABILITIES: [
        "能做什么", "能力", "功能", "帮助", "help", "capabilities", "what can you do",
    ],
    IntentType.STATE_UNDO: [
        "撤销", "回退", "取消上一步", "undo", "revert",
    ],
    IntentType.STATE_REDO: [
        "重做", "恢复", "取消撤销", "redo", "restore",
    ],
}


# ============================================================================
# 参数提取正则模式
# ============================================================================

_SLOT_ID_PATTERNS = [
    (re.compile(r"第\s*(\d+)\s*[个段片]"), lambda m: int(m.group(1)) - 1),
    (re.compile(r"#(\d+)"), lambda m: int(m.group(1)) - 1),
    (re.compile(r"slot[_ ]?(\d+)", re.IGNORECASE), lambda m: int(m.group(1)) - 1),
]

_VOLUME_PATTERNS = [
    (re.compile(r"音量[到为]?\s*([\d.]+)"), lambda m: float(m.group(1))),
    (re.compile(r"volume\s*[:=]?\s*([\d.]+)", re.IGNORECASE), lambda m: float(m.group(1))),
    (re.compile(r"([\d.]+)\s*倍"), lambda m: float(m.group(1))),
]


class IntentRecognizer:
    """V0.1 关键字匹配意图识别器"""

    def __init__(self, keyword_map: Optional[Dict[IntentType, List[str]]] = None):
        self.keyword_map = keyword_map or DEFAULT_INTENT_KEYWORDS
        self._compiled: Dict[IntentType, List[re.Pattern]] = {}
        self._compile_patterns()

    def _compile_patterns(self) -> None:
        for intent, keywords in self.keyword_map.items():
            self._compiled[intent] = [re.compile(re.escape(kw), re.IGNORECASE) for kw in keywords]

    def recognize(self, user_input: str) -> RecognizedIntent:
        """扫描输入文本，返回最佳匹配意图"""
        if not user_input or not user_input.strip():
            return RecognizedIntent(
                intent_type=IntentType.STATE_QUERY_CAPABILITIES,
                confidence=0.0,
                raw_input=user_input,
                tier=CommandTier.TIER_3,
            )

        scores: Dict[IntentType, int] = {}
        for intent, patterns in self._compiled.items():
            count = sum(1 for p in patterns if p.search(user_input))
            if count > 0:
                scores[intent] = count

        if not scores:
            return RecognizedIntent(
                intent_type=IntentType.STATE_QUERY_CAPABILITIES,
                confidence=0.3,
                raw_input=user_input,
                tier=CommandTier.TIER_3,
            )

        best_intent = max(scores, key=scores.get)
        max_score = scores[best_intent]
        total_matches = sum(scores.values())
        confidence = min(1.0, max_score / max(1, len(self._compiled.get(best_intent, [])) * 0.3))

        debug(f"IntentRecognizer: '{user_input[:50]}...' → {best_intent.value} (conf={confidence:.2f}, score={max_score})")

        return RecognizedIntent.from_match(best_intent, user_input, confidence)


class ParameterExtractor:
    """V0.1 正则参数提取器"""

    def extract(self, user_input: str, intent: RecognizedIntent, context: Any = None) -> ExtractedParams:
        params: Dict[str, Any] = {}
        missing: List[str] = []

        # 提取 slot_id
        for pattern, extractor in _SLOT_ID_PATTERNS:
            m = pattern.search(user_input)
            if m:
                params["slot_id"] = extractor(m)
                break

        # 提取音量值
        for pattern, extractor in _VOLUME_PATTERNS:
            m = pattern.search(user_input)
            if m:
                val = extractor(m)
                if val <= 2.0:
                    params["volume"] = val
                else:
                    params["volume"] = val / 100.0
                break

        # 尝试从 context 补全缺失的 slot_id
        if "slot_id" not in params and context is not None:
            active_slot = getattr(context, "active_slot_id", None)
            if active_slot is not None:
                params["slot_id"] = active_slot
            else:
                last_clip = getattr(context, "last_previewed_clip", None)
                if last_clip is not None:
                    params["slot_id"] = last_clip

        # 判断是否需要澄清
        if intent.intent_type.tier == CommandTier.TIER_1 and not params:
            missing.append("timeline_description")
        if intent.intent_type in (IntentType.CLIP_TRIM, IntentType.CLIP_REPLACE) and "slot_id" not in params:
            missing.append("slot_id")

        clarification_needed = len(missing) > 0
        clarification_message = None
        if clarification_needed:
            clarification_message = f"需要补充信息: {', '.join(missing)}"

        return ExtractedParams(
            parameters=params,
            missing_params=missing,
            clarification_needed=clarification_needed,
            clarification_message=clarification_message,
        )


# ============================================================================
# 单例
# ============================================================================

_recognizer: Optional[IntentRecognizer] = None
_extractor: Optional[ParameterExtractor] = None


def get_intent_recognizer() -> IntentRecognizer:
    global _recognizer
    if _recognizer is None:
        _recognizer = IntentRecognizer()
    return _recognizer


def get_parameter_extractor() -> ParameterExtractor:
    global _extractor
    if _extractor is None:
        _extractor = ParameterExtractor()
    return _extractor
