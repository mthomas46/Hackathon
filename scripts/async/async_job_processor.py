#!/usr/bin/env python3
"""
Async Job Processor for Background Task Processing

This script implements a comprehensive background job processing system
for the LLM Documentation Ecosystem. It provides async task execution,
job queuing, scheduling, and monitoring capabilities.

Features:
- Background job processing with Redis/Celery alternatives
- Job queuing and scheduling
- Task prioritization and retry logic
- Job monitoring and status tracking
- Async task execution with proper error handling
"""

import asyncio
import json
import os
import sys
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, asdict
import uuid

import redis.asyncio as redis
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()

class JobStatus(Enum):
    """Job status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRY = "retry"
    CANCELLED = "cancelled"


class JobPriority(Enum):
    """Job priority levels."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Job:
    """Background job data structure."""
    id: str
    name: str
    func_name: str
    args: List[Any]
    kwargs: Dict[str, Any]
    priority: JobPriority
    status: JobStatus
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    retry_count: int
    max_retries: int
    error_message: Optional[str]
    result: Optional[Any]
    timeout_seconds: Optional[int]

    def to_dict(self) -> Dict[str, Any]:
        """Convert job to dictionary for serialization."""
        data = asdict(self)
        # Convert enums to values
        data['priority'] = self.priority.value
        data['status'] = self.status.value
        # Convert datetimes to ISO format
        for field in ['created_at', 'started_at', 'completed_at']:
            if getattr(self, field):
                data[field] = getattr(self, field).isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Job':
        """Create job from dictionary."""
        # Convert values back to enums
        data['priority'] = JobPriority(data['priority'])
        data['status'] = JobStatus(data['status'])
        # Convert ISO strings back to datetimes
        for field in ['created_at', 'started_at', 'completed_at']:
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field])
        return cls(**data)


