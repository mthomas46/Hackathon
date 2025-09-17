"""Distributed Processor - Task processing with worker management."""

import asyncio
import uuid
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum

from services.shared.core.di.services import ILoggerService
from services.shared.core.logging.logger import get_logger


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Worker:
    """Worker node."""

    worker_id: str
    capabilities: List[str] = field(default_factory=list)
    current_tasks: int = 0
    max_tasks: int = 5

    def is_available(self) -> bool:
        """Check if worker can accept tasks."""
        return self.current_tasks < self.max_tasks


@dataclass
class Task:
    """Distributed task."""

    task_id: str
    task_type: str
    payload: Dict[str, Any]
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    assigned_worker: Optional[str] = None


class DistributedProcessor:
    """Distributed task processing coordinator."""

    def __init__(self, logger: Optional[ILoggerService] = None):
        self._logger = logger or get_logger()
        self._workers: Dict[str, Worker] = {}
        self._tasks: Dict[str, Task] = {}

    def register_worker(self, worker_id: str, capabilities: List[str] = None) -> None:
        """Register a worker."""
        worker = Worker(
            worker_id=worker_id,
            capabilities=capabilities or ["generic"]
        )
        self._workers[worker_id] = worker

    def get_available_workers(self) -> List[Worker]:
        """Get available workers."""
        return [w for w in self._workers.values() if w.is_available()]

    async def submit_task(self, task_type: str, payload: Dict[str, Any]) -> str:
        """Submit task for processing."""
        task = Task(
            task_id=str(uuid.uuid4()),
            task_type=task_type,
            payload=payload
        )

        self._tasks[task.task_id] = task

        # Assign to available worker
        available_workers = self.get_available_workers()
        if available_workers:
            worker = available_workers[0]  # Simple selection
            task.assigned_worker = worker.worker_id
            task.status = TaskStatus.RUNNING
            worker.current_tasks += 1

            # Process task
            asyncio.create_task(self._process_task(task, worker))

        return task.task_id

    async def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get task status."""
        task = self._tasks.get(task_id)
        if not task:
            return None

        return {
            "task_id": task.task_id,
            "status": task.status.value,
            "assigned_worker": task.assigned_worker
        }

    async def _process_task(self, task: Task, worker: Worker) -> None:
        """Process a task."""
        try:
            # Simulate processing
            await asyncio.sleep(1.0)

            task.status = TaskStatus.COMPLETED
            worker.current_tasks -= 1

            self._logger.info(f"Completed task {task.task_id}")

        except Exception as e:
            task.status = TaskStatus.FAILED
            worker.current_tasks -= 1

            self._logger.error(f"Task {task.task_id} failed: {e}")


# Global instance
_distributed_processor: Optional[DistributedProcessor] = None


def get_distributed_processor() -> DistributedProcessor:
    """Get global distributed processor."""
    global _distributed_processor
    if _distributed_processor is None:
        _distributed_processor = DistributedProcessor()
    return _distributed_processor


async def submit_distributed_task(task_type: str, payload: Dict[str, Any]) -> str:
    """Submit task for distributed processing."""
    return await get_distributed_processor().submit_task(task_type, payload)