"""Event schemas — WebSocket event payload models."""

from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class EventSchema(BaseModel):
    event_type: str
    session_id: Optional[str] = None
    data: Dict[str, Any] = Field(default_factory=dict)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