class AsyncJobProcessor:
    """Async job processor for background task execution."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self.job_queues = {
            JobPriority.LOW: "jobs:low",
            JobPriority.NORMAL: "jobs:normal",
            JobPriority.HIGH: "jobs:high",
            JobPriority.CRITICAL: "jobs:critical"
        }
        self.job_results_key = "job_results"
        self.active_jobs: Dict[str, asyncio.Task] = {}
        self.task_registry: Dict[str, Callable[..., Awaitable[Any]]] = {}

    async def connect(self) -> None:
        """Establish Redis connection."""
        if self.redis is None:
            self.redis = redis.from_url(self.redis_url, decode_responses=False)
            await self.redis.ping()
            console.print("[green]✓ Connected to Redis for job processing[/green]")

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            self.redis = None

    def register_task(self, name: str, func: Callable[..., Awaitable[Any]]) -> None:
        """Register a task function."""
        self.task_registry[name] = func
        console.print(f"[blue]✓ Registered task: {name}[/blue]")

    async def enqueue_job(
        self,
        name: str,
        func_name: str,
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        priority: JobPriority = JobPriority.NORMAL,
        max_retries: int = 3,
        timeout_seconds: Optional[int] = None
    ) -> str:
        """Enqueue a job for background processing."""
        await self.connect()

        job_id = str(uuid.uuid4())
        job = Job(
            id=job_id,
            name=name,
            func_name=func_name,
            args=args or [],
            kwargs=kwargs or {},
            priority=priority,
            status=JobStatus.PENDING,
            created_at=datetime.utcnow(),
            started_at=None,
            completed_at=None,
            retry_count=0,
            max_retries=max_retries,
            error_message=None,
            result=None,
            timeout_seconds=timeout_seconds
        )

        # Store job in Redis
        job_key = f"job:{job_id}"
        await self.redis.set(job_key, json.dumps(job.to_dict()))

        # Add to priority queue
        queue_name = self.job_queues[priority]
        await self.redis.rpush(queue_name, job_id)

        console.print(f"[green]✓ Enqueued job: {name} ({job_id})[/green]")
        return job_id

    async def process_jobs(self, workers: int = 4) -> None:
        """Start processing jobs with multiple workers."""
        console.print(f"[blue]🚀 Starting job processor with {workers} workers...[/blue]")

        # Create worker tasks
        workers_tasks = []
        for i in range(workers):
            task = asyncio.create_task(self._worker_loop(i))
            workers_tasks.append(task)

        # Wait for all workers
        await asyncio.gather(*workers_tasks, return_exceptions=True)

    async def _worker_loop(self, worker_id: int) -> None:
        """Worker loop for processing jobs."""
        console.print(f"[blue]Worker {worker_id} started[/blue]")

        while True:
            try:
                # Get next job from queues (highest priority first)
                job_id = await self._get_next_job()

                if job_id:
                    await self._process_job(job_id)
                else:
                    # No jobs available, wait before checking again
                    await asyncio.sleep(1)

            except Exception as e:
                console.print(f"[red]Worker {worker_id} error: {e}[/red]")
                await asyncio.sleep(5)  # Wait before retrying

    async def _get_next_job(self) -> Optional[str]:
        """Get next job from priority queues."""
        # Check queues in priority order
        for priority in [JobPriority.CRITICAL, JobPriority.HIGH, JobPriority.NORMAL, JobPriority.LOW]:
            queue_name = self.job_queues[priority]
            job_id = await self.redis.lpop(queue_name)
            if job_id:
                return job_id.decode() if isinstance(job_id, bytes) else job_id
        return None

    async def _process_job(self, job_id: str) -> None:
        """Process a single job."""
        job_key = f"job:{job_id}"

        try:
            # Get job data
            job_data = await self.redis.get(job_key)
            if not job_data:
                return

            job_dict = json.loads(job_data.decode() if isinstance(job_data, bytes) else job_data)
            job = Job.from_dict(job_dict)

            # Update job status to running
            job.status = JobStatus.RUNNING
            job.started_at = datetime.utcnow()
            await self.redis.set(job_key, json.dumps(job.to_dict()))

            # Execute the job
            result = await self._execute_job(job)

            # Update job with result
            job.status = JobStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.result = result
            await self.redis.set(job_key, json.dumps(job.to_dict()))

            console.print(f"[green]✓ Completed job: {job.name} ({job_id})[/green]")

        except Exception as e:
            await self._handle_job_error(job_id, str(e))

    async def _execute_job(self, job: Job) -> Any:
        """Execute a job function."""
        if job.func_name not in self.task_registry:
            raise ValueError(f"Task '{job.func_name}' not registered")

        func = self.task_registry[job.func_name]

        # Create task with timeout if specified
        if job.timeout_seconds:
            coro = func(*job.args, **job.kwargs)
            return await asyncio.wait_for(coro, timeout=job.timeout_seconds)
        else:
            return await func(*job.args, **job.kwargs)

    async def _handle_job_error(self, job_id: str, error_message: str) -> None:
        """Handle job execution error."""
        job_key = f"job:{job_id}"

        try:
            job_data = await self.redis.get(job_key)
            if job_data:
                job_dict = json.loads(job_data.decode() if isinstance(job_data, bytes) else job_data)
                job = Job.from_dict(job_dict)

                job.retry_count += 1
                job.error_message = error_message

                if job.retry_count < job.max_retries:
                    # Retry the job
                    job.status = JobStatus.RETRY
                    await self.redis.set(job_key, json.dumps(job.to_dict()))

                    # Re-queue the job
                    queue_name = self.job_queues[job.priority]
                    await self.redis.rpush(queue_name, job_id)

                    console.print(f"[yellow]↻ Retrying job {job_id} (attempt {job.retry_count}/{job.max_retries})[/yellow]")
                else:
                    # Mark as failed
                    job.status = JobStatus.FAILED
                    job.completed_at = datetime.utcnow()
                    await self.redis.set(job_key, json.dumps(job.to_dict()))

                    console.print(f"[red]✗ Failed job: {job.name} ({job_id}) - {error_message}[/red]")

        except Exception as e:
            console.print(f"[red]Error handling job failure: {e}[/red]")

    async def get_job_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job status and result."""
        await self.connect()

        job_key = f"job:{job_id}"
        job_data = await self.redis.get(job_key)

        if job_data:
            job_dict = json.loads(job_data.decode() if isinstance(job_data, bytes) else job_data)
            return job_dict
        return None

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a pending job."""
        await self.connect()

        job_key = f"job:{job_id}"
        job_data = await self.redis.get(job_key)

        if job_data:
            job_dict = json.loads(job_data.decode() if isinstance(job_data, bytes) else job_data)
            job = Job.from_dict(job_dict)

            if job.status == JobStatus.PENDING:
                job.status = JobStatus.CANCELLED
                job.completed_at = datetime.utcnow()
                await self.redis.set(job_key, json.dumps(job.to_dict()))
                return True

        return False

    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics."""
        await self.connect()

        stats = {}
        total_pending = 0

        for priority, queue_name in self.job_queues.items():
            queue_length = await self.redis.llen(queue_name)
            stats[priority.name.lower()] = queue_length
            total_pending += queue_length

        stats["total_pending"] = total_pending
        stats["active_workers"] = len(self.active_jobs)
        stats["registered_tasks"] = len(self.task_registry)

        return stats


