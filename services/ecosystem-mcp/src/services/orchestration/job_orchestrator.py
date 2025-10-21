"""
Job Orchestrator

Core orchestration logic for parallel sub-job execution.
Manages scheduling, execution, and coordination of sub-jobs.
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .dependency_manager import get_dependency_manager
from .resource_allocator import get_resource_allocator
from .sub_job_executor import get_sub_job_executor
from .progress_tracker import get_progress_tracker
from .execution_monitor import get_execution_monitor
from ...storage import get_database
from ...storage.models_discovery import ProcessingPlanModel, SubJobModel

logger = logging.getLogger(__name__)


class ExecutionStatus(str, Enum):
    """Execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class ExecutionResult:
    """Result of plan execution."""
    plan_id: str
    status: ExecutionStatus
    sub_jobs_completed: int
    sub_jobs_failed: int
    total_files_processed: int
    total_files_failed: int
    total_files_skipped: int
    start_time: datetime
    end_time: Optional[datetime]
    duration_seconds: float
    error_message: Optional[str] = None


@dataclass
class SubJobExecution:
    """Sub-job execution state."""
    sub_job_id: str
    status: ExecutionStatus
    files_processed: int
    files_failed: int
    files_skipped: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    worker_id: Optional[str]
    error_message: Optional[str] = None


