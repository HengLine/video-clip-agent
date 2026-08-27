"""VideoAsset entity — represents an uploaded video file and its metadata."""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class AssetStatus(str, Enum):
    UPLOADING = "uploading"
    UPLOADED = "uploaded"
    ANALYZING = "analyzing"
    ANALYZED = "analyzed"
    ERROR = "error"


class VideoAsset(BaseModel):
    asset_id: str = Field(default_factory=lambda: f"asset_{id(object())}")
    filename: str = ""
    file_path: str = ""
    file_hash: str = ""
    duration: float = 0.0
    width: int = 0
    height: int = 0
    bitrate: int = 0
    status: AssetStatus = AssetStatus.UPLOADING
    metadata: Dict[str, Any] = Field(default_factory=dict)
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def is_analyzed(self) -> bool:
        return self.status == AssetStatus.ANALYZED

    def get_thumbnail(self) -> str:
        return f"{self.file_path}.thumb.jpg"
