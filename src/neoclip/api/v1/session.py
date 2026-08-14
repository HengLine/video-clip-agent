"""Session API endpoints."""

from fastapi import APIRouter

router = APIRouter(prefix="/session", tags=["session"])


@router.post("/")
async def create_session():
    return {"status": "ok", "message": "Session created (stub)"}


@router.get("/{session_id}")
async def get_session(session_id: str):
    return {"session_id": session_id, "status": "active"}


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    return {"session_id": session_id, "status": "deleted"}
