"""PlannerAgent — creates and modifies timeline blueprints from user intents."""

import json
import os
from typing import Any, Dict, List, Optional

from penclip.agents.base import BaseAgent, ExecutionContext
from penclip.domain.value_objects.capability import CapabilityDeclaration
from penclip.domain.value_objects.execution_result import ExecutionResult
from penclip.domain.value_objects.intent import IntentType
from penclip.domain.value_objects.risk import RiskLevel
from penclip.domain.entities.timeline import TimelineBlueprint
from penclip.domain.entities.slot import Slot
from penclip.logger import info


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
        llm_slots = self._extract_slots_via_llm(text)
        if llm_slots:
            return [
                Slot(
                    position=i,
                    semantic_query=s["query"],
                    min_duration=3.0,
                    max_duration=15.0,
                    transition_type="fade",
                )
                for i, s in enumerate(llm_slots)
            ]
        return self._build_slots_by_keyword(text)

    def _build_slots_by_keyword(self, text: str) -> List[Slot]:
        """V0.1 兜底：逗号切分提取槽位。"""
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

    def _extract_slots_via_llm(self, text: str) -> Optional[List[Dict[str, Any]]]:
        """调用 LLM 解读需求并提取槽位；失败返回 None 回退关键词解析。"""
        try:
            from penclip.client.client_factory import get_ai_client, convert_response
            from penclip.services.llm_config import resolve_provider_config

            provider = os.environ.get("AI_PROVIDER") or "qwen"
            client = get_ai_client(provider)
            model = resolve_provider_config(provider).model

            messages = [
                {
                    "role": "system",
                    "content": (
                        "你是视频剪辑助手。根据用户需求提取时间线片段槽位，"
                        "返回 JSON 数组，每项含 query（片段描述）与 position（从 0 开始的序号）。"
                        "只输出 JSON，不要输出其他内容。"
                    ),
                },
                {"role": "user", "content": text},
            ]
            response = client.chat.completions.create(
                model=model, messages=messages, temperature=0.1
            )
            content = convert_response(provider, response)
            slots = json.loads(self._strip_markdown(content))
            if isinstance(slots, list):
                return [s for s in slots if isinstance(s, dict) and s.get("query")]
            return None
        except Exception as e:
            info(f"PlannerAgent: LLM 槽位提取不可用，回退关键词解析: {e}")
            return None

    @staticmethod
    def _strip_markdown(content: str) -> str:
        """去除 LLM 输出中的 Markdown 代码块标记，并提取 JSON 部分。"""
        content = content.strip()
        if content.startswith("```"):
            content = "\n".join(content.split("\n")[1:])
        if content.endswith("```"):
            content = "\n".join(content.split("\n")[:-1])
        if "{" in content and "}" in content:
            content = content[content.find("{") : content.rfind("}") + 1]
        return content

    def _apply_global_context(self, timeline: TimelineBlueprint) -> TimelineBlueprint:
        return timeline


_planner: PlannerAgent = None


def get_planner_agent() -> PlannerAgent:
    global _planner
    if _planner is None:
        _planner = PlannerAgent()
    return _planner
