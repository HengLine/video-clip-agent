"""Export API endpoints — render and download final videos."""

from fastapi import APIRouter

router = APIRouter(prefix="/export", tags=["export"])


@router.post("/render")
async def start_render():
    return {"status": "ok", "task_id": "stub-task-id", "message": "Render started (stub)"}


@router.get("/status/{task_id}")
async def get_render_status(task_id: str):
    return {"task_id": task_id, "status": "completed"}


@router.get("/download/{task_id}")
async def download_video(task_id: str):
    return {"task_id": task_id, "url": "/data/output/output.mp4"}
