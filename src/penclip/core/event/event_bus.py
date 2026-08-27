"""EventBus — singleton publish/subscribe event system."""

import threading
from typing import Callable, Dict, List

from penclip.core.event.event_types import Event, EventType
from penclip.logger import debug


class EventBus:
    def __init__(self):
        self._subscribers: Dict[EventType, List[Callable]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_type: EventType, handler: Callable[[Event], None]):
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            self._subscribers[event_type].append(handler)
            debug(f"EventBus: subscribed to {event_type.value}")

    def unsubscribe(self, event_type: EventType, handler: Callable[[Event], None]):
        with self._lock:
            if event_type in self._subscribers:
                self._subscribers[event_type] = [h for h in self._subscribers[event_type] if h is not handler]

    def publish(self, event: Event):
        with self._lock:
            handlers = self._subscribers.get(event.event_type, [])
        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                debug(f"EventBus: handler error for {event.event_type.value}: {e}")


_bus: EventBus = None


def get_event_bus() -> EventBus:
    global _bus
    if _bus is None:
        _bus = EventBus()
    return _bus
