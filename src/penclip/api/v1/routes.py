"""Route registration — aggregates all v1 API routers."""

from fastapi import APIRouter

from penclip.api.v1.session import router as session_router
from penclip.api.v1.asset import router as asset_router
from penclip.api.v1.timeline import router as timeline_router
from penclip.api.v1.export import router as export_router
from penclip.api.v1.webhook import router as webhook_router
from penclip.api.v1.task import router as task_router

router = APIRouter(prefix="/api/v1")
router.include_router(task_router)
router.include_router(session_router)
router.include_router(asset_router)
router.include_router(timeline_router)
router.include_router(export_router)
router.include_router(webhook_router)
