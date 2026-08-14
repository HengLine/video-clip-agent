"""Intent type enumeration — maps user commands to routable intent categories."""

from enum import Enum


class IntentType(str, Enum):
    # ── 规划类意图 ──
    PLAN_CREATE = "plan_create"
    PLAN_APPEND = "plan_append"
    PLAN_INSERT = "plan_insert"
    PLAN_DELETE = "plan_delete"
    PLAN_REORDER = "plan_reorder"
    PLAN_DUPLICATE = "plan_duplicate"

    # ── 分析类意图 ──
    ANALYZE_FULL = "analyze_full"
    ANALYZE_INCREMENTAL = "analyze_incremental"
    ANALYZE_PRIORITY = "analyze_priority"
    ANALYZE_CANCEL = "analyze_cancel"

    # ── 素材类意图 ──
    CLIP_TRIM = "clip_trim"
    CLIP_REPLACE = "clip_replace"
    CLIP_SWAP = "clip_swap"
    CLIP_PREVIEW = "clip_preview"
    CLIP_REMOVE = "clip_remove"

    # ── 效果类意图 ──
    EFFECT_ADD_TRANSITION = "effect_add_transition"
    EFFECT_CHANGE_TRANSITION = "effect_change_transition"
    EFFECT_ADD_FILTER = "effect_add_filter"
    EFFECT_REMOVE_FILTER = "effect_remove_filter"
    AUDIO_ADJUST_VOLUME = "audio_adjust_volume"
    AUDIO_ADD_BGM = "audio_add_bgm"
    AUDIO_ADJUST_BGM_VOLUME = "audio_adjust_bgm_volume"

    # ── 状态类意图 ──
    STATE_QUERY_PROGRESS = "state_query_progress"
    STATE_QUERY_CAPABILITIES = "state_query_capabilities"
    STATE_UNDO = "state_undo"
    STATE_REDO = "state_redo"
    STATE_RENDER = "state_render"

    # ── 通用 ──
    EXECUTE = "execute"
    UNKNOWN = "unknown"

    @classmethod
    def _missing_(cls, value):
        return cls.UNKNOWN
