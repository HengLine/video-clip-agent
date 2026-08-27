"""TimelineBlueprint entity — the top-level plan for a video assembly."""

from typing import List

from pydantic import BaseModel, Field

from penclip.domain.entities.slot import Slot


class TimelineBlueprint(BaseModel):
    timeline_id: str = Field(default_factory=lambda: f"tl_{id(object())}")
    slots: List[Slot] = Field(default_factory=list)
    total_duration: float = 0.0
    output_resolution: str = "1920x1080"
    output_format: str = "mp4"

    def get_slot(self, slot_id: str):
        for s in self.slots:
            if s.slot_id == slot_id:
                return s
        return None

    def get_slot_by_position(self, position: int):
        for s in self.slots:
            if s.position == position:
                return s
        return None
