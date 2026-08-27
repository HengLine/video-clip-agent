"""Segment entity — a continuous clip within a video asset, with semantic labels."""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Segment(BaseModel):
    segment_id: str = Field(default_factory=lambda: f"seg_{id(object())}")
    asset_id: str = ""
    start_time: float = 0.0
    end_time: float = 0.0
    labels: List[str] = Field(default_factory=list)
    label_scores: Dict[str, float] = Field(default_factory=dict)
    thumbnail_path: str = ""
    feature_vector: Optional[bytes] = None
    quality_score: float = 0.0

    @property
    def duration(self) -> float:
        return self.end_time - self.start_time

    def is_valid(self) -> bool:
        return self.duration > 0 and self.asset_id != ""

    def contains_time(self, time: float) -> bool:
        return self.start_time <= time <= self.end_time
