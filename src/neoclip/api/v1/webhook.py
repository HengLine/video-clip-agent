"""Webhook API endpoints — async event callbacks."""

from fastapi import APIRouter

router = APIRouter(prefix="/webhooks", tags=["webhook"])


@router.post("")
async def register_webhook():
    return {"status": "ok", "message": "Webhook registered (stub)"}


@router.delete("/{webhook_id}")
async def delete_webhook(webhook_id: str):
    return {"webhook_id": webhook_id, "status": "deleted"}
