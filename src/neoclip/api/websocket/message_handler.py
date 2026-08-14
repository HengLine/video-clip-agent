"""MessageHandler — WebSocket message routing to hub."""

from typing import Any, Dict
from neoclip.core.hub.central_hub import get_hub


class MessageHandler:
    def __init__(self):
        self._hub = get_hub()

    async def handle(self, session_id: str, message: Dict[str, Any]) -> Dict[str, Any]:
        user_input = message.get("text", "")
        response = self._hub.process(user_input, session_id=session_id)
        return {
            "success": response.success,
            "message": response.message,
            "data": response.data,
            "needs_confirmation": response.needs_confirmation,
        }
