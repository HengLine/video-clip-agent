"""
@FileName: function_calls.py
@Description: Function Call接口 - 供其他Python智能体调用
@Author: HiPeng
@Github: https://github.com/neopen/story-shot-agent
@Time: 2026/3/23 18:39
"""

import asyncio
import threading
import uuid
from contextvars import ContextVar
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Optional, List, Any, Callable

from neoclip.logger import info, error
from neoclip.utils.log_utils import print_log_exception
from neoclip.state.models import IntentType

# ============================================================================
# V0.1 类型 stub — 后续版本实现完整逻辑
# ============================================================================


class VideoStyle(str, Enum):
    REALISTIC = "realistic"
    ANIME = "anime"
    CARTOON = "cartoon"
    CINEMATIC = "cinematic"


class ShotLanguage(str, Enum):
    ZH = "zh"
    EN = "en"


class TaskStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"
    NOT_FOUND = "not_found"
    UNKNOWN = "unknown"

    def is_completed(self) -> bool:
        return self in (TaskStatus.SUCCESS, TaskStatus.FAILED, TaskStatus.CANCELLED, TaskStatus.TIMEOUT)


class TaskPriority(str, Enum):
    NORMAL = "normal"
    HIGH = "high"
    LOW = "low"


DEFAULT_TASK_TTL_SECONDS = 3600

script_id_ctx: ContextVar = ContextVar("script_id", default=None)


def set_language(lang):
    pass


@dataclass
class ShotConfig:
    pass


@dataclass
class TaskResponse:
    task_id: str = ""
    success: bool = False
    status: TaskStatus = TaskStatus.UNKNOWN
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time_ms: Optional[int] = None
    created_at: Any = None
    completed_at: Any = None

    def to_dict(self) -> Dict[str, Any]:
        return {"task_id": self.task_id, "success": self.success, "status": self.status.value}


@dataclass
class ProcessingStatus:
    task_id: str = ""
    status: TaskStatus = TaskStatus.UNKNOWN
    stage: str = ""
    progress: int = 0
    created_at: Any = None
    updated_at: Any = None
    error_message: Optional[str] = None
    current_stage: Optional[str] = None
    stage_name: Optional[str] = None
    stages_progress: Optional[Dict] = None


@dataclass
class TaskStage:
    code: str = ""
    name: str = ""

    @classmethod
    def from_code(cls, code: str):
        return cls(code=code, name=code)


@dataclass
class BatchResponse:
    batch_id: str = ""
    total_tasks: int = 0
    task_ids: list = field(default_factory=list)
    created_at: Any = None


