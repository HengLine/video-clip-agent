"""
@FileName: task_backend.py
@Description: 任务生命周期管理 — 真实 TaskFactory 后端
    TaskStore (线程安全内存存储) + TaskStateMachine (状态转换) + TaskLifecycleManager (高层接口)
    V0.1: 内存存储 (MemorySaver), V0.2: SQLite, V1.0: Redis
@Author: HiPeng
@Time: 2026/08
"""
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from neoclip.logger import debug, info, warning, error
from neoclip.state.models import IntentType, TaskLifecycleStage


# ============================================================================
# TaskRecord
# ============================================================================


class TaskRecord(BaseModel):
    """单条任务记录"""

    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    script_id: Optional[str] = None
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    status: str = "pending"  # TaskStatus value
    stage: str = TaskLifecycleStage.PENDING.value
    progress: int = Field(default=0, ge=0, le=100)
    intent_type: Optional[str] = None
    hub_result: Optional[Dict[str, Any]] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    batch_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return self.model_dump()


# ============================================================================
# TaskStore — 线程安全内存存储
# ============================================================================


class TaskStore:
    """线程安全的内存任务存储"""

    def __init__(self):
        self._tasks: Dict[str, TaskRecord] = {}
        self._lock = threading.Lock()

    def create(self, task_id: Optional[str] = None, script_id: Optional[str] = None,
               session_id: Optional[str] = None, intent_type: Optional[str] = None,
               batch_id: Optional[str] = None, metadata: Optional[Dict] = None) -> TaskRecord:
        record = TaskRecord(
            task_id=task_id or str(uuid.uuid4()),
            script_id=script_id,
            session_id=session_id or str(uuid.uuid4()),
            intent_type=intent_type,
            batch_id=batch_id,
            metadata=metadata or {},
        )
        with self._lock:
            self._tasks[record.task_id] = record
        debug(f"TaskStore: created task {record.task_id[:8]}")
        return record

    def get(self, task_id: str) -> Optional[TaskRecord]:
        with self._lock:
            return self._tasks.get(task_id)

    def update(self, task_id: str, **kwargs: Any) -> bool:
        with self._lock:
            record = self._tasks.get(task_id)
            if record is None:
                return False
            for key, value in kwargs.items():
                if hasattr(record, key):
                    setattr(record, key, value)
            record.updated_at = datetime.now(timezone.utc)
            return True

    def delete(self, task_id: str) -> bool:
        with self._lock:
            return self._tasks.pop(task_id, None) is not None

    def list_all(self) -> List[TaskRecord]:
        with self._lock:
            return list(self._tasks.values())

    def list_by_batch(self, batch_id: str) -> List[TaskRecord]:
        with self._lock:
            return [t for t in self._tasks.values() if t.batch_id == batch_id]

    def list_by_session(self, session_id: str) -> List[TaskRecord]:
        with self._lock:
            return [t for t in self._tasks.values() if t.session_id == session_id]

    def get_stats(self) -> Dict[str, Any]:
        with self._lock:
            tasks = list(self._tasks.values())
            total = len(tasks)
            by_status: Dict[str, int] = {}
            by_stage: Dict[str, int] = {}
            for t in tasks:
                by_status[t.status] = by_status.get(t.status, 0) + 1
                by_stage[t.stage] = by_stage.get(t.stage, 0) + 1
            return {
                "total_tasks": total,
                "by_status": by_status,
                "by_stage": by_stage,
                "total_submitted": total,
                "total_completed": by_status.get("success", 0) + by_status.get("failed", 0),
                "total_failed": by_status.get("failed", 0),
                "total_cancelled": by_status.get("cancelled", 0),
            }

    def get_pending_tasks(self, max_age_hours: float = 2) -> List[TaskRecord]:
        with self._lock:
            now = datetime.now(timezone.utc)
            return [
                t for t in self._tasks.values()
                if t.status in ("pending", "processing", "queued")
                and (now - t.created_at).total_seconds() < max_age_hours * 3600
            ]