# Example task functions
async def example_long_running_task(duration: int, message: str) -> str:
    """Example long-running task."""
    await asyncio.sleep(duration)
    return f"Task completed after {duration}s: {message}"


async def example_data_processing_task(data: List[Dict], operation: str) -> Dict[str, Any]:
    """Example data processing task."""
    await asyncio.sleep(1)  # Simulate processing time

    if operation == "count":
        return {"count": len(data)}
    elif operation == "sum":
        total = sum(item.get("value", 0) for item in data)
        return {"sum": total}
    else:
        return {"error": f"Unknown operation: {operation}"}


async def setup_async_job_processor() -> AsyncJobProcessor:
    """Set up and configure the async job processor."""
    processor = AsyncJobProcessor()

    # Register example tasks
    processor.register_task("long_running", example_long_running_task)
    processor.register_task("data_processing", example_data_processing_task)

    console.print("[green]✓ Async job processor configured with example tasks[/green]")
    return processor


async def main():
    """Main function to demonstrate async job processing."""
    console.print("[bold blue]🚀 Async Job Processor Demonstration[/bold blue]")
    console.print()

    processor = await setup_async_job_processor()

    try:
        # Enqueue some example jobs
        job1_id = await processor.enqueue_job(
            "Example Long Running Task",
            "long_running",
            args=[3],
            kwargs={"message": "Hello from async job!"},
            priority=JobPriority.HIGH
        )

        job2_id = await processor.enqueue_job(
            "Example Data Processing",
            "data_processing",
            args=[[{"value": 10}, {"value": 20}, {"value": 30}]],
            kwargs={"operation": "sum"},
            priority=JobPriority.NORMAL
        )

        console.print(f"[green]✓ Enqueued jobs: {job1_id}, {job2_id}[/green]")

        # Start processing in background
        processing_task = asyncio.create_task(processor.process_jobs(workers=2))

        # Wait a bit then check status
        await asyncio.sleep(2)

        # Check job statuses
        for job_id in [job1_id, job2_id]:
            status = await processor.get_job_status(job_id)
            if status:
                console.print(f"[blue]Job {job_id}: {status['status']}[/blue]")

        # Wait for jobs to complete
        await asyncio.sleep(4)

        # Check final results
        for job_id in [job1_id, job2_id]:
            status = await processor.get_job_status(job_id)
            if status:
                console.print(f"[green]Final result for {job_id}: {status}[/green]")

        # Get queue stats
        stats = await processor.get_queue_stats()
        console.print(f"[blue]Queue stats: {stats}[/blue]")

        # Stop processing
        processing_task.cancel()

    finally:
        await processor.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
