"""Worker Pool Repository Interface."""

from abc import ABC, abstractmethod
from typing import List, Optional

from services.training_coordinator.domain.entities.worker_pool import WorkerPool
from services.training_coordinator.domain.value_objects.worker_type import WorkerType


class WorkerPoolRepository(ABC):
    """
    Repository for worker pool persistence.
    
    Manages storage and retrieval of worker pools.
    """
    
    @abstractmethod
    async def save(self, pool: WorkerPool) -> None:
        """Save worker pool."""
        pass
    
    @abstractmethod
    async def get_by_id(self, pool_id: str) -> Optional[WorkerPool]:
        """Get pool by ID."""
        pass
    
    @abstractmethod
    async def get_by_worker_type(self, worker_type: WorkerType) -> Optional[WorkerPool]:
        """Get pool by worker type."""
        pass
    
    @abstractmethod
    async def list_all(self) -> List[WorkerPool]:
        """List all worker pools."""
        pass
    
    @abstractmethod
    async def list_healthy(self) -> List[WorkerPool]:
        """List healthy worker pools."""
        pass
    
    @abstractmethod
    async def delete(self, pool_id: str) -> bool:
        """Delete pool."""
        pass

