"""Response schemas — Pydantic models for API output."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class HubResponseSchema(BaseModel):
    success: bool
    intent: Optional[str] = None
    message: str = ""
    data: Optional[Dict[str, Any]] = None
    needs_confirmation: bool = False
    confirmation_message: str = ""