class JobOrchestrator:
    """
    Orchestrates parallel sub-job execution.
    
    Features:
    - Parallel execution (up to 5 concurrent)
    - Dependency management
    - Resource allocation
    - Error handling and retry
    - Status tracking
    - Graceful cancellation
    """
    
    def __init__(self, max_concurrent: int = 5):
        """
        Initialize job orchestrator.
        
        Args:
            max_concurrent: Maximum concurrent sub-jobs
        """
        self.max_concurrent = max_concurrent
        self.dependency_manager = get_dependency_manager()
        self.resource_allocator = get_resource_allocator(max_concurrent=max_concurrent)
        self.sub_job_executor = get_sub_job_executor()
        self.progress_tracker = get_progress_tracker()
        self.execution_monitor = get_execution_monitor()
        
        # Active executions
        self.active_executions: Dict[str, ExecutionResult] = {}
        self.sub_job_executions: Dict[str, Dict[str, SubJobExecution]] = {}
        
        # Control flags
        self.paused_plans: set = set()
        self.cancelled_plans: set = set()
        
        logger.info(f"JobOrchestrator initialized (max {max_concurrent} concurrent)")
    
    async def execute_plan(self, plan_id: str) -> ExecutionResult:
        """
        Execute a processing plan with parallel sub-jobs.
        
        Args:
            plan_id: Processing plan ID
        
        Returns:
            ExecutionResult with final status
        """
        logger.info(f"🚀 Starting execution of plan {plan_id}")
        start_time = datetime.utcnow()
        
        try:
            # Load plan from database
            plan, sub_jobs = await self._load_plan(plan_id)
            if not plan:
                raise ValueError(f"Plan {plan_id} not found")
            
            # Initialize execution tracking
            result = ExecutionResult(
                plan_id=plan_id,
                status=ExecutionStatus.RUNNING,
                sub_jobs_completed=0,
                sub_jobs_failed=0,
                total_files_processed=0,
                total_files_failed=0,
                total_files_skipped=0,
                start_time=start_time,
                end_time=None,
                duration_seconds=0.0
            )
            self.active_executions[plan_id] = result
            self.sub_job_executions[plan_id] = {}
            
            # Update plan status
            await self._update_plan_status(plan_id, "processing")
            
            # Start progress tracking
            await self.progress_tracker.start_tracking(
                plan_id=plan_id,
                total_files=plan.total_files,
                sub_jobs_total=len(sub_jobs)
            )
            
            # Start execution monitoring
            await self.execution_monitor.start_monitoring(plan_id)
            
            # Build dependency graph
            sub_job_dicts = [
                {
                    "sub_job_id": sj.sub_job_id,
                    "dependencies": sj.dependencies or []
                }
                for sj in sub_jobs
            ]
            self.dependency_manager.build_graph(plan_id, sub_job_dicts)
            
            # Check for circular dependencies
            cycles = self.dependency_manager.detect_cycles(plan_id)
            if cycles:
                raise ValueError(f"Circular dependencies detected: {cycles}")
            
            logger.info(f"📊 Executing {len(sub_jobs)} sub-jobs with max {self.max_concurrent} concurrent")
            
            # Execute sub-jobs in parallel
            await self._execute_sub_jobs_parallel(plan_id, sub_jobs)
            
            # Calculate final statistics
            result.end_time = datetime.utcnow()
            result.duration_seconds = (result.end_time - start_time).total_seconds()
            
            # Determine final status
            if plan_id in self.cancelled_plans:
                result.status = ExecutionStatus.CANCELLED
                self.cancelled_plans.remove(plan_id)
            elif result.sub_jobs_failed > 0:
                result.status = ExecutionStatus.FAILED
            else:
                result.status = ExecutionStatus.COMPLETED
            
            # Update plan status
            await self._update_plan_status(plan_id, result.status.value)
            
            logger.info(
                f"✅ Plan execution complete: {result.status.value}, "
                f"{result.sub_jobs_completed} completed, {result.sub_jobs_failed} failed, "
                f"{result.duration_seconds:.1f}s"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Plan execution failed: {e}", exc_info=True)
            
            # Update result
            if plan_id in self.active_executions:
                result = self.active_executions[plan_id]
                result.status = ExecutionStatus.FAILED
                result.error_message = str(e)
                result.end_time = datetime.utcnow()
                result.duration_seconds = (result.end_time - start_time).total_seconds()
            else:
                result = ExecutionResult(
                    plan_id=plan_id,
                    status=ExecutionStatus.FAILED,
                    sub_jobs_completed=0,
                    sub_jobs_failed=0,
                    total_files_processed=0,
                    total_files_failed=0,
                    total_files_skipped=0,
                    start_time=start_time,
                    end_time=datetime.utcnow(),
                    duration_seconds=0.0,
                    error_message=str(e)
                )
            
            await self._update_plan_status(plan_id, "failed")
            
            return result
        
        finally:
            # Stop progress tracking
            await self.progress_tracker.stop_tracking(plan_id)
            
            # Stop execution monitoring
            await self.execution_monitor.stop_monitoring(plan_id)
            
            # Cleanup
            if plan_id in self.active_executions:
                del self.active_executions[plan_id]
            if plan_id in self.sub_job_executions:
                del self.sub_job_executions[plan_id]
            self.dependency_manager.clear_graph(plan_id)
            await self.resource_allocator.cleanup()
    
    async def _execute_sub_jobs_parallel(self, plan_id: str, sub_jobs: List[SubJobModel]) -> None:
        """
        Execute sub-jobs in parallel respecting dependencies.
        
        Args:
            plan_id: Processing plan ID
            sub_jobs: List of sub-jobs to execute
        """
        # Create sub-job lookup
        sub_job_map = {sj.sub_job_id: sj for sj in sub_jobs}
        
        # Track active tasks
        active_tasks: Dict[str, asyncio.Task] = {}
        
        while True:
            # Check for cancellation
            if plan_id in self.cancelled_plans:
                logger.info(f"🛑 Cancelling execution of plan {plan_id}")
                for task in active_tasks.values():
                    task.cancel()
                break
            
            # Check for pause
            while plan_id in self.paused_plans:
                logger.debug(f"⏸️  Plan {plan_id} paused, waiting...")
                await asyncio.sleep(1.0)
            
            # Get ready sub-jobs (dependencies satisfied)
            ready_sub_jobs = self.dependency_manager.get_ready_sub_jobs(plan_id)
            
            # Filter out already executing or completed
            ready_sub_jobs = [
                sj_id for sj_id in ready_sub_jobs
                if sj_id not in active_tasks and sj_id in sub_job_map
            ]
            
            # Start new sub-jobs up to concurrent limit
            while ready_sub_jobs and len(active_tasks) < self.max_concurrent:
                sub_job_id = ready_sub_jobs.pop(0)
                sub_job = sub_job_map[sub_job_id]
                
                # Try to allocate resources
                allocation = await self.resource_allocator.allocate(
                    sub_job_id,
                    sub_job.file_count
                )
                
                if allocation:
                    # Start execution
                    task = asyncio.create_task(
                        self._execute_sub_job(plan_id, sub_job)
                    )
                    active_tasks[sub_job_id] = task
                    logger.info(f"🚀 Started sub-job: {sub_job_id} ({len(active_tasks)}/{self.max_concurrent} active)")
                else:
                    # No resources available, will retry later
                    ready_sub_jobs.insert(0, sub_job_id)
                    break
            
            # Wait for at least one task to complete
            if active_tasks:
                done, pending = await asyncio.wait(
                    active_tasks.values(),
                    return_when=asyncio.FIRST_COMPLETED,
                    timeout=1.0
                )
                
                # Process completed tasks
                for task in done:
                    # Find which sub-job completed
                    completed_id = None
                    for sj_id, t in active_tasks.items():
                        if t == task:
                            completed_id = sj_id
                            break
                    
                    if completed_id:
                        del active_tasks[completed_id]
                        
                        # Release resources
                        await self.resource_allocator.release(completed_id)
                        
                        # Mark as completed in dependency manager
                        self.dependency_manager.mark_completed(plan_id, completed_id)
                        
                        logger.info(f"✅ Completed sub-job: {completed_id} ({len(active_tasks)} remaining)")
            
            # Check if all done
            if not active_tasks and not ready_sub_jobs:
                if self.dependency_manager.is_complete(plan_id):
                    logger.info(f"✅ All sub-jobs completed for plan {plan_id}")
                    break
                else:
                    # Check if we're stuck (deadlock or all failed)
                    completed, total = self.dependency_manager.get_progress(plan_id)
                    if completed < total and not active_tasks:
                        logger.warning(f"⚠️  Execution stuck: {completed}/{total} completed, no active tasks")
                        break
            
            # Small delay to prevent tight loop
            await asyncio.sleep(0.1)
    
    async def _execute_sub_job(self, plan_id: str, sub_job: SubJobModel) -> None:
        """
        Execute a single sub-job.
        
        Args:
            plan_id: Processing plan ID
            sub_job: Sub-job to execute
        """
        sub_job_id = sub_job.sub_job_id
        start_time = datetime.utcnow()
        
        # Initialize execution state
        execution = SubJobExecution(
            sub_job_id=sub_job_id,
            status=ExecutionStatus.RUNNING,
            files_processed=0,
            files_failed=0,
            files_skipped=0,
            start_time=start_time,
            end_time=None,
            worker_id=None
        )
        
        if plan_id in self.sub_job_executions:
            self.sub_job_executions[plan_id][sub_job_id] = execution
        
        try:
            logger.info(f"▶️  Executing sub-job {sub_job_id}: {sub_job.file_count} files")
            
            # Update database status
            await self._update_sub_job_status(sub_job.id, "processing", start_time)
            
            # Mark sub-job as active in progress tracker
            await self.progress_tracker.mark_sub_job_active(plan_id, sub_job_id)
            
            # Get repository path from plan
            plan, _ = await self._load_plan(plan_id)
            repo_path = plan.repository_path if plan else "/app"
            
            # Progress callback for real-time updates
            async def progress_callback(processed, failed, skipped, total):
                execution.files_processed = processed
                execution.files_failed = failed
                execution.files_skipped = skipped
                
                # Update progress tracker
                await self.progress_tracker.update_sub_job_progress(
                    plan_id=plan_id,
                    sub_job_id=sub_job_id,
                    files_processed=processed,
                    files_failed=failed,
                    files_skipped=skipped,
                    total_files=total
                )
            
            # Execute sub-job with actual file processing
            stats = await self.sub_job_executor.execute_sub_job(
                sub_job=sub_job,
                repo_path=repo_path,
                progress_callback=progress_callback
            )
            
            # Update execution state
            execution.files_processed = stats["processed"]
            execution.files_failed = stats["failed"]
            execution.files_skipped = stats["skipped"]
            execution.status = ExecutionStatus.COMPLETED
            execution.end_time = datetime.utcnow()
            
            # Update database
            await self._update_sub_job_completion(
                sub_job.id,
                execution.files_processed,
                execution.files_failed,
                execution.files_skipped,
                execution.end_time
            )
            
            # Mark sub-job as complete in progress tracker
            await self.progress_tracker.mark_sub_job_complete(plan_id, sub_job_id, success=True)
            
            # Update plan result
            if plan_id in self.active_executions:
                result = self.active_executions[plan_id]
                result.sub_jobs_completed += 1
                result.total_files_processed += execution.files_processed
                result.total_files_failed += execution.files_failed
                result.total_files_skipped += execution.files_skipped
            
            logger.info(
                f"✅ Sub-job {sub_job_id} completed: "
                f"processed={execution.files_processed}, "
                f"failed={execution.files_failed}, "
                f"skipped={execution.files_skipped}"
            )
            
        except Exception as e:
            logger.error(f"❌ Sub-job {sub_job_id} failed: {e}", exc_info=True)
            
            execution.status = ExecutionStatus.FAILED
            execution.error_message = str(e)
            execution.end_time = datetime.utcnow()
            
            # Update database
            await self._update_sub_job_status(
                sub_job.id,
                "failed",
                execution.end_time,
                str(e)
            )
            
            # Mark sub-job as failed in progress tracker
            await self.progress_tracker.mark_sub_job_complete(plan_id, sub_job_id, success=False)
            
            # Update plan result
            if plan_id in self.active_executions:
                result = self.active_executions[plan_id]
                result.sub_jobs_failed += 1
    
    async def pause_execution(self, plan_id: str) -> bool:
        """
        Pause execution of a plan.
        
        Args:
            plan_id: Processing plan ID
        
        Returns:
            True if paused, False if not found
        """
        if plan_id in self.active_executions:
            self.paused_plans.add(plan_id)
            logger.info(f"⏸️  Paused execution of plan {plan_id}")
            return True
        return False
    
    async def resume_execution(self, plan_id: str) -> bool:
        """
        Resume execution of a paused plan.
        
        Args:
            plan_id: Processing plan ID
        
        Returns:
            True if resumed, False if not paused
        """
        if plan_id in self.paused_plans:
            self.paused_plans.remove(plan_id)
            logger.info(f"▶️  Resumed execution of plan {plan_id}")
            return True
        return False
    
    async def cancel_execution(self, plan_id: str) -> bool:
        """
        Cancel execution of a plan.
        
        Args:
            plan_id: Processing plan ID
        
        Returns:
            True if cancelled, False if not found
        """
        if plan_id in self.active_executions:
            self.cancelled_plans.add(plan_id)
            logger.info(f"🛑 Cancelled execution of plan {plan_id}")
            return True
        return False
    
    async def get_execution_status(self, plan_id: str) -> Optional[ExecutionResult]:
        """
        Get current execution status.
        
        Args:
            plan_id: Processing plan ID
        
        Returns:
            ExecutionResult if active, None otherwise
        """
        return self.active_executions.get(plan_id)
    
    async def _load_plan(self, plan_id: str) -> tuple:
        """Load plan and sub-jobs from database."""
        from sqlalchemy import select
        
        async with get_database().session() as session:
            # Load plan
            result = await session.execute(
                select(ProcessingPlanModel).where(ProcessingPlanModel.id == plan_id)
            )
            plan = result.scalar_one_or_none()
            
            if not plan:
                return None, []
            
            # Load sub-jobs
            result = await session.execute(
                select(SubJobModel)
                .where(SubJobModel.plan_id == plan_id)
                .order_by(SubJobModel.priority)
            )
            sub_jobs = result.scalars().all()
            
            return plan, list(sub_jobs)
    
    async def _update_plan_status(self, plan_id: str, status: str) -> None:
        """Update plan status in database."""
        from sqlalchemy import text
        
        async with get_database().session() as session:
            await session.execute(
                text(f"UPDATE processing_plans SET status=:status, updated_at=NOW() WHERE id=:plan_id"),
                {"status": status, "plan_id": plan_id}
            )
            await session.commit()
    
    async def _update_sub_job_status(
        self,
        sub_job_id: str,
        status: str,
        timestamp: datetime,
        error: Optional[str] = None
    ) -> None:
        """Update sub-job status in database."""
        from sqlalchemy import text
        
        async with get_database().session() as session:
            if status == "processing":
                await session.execute(
                    text(
                        "UPDATE sub_jobs SET status=:status, started_at=:timestamp "
                        "WHERE id=:sub_job_id"
                    ),
                    {"status": status, "timestamp": timestamp, "sub_job_id": sub_job_id}
                )
            elif error:
                await session.execute(
                    text(
                        "UPDATE sub_jobs SET status=:status, error_message=:error "
                        "WHERE id=:sub_job_id"
                    ),
                    {"status": status, "error": error, "sub_job_id": sub_job_id}
                )
            await session.commit()
    
    async def _update_sub_job_completion(
        self,
        sub_job_id: str,
        processed: int,
        failed: int,
        skipped: int,
        end_time: datetime
    ) -> None:
        """Update sub-job completion in database."""
        from sqlalchemy import text
        
        async with get_database().session() as session:
            await session.execute(
                text(
                    "UPDATE sub_jobs SET "
                    "status='completed', "
                    "processed_files=:processed, "
                    "failed_files=:failed, "
                    "skipped_files=:skipped, "
                    "completed_at=:end_time "
                    "WHERE id=:sub_job_id"
                ),
                {
                    "processed": processed,
                    "failed": failed,
                    "skipped": skipped,
                    "end_time": end_time,
                    "sub_job_id": sub_job_id
                }
            )
            await session.commit()


# Singleton instance
_job_orchestrator_instance = None

def get_job_orchestrator(max_concurrent: int = 5) -> JobOrchestrator:
    """Get singleton job orchestrator instance."""
    global _job_orchestrator_instance
    if _job_orchestrator_instance is None:
        _job_orchestrator_instance = JobOrchestrator(max_concurrent=max_concurrent)
    return _job_orchestrator_instance

