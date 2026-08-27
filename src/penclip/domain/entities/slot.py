"""Slot entity — a position in the timeline with semantic requirements."""

from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class Slot(BaseModel):
    slot_id: str = Field(default_factory=lambda: f"slot_{id(object())}")
    position: int = 0
    semantic_query: str = ""
    min_duration: float = 1.0
    max_duration: float = 30.0
    source_constraint: Optional[str] = None
    transition_type: str = "fade"
    assigned_segment_id: Optional[str] = None
    confidence: float = 0.0
    custom_params: Dict[str, Any] = Field(default_factory=dict)

    def is_filled(self) -> bool:
        return self.assigned_segment_id is not None

    def is_editable(self) -> bool:
        return True
