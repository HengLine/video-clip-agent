"""Timeline API endpoints — create, modify, query timelines."""

from fastapi import APIRouter

router = APIRouter(prefix="/timelines", tags=["timeline"])


@router.post("")
async def create_timeline():
    return {"status": "ok", "message": "Timeline created (stub)"}


@router.get("/{timeline_id}")
async def get_timeline(timeline_id: str):
    return {"timeline_id": timeline_id, "slots": []}


@router.put("/{timeline_id}/slots/{slot_id}")
async def update_slot(timeline_id: str, slot_id: str):
    return {"timeline_id": timeline_id, "slot_id": slot_id, "status": "updated"}
