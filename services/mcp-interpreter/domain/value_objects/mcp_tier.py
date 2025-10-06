"""MCP Tier Value Object."""

from enum import Enum


class MCPTier(int, Enum):
    """
    Hierarchical tiers for MCP organization.
    
    Lower tier = more specific context
    Higher tier = more general context
    """
    
    CLIENT = 0          # Client-specific MCP (most specific)
    PROJECT = 1         # Project-specific MCP
    TEAM = 2            # Team-specific MCP
    COMPANY = 3         # Company-wide MCP
    ECOSYSTEM = 4       # Ecosystem-wide MCP (most general)
    
    @property
    def name_str(self) -> str:
        """Get human-readable name."""
        names = {
            MCPTier.CLIENT: "Client",
            MCPTier.PROJECT: "Project",
            MCPTier.TEAM: "Team",
            MCPTier.COMPANY: "Company",
            MCPTier.ECOSYSTEM: "Ecosystem",
        }
        return names.get(self, "Unknown")
    
    @property
    def specificity(self) -> float:
        """
        Get specificity score (0.0-1.0).
        Higher = more specific/focused
        """
        scores = {
            MCPTier.CLIENT: 1.0,
            MCPTier.PROJECT: 0.8,
            MCPTier.TEAM: 0.6,
            MCPTier.COMPANY: 0.4,
            MCPTier.ECOSYSTEM: 0.2,
        }
        return scores.get(self, 0.5)
    
    @property
    def is_dynamic(self) -> bool:
        """
        Check if MCPs at this tier are dynamically provisioned.
        Client and Project tiers are typically dynamic.
        """
        return self in {MCPTier.CLIENT, MCPTier.PROJECT}
    
    @property
    def typical_size_mb(self) -> int:
        """Get typical MCP size in MB for this tier."""
        sizes = {
            MCPTier.CLIENT: 100,      # ~100MB per client
            MCPTier.PROJECT: 500,     # ~500MB per project
            MCPTier.TEAM: 1000,       # ~1GB per team
            MCPTier.COMPANY: 5000,    # ~5GB company-wide
            MCPTier.ECOSYSTEM: 10000, # ~10GB ecosystem
        }
        return sizes.get(self, 500)
    
    def should_query_before(self, other: "MCPTier") -> bool:
        """
        Determine if this tier should be queried before another.
        More specific tiers (lower value) should be queried first.
        """
        return self.value < other.value
    
    @classmethod
    def from_entity_types(cls, entity_types: set) -> "MCPTier":
        """
        Infer appropriate MCP tier from entity types in query.
        
        Args:
            entity_types: Set of EntityType values
        
        Returns:
            Appropriate MCPTier
        """
        from services.mcp_interpreter.domain.value_objects.entity_type import EntityType
        
        # Check for client-specific entities
        if EntityType.CLIENT in entity_types:
            return cls.CLIENT
        
        # Check for project-specific entities
        if EntityType.PROJECT in entity_types or EntityType.FEATURE in entity_types:
            return cls.PROJECT
        
        # Check for team-specific entities
        if EntityType.TEAM in entity_types or EntityType.SPRINT in entity_types:
            return cls.TEAM
        
        # Check for company-specific entities
        if EntityType.COMPANY in entity_types or EntityType.DEPARTMENT in entity_types:
            return cls.COMPANY
        
        # Default to ecosystem
        return cls.ECOSYSTEM

