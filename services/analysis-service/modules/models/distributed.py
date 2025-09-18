"""Distributed Models - Distributed processing request and response models."""

from typing import Optional, List, Dict, Any
from pydantic import Field

from .base import BaseModel


class DistributedTaskRequest(BaseModel):
    """Request for distributed task submission."""
    task_type: str = Field(..., description="Type of distributed task")
    data: Dict[str, Any] = Field(..., description="Task data payload")
    priority: str = Field("normal", description="Task priority")
    dependencies: Optional[List[str]] = Field(None, description="Task dependencies")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Task metadata")


class DistributedTaskResponse(BaseModel):
    """Response for distributed task submission."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    task_id: str = Field(..., description="Task ID")
    status: str = Field(..., description="Task status")
    estimated_completion_seconds: float = Field(..., description="Estimated completion time")
    queue_position: int = Field(..., description="Queue position")
    error_message: Optional[str] = Field(None, description="Error message if submission failed")


class BatchTasksRequest(BaseModel):
    """Request for batch task submission."""
    tasks: List[Dict[str, Any]] = Field(..., description="List of tasks to submit")
    batch_options: Optional[Dict[str, Any]] = Field(None, description="Batch processing options")


class BatchTasksResponse(BaseModel):
    """Response for batch task submission."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    batch_id: str = Field(..., description="Batch ID")
    task_count: int = Field(..., description="Number of tasks submitted")
    submitted_tasks: List[str] = Field(default_factory=list, description="Submitted task IDs")
    status: str = Field(..., description="Batch status")
    estimated_completion_seconds: float = Field(..., description="Estimated completion time")
    error_message: Optional[str] = Field(None, description="Error message if submission failed")


class TaskStatusRequest(BaseModel):
    """Request for task status."""
    task_id: str = Field(..., description="Task ID to check")


class TaskStatusResponse(BaseModel):
    """Response for task status."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    task_id: str = Field(..., description="Task ID")
    status: str = Field(..., description="Task status")
    progress: float = Field(..., ge=0.0, le=1.0, description="Task progress")
    started_at: Optional[str] = Field(None, description="Task start time")
    completed_at: Optional[str] = Field(None, description="Task completion time")
    result: Optional[Any] = Field(None, description="Task result")
    error_message: Optional[str] = Field(None, description="Error message if task failed")


class CancelTaskRequest(BaseModel):
    """Request for task cancellation."""
    task_id: str = Field(..., description="Task ID to cancel")


class WorkersStatusResponse(BaseModel):
    """Response for workers status."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    total_workers: int = Field(..., description="Total number of workers")
    active_workers: int = Field(..., description="Number of active workers")
    idle_workers: int = Field(..., description="Number of idle workers")
    workers: List[Dict[str, Any]] = Field(default_factory=list, description="Worker details")
    average_cpu_usage: float = Field(..., description="Average CPU usage")
    average_memory_usage: float = Field(..., description="Average memory usage")
    error_message: Optional[str] = Field(None, description="Error message if status check failed")


class ProcessingStatsResponse(BaseModel):
    """Response for processing statistics."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    total_tasks_processed: int = Field(..., description="Total tasks processed")
    tasks_completed: int = Field(..., description="Tasks completed")
    tasks_failed: int = Field(..., description="Tasks failed")
    tasks_cancelled: int = Field(..., description="Tasks cancelled")
    average_processing_time_seconds: float = Field(..., description="Average processing time")
    throughput_tasks_per_minute: float = Field(..., description="Throughput rate")
    queue_length: int = Field(..., description="Current queue length")
    oldest_task_age_seconds: float = Field(..., description="Age of oldest task")
    worker_utilization_percentage: float = Field(..., description="Worker utilization")
    peak_concurrent_tasks: int = Field(..., description="Peak concurrent tasks")
    system_uptime_seconds: int = Field(..., description="System uptime")
    memory_usage_mb: float = Field(..., description="Memory usage")
    cpu_usage_percentage: float = Field(..., description="CPU usage")
    error_message: Optional[str] = Field(None, description="Error message if stats check failed")


class ScaleWorkersRequest(BaseModel):
    """Request for worker scaling."""
    target_worker_count: int = Field(..., ge=1, le=50, description="Target number of workers")
    scaling_reason: Optional[str] = Field(None, description="Reason for scaling")


class ScaleWorkersResponse(BaseModel):
    """Response for worker scaling."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    previous_worker_count: int = Field(..., description="Previous worker count")
    new_worker_count: int = Field(..., description="New worker count")
    scaling_reason: str = Field(..., description="Reason for scaling")
    estimated_scaling_time_seconds: float = Field(..., description="Estimated scaling time")
    error_message: Optional[str] = Field(None, description="Error message if scaling failed")


class LoadBalancingStrategyRequest(BaseModel):
    """Request for load balancing strategy configuration."""
    strategy: str = Field(..., description="Load balancing strategy")


class LoadBalancingStrategyResponse(BaseModel):
    """Response for load balancing strategy configuration."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    previous_strategy: str = Field(..., description="Previous strategy")
    new_strategy: str = Field(..., description="New strategy")
    changed_at: str = Field(..., description="When strategy was changed")
    error_message: Optional[str] = Field(None, description="Error message if configuration failed")


class QueueStatusResponse(BaseModel):
    """Response for queue status."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    queue_length: int = Field(..., description="Current queue length")
    priority_distribution: Dict[str, int] = Field(default_factory=dict, description="Priority distribution")
    oldest_task_age_seconds: float = Field(..., description="Age of oldest task")
    queue_efficiency: float = Field(..., description="Queue efficiency")
    processing_rate: float = Field(..., description="Processing rate")
    estimated_empty_time_seconds: float = Field(..., description="Estimated time to empty queue")
    error_message: Optional[str] = Field(None, description="Error message if status check failed")


class LoadBalancingConfigRequest(BaseModel):
    """Request for load balancing configuration."""
    strategy: Optional[str] = Field(None, description="Load balancing strategy")
    worker_count: Optional[int] = Field(None, ge=1, le=50, description="Worker count")
    max_queue_size: Optional[int] = Field(None, ge=10, le=10000, description="Max queue size")
    enable_auto_scaling: Optional[bool] = Field(None, description="Enable auto scaling")


class LoadBalancingConfigResponse(BaseModel):
    """Response for load balancing configuration."""
    analysis_id: str = Field(..., description="Unique analysis identifier")
    strategy: str = Field(..., description="Configured strategy")
    worker_count: int = Field(..., description="Configured worker count")
    max_queue_size: Optional[int] = Field(None, description="Configured max queue size")
    enable_auto_scaling: bool = Field(..., description="Auto scaling enabled")
    configured_at: str = Field(..., description="When configuration was applied")
    error_message: Optional[str] = Field(None, description="Error message if configuration failed")
