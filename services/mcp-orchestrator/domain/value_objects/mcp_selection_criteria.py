"""MCP Selection Criteria Value Object."""

from dataclasses import dataclass
from typing import List, Optional, Set


@dataclass(frozen=True)
class MCPSelectionCriteria:
    """
    Criteria for selecting which MCPs to query.
    
    Used by the orchestrator to determine which MCP instances
    are relevant for a given query.
    """
    
    # Required tiers (from interpreter)
    required_tiers: List[int]
    
    # Optional filters
    client_ids: Optional[Set[str]] = None
    project_ids: Optional[Set[str]] = None
    team_ids: Optional[Set[str]] = None
    
    # Temporal filters
    include_historical: bool = True
    time_range_days: Optional[int] = None  # Last N days
    
    # Quality filters
    min_knowledge_completeness: float = 0.0  # 0.0-1.0
    min_last_updated_days: Optional[int] = None  # Max days since update
    
    # Performance constraints
    max_mcps: Optional[int] = None  # Limit number of MCPs
    prefer_hot_instances: bool = True  # Prefer already-running MCPs
    
    # Scope filters
    include_archived: bool = False
    require_active: bool = True
    
    def __post_init__(self):
        """Validate the criteria."""
        if not self.required_tiers:
            raise ValueError("MCPSelectionCriteria must have at least one required tier")
        
        if self.min_knowledge_completeness < 0.0 or self.min_knowledge_completeness > 1.0:
            raise ValueError("min_knowledge_completeness must be between 0.0 and 1.0")
        
        if self.max_mcps is not None and self.max_mcps < 1:
            raise ValueError("max_mcps must be at least 1")
    
    @property
    def is_restrictive(self) -> bool:
        """Check if criteria is highly restrictive."""
        restrictive_count = 0
        
        if self.client_ids:
            restrictive_count += 1
        if self.project_ids:
            restrictive_count += 1
        if self.team_ids:
            restrictive_count += 1
        if self.time_range_days and self.time_range_days < 90:
            restrictive_count += 1
        if self.min_knowledge_completeness > 0.7:
            restrictive_count += 1
        if self.max_mcps and self.max_mcps < 3:
            restrictive_count += 1
        
        return restrictive_count >= 3
    
    @property
    def estimated_mcp_count(self) -> int:
        """
        Estimate how many MCPs will match these criteria.
        
        Returns:
            Estimated count
        """
        # Base estimate from tiers
        base_count = len(self.required_tiers) * 2  # ~2 MCPs per tier on average
        
        # Apply filters
        if self.client_ids:
            base_count = min(base_count, len(self.client_ids) * 2)
        
        if self.max_mcps:
            base_count = min(base_count, self.max_mcps)
        
        if self.time_range_days and self.time_range_days < 30:
            base_count = int(base_count * 0.5)  # Recent data reduces options
        
        if self.min_knowledge_completeness > 0.8:
            base_count = int(base_count * 0.6)  # High quality requirement reduces options
        
        return max(1, base_count)
    
    def matches_mcp(
        self,
        mcp_tier: int,
        client_id: Optional[str] = None,
        project_id: Optional[str] = None,
        team_id: Optional[str] = None,
        is_hot: bool = False,
        is_active: bool = True,
        knowledge_completeness: float = 1.0,
        days_since_update: int = 0,
    ) -> bool:
        """
        Check if an MCP matches these criteria.
        
        Args:
            mcp_tier: MCP tier (0-4)
            client_id: Client ID (if tier 0)
            project_id: Project ID (if tier 1)
            team_id: Team ID (if tier 2)
            is_hot: Whether MCP is currently running
            is_active: Whether MCP is active
            knowledge_completeness: Completeness score (0.0-1.0)
            days_since_update: Days since last update
        
        Returns:
            True if MCP matches criteria
        """
        # Check tier
        if mcp_tier not in self.required_tiers:
            return False
        
        # Check active status
        if self.require_active and not is_active:
            return False
        
        # Check hot instance preference (soft requirement)
        # Note: This doesn't exclude cold instances, just used for sorting
        
        # Check client filter
        if self.client_ids and client_id not in self.client_ids:
            return False
        
        # Check project filter
        if self.project_ids and project_id not in self.project_ids:
            return False
        
        # Check team filter
        if self.team_ids and team_id not in self.team_ids:
            return False
        
        # Check knowledge completeness
        if knowledge_completeness < self.min_knowledge_completeness:
            return False
        
        # Check update recency
        if self.min_last_updated_days is not None:
            if days_since_update > self.min_last_updated_days:
                return False
        
        # Check time range
        if self.time_range_days is not None:
            if days_since_update > self.time_range_days:
                return False
        
        return True
    
    @classmethod
    def create_simple(cls, required_tiers: List[int]) -> "MCPSelectionCriteria":
        """
        Create simple criteria with just required tiers.
        
        Args:
            required_tiers: List of required tier numbers
        
        Returns:
            MCPSelectionCriteria with defaults
        """
        return cls(required_tiers=required_tiers)
    
    @classmethod
    def create_for_client(
        cls,
        client_id: str,
        include_broader_context: bool = True
    ) -> "MCPSelectionCriteria":
        """
        Create criteria focused on a specific client.
        
        Args:
            client_id: Client ID to focus on
            include_broader_context: Include team/company tiers
        
        Returns:
            MCPSelectionCriteria for client
        """
        tiers = [0]  # CLIENT tier
        if include_broader_context:
            tiers.extend([1, 2, 3])  # PROJECT, TEAM, COMPANY
        
        return cls(
            required_tiers=tiers,
            client_ids={client_id},
            prefer_hot_instances=True,
        )

