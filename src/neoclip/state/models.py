"""Bridge module — re-exports IntentType and TaskLifecycleStage for backward compatibility.

Existing code imports:
    from neoclip.state.models import IntentType, TaskLifecycleStage
"""

from neoclip.domain.value_objects.intent import IntentType
from neoclip.core.state.state_schema import TaskLifecycleStage

__all__ = ["IntentType", "TaskLifecycleStage"]
