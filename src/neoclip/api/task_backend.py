"""
@FileName: task_backend.py
@Description: 任务生命周期管理 — neotask.TaskPool 后端
    将原先「内存假异步」实现替换为自研 neotask 组件：
    - 真正的异步 worker 池执行中枢处理（hub.process）
    - 内存 / SQLite / Redis 存储后端可切换
    - 对外保持原有方法契约，由 api/v1/task 路由消费
@Author: HiPeng
@Time: 2026/08
"""
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from neotask.api.task_pool import TaskPool, TaskPoolConfig

from neoclip.logger import debug, info, warning
from neoclip.state.models import TaskLifecycleStage


# ============================================================================
# 状态映射 — neotask 状态 → NeoClip 状态/阶段
# ============================================================================

_STATUS_MAP = {
    "pending": "pending",
    "scheduled": "pending",
    "running": "processing",
    "success": "success",
    "failed": "failed",
    "cancelled": "cancelled",
}

_STAGE_MAP = {
    "pending": TaskLifecycleStage.PENDING.value,
    "scheduled": TaskLifecycleStage.QUEUED.value,
    "running": TaskLifecycleStage.ANALYZING.value,
    "success": TaskLifecycleStage.COMPLETED.value,
    "failed": TaskLifecycleStage.FAILED.value,
    "cancelled": TaskLifecycleStage.CANCELLED.value,
}

_NON_TERMINAL = ("pending", "scheduled", "running")


def _parse_json(raw: Any) -> Any:
    """把 neotask 序列化后的 JSON 字符串还原为对象。"""
    if not raw:
        return {}
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return {}


# ============================================================================
# TaskLifecycleManager — neotask 后端
# ============================================================================


