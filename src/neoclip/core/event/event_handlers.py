"""Event handlers — base class and built-in handlers for event processing."""

from abc import ABC, abstractmethod

from neoclip.core.event.event_types import Event
from neoclip.logger import info


class EventHandler(ABC):
    @abstractmethod
    def handle(self, event: Event) -> None:
        ...


class LoggingEventHandler(EventHandler):
    def handle(self, event: Event) -> None:
        info(f"[Event] {event.event_type.value} session={event.session_id or '-'}")
