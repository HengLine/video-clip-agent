"""Bridge module — re-exports IntentType and TaskLifecycleStage for backward compatibility.

Existing code imports:
    from penclip.state.models import IntentType, TaskLifecycleStage
"""

from penclip.domain.value_objects.intent import IntentType
from penclip.core.state.state_schema import TaskLifecycleStage

__all__ = ["IntentType", "TaskLifecycleStage"]
