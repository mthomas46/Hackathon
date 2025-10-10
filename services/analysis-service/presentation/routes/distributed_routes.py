"""Distributed Processing Routes.

Task submission, worker management, load balancing, and distributed processing control.
"""
from fastapi import APIRouter

# Import shared utilities
from services.shared.presentation.api.responses import create_success_response, create_error_response
from services.shared.core.constants_new import ErrorCodes
from services.shared.infrastructure.monitoring.logging import fire_and_forget

# Import models
from ...modules.models import (
    DistributedTaskRequest,
    BatchTasksRequest,
    TaskStatusRequest,
    CancelTaskRequest,
    ScaleWorkersRequest,
    LoadBalancingStrategyRequest,
    LoadBalancingConfigRequest
)

# Service metadata
SERVICE_NAME = "analysis-service"

# Create router
router = APIRouter(tags=["Distributed Processing"])


@router.post("/distributed/tasks")
async def submit_distributed_task_endpoint(req: DistributedTaskRequest):
    """Submit a task for distributed processing.

    Submits analysis tasks to be processed asynchronously across multiple workers,
    enabling high-performance parallel processing of large document analysis workloads.

    Args:
        req: Distributed task request with task details

    Returns:
        Task submission confirmation with task ID and status
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_submit_distributed_task(req)

        # Log successful submission
        task_id = result.task_id
        task_type = result.task_type
        fire_and_forget(
            "info",
            "Distributed task submitted",
            SERVICE_NAME,
            {
                "task_id": task_id,
                "task_type": task_type,
                "priority": result.priority,
                "status": result.status
            }
        )

        return create_success_response(
            f"Distributed task {task_type} submitted successfully",
            {
                "task_id": task_id,
                "task_type": task_type,
                "status": result.status,
                "priority": result.priority,
                "submitted_at": result.submitted_at,
                "estimated_completion": result.estimated_completion
            },
            task_id=task_id,
            task_type=task_type,
            priority=result.priority
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Distributed task submission failed",
            SERVICE_NAME,
            {"task_type": req.task_type, "error": str(e)}
        )

        return create_error_response(
            f"Distributed task submission failed: {str(e)}",
            error_code=ErrorCodes.PROCESSING_FAILED
        )


@router.post("/distributed/tasks/batch")
async def submit_batch_tasks_endpoint(req: BatchTasksRequest):
    """Submit multiple tasks for batch distributed processing.

    Submits a batch of analysis tasks to be processed in parallel across multiple workers,
    optimizing throughput for large-scale document analysis operations.

    Args:
        req: Batch tasks request with multiple task definitions

    Returns:
        Batch submission confirmation with task IDs
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_submit_batch_tasks(req)

        # Log successful submission
        total_tasks = result.total_tasks
        fire_and_forget(
            "info",
            "Batch tasks submitted",
            SERVICE_NAME,
            {
                "total_tasks": total_tasks,
                "submitted_at": result.submitted_at
            }
        )

        return create_success_response(
            f"Batch of {total_tasks} tasks submitted successfully",
            {
                "task_ids": result.task_ids,
                "total_tasks": total_tasks,
                "submitted_at": result.submitted_at
            },
            total_tasks=total_tasks
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Batch task submission failed",
            SERVICE_NAME,
            {"task_count": len(req.tasks), "error": str(e)}
        )

        return create_error_response(
            f"Batch task submission failed: {str(e)}",
            error_code=ErrorCodes.PROCESSING_FAILED
        )


