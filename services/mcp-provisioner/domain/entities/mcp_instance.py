"""MCP Instance Entity - Aggregate Root."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Optional, Dict
from uuid import uuid4

from services.mcp_provisioner.domain.value_objects.mcp_state import MCPState, MCPStateEnum, cold_state
from services.mcp_provisioner.domain.value_objects.mcp_config import MCPConfig
from services.mcp_provisioner.domain.value_objects.resource_limits import ResourceLimits, medium_resources


@dataclass
class MCPInstance:
    """
    Domain entity representing an MCP instance.
    
    This is the aggregate root for MCP provisioning.
    Contains business logic for lifecycle management.
    """
    
    # Identity
    mcp_id: str = field(default_factory=lambda: f"mcp-{uuid4().hex[:8]}")
    
    # State
    state: MCPState = field(default_factory=cold_state)
    
    # Configuration
    config: MCPConfig = field(default_factory=lambda: None)
    resource_limits: ResourceLimits = field(default_factory=medium_resources)
    
    # Runtime information
    container_id: Optional[str] = None
    endpoint: Optional[str] = None  # http://container:port
    host_port: Optional[int] = None  # External port mapping
    
    # Metadata and additional information
    metadata: Dict[str, any] = field(default_factory=dict)
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_health_check: Optional[datetime] = None
    last_query_time: Optional[datetime] = None
    
    # Metrics
    query_count: int = 0
    total_cpu_time: float = 0.0
    total_memory_mb: float = 0.0
    
    # Health
    health_check_failures: int = 0
    is_healthy: bool = True
    
    def __post_init__(self):
        """Validate entity after initialization."""
        if not self.mcp_id:
            raise ValueError("MCP ID cannot be empty")
        
        if self.config is None:
            # Set default config if not provided
            from domain.value_objects.mcp_config import default_config_for_tier
            object.__setattr__(self, 'config', default_config_for_tier(4, self.mcp_id))
    
    # === State Transition Methods (Business Logic) ===
    
    def start_provisioning(self) -> None:
        """
        Transition from COLD to WARMING state.
        
        Business rule: Can only provision from COLD state.
        """
        if self.state.state != MCPStateEnum.COLD:
            raise ValueError(
                f"Cannot provision MCP in {self.state} state. Must be COLD."
            )
        
        self._transition_to(MCPState(MCPStateEnum.WARMING))
    
    def mark_as_hot(self, container_id: str, endpoint: str, host_port: int) -> None:
        """
        Transition from WARMING to HOT state.
        
        Business rule: Can only go HOT from WARMING state.
        """
        if self.state.state != MCPStateEnum.WARMING:
            raise ValueError(
                f"Cannot mark as HOT from {self.state} state. Must be WARMING."
            )
        
        self.container_id = container_id
        self.endpoint = endpoint
        self.host_port = host_port
        self.last_health_check = datetime.utcnow()
        self.is_healthy = True
        self.health_check_failures = 0
        
        self._transition_to(MCPState(MCPStateEnum.HOT))
    
    def start_cooling(self) -> None:
        """
        Transition from HOT to COOLING state.
        
        Business rule: Begin graceful shutdown.
        """
        if self.state.state != MCPStateEnum.HOT:
            raise ValueError(
                f"Cannot cool down from {self.state} state. Must be HOT."
            )
        
        self._transition_to(MCPState(MCPStateEnum.COOLING))
    
    def mark_as_cold(self) -> None:
        """
        Transition from COOLING to COLD state.
        
        Business rule: Complete shutdown.
        """
        if self.state.state != MCPStateEnum.COOLING:
            raise ValueError(
                f"Cannot mark as COLD from {self.state} state. Must be COOLING."
            )
        
        # Clear runtime information
        self.container_id = None
        self.endpoint = None
        self.host_port = None
        
        self._transition_to(cold_state())
    
    def mark_as_failed(self, reason: str = "") -> None:
        """
        Transition to FAILED state from any state.
        
        Business rule: Failure can happen from any state.
        """
        self.is_healthy = False
        self._transition_to(MCPState(MCPStateEnum.FAILED))
    
    def recover_from_failure(self) -> None:
        """
        Recover from FAILED state to COLD.
        
        Business rule: Manual recovery only.
        """
        if self.state.state != MCPStateEnum.FAILED:
            raise ValueError(
                f"Cannot recover from {self.state} state. Must be FAILED."
            )
        
        self.is_healthy = True
        self.health_check_failures = 0
        self.container_id = None
        self.endpoint = None
        self.host_port = None
        
        self._transition_to(cold_state())
    
    # === Query Management ===
    
    def record_query(self) -> None:
        """
        Record that a query was processed.
        
        Business rule: Can only query HOT instances.
        """
        if not self.state.is_active():
            raise ValueError(
                f"Cannot query MCP in {self.state} state. Must be HOT."
            )
        
        self.query_count += 1
        self.last_query_time = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def is_idle(self, idle_threshold_minutes: int = 15) -> bool:
        """
        Check if MCP has been idle (no queries) for threshold time.
        
        Business rule for auto-shutdown.
        """
        if not self.last_query_time:
            # Never queried
            return True
        
        idle_duration = datetime.utcnow() - self.last_query_time
        return idle_duration > timedelta(minutes=idle_threshold_minutes)
    
    # === Health Management ===
    
    def update_health_status(self, is_healthy: bool) -> None:
        """
        Update health status from health check.
        
        Business rule: Track failures, mark as FAILED after threshold.
        """
        self.last_health_check = datetime.utcnow()
        self.is_healthy = is_healthy
        
        if not is_healthy:
            self.health_check_failures += 1
            
            # Business rule: 3 consecutive failures = FAILED state
            if self.health_check_failures >= 3:
                self.mark_as_failed("Too many health check failures")
        else:
            self.health_check_failures = 0
        
        self.updated_at = datetime.utcnow()
    
    def needs_health_check(self, interval_seconds: int = 30) -> bool:
        """
        Check if health check is needed.
        
        Business rule: Check every interval_seconds.
        """
        if not self.state.is_active():
            return False
        
        if not self.last_health_check:
            return True
        
        time_since_check = datetime.utcnow() - self.last_health_check
        return time_since_check > timedelta(seconds=interval_seconds)
    
    # === Resource Management ===
    
    def update_resource_usage(self, cpu_time: float, memory_mb: float) -> None:
        """Update resource usage metrics."""
        self.total_cpu_time += cpu_time
        self.total_memory_mb = memory_mb
        self.updated_at = datetime.utcnow()
    
    def is_overloaded(self, cpu_threshold: float = 0.8, memory_threshold: float = 0.8) -> bool:
        """
        Check if instance is overloaded.
        
        Business rule for scaling decisions.
        """
        cpu_usage = self.total_cpu_time / self.resource_limits.cpu_limit
        memory_usage = self.total_memory_mb / self.resource_limits.memory_limit_mb
        
        return cpu_usage > cpu_threshold or memory_usage > memory_threshold
    
    # === Helper Methods ===
    
    def _transition_to(self, new_state: MCPState) -> None:
        """
        Internal method to transition state.
        
        Validates transition and updates metadata.
        """
        if not self.state.can_transition_to(new_state):
            raise ValueError(
                f"Invalid state transition from {self.state} to {new_state}"
            )
        
        self.state = new_state
        self.updated_at = datetime.utcnow()
    
    def to_dict(self) -> Dict:
        """Convert entity to dictionary for serialization."""
        return {
            "mcp_id": self.mcp_id,
            "state": self.state.state.value,
            "tier": self.config.tier,
            "tier_name": self.config.tier_name(),
            "container_id": self.container_id,
            "endpoint": self.endpoint,
            "host_port": self.host_port,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "last_query_time": self.last_query_time.isoformat() if self.last_query_time else None,
            "query_count": self.query_count,
            "is_healthy": self.is_healthy,
            "health_check_failures": self.health_check_failures,
            "resource_limits": {
                "cpu": self.resource_limits.cpu_limit,
                "memory_mb": self.resource_limits.memory_limit_mb,
                "disk_mb": self.resource_limits.disk_limit_mb
            }
        }
    
    def __str__(self) -> str:
        return f"MCPInstance({self.mcp_id}, state={self.state}, tier={self.config.tier})"
    
    def __repr__(self) -> str:
        return self.__str__()

