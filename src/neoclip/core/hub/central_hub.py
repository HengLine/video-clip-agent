"""CentralHub — the star-hub command dispatch center."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from neoclip.core.hub.capability_registry import CapabilityRegistry
from neoclip.core.hub.intent_recognizer import IntentRecognizer, IntentResult
from neoclip.core.hub.risk_assessor import RiskAssessor
from neoclip.core.hub.context_manager import ContextManager
from neoclip.core.state.state_manager import get_state_manager
from neoclip.core.event.event_bus import get_event_bus
from neoclip.core.event.event_types import Event, EventType
from neoclip.domain.value_objects.intent import IntentType
from neoclip.domain.value_objects.risk import RiskLevel
from neoclip.domain.value_objects.execution_result import ExecutionResult
from neoclip.logger import info, warning


@dataclass
class HubRequest:
    user_input: str
    session_id: Optional[str] = None
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HubResponse:
    success: bool
    intent: Optional[IntentType] = None
    message: str = ""
    data: Optional[Dict[str, Any]] = None
    needs_confirmation: bool = False
    confirmation_message: str = ""


class CentralHub:
    def __init__(self):
        self.registry = CapabilityRegistry()
        self.intent_recognizer = IntentRecognizer()
        self.risk_assessor = RiskAssessor()
        self.context_manager = ContextManager()
        self.state_manager = get_state_manager()
        self.event_bus = get_event_bus()
        self._agents: Dict[str, Any] = {}
        info("CentralHub initialized")

    def process(self, user_input: str, session_id: Optional[str] = None) -> HubResponse:
        session_id = session_id or f"sess_{id(self)}"
        ctx = self.context_manager.get_context(session_id)

        # 1. Intent recognition
        intent_result = self.intent_recognizer.recognize(user_input)
        self.event_bus.publish(Event(
            event_type=EventType.INTENT_RECOGNIZED,
            session_id=session_id,
            data={"intent": intent_result.intent.value},
        ))

        # 2. Context update
        self.context_manager.add_history(session_id, {
            "role": "user", "content": user_input,
            "intent": intent_result.intent.value,
        })

        # 3. Risk assessment
        risk = self.risk_assessor.assess(intent_result.intent)
        needs_confirmation = self.risk_assessor.needs_confirmation(risk)

        # 4. Route to capability
        capabilities = self.registry.find_by_intent(intent_result.intent)
        if not capabilities:
            return HubResponse(
                success=False,
                intent=intent_result.intent,
                message=f"No capability registered for intent: {intent_result.intent.value}",
            )

        # 5. Execute first matching capability
        cap = capabilities[0]
        agent = self._agents.get(cap.agent_id) if cap.agent_id else None
        if agent:
            result = agent.execute(intent_result.params, {"session_id": session_id})
        else:
            result = ExecutionResult(success=True, message=f"Capability '{cap.name}' executed (no agent attached)")

        # 6. Build response
        return HubResponse(
            success=result.success,
            intent=intent_result.intent,
            message=result.message,
            data=result.data,
            needs_confirmation=needs_confirmation,
            confirmation_message=self.risk_assessor.generate_confirmation_message(intent_result.intent) if needs_confirmation else "",
        )

    def register_agent(self, agent: Any) -> bool:
        """Register an agent and its capabilities with the hub."""
        try:
            declaration = agent.declare_capabilities()
            declaration.agent_id = agent.agent_id
            self._agents[agent.agent_id] = agent
            self.registry.register(declaration)
            self.event_bus.publish(Event(
                event_type=EventType.CAPABILITY_REGISTERED,
                data={"agent_id": agent.agent_id, "capability": declaration.name},
            ))
            info(f"CentralHub: agent '{agent.agent_id}' registered")
            return True
        except Exception as e:
            warning(f"CentralHub: failed to register agent: {e}")
            return False

    def unregister_agent(self, agent_id: str) -> bool:
        agent = self._agents.pop(agent_id, None)
        if agent is None:
            return False
        self.registry.unregister(agent.declare_capabilities().name)
        return True

    def get_capabilities(self) -> List[Any]:
        return self.registry.list_all()

    def handle_interrupt(self, session_id: str, user_input: str) -> HubResponse:
        """Resume from an interrupt (e.g., user confirmation)."""
        return self.process(user_input, session_id=session_id)


_hub: CentralHub = None


def get_hub() -> CentralHub:
    global _hub
    if _hub is None:
        _hub = CentralHub()
    return _hub
