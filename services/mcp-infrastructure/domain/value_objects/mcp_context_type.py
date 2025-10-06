"""MCP Context Type - Value Object.

Defines the types of context that can be stored in the infrastructure service.
"""

from enum import Enum


class MCPContextType(str, Enum):
    """
    Types of MCP context stored in the infrastructure service.
    
    This enum defines the different categories of operational context
    that can be tracked for MCP instances.
    """
    
    INSTANCE = "instance"         # MCP instance metadata and configuration
    TRAINING = "training"         # Training state and progress
    KNOWLEDGE = "knowledge"       # Knowledge graph metadata
    PERFORMANCE = "performance"   # Performance metrics and analytics
    COORDINATION = "coordination" # Cross-service coordination state
    QUERY = "query"              # Query history and patterns
    RELATIONSHIP = "relationship" # Inter-MCP relationships
    ERROR = "error"              # Error tracking and diagnostics
    
    def __str__(self) -> str:
        """String representation of context type."""
        return self.value
    
    @property
    def default_ttl(self) -> int:
        """Get default TTL in seconds for this context type."""
        ttl_map = {
            MCPContextType.INSTANCE: 7200,      # 2 hours
            MCPContextType.TRAINING: 86400,     # 24 hours (longer for training)
            MCPContextType.KNOWLEDGE: 14400,    # 4 hours
            MCPContextType.PERFORMANCE: 3600,   # 1 hour
            MCPContextType.COORDINATION: 7200,  # 2 hours
            MCPContextType.QUERY: 3600,         # 1 hour
            MCPContextType.RELATIONSHIP: 14400, # 4 hours
            MCPContextType.ERROR: 86400,        # 24 hours (keep errors longer)
        }
        return ttl_map.get(self, 3600)  # Default 1 hour