class TaskFactory:
    """任务工厂 — 委托 TaskLifecycleManager + CentralHub"""

    def __init__(self):
        from neoclip.api.task_backend import TaskLifecycleManager, get_task_lifecycle_manager
        from neoclip.hub.hub_core import get_hub
        self.task_manager = get_task_lifecycle_manager()
        self._hub = get_hub()
        self._max_concurrent = 10

    def submit(self, **kwargs):
        script = kwargs.get("script", "")
        script_id = kwargs.get("script_id")
        language = kwargs.get("language", "zh")
        callback = kwargs.get("callback")

        session_id = script_id or str(uuid.uuid4())
        intent_type = IntentType.PLAN_CREATE.value

        sid, task_id = self.task_manager.submit(
            script=script,
            script_id=script_id,
            session_id=session_id,
            intent_type=intent_type,
            metadata={"language": str(language) if hasattr(language, 'value') else language},
        )

        # 通过 Hub 处理
        hub_result = self._hub.process(user_input=script, session_id=session_id)
        self.task_manager.store.update(task_id, hub_result=hub_result)

        # V0.1: 如果有 callback，立即以 success 回调
        if callback:
            try:
                tr = TaskResponse(task_id=task_id, success=True, status=TaskStatus.SUCCESS,
                                  created_at=datetime.now(timezone.utc), completed_at=datetime.now(timezone.utc))
                callback(tr)
            except Exception as e:
                error(f"TaskFactory callback error: {e}")

        return (sid, task_id)

    def get_status(self, task_id):
        raw = self.task_manager.get_status(task_id)
        if raw is None:
            return None
        return ProcessingStatus(
            task_id=raw["task_id"],
            status=TaskStatus(raw.get("status", "unknown")),
            stage=raw.get("stage", ""),
            progress=raw.get("progress", 0),
            created_at=raw.get("created_at"),
            updated_at=raw.get("updated_at"),
            error_message=None,
        )

    def get_result(self, task_id):
        raw = self.task_manager.get_result(task_id)
        if raw is None:
            return None
        status_str = raw.get("status", "unknown")
        try:
            status = TaskStatus(status_str)
        except ValueError:
            status = TaskStatus.UNKNOWN
        return TaskResponse(
            task_id=raw["task_id"],
            success=raw.get("success", False),
            status=status,
            data=raw.get("data"),
            error=raw.get("error"),
            processing_time_ms=raw.get("processing_time_ms"),
            created_at=raw.get("created_at"),
            completed_at=raw.get("completed_at"),
        )

    def cancel(self, task_id):
        return self.task_manager.cancel(task_id)

    def wait_for_result(self, task_id, timeout):
        import time
        deadline = time.time() + timeout
        while time.time() < deadline:
            result = self.get_result(task_id)
            if result and result.status.is_completed():
                return result
            time.sleep(0.5)
        return self.get_result(task_id)

    async def wait_for_result_async(self, task_id, timeout, poll_interval=0.5):
        import asyncio
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            result = self.get_result(task_id)
            if result and result.status.is_completed():
                return result
            await asyncio.sleep(poll_interval)
        return self.get_result(task_id)

    def batch(self, **kwargs):
        scripts = kwargs.get("scripts", [])
        config = kwargs.get("config")
        language = kwargs.get("language", "zh")
        timeout = kwargs.get("timeout", 600)

        batch_result = self.task_manager.batch_submit(
            scripts=scripts, config=config, language=language
        )
        results = []
        import time
        deadline = time.time() + timeout
        for tid in batch_result["task_ids"]:
            while time.time() < deadline:
                r = self.get_result(tid)
                if r and r.status.is_completed():
                    results.append(r)
                    break
                time.sleep(0.5)
            else:
                results.append(self.get_result(tid))
        return results

    async def batch_async(self, **kwargs):
        import asyncio
        scripts = kwargs.get("scripts", [])
        config = kwargs.get("config")
        language = kwargs.get("language", "zh")
        max_concurrent = kwargs.get("max_concurrent", 3)

        batch_result = self.task_manager.batch_submit(
            scripts=scripts, config=config, language=language
        )
        results = []
        for tid in batch_result["task_ids"]:
            r = await self.wait_for_result_async(tid, timeout=600)
            results.append(r)
        return results

    def batch_submit(self, **kwargs):
        scripts = kwargs.get("scripts", [])
        config = kwargs.get("config")
        language = kwargs.get("language", "zh")
        result = self.task_manager.batch_submit(scripts=scripts, config=config, language=language)
        return BatchResponse(
            batch_id=result["batch_id"],
            total_tasks=result["total_tasks"],
            task_ids=result["task_ids"],
            created_at=result["created_at"],
        )

    def batch_get_status(self, batch_id):
        statuses = self.task_manager.batch_get_status(batch_id)
        return [
            ProcessingStatus(
                task_id=s.get("task_id", ""),
                status=TaskStatus(s.get("status", "unknown")),
                stage=s.get("stage", ""),
                progress=s.get("progress", 0),
                created_at=s.get("created_at"),
                updated_at=s.get("updated_at"),
            )
            for s in statuses
        ]

    def batch_get_results(self, batch_id):
        return self.task_manager.batch_get_results(batch_id)

    def get_queue_status(self):
        return self.task_manager.get_queue_status()

    def get_stats(self):
        return self.task_manager.get_stats()

    def set_max_concurrent(self, n):
        self._max_concurrent = n
        info(f"TaskFactory max_concurrent set to {n}")

    def recover_pending_tasks(self, **kwargs):
        max_age = kwargs.get("max_age_hours", 2)
        return self.task_manager.recover_pending_tasks(max_age_hours=max_age)

    def get_pending_tasks(self, **kwargs):
        max_age = kwargs.get("max_age_hours", 2)
        return self.task_manager.get_pending_tasks(max_age_hours=max_age)

    async def shutdown(self, wait_for_completion=True, timeout=30):
        info("TaskFactory shutdown")
        return True

    def submit_and_wait(self, **kwargs):
        script = kwargs.get("script", "")
        script_id = kwargs.get("script_id")
        language = kwargs.get("language", "zh")
        timeout = kwargs.get("timeout", 300)

        sid, task_id = self.submit(
            script=script,
            script_id=script_id,
            language=language,
        )
        return self.wait_for_result(task_id, timeout)


