"""Request schemas — Pydantic models for API input."""

from typing import Optional
from pydantic import BaseModel, Field


class HubRequestSchema(BaseModel):
    user_input: str = Field(..., min_length=1, description="Natural language instruction")
    session_id: Optional[str] = Field(None, description="Session identifier")
    language: str = Field(default="zh", description="Language code")