@router.get("/distributed/tasks/{task_id}")
async def get_task_status_endpoint(task_id: str):
    """Get the status of a distributed task.

    Retrieves real-time status, progress, and results for distributed processing tasks,
    enabling monitoring and tracking of long-running analysis operations.

    Args:
        task_id: Unique identifier for the distributed task

    Returns:
        Task status with progress, timing, and results
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        req = TaskStatusRequest(task_id=task_id)
        result = await analysis_handlers.handle_get_task_status(req)

        # Log status retrieval
        status = result.status
        progress = result.progress
        fire_and_forget(
            "info",
            "Task status retrieved",
            SERVICE_NAME,
            {
                "task_id": task_id,
                "status": status,
                "progress": progress
            }
        )

        return create_success_response(
            f"Task {task_id} status: {status}",
            {
                "task_id": result.task_id,
                "task_type": result.task_type,
                "status": status,
                "priority": result.priority,
                "progress": progress,
                "created_at": result.created_at,
                "started_at": result.started_at,
                "completed_at": result.completed_at,
                "assigned_worker": result.assigned_worker,
                "error_message": result.error_message,
                "estimated_completion": result.estimated_completion,
                "retry_count": result.retry_count
            },
            task_id=task_id,
            status=status,
            progress=progress
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Task status retrieval failed",
            SERVICE_NAME,
            {"task_id": task_id, "error": str(e)}
        )

        return create_error_response(
            f"Task status retrieval failed: {str(e)}",
            error_code=ErrorCodes.PROCESSING_FAILED
        )


@router.delete("/distributed/tasks/{task_id}")
async def cancel_task_endpoint(task_id: str):
    """Cancel a distributed task.

    Cancels a running distributed processing task, freeing up worker resources
    and preventing completion of unnecessary analysis operations.

    Args:
        task_id: Unique identifier for the task to cancel

    Returns:
        Cancellation confirmation
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        req = CancelTaskRequest(task_id=task_id)
        result = await analysis_handlers.handle_cancel_task(req)

        # Log cancellation
        cancelled = result['cancelled']
        fire_and_forget(
            "info",
            "Task cancellation attempted",
            SERVICE_NAME,
            {
                "task_id": task_id,
                "cancelled": cancelled,
                "message": result['message']
            }
        )

        return create_success_response(
            result['message'],
            {
                "task_id": task_id,
                "cancelled": cancelled,
                "message": result['message']
            },
            cancelled=cancelled
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Task cancellation failed",
            SERVICE_NAME,
            {"task_id": task_id, "error": str(e)}
        )

        return create_error_response(
            f"Task cancellation failed: {str(e)}",
            error_code=ErrorCodes.PROCESSING_FAILED
        )


@router.get("/distributed/workers")
async def get_workers_status_endpoint():
    """Get status of all distributed processing workers.

    Provides comprehensive information about worker availability, performance,
    and current task assignments for monitoring and optimization.

    Returns:
        Worker status for all processing workers
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_get_workers_status()

        # Log status retrieval
        total_workers = result.total_workers
        available_workers = result.available_workers
        busy_workers = result.busy_workers
        fire_and_forget(
            "info",
            "Workers status retrieved",
            SERVICE_NAME,
            {
                "total_workers": total_workers,
                "available_workers": available_workers,
                "busy_workers": busy_workers
            }
        )

        return create_success_response(
            f"Retrieved status for {total_workers} workers",
            {
                "workers": result.workers,
                "total_workers": total_workers,
                "available_workers": available_workers,
                "busy_workers": busy_workers
            },
            total_workers=total_workers,
            available_workers=available_workers,
            busy_workers=busy_workers
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Workers status retrieval failed",
            SERVICE_NAME,
            {"error": str(e)}
        )

        return create_error_response(
            f"Workers status retrieval failed: {str(e)}",
            error_code=ErrorCodes.PROCESSING_FAILED
        )


@router.get("/distributed/stats")
async def get_processing_stats_endpoint():
    """Get distributed processing statistics.

    Provides comprehensive metrics about task processing performance,
    throughput, completion rates, and system utilization.

    Returns:
        Processing statistics and performance metrics
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_get_processing_stats()

        # Log stats retrieval
        total_tasks = result.total_tasks
        completion_rate = result.completion_rate
        throughput = result.throughput_per_minute
        fire_and_forget(
            "info",
            "Processing stats retrieved",
            SERVICE_NAME,
            {
                "total_tasks": total_tasks,
                "completion_rate": completion_rate,
                "throughput_per_minute": throughput
            }
        )

        return create_success_response(
            f"Retrieved processing stats for {total_tasks} total tasks",
            {
                "total_tasks": total_tasks,
                "completed_tasks": result.completed_tasks,
                "failed_tasks": result.failed_tasks,
                "active_workers": result.active_workers,
                "avg_processing_time": result.avg_processing_time,
                "throughput_per_minute": throughput,
                "completion_rate": completion_rate
            },
            total_tasks=total_tasks,
            completion_rate=completion_rate,
            throughput_per_minute=throughput
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Processing stats retrieval failed",
            SERVICE_NAME,
            {"error": str(e)}
        )

        return create_error_response(
            f"Processing stats retrieval failed: {str(e)}",
            error_code=ErrorCodes.PROCESSING_FAILED
        )


