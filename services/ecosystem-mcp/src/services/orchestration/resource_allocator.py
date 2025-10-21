"""
Resource Allocator

Manages computational resource allocation for sub-job execution.
Tracks memory, CPU, and concurrency limits.
"""

import logging
import psutil
import asyncio
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ResourceAllocation:
    """Resource allocation for a sub-job."""
    sub_job_id: str
    memory_mb: int
    cpu_cores: float
    allocated_at: datetime
    
    def __str__(self) -> str:
        return f"Allocation({self.sub_job_id}: {self.memory_mb}MB, {self.cpu_cores} cores)"


@dataclass
class SystemResources:
    """Current system resource availability."""
    total_memory_mb: int
    available_memory_mb: int
    total_cpu_cores: int
    available_cpu_cores: float
    active_allocations: int
    max_concurrent: int
    
    def can_allocate(self, memory_mb: int, cpu_cores: float) -> bool:
        """Check if resources can be allocated."""
        return (
            self.available_memory_mb >= memory_mb and
            self.available_cpu_cores >= cpu_cores and
            self.active_allocations < self.max_concurrent
        )


class ResourceAllocator:
    """
    Manages resource allocation for sub-job execution.
    
    Features:
    - Memory allocation tracking
    - CPU core allocation
    - Concurrent execution limits
    - Dynamic resource monitoring
    - Automatic cleanup
    """
    
    def __init__(self, max_concurrent: int = 5, memory_per_job_mb: int = 512):
        """
        Initialize resource allocator.
        
        Args:
            max_concurrent: Maximum concurrent sub-jobs
            memory_per_job_mb: Default memory per sub-job (MB)
        """
        self.max_concurrent = max_concurrent
        self.memory_per_job_mb = memory_per_job_mb
        self.allocations: Dict[str, ResourceAllocation] = {}
        
        # Get system resources
        self.total_memory_mb = psutil.virtual_memory().total // (1024 * 1024)
        self.total_cpu_cores = psutil.cpu_count()
        
        # Calculate available resources (reserve 20% for system)
        self.max_memory_mb = int(self.total_memory_mb * 0.8)
        self.max_cpu_cores = max(1, self.total_cpu_cores - 1)  # Reserve 1 core
        
        logger.info(
            f"ResourceAllocator initialized: "
            f"{self.max_memory_mb}MB memory, "
            f"{self.max_cpu_cores} CPU cores, "
            f"max {self.max_concurrent} concurrent"
        )
    
    async def allocate(self, sub_job_id: str, file_count: int) -> Optional[ResourceAllocation]:
        """
        Allocate resources for a sub-job.
        
        Args:
            sub_job_id: Sub-job ID
            file_count: Number of files in sub-job
        
        Returns:
            ResourceAllocation if successful, None if insufficient resources
        """
        # Check if already allocated
        if sub_job_id in self.allocations:
            logger.warning(f"⚠️  Sub-job {sub_job_id} already has allocation")
            return self.allocations[sub_job_id]
        
        # Check concurrent limit
        if len(self.allocations) >= self.max_concurrent:
            logger.debug(f"⏳ Max concurrent limit reached ({self.max_concurrent})")
            return None
        
        # Calculate required resources based on file count
        # More files = more memory needed
        memory_mb = min(
            self.memory_per_job_mb + (file_count // 100) * 50,  # +50MB per 100 files
            self.max_memory_mb // self.max_concurrent  # Don't exceed fair share
        )
        
        cpu_cores = self.max_cpu_cores / self.max_concurrent  # Fair share
        
        # Check if resources available
        resources = await self.get_available_resources()
        if not resources.can_allocate(memory_mb, cpu_cores):
            logger.debug(
                f"⏳ Insufficient resources: need {memory_mb}MB, {cpu_cores} cores, "
                f"have {resources.available_memory_mb}MB, {resources.available_cpu_cores} cores"
            )
            return None
        
        # Create allocation
        allocation = ResourceAllocation(
            sub_job_id=sub_job_id,
            memory_mb=memory_mb,
            cpu_cores=cpu_cores,
            allocated_at=datetime.utcnow()
        )
        
        self.allocations[sub_job_id] = allocation
        
        logger.info(f"✅ Allocated resources: {allocation}")
        
        return allocation
    
    async def release(self, sub_job_id: str) -> None:
        """
        Release resources for a sub-job.
        
        Args:
            sub_job_id: Sub-job ID
        """
        if sub_job_id in self.allocations:
            allocation = self.allocations.pop(sub_job_id)
            logger.info(f"🗑️  Released resources: {allocation}")
        else:
            logger.warning(f"⚠️  No allocation found for sub-job {sub_job_id}")
    
    async def get_available_resources(self) -> SystemResources:
        """
        Get current available system resources.
        
        Returns:
            SystemResources with current availability
        """
        # Calculate allocated resources
        allocated_memory = sum(a.memory_mb for a in self.allocations.values())
        allocated_cpu = sum(a.cpu_cores for a in self.allocations.values())
        
        # Get current system memory
        mem = psutil.virtual_memory()
        current_available_mb = mem.available // (1024 * 1024)
        
        # Available = min(system available, max - allocated)
        available_memory_mb = min(
            current_available_mb,
            self.max_memory_mb - allocated_memory
        )
        
        available_cpu_cores = self.max_cpu_cores - allocated_cpu
        
        return SystemResources(
            total_memory_mb=self.total_memory_mb,
            available_memory_mb=max(0, available_memory_mb),
            total_cpu_cores=self.total_cpu_cores,
            available_cpu_cores=max(0, available_cpu_cores),
            active_allocations=len(self.allocations),
            max_concurrent=self.max_concurrent
        )
    
    async def get_allocation(self, sub_job_id: str) -> Optional[ResourceAllocation]:
        """
        Get allocation for a sub-job.
        
        Args:
            sub_job_id: Sub-job ID
        
        Returns:
            ResourceAllocation if exists, None otherwise
        """
        return self.allocations.get(sub_job_id)
    
    async def wait_for_resources(
        self,
        sub_job_id: str,
        file_count: int,
        timeout: float = 300.0
    ) -> Optional[ResourceAllocation]:
        """
        Wait for resources to become available.
        
        Args:
            sub_job_id: Sub-job ID
            file_count: Number of files
            timeout: Max wait time in seconds
        
        Returns:
            ResourceAllocation if successful, None if timeout
        """
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # Try to allocate
            allocation = await self.allocate(sub_job_id, file_count)
            if allocation:
                return allocation
            
            # Check timeout
            elapsed = asyncio.get_event_loop().time() - start_time
            if elapsed >= timeout:
                logger.warning(f"⏰ Resource allocation timeout for {sub_job_id}")
                return None
            
            # Wait before retry
            await asyncio.sleep(1.0)
    
    def get_stats(self) -> Dict:
        """Get resource allocation statistics."""
        resources = asyncio.run(self.get_available_resources())
        
        return {
            "total_memory_mb": resources.total_memory_mb,
            "available_memory_mb": resources.available_memory_mb,
            "total_cpu_cores": resources.total_cpu_cores,
            "available_cpu_cores": resources.available_cpu_cores,
            "active_allocations": resources.active_allocations,
            "max_concurrent": resources.max_concurrent,
            "utilization_pct": (resources.active_allocations / resources.max_concurrent) * 100
        }
    
    async def cleanup(self) -> None:
        """Clean up all allocations."""
        logger.info(f"🧹 Cleaning up {len(self.allocations)} allocations")
        self.allocations.clear()


# Singleton instance
_resource_allocator_instance = None

def get_resource_allocator(
    max_concurrent: int = 5,
    memory_per_job_mb: int = 512
) -> ResourceAllocator:
    """Get singleton resource allocator instance."""
    global _resource_allocator_instance
    if _resource_allocator_instance is None:
        _resource_allocator_instance = ResourceAllocator(max_concurrent, memory_per_job_mb)
    return _resource_allocator_instance

