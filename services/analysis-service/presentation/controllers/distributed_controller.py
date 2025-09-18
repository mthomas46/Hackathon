"""Distributed Controller - Handles distributed processing endpoints."""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException

from ...modules.models import (
    DistributedTaskRequest,
    BatchTasksRequest,
    TaskStatusRequest,
    CancelTaskRequest,
    ScaleWorkersRequest,
    LoadBalancingStrategyRequest,
    LoadBalancingConfigRequest
)
from ...modules.analysis_handlers import analysis_handlers


class DistributedController:
    """Controller for distributed processing endpoints."""

    def __init__(self):
        """Initialize controller."""
        self.router = APIRouter()
        self._setup_routes()

    def _setup_routes(self):
        """Set up API routes."""

        @self.router.post("/distributed/tasks")
        async def submit_distributed_task_endpoint(req: DistributedTaskRequest):
            """Submit a task for distributed processing.

            Submits individual analysis tasks for parallel processing across
            multiple workers with intelligent load balancing and prioritization.
            """
            return await analysis_handlers.handle_submit_distributed_task(req)

        @self.router.post("/distributed/tasks/batch")
        async def submit_batch_tasks_endpoint(req: BatchTasksRequest):
            """Submit multiple tasks for batch distributed processing.

            Processes multiple analysis tasks as a batch with optimized resource
            allocation and parallel execution across available workers.
            """
            return await analysis_handlers.handle_submit_batch_tasks(req)

        @self.router.get("/distributed/tasks/{task_id}")
        async def get_task_status_endpoint(task_id: str):
            """Get the status of a distributed task.

            Retrieves detailed status information for a specific distributed task
            including progress, results, worker assignment, and performance metrics.
            """
            return await analysis_handlers.handle_get_task_status(
                TaskStatusRequest(task_id=task_id)
            )

        @self.router.delete("/distributed/tasks/{task_id}")
        async def cancel_task_endpoint(task_id: str):
            """Cancel a distributed task.

            Cancels a running distributed task and releases associated resources.
            Provides graceful shutdown and cleanup of task state.
            """
            return await analysis_handlers.handle_cancel_task(
                CancelTaskRequest(task_id=task_id)
            )

        @self.router.get("/distributed/workers")
        async def get_workers_status_endpoint():
            """Get status of all distributed processing workers.

            Provides comprehensive view of all worker nodes including their
            current load, health status, task assignments, and performance metrics.
            """
            return await analysis_handlers.handle_get_workers_status()

        @self.router.get("/distributed/stats")
        async def get_processing_stats_endpoint():
            """Get distributed processing statistics.

            Returns comprehensive statistics about the distributed processing system
            including throughput, latency, error rates, and resource utilization.
            """
            return await analysis_handlers.handle_get_processing_stats()

        @self.router.post("/distributed/workers/scale")
        async def scale_workers_endpoint(req: ScaleWorkersRequest):
            """Scale the number of distributed processing workers.

            Dynamically adjusts the worker pool size based on workload demands,
            system capacity, and performance requirements.
            """
            return await analysis_handlers.handle_scale_workers(req)

        @self.router.post("/distributed/start")
        async def start_distributed_processing_endpoint():
            """Start the distributed processing system.

            Initializes and starts the distributed processing system with
            configured worker pools and load balancing strategies.
            """
            return await analysis_handlers.handle_start_processing()

        @self.router.put("/distributed/load-balancing/strategy")
        async def set_load_balancing_strategy_endpoint(req: LoadBalancingStrategyRequest):
            """Configure load balancing strategy.

            Sets the load balancing algorithm used for task distribution
            across available workers (round-robin, least-loaded, performance-based, adaptive).
            """
            return await analysis_handlers.handle_set_load_balancing_strategy(req)

        @self.router.get("/distributed/queue/status")
        async def get_queue_status_endpoint():
            """Get detailed status of the distributed processing queue.

            Provides comprehensive queue statistics including task counts by priority,
            average wait times, processing rates, and queue efficiency metrics.
            """
            return await analysis_handlers.handle_get_queue_status()

        @self.router.put("/distributed/load-balancing/config")
        async def configure_load_balancing_endpoint(req: LoadBalancingConfigRequest):
            """Configure comprehensive load balancing settings.

            Sets advanced load balancing parameters including worker weights,
            performance thresholds, adaptive algorithm settings, and failover policies.
            """
            return await analysis_handlers.handle_configure_load_balancing(req)

        @self.router.get("/distributed/load-balancing/config")
        async def get_load_balancing_config_endpoint():
            """Get current load balancing configuration.

            Returns the current load balancing strategy and all associated
            configuration parameters and performance settings.
            """
            return await analysis_handlers.handle_get_load_balancing_config()

    def get_router(self) -> APIRouter:
        """Get the FastAPI router for this controller."""
        return self.router
