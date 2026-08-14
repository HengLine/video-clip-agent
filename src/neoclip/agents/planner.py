"""PlannerAgent — creates and modifies timeline blueprints from user intents."""

from typing import Any, Dict, List, Optional

from neoclip.agents.base import BaseAgent, ExecutionContext
from neoclip.domain.value_objects.capability import CapabilityDeclaration
from neoclip.domain.value_objects.execution_result import ExecutionResult
from neoclip.domain.value_objects.intent import IntentType
from neoclip.domain.value_objects.risk import RiskLevel
from neoclip.domain.entities.timeline import TimelineBlueprint
from neoclip.domain.entities.slot import Slot
from neoclip.logger import info


DEFAULT_CONFIG = {
    "max_slots": 20,
    "default_duration": 5.0,
}


class PlannerAgent(BaseAgent):
    agent_id = "planner"
    agent_name = "PlannerAgent"
    version = "0.1.0"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        cfg = {**DEFAULT_CONFIG, **(config or {})}
        super().__init__(config=cfg)

    def declare_capabilities(self) -> CapabilityDeclaration:
        return CapabilityDeclaration(
            name="timeline_planner",
            intents=[
                IntentType.PLAN_CREATE, IntentType.PLAN_APPEND,
                IntentType.PLAN_INSERT, IntentType.PLAN_DELETE,
                IntentType.PLAN_REORDER, IntentType.PLAN_DUPLICATE,
            ],
            description="Creates and modifies timeline blueprints from user instructions",
            input_schema={
                "instruction": {"type": "string", "description": "Natural language instruction"},
            },
            output_schema={
                "timeline": {"type": "object", "description": "TimelineBlueprint"},
            },
            risk_level=RiskLevel.HIGH,
            version=self.version,
            agent_id=self.agent_id,
        )

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        instruction = params.get("raw_text", "") or params.get("instruction", "")
        timeline = self._parse_intent(instruction)
        return ExecutionResult(
            success=True,
            data={"timeline": timeline.model_dump()},
            message=f"Created timeline with {len(timeline.slots)} slot(s)",
        )

    def _parse_intent(self, text: str) -> TimelineBlueprint:
        slots = self._build_slots(text)
        timeline = TimelineBlueprint(slots=slots, total_duration=sum(
            (s.min_duration + s.max_duration) / 2 for s in slots
        ))
        return self._apply_global_context(timeline)

    def _build_slots(self, text: str) -> List[Slot]:
        """V0.1: simple keyword-based slot extraction."""
        segments = text.replace("，", ",").replace("、", ",").split(",")
        slots = []
        for i, seg in enumerate(segments):
            seg = seg.strip()
            if not seg:
                continue
            slots.append(Slot(
                position=i,
                semantic_query=seg,
                min_duration=3.0,
                max_duration=15.0,
                transition_type="fade",
            ))
        return slots

    def _apply_global_context(self, timeline: TimelineBlueprint) -> TimelineBlueprint:
        return timeline


_planner: PlannerAgent = None


def get_planner_agent() -> PlannerAgent:
    global _planner
    if _planner is None:
        _planner = PlannerAgent()
    return _planner
