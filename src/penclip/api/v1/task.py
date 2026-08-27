"""Task API endpoints — submit natural-language instructions for async processing."""

from fastapi import APIRouter, HTTPException

from penclip.api.schemas.request import HubRequestSchema
from penclip.api.task_backend import get_task_lifecycle_manager

router = APIRouter(prefix="/tasks", tags=["task"])


@router.post("")
def submit_task(request: HubRequestSchema):
    """提交自然语言指令，异步执行中枢处理，返回任务 ID。"""
    manager = get_task_lifecycle_manager()
    session_id, task_id = manager.submit(
        script=request.user_input,
        session_id=request.session_id,
        metadata={"language": request.language},
    )
    return {"task_id": task_id, "session_id": session_id, "status": "pending"}


@router.get("/{task_id}")
def get_task_status(task_id: str):
    """查询任务状态。"""
    manager = get_task_lifecycle_manager()
    status = manager.get_status(task_id)
    if status is None:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
    return status


@router.get("/{task_id}/result")
def get_task_result(task_id: str):
    """查询任务结果。"""
    manager = get_task_lifecycle_manager()
    result = manager.get_result(task_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
    return result


@router.delete("/{task_id}")
def cancel_task(task_id: str):
    """取消任务。"""
    manager = get_task_lifecycle_manager()
    if manager.get_status(task_id) is None:
        raise HTTPException(status_code=404, detail=f"任务不存在: {task_id}")
    cancelled = manager.cancel(task_id)
    return {"task_id": task_id, "cancelled": cancelled}
