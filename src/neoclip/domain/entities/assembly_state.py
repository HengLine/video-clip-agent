"""AssemblyState — the central global state shared across all agents and the hub."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from neoclip.domain.entities.slot import Slot
from neoclip.domain.entities.segment import Segment
from neoclip.domain.entities.video_asset import VideoAsset


class GlobalContext(BaseModel):
    mood: str = ""
    bgm_path: Optional[str] = None
    bgm_volume: float = 0.5
    output_resolution: str = "1920x1080"
    output_format: str = "mp4"
    style_prompt: Optional[str] = None
    custom_settings: Dict[str, Any] = Field(default_factory=dict)


class InteractionContext(BaseModel):
    active_slot_id: Optional[str] = None
    last_previewed_clip: Optional[str] = None
    pending_clarification: Optional[str] = None
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    undo_stack: List[Dict[str, Any]] = Field(default_factory=list)
    current_operation: Optional[str] = None


class AnalysisResult(BaseModel):
    asset_id: str = ""
    segments: List[Segment] = Field(default_factory=list)
    scene_breakdown: Dict[str, float] = Field(default_factory=dict)
    analysis_duration: float = 0.0
    status: str = "pending"
    completed_at: Optional[datetime] = None

    def get_segment_by_label(self, label: str) -> List[Segment]:
        return [s for s in self.segments if label in s.labels]

    def get_segments_by_time(self, start: float, end: float) -> List[Segment]:
        return [s for s in self.segments if s.start_time >= start and s.end_time <= end]


class MatchCandidate(BaseModel):
    candidate_id: str = Field(default_factory=lambda: f"cand_{id(object())}")
    segment_id: str = ""
    similarity_score: float = 0.0
    duration_match_score: float = 0.0
    overall_score: float = 0.0
    score_breakdown: Dict[str, float] = Field(default_factory=dict)

    def meets_constraints(self) -> bool:
        return self.overall_score > 0


class MatchResult(BaseModel):
    slot_id: str = ""
    candidates: List[MatchCandidate] = Field(default_factory=list)
    selected_candidate_id: Optional[str] = None
    match_duration: float = 0.0
    is_confirmed: bool = False

    def get_best_candidate(self) -> Optional[MatchCandidate]:
        if not self.candidates:
            return None
        return max(self.candidates, key=lambda c: c.overall_score)

    def select_candidate(self, candidate_id: str):
        self.selected_candidate_id = candidate_id
        self.is_confirmed = True


class AssemblyState(BaseModel):
    session_id: str = Field(default_factory=lambda: f"sess_{id(object())}")
    assets: List[VideoAsset] = Field(default_factory=list)
    slots: List[Slot] = Field(default_factory=list)
    analysis_results: Dict[str, AnalysisResult] = Field(default_factory=dict)
    match_results: Dict[str, MatchResult] = Field(default_factory=dict)
    global_context: GlobalContext = Field(default_factory=GlobalContext)
    interaction_context: InteractionContext = Field(default_factory=InteractionContext)
    current_phase: str = "idle"
    history: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def get_asset(self, asset_id: str) -> Optional[VideoAsset]:
        for a in self.assets:
            if a.asset_id == asset_id:
                return a
        return None

    def get_slot(self, slot_id: str) -> Optional[Slot]:
        for s in self.slots:
            if s.slot_id == slot_id:
                return s
        return None

    def add_asset(self, asset: VideoAsset):
        self.assets.append(asset)
        self.updated_at = datetime.now(timezone.utc)

    def add_slot(self, slot: Slot):
        self.slots.append(slot)
        self.updated_at = datetime.now(timezone.utc)

    def update_slot(self, slot_id: str, update: Dict[str, Any]):
        slot = self.get_slot(slot_id)
        if slot:
            for k, v in update.items():
                if hasattr(slot, k):
                    setattr(slot, k, v)
            self.updated_at = datetime.now(timezone.utc)