class TaskLifecycleManager:
    """任务生命周期管理器 — 封装 neotask.TaskPool，保持原方法契约。

    V0.2: 默认内存存储；可通过 storage_type="sqlite" / "redis" 切换。
    """

    def __init__(
            self,
            storage_type: str = "memory",
            sqlite_path: Optional[str] = None,
            redis_url: Optional[str] = None,
            worker_concurrency: int = 10,
    ):
        from neoclip.hub.hub_core import get_hub  # 延迟导入，避免循环依赖

        self._hub = get_hub()

        config = TaskPoolConfig(
            storage_type=storage_type,
            sqlite_path=sqlite_path or "neotask.db",
            redis_url=redis_url,
            worker_concurrency=worker_concurrency,
            # 混剪任务失败不自动重试（重试策略由上层决定）
            max_retries=0,
            retry_delay=0,
        )
        self.pool = TaskPool(executor=self._execute, config=config)

        # batch_id → task_ids 侧索引（batch 分组查询用）
        self._batch_index: Dict[str, List[str]] = {}
        # task_id → 完成回调
        self._callbacks: Dict[str, Any] = {}

        # 订阅任务完成事件，驱动回调
        self.pool.on_completed(self._on_completed)

    # ── neotask executor：真正执行中枢处理 ──

    def _execute(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """neotask worker 调用的执行函数。返回 JSON 可序列化结果。"""
        script = data.get("script", "")
        session_id = data.get("session_id") or data.get("script_id") or str(uuid.uuid4())
        resp = self._hub.process(user_input=script, session_id=session_id)
        return {
            "success": resp.success,
            "intent": resp.intent.value if resp.intent else None,
            "message": resp.message,
            "data": resp.data,
            "needs_confirmation": resp.needs_confirmation,
            "confirmation_message": resp.confirmation_message,
        }

    def _on_completed(self, event: Any) -> None:
        """任务完成事件回调（由 neotask 事件总线触发，同步函数会被包装）。"""
        task_id = getattr(event, "task_id", None)
        callback = self._callbacks.pop(task_id, None) if task_id else None
        if callback is None:
            return
        result = getattr(event, "data", None) or {}
        if isinstance(result, dict):
            success = result.get("success", True)
            data = result.get("data")
        else:
            success, data = True, result
        # 这里回调签名由上层负责封装，见 api/v1/task
        try:
            callback(task_id, success, data)
        except Exception as e:  # noqa: BLE001
            warning(f"TaskLifecycleManager callback error for {task_id}: {e}")

    def register_callback(self, task_id: str, callback: Any) -> None:
        """注册任务完成回调，签名 callback(task_id, success, data)。"""
        self._callbacks[task_id] = callback

    # ── 内部工具 ──

    def _full(self, task_id: str) -> Optional[Dict[str, Any]]:
        """获取完整任务信息：{raw, data, result}。"""
        raw = self.pool.get_task(task_id)
        if not raw:
            return None
        return {
            "raw": raw,
            "data": _parse_json(raw.get("data")),
            "result": _parse_json(raw.get("result")),
        }

    @staticmethod
    def _elapsed_ms(created_at: Any, completed_at: Any) -> Optional[int]:
        try:
            start = datetime.fromisoformat(created_at)
            end = datetime.fromisoformat(completed_at)
            return int((end - start).total_seconds() * 1000)
        except (ValueError, TypeError):
            return None

    # ── 提交 ──

    def submit(
            self,
            script: str = "",
            script_id: Optional[str] = None,
            session_id: Optional[str] = None,
            intent_type: Optional[str] = None,
            batch_id: Optional[str] = None,
            metadata: Optional[Dict] = None,
    ) -> Tuple[str, str]:
        """提交任务，返回 (script_id, task_id)。"""
        sid = script_id or str(uuid.uuid4())
        data = {
            "script": script,
            "script_id": sid,
            "session_id": session_id or sid,
            "intent_type": intent_type,
            "batch_id": batch_id,
        }
        if metadata:
            data.update(metadata)

        task_id = self.pool.submit(data)
        if batch_id:
            self._batch_index.setdefault(batch_id, []).append(task_id)
        info(f"Task submitted: {task_id[:8]} [intent={intent_type}, session={sid[:8]}]")
        return sid, task_id

    # ── 状态查询 ──

    def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        full = self._full(task_id)
        if full is None:
            return None
        raw, data = full["raw"], full["data"]
        status = raw.get("status", "pending")
        return {
            "task_id": task_id,
            "script_id": data.get("script_id"),
            "status": _STATUS_MAP.get(status, status),
            "stage": _STAGE_MAP.get(status, TaskLifecycleStage.PENDING.value),
            "progress": int((raw.get("progress") or 0) * 100),
            "created_at": raw.get("created_at"),
            "updated_at": raw.get("completed_at") or raw.get("started_at") or raw.get("created_at"),
            "completed_at": raw.get("completed_at"),
        }

    def get_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        full = self._full(task_id)
        if full is None:
            return None
        raw, data, result = full["raw"], full["data"], full["result"]
        status = raw.get("status", "pending")
        return {
            "task_id": task_id,
            "script_id": data.get("script_id"),
            "session_id": data.get("session_id"),
            "status": _STATUS_MAP.get(status, status),
            "stage": _STAGE_MAP.get(status, TaskLifecycleStage.PENDING.value),
            "progress": int((raw.get("progress") or 0) * 100),
            "intent_type": data.get("intent_type"),
            "hub_result": {"result": result},
            "result": result,
            "created_at": raw.get("created_at"),
            "updated_at": raw.get("completed_at") or raw.get("started_at") or raw.get("created_at"),
            "completed_at": raw.get("completed_at"),
            "error_message": raw.get("error") or None,
            "error": raw.get("error") or None,
            "metadata": data,
            "batch_id": data.get("batch_id"),
        }

    def get_tasks_by_batch(self, batch_id: str) -> List[Dict[str, Any]]:
        return [
            task
            for tid in self._batch_index.get(batch_id, [])
            if (task := self.get_task(tid)) is not None
        ]

    # ── 结果查询 ──

    def get_result(self, task_id: str) -> Optional[Dict[str, Any]]:
        full = self._full(task_id)
        if full is None:
            return None
        raw, data, result = full["raw"], full["data"], full["result"]
        status = raw.get("status", "pending")
        return {
            "task_id": task_id,
            "script_id": data.get("script_id"),
            "success": status == "success",
            "status": _STATUS_MAP.get(status, status),
            "data": result.get("data"),
            "error": raw.get("error") or None,
            "processing_time_ms": self._elapsed_ms(raw.get("created_at"), raw.get("completed_at")),
            "created_at": raw.get("created_at"),
            "completed_at": raw.get("completed_at"),
        }

    # ── 取消 ──

    def cancel(self, task_id: str) -> bool:
        return self.pool.cancel(task_id)

    # ── 批量 ──

    def batch_submit(
            self,
            scripts: List[str],
            config: Optional[Dict] = None,
            language: str = "zh",
            session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        batch_id = str(uuid.uuid4())
        task_ids: List[str] = []
        for script in scripts:
            _, tid = self.submit(
                script=script,
                script_id=str(uuid.uuid4()),
                session_id=session_id or str(uuid.uuid4()),
                batch_id=batch_id,
                metadata={"config": config, "language": language},
            )
            task_ids.append(tid)
        return {
            "batch_id": batch_id,
            "total_tasks": len(task_ids),
            "task_ids": task_ids,
            "created_at": datetime.now(timezone.utc),
        }

    def batch_get_status(self, batch_id: str) -> List[Dict[str, Any]]:
        return [
            status
            for tid in self._batch_index.get(batch_id, [])
            if (status := self.get_status(tid)) is not None
        ]

    def batch_get_results(self, batch_id: str) -> List[Dict[str, Any]]:
        return [
            result
            for tid in self._batch_index.get(batch_id, [])
            if (result := self.get_result(tid)) is not None
        ]

    # ── 队列 & 统计 ──

    def get_queue_status(self) -> Dict[str, Any]:
        stats = self.pool.get_stats()
        return {
            "queue_length": stats.get("pending", 0) + stats.get("running", 0),
            "processing": stats.get("running", 0),
            "total_pending": stats.get("pending", 0),
            "stats": self.get_stats(),
        }

    def get_stats(self) -> Dict[str, Any]:
        s = self.pool.get_stats()
        completed = s.get("completed", 0)
        failed = s.get("failed", 0)
        cancelled = s.get("cancelled", 0)
        total = s.get("total", 0)
        return {
            "total_tasks": total,
            "total_submitted": total,
            "total_completed": completed,
            "total_failed": failed,
            "total_cancelled": cancelled,
            "by_status": {
                "pending": s.get("pending", 0),
                "processing": s.get("running", 0),
                "success": completed,
                "failed": failed,
                "cancelled": cancelled,
            },
            "by_stage": {},
        }

    def get_pending_tasks(self, max_age_hours: float = 2) -> List[Dict[str, Any]]:
        tasks = self.pool.list_tasks(limit=10000)
        now = datetime.now(timezone.utc)
        out: List[Dict[str, Any]] = []
        for t in tasks:
            if t.get("status") not in _NON_TERMINAL:
                continue
            created = t.get("created_at")
            if created:
                try:
                    age_h = (now - datetime.fromisoformat(created)).total_seconds() / 3600
                    if age_h > max_age_hours:
                        continue
                except (ValueError, TypeError):
                    pass
            out.append(self.get_task(t.get("task_id")) or t)
        return out

    def recover_pending_tasks(self, max_age_hours: float = 2) -> int:
        """恢复未完成任务（V0.1: 仅计数，实际重入队由 neotask reclaimer / V0.3 处理）。"""
        pending = self.get_pending_tasks(max_age_hours=max_age_hours)
        info(f"Task recovery: found {len(pending)} pending tasks (max_age={max_age_hours}h)")
        return len(pending)

    # ── 生命周期 ──

    def shutdown(self, graceful: bool = True, timeout: float = 30) -> None:
        self.pool.shutdown(graceful=graceful, timeout=timeout)


# ============================================================================
# 单例
# ============================================================================

_manager: Optional[TaskLifecycleManager] = None


def get_task_lifecycle_manager() -> TaskLifecycleManager:
    global _manager
    if _manager is None:
        _manager = TaskLifecycleManager()
    return _manager