@router.post("/distributed/workers/scale")
async def scale_workers_endpoint(req: ScaleWorkersRequest):
    """Scale the number of distributed processing workers.

    Dynamically adjusts the worker pool size based on workload demands,
    enabling automatic scaling for optimal performance and resource utilization.

    Args:
        req: Worker scaling request with target count

    Returns:
        Scaling confirmation with worker counts
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_scale_workers(req)

        # Log scaling
        previous_count = result.previous_count
        new_count = result.new_count
        fire_and_forget(
            "info",
            "Workers scaled",
            SERVICE_NAME,
            {
                "previous_count": previous_count,
                "new_count": new_count,
                "scaled_at": result.scaled_at
            }
        )

        return create_success_response(
            f"Workers scaled from {previous_count} to {new_count}",
            {
                "previous_count": previous_count,
                "new_count": new_count,
                "scaled_at": result.scaled_at
            },
            previous_count=previous_count,
            new_count=new_count
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Worker scaling failed",
            SERVICE_NAME,
            {"target_count": req.target_count, "error": str(e)}
        )

        return create_error_response(
            f"Worker scaling failed: {str(e)}",
            error_code=ErrorCodes.PROCESSING_FAILED
        )


@router.post("/distributed/start")
async def start_distributed_processing_endpoint():
    """Start the distributed processing system.

    Initializes the distributed task processing loop and begins accepting
    tasks for parallel processing across the worker pool.

    Returns:
        Processing start confirmation
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_start_processing()

        # Log processing start
        started = result['started']
        fire_and_forget(
            "info",
            "Distributed processing start attempted",
            SERVICE_NAME,
            {
                "started": started,
                "message": result['message']
            }
        )

        return create_success_response(
            result['message'],
            {
                "started": started,
                "message": result['message']
            },
            started=started
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Distributed processing start failed",
            SERVICE_NAME,
            {"error": str(e)}
        )

        return create_error_response(
            f"Distributed processing start failed: {str(e)}",
            error_code=ErrorCodes.PROCESSING_FAILED
        )


