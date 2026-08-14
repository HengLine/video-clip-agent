"""Webhook API endpoints — async event callbacks."""

from fastapi import APIRouter

router = APIRouter(prefix="/webhook", tags=["webhook"])


@router.post("/register")
async def register_webhook():
    return {"status": "ok", "message": "Webhook registered (stub)"}


@router.delete("/{webhook_id}")
async def delete_webhook(webhook_id: str):
    return {"webhook_id": webhook_id, "status": "deleted"}
