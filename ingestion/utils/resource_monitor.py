"""
Resource monitoring for dynamic batch sizing.
"""
import psutil
import asyncio
from typing import Dict, Any
from dataclasses import dataclass


@dataclass
class ResourceMetrics:
    """Current resource usage metrics."""
    cpu_percent: float
    memory_percent: float
    memory_available_gb: float
    suggested_batch_size: int
    suggested_concurrency: int


class ResourceMonitor:
    """Monitor system resources and suggest optimal batch sizes."""
    
    def __init__(self):
        self.process = psutil.Process()
        self.baseline_memory_mb = None
    
    def get_metrics(self) -> ResourceMetrics:
        """Get current resource metrics."""
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_gb = memory.available / (1024**3)
        
        # Dynamic batch sizing based on available resources
        if memory_available_gb > 8:
            batch_size = 20
            concurrency = 10
        elif memory_available_gb > 4:
            batch_size = 10
            concurrency = 5
        elif memory_available_gb > 2:
            batch_size = 5
            concurrency = 3
        else:
            batch_size = 3
            concurrency = 2
        
        # Adjust for CPU
        if cpu_percent > 80:
            batch_size = max(2, batch_size // 2)
            concurrency = max(2, concurrency // 2)
        
        return ResourceMetrics(
            cpu_percent=cpu_percent,
            memory_percent=memory_percent,
            memory_available_gb=memory_available_gb,
            suggested_batch_size=batch_size,
            suggested_concurrency=concurrency
        )
    
    def get_memory_usage_mb(self) -> float:
        """Get current process memory usage in MB."""
        return self.process.memory_info().rss / (1024 * 1024)
    
    def set_baseline(self):
        """Set baseline memory usage."""
        self.baseline_memory_mb = self.get_memory_usage_mb()
    
    def get_memory_delta_mb(self) -> float:
        """Get memory usage increase since baseline."""
        if self.baseline_memory_mb is None:
            return 0.0
        return self.get_memory_usage_mb() - self.baseline_memory_mb

