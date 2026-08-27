"""Capability declaration — how agents advertise their abilities to the hub."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from penclip.domain.value_objects.intent import IntentType
from penclip.domain.value_objects.risk import RiskLevel


@dataclass
class CapabilityDeclaration:
    name: str
    intents: List[IntentType] = field(default_factory=list)
    description: str = ""
    input_schema: Dict[str, Any] = field(default_factory=dict)
    output_schema: Dict[str, Any] = field(default_factory=dict)
    risk_level: RiskLevel = RiskLevel.MEDIUM
    version: str = "0.1.0"
    agent_id: Optional[str] = None