# ============================================================================
# TaskStateMachine
# ============================================================================


class TaskStateMachine:
    """校验任务状态转换合法性"""

    # 来源 → 合法目标
    TRANSITIONS: Dict[str, List[str]] = {
        TaskLifecycleStage.PENDING.value: [
            TaskLifecycleStage.QUEUED.value,
            TaskLifecycleStage.CANCELLED.value,
            TaskLifecycleStage.FAILED.value,
        ],
        TaskLifecycleStage.QUEUED.value: [
            TaskLifecycleStage.ANALYZING.value,
            TaskLifecycleStage.CANCELLED.value,
            TaskLifecycleStage.FAILED.value,
        ],
        TaskLifecycleStage.ANALYZING.value: [
            TaskLifecycleStage.MATCHING.value,
            TaskLifecycleStage.CANCELLED.value,
            TaskLifecycleStage.FAILED.value,
        ],
        TaskLifecycleStage.MATCHING.value: [
            TaskLifecycleStage.COMPOSING.value,
            TaskLifecycleStage.CANCELLED.value,
            TaskLifecycleStage.FAILED.value,
        ],
        TaskLifecycleStage.COMPOSING.value: [
            TaskLifecycleStage.COMPLETED.value,
            TaskLifecycleStage.CANCELLED.value,
            TaskLifecycleStage.FAILED.value,
        ],
        TaskLifecycleStage.REVIEW.value: [
            TaskLifecycleStage.ANALYZING.value,
            TaskLifecycleStage.CANCELLED.value,
        ],
    }

    @classmethod
    def can_transition(cls, from_stage: str, to_stage: str) -> bool:
        if from_stage == to_stage:
            return True
        allowed = cls.TRANSITIONS.get(from_stage, [])
        return to_stage in allowed

    @classmethod
    def transition(cls, task: TaskRecord, new_stage: str) -> bool:
        if not cls.can_transition(task.stage, new_stage):
            warning(f"TaskStateMachine: invalid transition {task.stage} → {new_stage} (task={task.task_id[:8]})")
            return False
        task.stage = new_stage
        task.updated_at = datetime.now(timezone.utc)
        if new_stage == TaskLifecycleStage.COMPLETED.value:
            task.status = "success"
            task.completed_at = datetime.now(timezone.utc)
            task.progress = 100
        elif new_stage == TaskLifecycleStage.FAILED.value:
            task.status = "failed"
            task.completed_at = datetime.now(timezone.utc)
        elif new_stage == TaskLifecycleStage.CANCELLED.value:
            task.status = "cancelled"
            task.completed_at = datetime.now(timezone.utc)
        return True


# ============================================================================
# TaskLifecycleManager
# ============================================================================


