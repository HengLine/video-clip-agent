"""CLI commands — command handling and hub integration."""

from typing import Any, Dict, Optional
from neoclip.core.hub.central_hub import get_hub, HubResponse


def handle_command(command: str, session_id: Optional[str] = None, user_input: Optional[str] = None) -> HubResponse:
    hub = get_hub()

    if command == "help":
        return HubResponse(success=True, message="Available: process, status, capabilities, exit")

    if command == "capabilities":
        caps = hub.get_capabilities()
        return HubResponse(success=True, message=f"{len(caps)} capability(s) registered", data={"capabilities": [c.name for c in caps]})

    if command == "status":
        return HubResponse(success=True, message="System is running")

    if command == "process" and user_input:
        return hub.process(user_input=user_input, session_id=session_id)

    return HubResponse(success=False, message=f"Unknown command: {command}. Type 'help' for available commands.")
