"""Registry Status Value Object."""

from enum import Enum


class RegistryStatus(str, Enum):
    """
    Status of an MCP in the registry.
    
    Tracks the lifecycle and availability of registered MCPs.
    """
    
    PENDING = "pending"
    """MCP is being uploaded/imported."""
    
    AVAILABLE = "available"
    """MCP is fully available for use."""
    
    DEPRECATED = "deprecated"
    """MCP is deprecated, not recommended for new use."""
    
    ARCHIVED = "archived"
    """MCP is archived, read-only access."""
    
    CORRUPTED = "corrupted"
    """MCP has integrity issues."""
    
    QUARANTINED = "quarantined"
    """MCP is quarantined pending security review."""
    
    DELETED = "deleted"
    """MCP is marked for deletion."""
    
    @property
    def is_usable(self) -> bool:
        """Check if MCP can be used."""
        return self in {
            RegistryStatus.AVAILABLE,
            RegistryStatus.DEPRECATED,  # Can still use, just not recommended
        }
    
    @property
    def is_terminal(self) -> bool:
        """Check if status is terminal (no further transitions)."""
        return self in {
            RegistryStatus.DELETED,
        }
    
    @property
    def requires_review(self) -> bool:
        """Check if status requires human review."""
        return self in {
            RegistryStatus.CORRUPTED,
            RegistryStatus.QUARANTINED,
        }
    
    def can_transition_to(self, new_status: "RegistryStatus") -> bool:
        """
        Check if transition to new status is valid.
        
        Args:
            new_status: Target status
        
        Returns:
            True if transition is allowed
        """
        # Terminal states cannot transition
        if self.is_terminal:
            return False
        
        # Valid transitions
        valid_transitions = {
            RegistryStatus.PENDING: {
                RegistryStatus.AVAILABLE,
                RegistryStatus.CORRUPTED,
                RegistryStatus.QUARANTINED,
            },
            RegistryStatus.AVAILABLE: {
                RegistryStatus.DEPRECATED,
                RegistryStatus.ARCHIVED,
                RegistryStatus.QUARANTINED,
                RegistryStatus.DELETED,
            },
            RegistryStatus.DEPRECATED: {
                RegistryStatus.ARCHIVED,
                RegistryStatus.DELETED,
            },
            RegistryStatus.ARCHIVED: {
                RegistryStatus.DELETED,
            },
            RegistryStatus.CORRUPTED: {
                RegistryStatus.QUARANTINED,
                RegistryStatus.DELETED,
            },
            RegistryStatus.QUARANTINED: {
                RegistryStatus.AVAILABLE,  # After review
                RegistryStatus.DELETED,
            },
        }
        
        allowed = valid_transitions.get(self, set())
        return new_status in allowed

