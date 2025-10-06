"""MCP Instance Entity - Domain Layer."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import uuid

from services.mcp_gateway.domain.value_objects.mcp_instance_status import MCPInstanceStatus


@dataclass
class MCPInstance:
    """
    Represents a registered MCP instance in the Gateway's registry.
    
    This is a core aggregate root tracking MCP availability, health,
    and routing metrics.
    """
    
    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    mcp_id: str = ""  # Unique MCP identifier (e.g., "client-acme-mcp")
    name: str = ""  # Human-readable name
    
    # Network location
    host: str = ""  # Hostname or IP
    port: int = 0  # Port number
    base_url: str = ""  # Complete base URL (e.g., "http://mcp-instance:3000")
    
    # Status and health
    status: MCPInstanceStatus = MCPInstanceStatus.UNKNOWN
    health_check_url: str = ""  # Health check endpoint
    last_health_check: Optional[datetime] = None
    consecutive_failures: int = 0
    
    # Load metrics
    active_requests: int = 0
    total_requests: int = 0
    average_response_time_ms: float = 0.0
    
    # Routing metadata
    tier: int = 0  # MCP tier (0=client, 1=project, 2=team, etc.)
    priority: int = 100  # Routing priority (higher = preferred)
    weight: int = 100  # Load balancing weight
    max_concurrent_requests: int = 100
    
    # Lifecycle
    registered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_seen_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    version: int = 1
    
    # Additional metadata
    tags: list[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate the instance after initialization."""
        if not self.mcp_id:
            raise ValueError("MCPInstance must have an mcp_id")
        if not self.host:
            raise ValueError("MCPInstance must have a host")
        if self.port <= 0:
            raise ValueError("MCPInstance must have a valid port")
        
        # Auto-generate base_url if not provided
        if not self.base_url:
            self.base_url = f"http://{self.host}:{self.port}"
        
        # Auto-generate health check URL if not provided
        if not self.health_check_url:
            self.health_check_url = f"{self.base_url}/health"
    
    def update_health(self, is_healthy: bool) -> None:
        """
        Update health status based on health check result.
        
        Args:
            is_healthy: Whether the health check passed
        """
        if is_healthy:
            self.consecutive_failures = 0
            if self.status == MCPInstanceStatus.UNHEALTHY:
                self.status = MCPInstanceStatus.AVAILABLE
        else:
            self.consecutive_failures += 1
            if self.consecutive_failures >= 3:
                self.status = MCPInstanceStatus.UNHEALTHY
        
        self.last_health_check = datetime.now(timezone.utc)
        self.last_seen_at = datetime.now(timezone.utc)
        self.version += 1
    
    def mark_request_start(self) -> None:
        """Mark that a request has started."""
        self.active_requests += 1
        self.total_requests += 1
        
        # Update status based on load
        if self.active_requests >= self.max_concurrent_requests:
            self.status = MCPInstanceStatus.BUSY
    
    def mark_request_end(self, response_time_ms: float) -> None:
        """
        Mark that a request has completed.
        
        Args:
            response_time_ms: Request duration in milliseconds
        """
        if self.active_requests > 0:
            self.active_requests -= 1
        
        # Update average response time (exponential moving average)
        alpha = 0.3  # Smoothing factor
        self.average_response_time_ms = (
            alpha * response_time_ms + 
            (1 - alpha) * self.average_response_time_ms
        )
        
        # Update status if no longer busy
        if self.active_requests < self.max_concurrent_requests * 0.8:
            if self.status == MCPInstanceStatus.BUSY:
                self.status = MCPInstanceStatus.AVAILABLE
        
        self.last_seen_at = datetime.now(timezone.utc)
    
    def set_draining(self) -> None:
        """Set instance to draining mode (no new requests)."""
        self.status = MCPInstanceStatus.DRAINING
        self.version += 1
    
    def is_available_for_routing(self) -> bool:
        """Check if instance can accept new requests."""
        return (
            self.status.is_routable and
            self.active_requests < self.max_concurrent_requests
        )
    
    def get_load_factor(self) -> float:
        """
        Calculate current load factor (0.0 = idle, 1.0 = full capacity).
        
        Returns:
            Load factor between 0.0 and 1.0
        """
        if self.max_concurrent_requests == 0:
            return 0.0
        return min(1.0, self.active_requests / self.max_concurrent_requests)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "id": self.id,
            "mcp_id": self.mcp_id,
            "name": self.name,
            "host": self.host,
            "port": self.port,
            "base_url": self.base_url,
            "status": self.status.value,
            "health_check_url": self.health_check_url,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "consecutive_failures": self.consecutive_failures,
            "active_requests": self.active_requests,
            "total_requests": self.total_requests,
            "average_response_time_ms": self.average_response_time_ms,
            "tier": self.tier,
            "priority": self.priority,
            "weight": self.weight,
            "max_concurrent_requests": self.max_concurrent_requests,
            "registered_at": self.registered_at.isoformat(),
            "last_seen_at": self.last_seen_at.isoformat(),
            "version": self.version,
            "tags": self.tags,
            "metadata": self.metadata,
            "load_factor": self.get_load_factor(),
            "is_available": self.is_available_for_routing(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPInstance":
        """Create instance from dictionary."""
        return cls(
            id=data["id"],
            mcp_id=data["mcp_id"],
            name=data.get("name", ""),
            host=data["host"],
            port=data["port"],
            base_url=data.get("base_url", ""),
            status=MCPInstanceStatus(data.get("status", "unknown")),
            health_check_url=data.get("health_check_url", ""),
            last_health_check=datetime.fromisoformat(data["last_health_check"]) if data.get("last_health_check") else None,
            consecutive_failures=data.get("consecutive_failures", 0),
            active_requests=data.get("active_requests", 0),
            total_requests=data.get("total_requests", 0),
            average_response_time_ms=data.get("average_response_time_ms", 0.0),
            tier=data.get("tier", 0),
            priority=data.get("priority", 100),
            weight=data.get("weight", 100),
            max_concurrent_requests=data.get("max_concurrent_requests", 100),
            registered_at=datetime.fromisoformat(data["registered_at"]),
            last_seen_at=datetime.fromisoformat(data["last_seen_at"]),
            version=data.get("version", 1),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
        )
    
    def __eq__(self, other) -> bool:
        """Check equality based on ID."""
        if not isinstance(other, MCPInstance):
            return False
        return self.id == other.id
    
    def __hash__(self) -> int:
        """Hash based on ID."""
        return hash(self.id)
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"MCPInstance(id={self.id}, mcp_id={self.mcp_id}, "
            f"status={self.status}, load={self.get_load_factor():.2f})"
        )

