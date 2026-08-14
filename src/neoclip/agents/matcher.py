"""MatcherAgent — matches timeline slots to video segments via semantic search."""

from typing import Any, Dict, List, Optional

from neoclip.agents.base import BaseAgent, ExecutionContext
from neoclip.domain.value_objects.capability import CapabilityDeclaration
from neoclip.domain.value_objects.execution_result import ExecutionResult
from neoclip.domain.value_objects.intent import IntentType
from neoclip.domain.value_objects.risk import RiskLevel
from neoclip.domain.entities.segment import Segment
from neoclip.domain.entities.assembly_state import MatchCandidate, MatchResult
from neoclip.logger import info


DEFAULT_CONFIG = {
    "similarity_threshold": 0.3,
    "max_candidates_per_slot": 3,
}


class MatcherAgent(BaseAgent):
    agent_id = "matcher"
    agent_name = "MatcherAgent"
    version = "0.1.0"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        cfg = {**DEFAULT_CONFIG, **(config or {})}
        super().__init__(config=cfg)

    def declare_capabilities(self) -> CapabilityDeclaration:
        return CapabilityDeclaration(
            name="segment_matcher",
            intents=[
                IntentType.CLIP_TRIM, IntentType.CLIP_REPLACE,
                IntentType.CLIP_SWAP, IntentType.CLIP_REMOVE,
                IntentType.CLIP_PREVIEW, IntentType.EXECUTE,
            ],
            description="Semantic search and match of video segments to timeline slots",
            input_schema={
                "slots": {"type": "list", "description": "Slots to match"},
                "segments": {"type": "list", "description": "Available segments"},
            },
            output_schema={
                "match_results": {"type": "object", "description": "Per-slot match results"},
            },
            risk_level=RiskLevel.MEDIUM,
            version=self.version,
            agent_id=self.agent_id,
        )

    def execute(self, params: Dict[str, Any], context: ExecutionContext) -> ExecutionResult:
        slots = params.get("slots", [])
        segments = params.get("segments", [])
        info(f"MatcherAgent: matching {len(slots)} slot(s) against {len(segments)} segment(s)")

        results = {}
        for slot_data in slots:
            matches = self._semantic_search(slot_data.get("semantic_query", ""), segments)
            constrained = self._apply_constraints(matches, slot_data)
            ranked = self._rank_by_similarity(constrained)
            results[slot_data.get("slot_id", "")] = {
                "candidates": [m.model_dump() for m in ranked[:self._config.get("max_candidates_per_slot", 3)]],
            }

        return ExecutionResult(
            success=True,
            data={"match_results": results},
            message=f"Matched {len(results)} slot(s)",
        )

    def _semantic_search(self, query: str, segments: List[Dict]) -> List[MatchCandidate]:
        return []

    def _apply_constraints(self, candidates: List[MatchCandidate], constraints: Dict) -> List[MatchCandidate]:
        return candidates

    def _rank_by_similarity(self, candidates: List[MatchCandidate]) -> List[MatchCandidate]:
        return sorted(candidates, key=lambda c: c.overall_score, reverse=True)
