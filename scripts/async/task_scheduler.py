#!/usr/bin/env python3
"""
Task Scheduler for Recurring and Scheduled Jobs

This script implements a comprehensive task scheduling system for the LLM
Documentation Ecosystem. It provides cron-like scheduling, recurring tasks,
and time-based job execution.

Features:
- Cron-style job scheduling
- Recurring task management
- Time-based job execution
- Schedule persistence and recovery
- Job dependency management
- Schedule monitoring and metrics
"""

import asyncio
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Callable, Awaitable
from dataclasses import dataclass, asdict
import uuid
import croniter
import pytz

import redis.asyncio as redis
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

class ScheduleType(Enum):
    """Schedule type enumeration."""
    CRON = "cron"
    INTERVAL = "interval"
    ONE_TIME = "one_time"


@dataclass
class ScheduledTask:
    """Scheduled task data structure."""
    id: str
    name: str
    func_name: str
    args: List[Any]
    kwargs: Dict[str, Any]
    schedule_type: ScheduleType
    schedule_config: Dict[str, Any]  # cron expression, interval, or datetime
    enabled: bool
    created_at: datetime
    last_run: Optional[datetime]
    next_run: Optional[datetime]
    run_count: int
    max_runs: Optional[int]
    timezone: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary."""
        data = asdict(self)
        data['schedule_type'] = self.schedule_type.value
        for field in ['created_at', 'last_run', 'next_run']:
            if getattr(self, field):
                data[field] = getattr(self, field).isoformat()
        return data

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ScheduledTask':
        """Create task from dictionary."""
        data['schedule_type'] = ScheduleType(data['schedule_type'])
        for field in ['created_at', 'last_run', 'next_run']:
            if data.get(field):
                data[field] = datetime.fromisoformat(data[field])
        return cls(**data)


class TaskScheduler:
    """Task scheduler for recurring and scheduled jobs."""

    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self.redis: Optional[redis.Redis] = None
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.task_registry: Dict[str, Callable[..., Awaitable[Any]]] = {}
        self.running = False
        self.check_interval = 30  # Check for due tasks every 30 seconds

    async def connect(self) -> None:
        """Establish Redis connection."""
        if self.redis is None:
            self.redis = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis.ping()
            console.print("[green]✓ Connected to Redis for task scheduling[/green]")

    async def disconnect(self) -> None:
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            self.redis = None

    def register_task(self, name: str, func: Callable[..., Awaitable[Any]]) -> None:
        """Register a task function."""
        self.task_registry[name] = func
        console.print(f"[blue]✓ Registered scheduled task: {name}[/blue]")

    async def schedule_task(
        self,
        name: str,
        func_name: str,
        schedule_type: ScheduleType,
        schedule_config: Dict[str, Any],
        args: Optional[List[Any]] = None,
        kwargs: Optional[Dict[str, Any]] = None,
        max_runs: Optional[int] = None,
        timezone: str = "UTC"
    ) -> str:
        """Schedule a recurring task."""
        await self.connect()

        task_id = str(uuid.uuid4())
        task = ScheduledTask(
            id=task_id,
            name=name,
            func_name=func_name,
            args=args or [],
            kwargs=kwargs or {},
            schedule_type=schedule_type,
            schedule_config=schedule_config,
            enabled=True,
            created_at=datetime.utcnow(),
            last_run=None,
            next_run=self._calculate_next_run(schedule_type, schedule_config, timezone),
            run_count=0,
            max_runs=max_runs,
            timezone=timezone
        )

        # Store in Redis
        task_key = f"scheduled_task:{task_id}"
        await self.redis.set(task_key, json.dumps(task.to_dict()))

        # Add to active tasks set
        await self.redis.sadd("active_scheduled_tasks", task_id)

        self.scheduled_tasks[task_id] = task
        console.print(f"[green]✓ Scheduled task: {name} ({task_id})[/green]")

        return task_id

    def _calculate_next_run(
        self,
        schedule_type: ScheduleType,
        schedule_config: Dict[str, Any],
        timezone: str
    ) -> datetime:
        """Calculate next run time for a task."""
        now = datetime.utcnow()

        if schedule_type == ScheduleType.ONE_TIME:
            run_at = schedule_config.get("run_at")
            if isinstance(run_at, str):
                return datetime.fromisoformat(run_at)
            return run_at

        elif schedule_type == ScheduleType.INTERVAL:
            interval_seconds = schedule_config.get("interval_seconds", 3600)
            return now + timedelta(seconds=interval_seconds)

        elif schedule_type == ScheduleType.CRON:
            cron_expression = schedule_config.get("cron", "0 * * * *")
            cron = croniter.croniter(cron_expression, now)
            return cron.get_next(datetime)

        return now + timedelta(hours=1)  # Default fallback

    async def start_scheduler(self) -> None:
        """Start the task scheduler."""
        console.print("[blue]🚀 Starting task scheduler...[/blue]")
        self.running = True

        # Load existing tasks from Redis
        await self._load_scheduled_tasks()

        # Start scheduler loop
        while self.running:
            try:
                await self._check_due_tasks()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                console.print(f"[red]Scheduler error: {e}[/red]")
                await asyncio.sleep(5)

    async def stop_scheduler(self) -> None:
        """Stop the task scheduler."""
        console.print("[blue]🛑 Stopping task scheduler...[/blue]")
        self.running = False

    async def _load_scheduled_tasks(self) -> None:
        """Load scheduled tasks from Redis."""
        await self.connect()

        task_ids = await self.redis.smembers("active_scheduled_tasks")
        for task_id_bytes in task_ids:
            task_id = task_id_bytes.decode() if isinstance(task_id_bytes, bytes) else task_id_bytes
            task_key = f"scheduled_task:{task_id}"
            task_data = await self.redis.get(task_key)

            if task_data:
                task_dict = json.loads(task_data)
                task = ScheduledTask.from_dict(task_dict)
                self.scheduled_tasks[task_id] = task

        console.print(f"[green]✓ Loaded {len(self.scheduled_tasks)} scheduled tasks[/green]")

    async def _check_due_tasks(self) -> None:
        """Check for tasks that are due to run."""
        now = datetime.utcnow()
        due_tasks = []

        for task_id, task in self.scheduled_tasks.items():
            if task.enabled and task.next_run and task.next_run <= now:
                # Check if we've reached max runs
                if task.max_runs and task.run_count >= task.max_runs:
                    await self._disable_task(task_id)
                    continue

                due_tasks.append(task_id)

        # Execute due tasks
        for task_id in due_tasks:
            await self._execute_scheduled_task(task_id)

    async def _execute_scheduled_task(self, task_id: str) -> None:
        """Execute a scheduled task."""
        task = self.scheduled_tasks.get(task_id)
        if not task:
            return

        try:
            console.print(f"[blue]▶ Executing scheduled task: {task.name}[/blue]")

            # Execute the task
            if task.func_name in self.task_registry:
                func = self.task_registry[task.func_name]
                await func(*task.args, **task.kwargs)

                # Update task metadata
                task.last_run = datetime.utcnow()
                task.run_count += 1
                task.next_run = self._calculate_next_run(
                    task.schedule_type, task.schedule_config, task.timezone
                )

                # Save updated task
                task_key = f"scheduled_task:{task_id}"
                await self.redis.set(task_key, json.dumps(task.to_dict()))

                console.print(f"[green]✓ Completed scheduled task: {task.name}[/green]")

        except Exception as e:
            console.print(f"[red]✗ Failed scheduled task {task.name}: {e}[/red]")

            # Still update next run time even on failure
            task.next_run = self._calculate_next_run(
                task.schedule_type, task.schedule_config, task.timezone
            )
            task_key = f"scheduled_task:{task_id}"
            await self.redis.set(task_key, json.dumps(task.to_dict()))

    async def _disable_task(self, task_id: str) -> None:
        """Disable a completed task."""
        task = self.scheduled_tasks.get(task_id)
        if task:
            task.enabled = False
            task_key = f"scheduled_task:{task_id}"
            await self.redis.set(task_key, json.dumps(task.to_dict()))

            # Remove from active tasks
            await self.redis.srem("active_scheduled_tasks", task_id)
            del self.scheduled_tasks[task_id]

            console.print(f"[yellow]📴 Disabled completed task: {task.name}[/yellow]")

    async def list_scheduled_tasks(self) -> List[Dict[str, Any]]:
        """List all scheduled tasks."""
        tasks = []
        for task in self.scheduled_tasks.values():
            task_dict = task.to_dict()
            tasks.append(task_dict)
        return tasks

    async def get_scheduler_stats(self) -> Dict[str, Any]:
        """Get scheduler statistics."""
        total_tasks = len(self.scheduled_tasks)
        enabled_tasks = len([t for t in self.scheduled_tasks.values() if t.enabled])
        disabled_tasks = total_tasks - enabled_tasks

        next_runs = [t.next_run for t in self.scheduled_tasks.values() if t.next_run]
        avg_runs = sum(t.run_count for t in self.scheduled_tasks.values()) / max(total_tasks, 1)

        return {
            "total_tasks": total_tasks,
            "enabled_tasks": enabled_tasks,
            "disabled_tasks": disabled_tasks,
            "next_scheduled_run": min(next_runs) if next_runs else None,
            "average_run_count": avg_runs,
            "running": self.running
        }


# Example scheduled task functions
async def maintenance_cleanup_task() -> str:
    """Example maintenance cleanup task."""
    console.print("[blue]🧹 Running maintenance cleanup...[/blue]")
    await asyncio.sleep(2)  # Simulate cleanup work
    return "Maintenance cleanup completed"

async def cache_warming_task() -> str:
    """Example cache warming task."""
    console.print("[blue]🔥 Warming caches...[/blue]")
    await asyncio.sleep(1)  # Simulate cache warming
    return "Cache warming completed"

async def health_check_task() -> str:
    """Example health check task."""
    console.print("[blue]🏥 Running health checks...[/blue]")
    await asyncio.sleep(0.5)  # Simulate health checks
    return "Health checks completed"

async def backup_task() -> str:
    """Example backup task."""
    console.print("[blue]💾 Creating backups...[/blue]")
    await asyncio.sleep(3)  # Simulate backup process
    return "Backup completed"


async def setup_task_scheduler() -> TaskScheduler:
    """Set up and configure the task scheduler."""
    scheduler = TaskScheduler()

    # Register example tasks
    scheduler.register_task("maintenance_cleanup", maintenance_cleanup_task)
    scheduler.register_task("cache_warming", cache_warming_task)
    scheduler.register_task("health_check", health_check_task)
    scheduler.register_task("backup", backup_task)

    console.print("[green]✓ Task scheduler configured with example tasks[/green]")
    return scheduler


async def main():
    """Main function to demonstrate task scheduling."""
    console.print("[bold blue]🚀 Task Scheduler Demonstration[/bold blue]")
    console.print()

    scheduler = await setup_task_scheduler()

    try:
        # Schedule some example tasks
        cleanup_id = await scheduler.schedule_task(
            "Daily Maintenance Cleanup",
            "maintenance_cleanup",
            ScheduleType.CRON,
            {"cron": "0 2 * * *"}  # Daily at 2 AM
        )

        cache_warm_id = await scheduler.schedule_task(
            "Hourly Cache Warming",
            "cache_warming",
            ScheduleType.INTERVAL,
            {"interval_seconds": 3600}  # Every hour
        )

        health_check_id = await scheduler.schedule_task(
            "Health Check Every 5 Minutes",
            "health_check",
            ScheduleType.INTERVAL,
            {"interval_seconds": 300}  # Every 5 minutes
        )

        backup_id = await scheduler.schedule_task(
            "Weekly Backup",
            "backup",
            ScheduleType.CRON,
            {"cron": "0 3 * * 0"}  # Weekly on Sunday at 3 AM
        )

        console.print(f"[green]✓ Scheduled tasks: cleanup({cleanup_id[:8]}), cache({cache_warm_id[:8]}), health({health_check_id[:8]}), backup({backup_id[:8]})[/green]")

        # List scheduled tasks
        tasks = await scheduler.list_scheduled_tasks()
        console.print(f"[blue]📅 Total scheduled tasks: {len(tasks)}[/blue]")

        # Show scheduler stats
        stats = await scheduler.get_scheduler_stats()
        console.print(f"[blue]📊 Scheduler stats: {stats}[/blue]")

        # Start scheduler for a short demonstration
        console.print("[blue]▶ Starting scheduler for 30 seconds...[/blue]")
        scheduler_task = asyncio.create_task(scheduler.start_scheduler())

        # Let it run for 30 seconds
        await asyncio.sleep(30)

        # Stop scheduler
        await scheduler.stop_scheduler()
        scheduler_task.cancel()

        console.print("[green]✓ Scheduler demonstration completed[/green]")

    finally:
        await scheduler.disconnect()


if __name__ == "__main__":
    asyncio.run(main())
