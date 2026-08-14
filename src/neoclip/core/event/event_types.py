"""Event type definitions for the event system."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional


class EventType(str, Enum):
    SESSION_CREATED = "session_created"
    SESSION_CLOSED = "session_closed"
    ASSET_UPLOADED = "asset_uploaded"
    ASSET_ANALYZED = "asset_analyzed"
    INTENT_RECOGNIZED = "intent_recognized"
    CAPABILITY_REGISTERED = "capability_registered"
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    STATE_UPDATED = "state_updated"
    CONFIRMATION_REQUIRED = "confirmation_required"
    ERROR_OCCURRED = "error_occurred"


@dataclass
class Event:
    event_type: EventType
    session_id: Optional[str] = None
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    event_id: str = field(default_factory=lambda: f"evt_{id(object())}")
