"""Resource Limits Value Object."""

from dataclasses import dataclass


@dataclass(frozen=True)  # Immutable value object
class ResourceLimits:
    """
    Value object representing resource limits for an MCP container.
    
    Immutable resource allocation settings.
    """
    
    cpu_limit: float  # CPU cores (e.g., 2.0)
    memory_limit_mb: int  # RAM in MB (e.g., 4096)
    disk_limit_mb: int  # Disk space in MB (e.g., 10240)
    
    def __post_init__(self):
        """Validate resource limits."""
        if self.cpu_limit <= 0:
            raise ValueError(f"CPU limit must be positive: {self.cpu_limit}")
        
        if self.memory_limit_mb <= 0:
            raise ValueError(f"Memory limit must be positive: {self.memory_limit_mb}")
        
        if self.disk_limit_mb <= 0:
            raise ValueError(f"Disk limit must be positive: {self.disk_limit_mb}")
        
        # Reasonable limits
        if self.cpu_limit > 32:
            raise ValueError(f"CPU limit too high: {self.cpu_limit}. Max 32 cores.")
        
        if self.memory_limit_mb > 128 * 1024:  # 128 GB
            raise ValueError(f"Memory limit too high: {self.memory_limit_mb}. Max 128GB.")
    
    def memory_limit_gb(self) -> float:
        """Get memory limit in GB."""
        return self.memory_limit_mb / 1024.0
    
    def disk_limit_gb(self) -> float:
        """Get disk limit in GB."""
        return self.disk_limit_mb / 1024.0
    
    def is_within_budget(self, available_cpu: float, available_memory_mb: int) -> bool:
        """Check if limits fit within available resources."""
        return (
            self.cpu_limit <= available_cpu and
            self.memory_limit_mb <= available_memory_mb
        )
    
    def scale(self, factor: float) -> "ResourceLimits":
        """Create new limits scaled by factor (immutable pattern)."""
        if factor <= 0:
            raise ValueError(f"Scale factor must be positive: {factor}")
        
        return ResourceLimits(
            cpu_limit=self.cpu_limit * factor,
            memory_limit_mb=int(self.memory_limit_mb * factor),
            disk_limit_mb=int(self.disk_limit_mb * factor)
        )
    
    def __str__(self) -> str:
        return f"ResourceLimits(cpu={self.cpu_limit}, mem={self.memory_limit_gb():.1f}GB, disk={self.disk_limit_gb():.1f}GB)"


# Preset resource configurations
def small_resources() -> ResourceLimits:
    """Small MCP instance (for testing)."""
    return ResourceLimits(
        cpu_limit=0.5,
        memory_limit_mb=512,  # 512 MB
        disk_limit_mb=1024    # 1 GB
    )


def medium_resources() -> ResourceLimits:
    """Medium MCP instance (default)."""
    return ResourceLimits(
        cpu_limit=2.0,
        memory_limit_mb=4096,  # 4 GB
        disk_limit_mb=10240    # 10 GB
    )


def large_resources() -> ResourceLimits:
    """Large MCP instance (production)."""
    return ResourceLimits(
        cpu_limit=4.0,
        memory_limit_mb=8192,  # 8 GB
        disk_limit_mb=20480    # 20 GB
    )

