"""CapabilityRegistry — maps intent types to registered agent capabilities."""

import threading
from typing import Dict, List, Optional

from neoclip.domain.value_objects.intent import IntentType
from neoclip.domain.value_objects.capability import CapabilityDeclaration
from neoclip.logger import debug, info


class CapabilityRegistry:
    def __init__(self):
        self._capabilities: Dict[str, CapabilityDeclaration] = {}
        self._intent_index: Dict[IntentType, List[str]] = {}
        self._lock = threading.Lock()

    def register(self, declaration: CapabilityDeclaration) -> bool:
        with self._lock:
            self._capabilities[declaration.name] = declaration
            for intent in declaration.intents:
                if intent not in self._intent_index:
                    self._intent_index[intent] = []
                self._intent_index[intent].append(declaration.name)
            info(f"CapabilityRegistry: registered '{declaration.name}' with {len(declaration.intents)} intent(s)")
            return True

    def unregister(self, name: str) -> bool:
        with self._lock:
            decl = self._capabilities.pop(name, None)
            if decl is None:
                return False
            for intent in decl.intents:
                if intent in self._intent_index:
                    self._intent_index[intent] = [n for n in self._intent_index[intent] if n != name]
            return True

    def find_by_intent(self, intent: IntentType) -> List[CapabilityDeclaration]:
        with self._lock:
            names = self._intent_index.get(intent, [])
            return [self._capabilities[n] for n in names if n in self._capabilities]

    def find_by_name(self, name: str) -> Optional[CapabilityDeclaration]:
        with self._lock:
            return self._capabilities.get(name)

    def list_all(self) -> List[CapabilityDeclaration]:
        with self._lock:
            return list(self._capabilities.values())

    def get_intent_map(self) -> Dict[IntentType, List[str]]:
        with self._lock:
            return dict(self._intent_index)
