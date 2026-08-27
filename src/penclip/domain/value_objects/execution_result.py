"""Execution result — standardized response from capability execution."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ExecutionResult:
    success: bool
    data: Optional[Dict[str, Any]] = None
    message: str = ""
    suggestions: List[str] = field(default_factory=list)
    status: str = "completed"
    command_id: Optional[str] = None
