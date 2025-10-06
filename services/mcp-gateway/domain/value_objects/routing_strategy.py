"""Routing Strategy Value Object."""

from enum import Enum


class RoutingStrategy(str, Enum):
    """
    Strategy for routing requests to MCP instances.
    
    Different strategies optimize for different objectives.
    """
    
    ROUND_ROBIN = "round_robin"        # Distribute evenly across all instances
    LEAST_LOADED = "least_loaded"      # Route to instance with lowest load
    RANDOM = "random"                  # Random selection (good for load spreading)
    STICKY_SESSION = "sticky_session"  # Route to same instance for session
    CLOSEST = "closest"                # Route to geographically/network closest
    PRIORITY = "priority"              # Route based on instance priority/tier
    
    @property
    def requires_session_affinity(self) -> bool:
        """Check if strategy requires session tracking."""
        return self == RoutingStrategy.STICKY_SESSION
    
    @property
    def requires_load_metrics(self) -> bool:
        """Check if strategy requires real-time load metrics."""
        return self in {
            RoutingStrategy.LEAST_LOADED,
            RoutingStrategy.PRIORITY,
        }

