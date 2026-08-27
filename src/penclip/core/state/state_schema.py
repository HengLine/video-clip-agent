"""State schema — TaskLifecycleStage enum and re-exports from domain."""

from enum import Enum


class TaskLifecycleStage(str, Enum):
    PENDING = "pending"
    QUEUED = "queued"
    ANALYZING = "analyzing"
    MATCHING = "matching"
    COMPOSING = "composing"
    REVIEW = "review"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