@router.put("/distributed/load-balancing/strategy")
async def set_load_balancing_strategy_endpoint(req: LoadBalancingStrategyRequest):
    """Configure load balancing strategy for distributed processing.

    Changes the algorithm used to distribute tasks across available workers,
    optimizing for different workload patterns and performance requirements.

    Args:
        req: Load balancing strategy request

    Returns:
        Strategy configuration confirmation
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_set_load_balancing_strategy(req)

        # Log strategy change
        current_strategy = result.current_strategy
        fire_and_forget(
            "info",
            "Load balancing strategy changed",
            SERVICE_NAME,
            {
                "strategy": current_strategy,
                "changed_at": result.changed_at
            }
        )

        return create_success_response(
            f"Load balancing strategy changed to {current_strategy}",
            {
                "current_strategy": current_strategy,
                "available_strategies": result.available_strategies,
                "changed_at": result.changed_at
            },
            strategy=current_strategy
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Load balancing strategy change failed",
            SERVICE_NAME,
            {"strategy": req.strategy, "error": str(e)}
        )

        return create_error_response(
            f"Load balancing strategy change failed: {str(e)}",
            error_code=ErrorCodes.PROCESSING_FAILED
        )


@router.get("/distributed/queue/status")
async def get_queue_status_endpoint():
    """Get detailed status of the distributed processing queue.

    Provides comprehensive information about queue length, priority distribution,
    processing efficiency, and task aging for performance monitoring.

    Returns:
        Queue status with efficiency metrics
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_get_queue_status()

        # Log queue status retrieval
        queue_length = result.queue_length
        queue_efficiency = result.queue_efficiency
        processing_rate = result.processing_rate
        fire_and_forget(
            "info",
            "Queue status retrieved",
            SERVICE_NAME,
            {
                "queue_length": queue_length,
                "queue_efficiency": queue_efficiency,
                "processing_rate": processing_rate
            }
        )

        return create_success_response(
            f"Retrieved queue status with {queue_length} tasks",
            {
                "queue_length": queue_length,
                "priority_distribution": result.priority_distribution,
                "oldest_task_age": result.oldest_task_age,
                "queue_efficiency": queue_efficiency,
                "processing_rate": processing_rate
            },
            queue_length=queue_length,
            queue_efficiency=queue_efficiency,
            processing_rate=processing_rate
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Queue status retrieval failed",
            SERVICE_NAME,
            {"error": str(e)}
        )

        return create_error_response(
            f"Queue status retrieval failed: {str(e)}",
            error_code=ErrorCodes.PROCESSING_FAILED
        )


@router.put("/distributed/load-balancing/config")
async def configure_load_balancing_endpoint(req: LoadBalancingConfigRequest):
    """Configure comprehensive load balancing settings.

    Sets up advanced load balancing parameters including strategy,
    worker scaling, queue management, and auto-scaling policies.

    Args:
        req: Load balancing configuration request

    Returns:
        Configuration confirmation
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_configure_load_balancing(req)

        # Log configuration
        strategy = result.strategy
        worker_count = result.worker_count
        fire_and_forget(
            "info",
            "Load balancing configuration updated",
            SERVICE_NAME,
            {
                "strategy": strategy,
                "worker_count": worker_count,
                "configured_at": result.configured_at
            }
        )

        return create_success_response(
            f"Load balancing configured with strategy '{strategy}' and {worker_count} workers",
            {
                "strategy": strategy,
                "worker_count": worker_count,
                "max_queue_size": result.max_queue_size,
                "enable_auto_scaling": result.enable_auto_scaling,
                "configured_at": result.configured_at
            },
            strategy=strategy,
            worker_count=worker_count
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Load balancing configuration failed",
            SERVICE_NAME,
            {"error": str(e)}
        )

        return create_error_response(
            f"Load balancing configuration failed: {str(e)}",
            error_code=ErrorCodes.PROCESSING_FAILED
        )


@router.get("/distributed/load-balancing/config")
async def get_load_balancing_config_endpoint():
    """Get current load balancing configuration.

    Retrieves the current load balancing strategy, worker count,
    and configuration settings for monitoring and management.

    Returns:
        Current load balancing configuration
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_get_load_balancing_config()

        # Log configuration retrieval
        strategy = result.strategy
        worker_count = result.worker_count
        fire_and_forget(
            "info",
            "Load balancing configuration retrieved",
            SERVICE_NAME,
            {
                "strategy": strategy,
                "worker_count": worker_count
            }
        )

        return create_success_response(
            f"Retrieved load balancing configuration: {strategy} strategy with {worker_count} workers",
            {
                "strategy": strategy,
                "worker_count": worker_count,
                "max_queue_size": result.max_queue_size,
                "enable_auto_scaling": result.enable_auto_scaling,
                "configured_at": result.configured_at
            },
            strategy=strategy,
            worker_count=worker_count
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Load balancing configuration retrieval failed",
            SERVICE_NAME,
            {"error": str(e)}
        )

        return create_error_response(
            f"Load balancing configuration retrieval failed: {str(e)}",
            error_code=ErrorCodes.PROCESSING_FAILED
        )