_factory = None


def create_task_factory(**kwargs) -> TaskFactory:
    return TaskFactory()


def get_task_factory() -> TaskFactory:
    global _factory
    if _factory is None:
        _factory = TaskFactory()
    return _factory


@dataclass
class PenshotResult:
    """Penshot 执行结果"""
    task_id: str
    success: bool
    status: TaskStatus  # pending, processing, completed, failed, timeout, not_found
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    processing_time_ms: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "success": self.success,
            "status": self.status,
            "data": self.data,
            "error": self.error,
            "processing_time_ms": self.processing_time_ms
        }


class PenshotFunction:
    """
    Penshot 智能体功能调用接口

    使用 TaskFactory 统一管理任务队列、并发控制和任务生命周期
    """

    def __init__(
            self,
            config: Optional[ShotConfig] = None,
            language: ShotLanguage = ShotLanguage.ZH,
            max_concurrent: int = 10,
            queue_size: int = 1000
    ):
        """
        初始化 Penshot 功能接口

        Args:
            config: 系统配置
            language: 输出语言
            max_concurrent: 最大并发数（默认10）
            queue_size: 队列大小（默认1000）
        """
        self.config = config or ShotConfig()
        self.language = language

        # 使用 TaskFactory 替代原始的 TaskManager + TaskProcessor
        self.task_factory: TaskFactory = create_task_factory(
            max_concurrent=max_concurrent,
            queue_size=queue_size,
            default_config=config,
            default_language=language,
            task_ttl_seconds=DEFAULT_TASK_TTL_SECONDS
        )

        # 保持兼容性
        self.task_manager = self.task_factory.task_manager

        # 回调存储
        self._callbacks: Dict[str, Callable] = {}

        # 后台任务事件循环
        self._background_loop: Optional[asyncio.AbstractEventLoop] = None
        self._background_thread: Optional[threading.Thread] = None
        self._start_background_loop()

        info(f"PenshotFunction 初始化完成，最大并发: {max_concurrent}")

    def _start_background_loop(self):
        """启动后台事件循环"""

        def run_loop():
            self._background_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self._background_loop)
            self._background_loop.run_forever()

        self._background_thread = threading.Thread(target=run_loop, daemon=True)
        self._background_thread.start()

        # 等待循环启动
        while self._background_loop is None:
            pass

    def _run_async_in_background(self, coro):
        """在后台事件循环中运行协程"""
        if self._background_loop is None:
            raise RuntimeError("后台事件循环未启动")
        return asyncio.run_coroutine_threadsafe(coro, self._background_loop)

    # ==================== 核心方法 ====================
    def breakdown_script(
            self,
            script_text: str,
            script_id: Optional[str] = None,
            style: Optional[VideoStyle] = None,
            language: Optional[ShotLanguage] = None,
            wait_timeout: float = 300.0,
            priority: TaskPriority = TaskPriority.NORMAL
    ) -> PenshotResult:
        """
        同步执行剧本分镜拆分（等待完成）

        Args:
            script_text: 剧本文本
            script_id: 剧本ID：如果是属于同一个剧本的不同请求，可以使用相同的ID，否则就是不同（可选）
            language: 输出语言
            style: 视频风格
            wait_timeout: 等待超时时间（秒）
            priority: 任务优先级

        Returns:
            PenshotResult: 执行结果
        """
        task_id = self.breakdown_script_async(
            script_text=script_text,
            script_id=script_id,
            style=style,
            language=language,
            priority=priority
        )
        return self.wait_for_result(task_id, timeout=wait_timeout)

    def breakdown_script_async(
            self,
            script_text: str,
            script_id: Optional[str] = None,
            style: Optional[VideoStyle] = None,
            language: Optional[ShotLanguage] = None,
            callback: Optional[Callable] = None,
            priority: TaskPriority = TaskPriority.NORMAL
    ) -> str:
        """
        异步执行剧本分镜拆分（立即返回 task_id）

        Args:
            script_text: 剧本文本
            style: 视频风格
            script_id: 剧本ID：如果是属于同一个剧本的不同请求，可以使用相同的ID，否则就是不同（可选）
            language: 输出语言
            callback: 任务完成回调函数
            priority: 任务优先级

        Returns:
            str: 任务ID
        """
        # 生成任务ID
        lang = language or self.language

        # 设置语言
        set_language(lang)

        # 内部回调：TaskFactory 会在任务完成时把 TaskResponse 传入
        def _internal_callback(task_response: TaskResponse):
            try:
                # 先让 PenshotFunction 自身处理完成事件（日志/内部清理/兼容行为）
                try:
                    self._on_task_complete(task_response.task_id, task_response)
                except Exception as _e:
                    # _on_task_complete 内部已经有日志与异常打印，但这里再捕获以防止阻断用户回调
                    error(f"内部任务完成处理失败: {task_response.task_id}, 错误: {_e}")
                    print_log_exception()

                # 如果有用户回调，直接调用（使用 TaskResponse 中的 task_id），避免竞态和重复调用
                if callback:
                    try:
                        user_result = PenshotResult(
                            task_id=task_response.task_id,
                            success=task_response.success,
                            status=task_response.status,
                            data=task_response.data,
                            error=task_response.error,
                            processing_time_ms=task_response.processing_time_ms
                        )
                        callback(user_result)
                    except Exception as e:
                        error(f"用户回调执行失败: {task_response.task_id}, 错误: {e}")
                        print_log_exception()

            except Exception as e:
                # 最外层保护，确保任何异常不会破坏 TaskFactory 的流程
                error(f"任务回调处理异常: {str(e)}")
                print_log_exception()

        # 使用 TaskFactory 提交任务，TaskFactory 会在任务完成时调用上面的 _internal_callback
        script_id2, task_id = self.task_factory.submit(
            script_id=script_id,
            script=script_text,
            style=style,
            config=self.config,
            language=lang,
            priority=priority,
            # callback=lambda r: self._on_task_complete(task_id, r)
            callback=_internal_callback
        )

        return task_id

    def _on_task_complete(self, task_id: str, task_response: TaskResponse):
        """任务完成回调"""
        # task_response 已经是 TaskResponse，直接使用
        result = PenshotResult(
            task_id=task_response.task_id,
            success=task_response.success,
            status=task_response.status,
            data=task_response.data,  # 直接是业务数据
            error=task_response.error,
            processing_time_ms=task_response.processing_time_ms
        )

        # 触发用户回调
        if task_id in self._callbacks:
            callback = self._callbacks[task_id]
            try:
                callback(result)
            except Exception as e:
                error(f"回调失败: {task_id}, 错误: {str(e)}")
                print_log_exception()
            finally:
                del self._callbacks[task_id]

    # ==================== 状态查询方法 ====================

    def get_task_status(self, task_id: str) -> Optional[Dict]:
        """
        获取任务状态（增强版）

        返回包含详细进度信息的字典
        """
        status = self.task_factory.get_status(task_id)
        if not status:
            return None

        # 构建详细进度信息
        result = {
            "task_id": status.task_id,
            "status": status.status,
            "stage": status.stage,
            "stage_name": status.stage_name if hasattr(status, 'stage_name') else status.stage,
            "progress": status.progress,
            "created_at": status.created_at,
            "updated_at": status.updated_at,
            "error": status.error_message
        }

        # 添加详细阶段进度
        if hasattr(status, 'current_stage') and status.current_stage:
            result["current_stage"] = status.current_stage

        if hasattr(status, 'stages_progress') and status.stages_progress:
            result["stages_progress"] = status.stages_progress

        return result

    def get_task_result(self, task_id: str) -> Optional[PenshotResult]:
        """
        获取任务结果

        Args:
            task_id: 任务ID

        Returns:
            PenshotResult: 任务结果
        """
        result = self.task_factory.get_result(task_id)
        if not result:
            return None

        return PenshotResult(
            task_id=result.task_id,
            success=result.success,
            status=result.status,
            data=result.data,
            error=result.error,
            processing_time_ms=result.processing_time_ms
        )

    def wait_for_result(
            self,
            task_id: str,
            timeout: float = 300.0
    ) -> Optional[PenshotResult]:
        """
        同步等待任务完成

        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）

        Returns:
            PenshotResult: 任务结果
        """
        task_response = self.task_factory.wait_for_result(
            task_id=task_id,
            timeout=timeout,
        )

        if not task_response:
            return None

        # task_response 已经是 TaskResponse，直接使用
        return PenshotResult(
            task_id=task_response.task_id,
            success=task_response.success,
            status=task_response.status,
            data=task_response.data,
            error=task_response.error,
            processing_time_ms=task_response.processing_time_ms
        )

    async def wait_for_result_async(
            self,
            task_id: str,
            timeout: float = 300.0,
            poll_interval: float = 0.5
    ) -> PenshotResult:
        """
        异步等待任务完成

        Args:
            task_id: 任务ID
            timeout: 超时时间（秒）
            poll_interval: 轮询间隔（秒）

        Returns:
            PenshotResult: 任务结果
        """
        result = await self.task_factory.wait_for_result_async(
            task_id=task_id,
            timeout=timeout,
            poll_interval=poll_interval
        )

        return PenshotResult(
            task_id=result.task_id,
            success=result.success,
            status=result.status,
            data=result.data,
            error=result.error,
            processing_time_ms=result.processing_time_ms
        )

    # ==================== 任务管理方法 ====================

    def cancel_task(self, task_id: str) -> bool:
        """
        取消任务

        Args:
            task_id: 任务ID

        Returns:
            bool: 是否成功取消
        """
        return self.task_factory.cancel(task_id)

    def batch_breakdown(
            self,
            scripts: List[str],
            language: Optional[ShotLanguage] = None,
            wait_timeout: float = 600.0,
            priority: TaskPriority = TaskPriority.NORMAL
    ) -> List[PenshotResult]:
        """
        批量处理多个剧本（同步，等待全部完成）
        """
        results = self.task_factory.batch(
            scripts=scripts,
            config=self.config,
            language=language.value if language else self.language.value,
            priority=priority,
            timeout=wait_timeout
        )

        # 每个 result 已经是 TaskResponse
        return [
            PenshotResult(
                task_id=r.task_id,
                success=r.success,
                status=r.status,
                data=r.data,  # 直接是业务数据
                error=r.error,
                processing_time_ms=r.processing_time_ms
            )
            for r in results
        ]

    async def batch_breakdown_async(
            self,
            scripts: List[str],
            language: Optional[ShotLanguage] = None,
            max_concurrent: int = 3,
            priority: TaskPriority = TaskPriority.NORMAL
    ) -> List[PenshotResult]:
        """
        批量处理多个剧本（异步，支持并发控制）
        """
        results = await self.task_factory.batch_async(
            scripts=scripts,
            config=self.config,
            language=language.value if language else self.language.value,
            priority=priority,
            max_concurrent=max_concurrent
        )

        return [
            PenshotResult(
                task_id=r.task_id,
                success=r.success,
                status=r.status,
                data=r.data,  # 直接是业务数据
                error=r.error,
                processing_time_ms=r.processing_time_ms
            )
            for r in results
        ]

    # ==================== 队列监控方法 ====================

    def get_queue_status(self) -> Dict[str, Any]:
        """
        获取队列状态

        Returns:
            Dict: 队列状态信息
        """
        return self.task_factory.get_queue_status()

    def get_stats(self) -> Dict[str, Any]:
        """
        获取统计信息

        Returns:
            Dict: 统计信息
        """
        return self.task_factory.get_stats()

    def set_max_concurrent(self, max_concurrent: int):
        """
        动态设置最大并发数

        Args:
            max_concurrent: 最大并发数
        """
        self.task_factory.set_max_concurrent(max_concurrent)
        info(f"最大并发数已调整为: {max_concurrent}")

    # ==================== 生命周期管理 ====================

    def shutdown(self):
        """
        关闭 Penshot 功能接口

        等待所有任务完成后关闭
        """
        info("正在关闭 PenshotFunction...")
        # 使用异步方式关闭
        future = self._run_async_in_background(
            self.task_factory.shutdown(wait_for_completion=True, timeout=30)
        )
        try:
            future.result(timeout=35)
        except Exception as e:
            error(f"关闭时发生错误: {str(e)}")

        # 停止后台事件循环
        if self._background_loop:
            self._background_loop.call_soon_threadsafe(self._background_loop.stop)
        if self._background_thread:
            self._background_thread.join(timeout=5)

        info("PenshotFunction 已关闭")


# ==================== 便捷函数 ====================

def create_penshot_agent(
        config: Optional[ShotConfig] = None,
        language: ShotLanguage = ShotLanguage.ZH,
        max_concurrent: int = 10,
        queue_size: int = 1000
) -> PenshotFunction:
    """
    创建 Penshot 智能体实例

    Args:
        config: 系统配置
        language: 输出语言
        max_concurrent: 最大并发数
        queue_size: 队列大小

    Returns:
        PenshotFunction: 智能体实例
    """
    return PenshotFunction(
        config=config,
        language=language,
        max_concurrent=max_concurrent,
        queue_size=queue_size
    )
