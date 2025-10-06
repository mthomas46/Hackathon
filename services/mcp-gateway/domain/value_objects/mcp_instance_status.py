"""MCP Instance Status Value Object."""

from enum import Enum


class MCPInstanceStatus(str, Enum):
    """
    Status of an MCP instance from Gateway's perspective.
    
    This reflects the operational state as tracked by the Gateway
    for routing decisions.
    """
    
    # Instance states
    AVAILABLE = "available"      # Ready to accept requests
    BUSY = "busy"                # At capacity, prefer other instances
    DRAINING = "draining"        # Finishing existing requests, no new requests
    UNHEALTHY = "unhealthy"      # Failed health checks, circuit open
    UNKNOWN = "unknown"          # Status not yet determined
    OFFLINE = "offline"          # Instance not responding
    
    @property
    def is_routable(self) -> bool:
        """Check if the instance can receive new requests."""
        return self in {
            MCPInstanceStatus.AVAILABLE,
            MCPInstanceStatus.BUSY,  # Can route but with lower priority
        }
    
    @property
    def is_healthy(self) -> bool:
        """Check if the instance is healthy."""
        return self in {
            MCPInstanceStatus.AVAILABLE,
            MCPInstanceStatus.BUSY,
            MCPInstanceStatus.DRAINING,
        }