class TaskLifecycleManager:
    """任务生命周期管理器 — TaskFactory 的后端"""

    def __init__(self):
        self.store = TaskStore()

    # ── 提交 ──

    def submit(self, script: str = "", script_id: Optional[str] = None,
               session_id: Optional[str] = None, intent_type: Optional[str] = None,
               batch_id: Optional[str] = None, metadata: Optional[Dict] = None) -> Tuple[str, str]:
        """返回 (script_id, task_id)"""
        sid = script_id or str(uuid.uuid4())
        task = self.store.create(
            task_id=str(uuid.uuid4()),
            script_id=sid,
            session_id=session_id or sid,
            intent_type=intent_type,
            batch_id=batch_id,
            metadata=metadata or {"script": script[:200]},
        )
        info(f"Task submitted: {task.task_id[:8]} [intent={intent_type}, session={sid[:8]}]")
        return sid, task.task_id

    # ── 状态查询 ──

    def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        task = self.store.get(task_id)
        if task is None:
            return None
        return {
            "task_id": task.task_id,
            "script_id": task.script_id,
            "status": task.status,
            "stage": task.stage,
            "progress": task.progress,
            "created_at": task.created_at,
            "updated_at": task.updated_at,
            "completed_at": task.completed_at,
        }

    def get_task(self, task_id: str) -> Optional[TaskRecord]:
        return self.store.get(task_id)

    def get_tasks_by_batch(self, batch_id: str) -> List[TaskRecord]:
        return self.store.list_by_batch(batch_id)

    # ── 结果查询 ──

    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        task = self.store.get(task_id)
        if task is None:
            return None
        return {
            "task_id": task.task_id,
            "script_id": task.script_id,
            "success": task.status == "success",
            "status": task.status,
            "data": (((task.hub_result or {}).get("result") or {}).get("data") if task.hub_result else None),
            "error": task.error_message,
            "processing_time_ms": int((task.completed_at - task.created_at).total_seconds() * 1000) if task.completed_at else None,
            "created_at": task.created_at,
            "completed_at": task.completed_at,
        }

    # ── 取消 ──

    def cancel(self, task_id: str) -> bool:
        task = self.store.get(task_id)
        if task is None:
            return False
        if task.status in ("success", "failed", "cancelled"):
            return False
        TaskStateMachine.transition(task, TaskLifecycleStage.CANCELLED.value)
        self.store.update(task_id, **task.model_dump())
        return True

    # ── 批量 ──

    def batch_submit(self, scripts: List[str], config: Optional[Dict] = None,
                     language: str = "zh", session_id: Optional[str] = None) -> Dict[str, Any]:
        batch_id = str(uuid.uuid4())
        task_ids = []
        for script in scripts:
            sid, tid = self.submit(
                script=script,
                script_id=str(uuid.uuid4()),
                session_id=session_id or str(uuid.uuid4()),
                batch_id=batch_id,
                metadata={"config": config, "language": language, "script": script[:200]},
            )
            task_ids.append(tid)
        return {
            "batch_id": batch_id,
            "total_tasks": len(task_ids),
            "task_ids": task_ids,
            "created_at": datetime.now(timezone.utc),
        }

    def batch_get_status(self, batch_id: str) -> List[Dict[str, Any]]:
        tasks = self.store.list_by_batch(batch_id)
        return [self.get_status(t.task_id) for t in tasks if self.get_status(t.task_id)]

    def batch_get_results(self, batch_id: str) -> List[Dict[str, Any]]:
        tasks = self.store.list_by_batch(batch_id)
        return [self.get_result(t.task_id) for t in tasks if self.get_result(t.task_id)]

    # ── 队列 & 统计 ──

    def get_queue_status(self) -> Dict[str, Any]:
        stats = self.store.get_stats()
        pending = self.store.get_pending_tasks()
        return {
            "queue_length": stats.get("by_status", {}).get("pending", 0),
            "processing": stats.get("by_status", {}).get("processing", 0),
            "total_pending": len(pending),
            "stats": stats,
        }

    def get_stats(self) -> Dict[str, Any]:
        return self.store.get_stats()

    def get_pending_tasks(self, max_age_hours: float = 2) -> List[Dict[str, Any]]:
        tasks = self.store.get_pending_tasks(max_age_hours)
        return [t.to_dict() for t in tasks]

    def recover_pending_tasks(self, max_age_hours: float = 2) -> int:
        """恢复未完成任务（V0.1: 仅计数，V0.3: 实际重新入队）"""
        tasks = self.store.get_pending_tasks(max_age_hours)
        info(f"Task recovery: found {len(tasks)} pending tasks (max_age={max_age_hours}h)")
        return len(tasks)


# ============================================================================
# 单例
# ============================================================================

_manager: Optional[TaskLifecycleManager] = None


def get_task_lifecycle_manager() -> TaskLifecycleManager:
    global _manager
    if _manager is None:
        _manager = TaskLifecycleManager()
    return _manager
