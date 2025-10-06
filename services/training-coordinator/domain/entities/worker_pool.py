"""Worker Pool Entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

from services.training_coordinator.domain.value_objects.worker_type import WorkerType


@dataclass
class WorkerPool:
    """
    Pool of workers for a specific worker type.
    
    Manages available workers and their capacity.
    """
    
    # Identity
    pool_id: str
    worker_type: WorkerType
    
    # Capacity
    max_workers: int
    active_workers: int = 0
    available_capacity: int = 0
    
    # Worker tracking
    worker_ids: List[str] = field(default_factory=list)
    busy_worker_ids: List[str] = field(default_factory=list)
    
    # Performance metrics
    jobs_completed: int = 0
    jobs_failed: int = 0
    total_processing_time_seconds: float = 0.0
    
    # Health
    is_healthy: bool = True
    last_health_check: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate pool."""
        if not self.pool_id:
            raise ValueError("Pool ID is required")
        if self.max_workers < 1:
            raise ValueError("Max workers must be at least 1")
        
        self.available_capacity = self.max_workers - self.active_workers
    
    def can_accept_job(self) -> bool:
        """Check if pool can accept a new job."""
        return self.is_healthy and self.available_capacity > 0
    
    def allocate_worker(self, worker_id: str) -> bool:
        """
        Allocate a worker for a job.
        
        Args:
            worker_id: Worker ID
        
        Returns:
            True if allocated successfully
        """
        if not self.can_accept_job():
            return False
        
        if worker_id not in self.worker_ids:
            self.worker_ids.append(worker_id)
        
        if worker_id not in self.busy_worker_ids:
            self.busy_worker_ids.append(worker_id)
        
        self.active_workers = len(self.busy_worker_ids)
        self.available_capacity = self.max_workers - self.active_workers
        
        return True
    
    def release_worker(self, worker_id: str, success: bool, processing_time: float) -> None:
        """
        Release a worker after job completion.
        
        Args:
            worker_id: Worker ID
            success: Whether job succeeded
            processing_time: Time taken in seconds
        """
        if worker_id in self.busy_worker_ids:
            self.busy_worker_ids.remove(worker_id)
        
        self.active_workers = len(self.busy_worker_ids)
        self.available_capacity = self.max_workers - self.active_workers
        
        # Update metrics
        if success:
            self.jobs_completed += 1
        else:
            self.jobs_failed += 1
        
        self.total_processing_time_seconds += processing_time
    
    def get_average_processing_time(self) -> float:
        """Get average processing time per job."""
        total_jobs = self.jobs_completed + self.jobs_failed
        if total_jobs == 0:
            return 0.0
        return self.total_processing_time_seconds / total_jobs
    
    def get_success_rate(self) -> float:
        """Get job success rate."""
        total_jobs = self.jobs_completed + self.jobs_failed
        if total_jobs == 0:
            return 0.0
        return self.jobs_completed / total_jobs
    
    def update_health(self, is_healthy: bool) -> None:
        """Update pool health status."""
        self.is_healthy = is_healthy
        self.last_health_check = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "pool_id": self.pool_id,
            "worker_type": self.worker_type.value,
            "max_workers": self.max_workers,
            "active_workers": self.active_workers,
            "available_capacity": self.available_capacity,
            "worker_ids": self.worker_ids,
            "busy_worker_ids": self.busy_worker_ids,
            "jobs_completed": self.jobs_completed,
            "jobs_failed": self.jobs_failed,
            "total_processing_time_seconds": self.total_processing_time_seconds,
            "average_processing_time": self.get_average_processing_time(),
            "success_rate": self.get_success_rate(),
            "is_healthy": self.is_healthy,
            "last_health_check": self.last_health_check.isoformat(),
            "metadata": self.metadata,
        }

