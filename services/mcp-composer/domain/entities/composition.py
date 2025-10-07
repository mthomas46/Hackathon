"""MCP Composition entity."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class CompositionStrategy(Enum):
    """Strategy for composing multiple MCPs."""
    SEQUENTIAL = "sequential"      # Execute MCPs in sequence
    PARALLEL = "parallel"          # Execute MCPs in parallel
    HIERARCHICAL = "hierarchical"  # Execute in hierarchy (parent->children)
    WEIGHTED = "weighted"          # Weighted combination
    FALLBACK = "fallback"          # Try in order, use first success


class ConflictResolution(Enum):
    """Strategy for resolving conflicts between MCPs."""
    PRIORITY = "priority"          # Use priority order
    MERGE = "merge"                # Merge responses
    VOTE = "vote"                  # Democratic voting
    EXPERT = "expert"              # Defer to expert MCP
    LATEST = "latest"              # Use most recent
    CONSENSUS = "consensus"        # Require agreement


@dataclass
class MCPReference:
    """Reference to an MCP in a composition."""
    
    mcp_id: str
    tier: str  # "ecosystem", "team", "company", "project", "client"
    priority: int = 1
    weight: float = 1.0
    fallback: bool = False
    required: bool = True
    timeout_ms: int = 30000
    retry_count: int = 3
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate MCP reference."""
        if self.priority < 1:
            raise ValueError("Priority must be >= 1")
        if not 0.0 <= self.weight <= 1.0:
            raise ValueError("Weight must be between 0.0 and 1.0")
        if self.timeout_ms < 1000:
            raise ValueError("Timeout must be >= 1000ms")


@dataclass
class Composition:
    """
    Represents a composition of multiple MCPs.
    
    A composition defines how multiple MCPs work together to answer queries,
    including routing strategies, conflict resolution, and merging logic.
    """
    
    composition_id: str
    name: str
    description: str
    mcps: List[MCPReference]
    strategy: CompositionStrategy
    conflict_resolution: ConflictResolution
    version: str = "1.0.0"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    
    # Configuration
    merge_responses: bool = True
    deduplicate: bool = True
    max_response_length: int = 10000
    min_confidence: float = 0.5
    require_sources: bool = True
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # State
    is_active: bool = True
    execution_count: int = 0
    success_count: int = 0
    failure_count: int = 0
    
    def __post_init__(self):
        """Validate composition."""
        if not self.mcps:
            raise ValueError("Composition must have at least one MCP")
        
        if self.strategy == CompositionStrategy.WEIGHTED:
            total_weight = sum(mcp.weight for mcp in self.mcps)
            if abs(total_weight - 1.0) > 0.01:
                raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
    
    def add_mcp(self, mcp: MCPReference) -> None:
        """Add an MCP to the composition."""
        if any(m.mcp_id == mcp.mcp_id for m in self.mcps):
            raise ValueError(f"MCP {mcp.mcp_id} already in composition")
        self.mcps.append(mcp)
        self.updated_at = datetime.now()
    
    def remove_mcp(self, mcp_id: str) -> None:
        """Remove an MCP from the composition."""
        self.mcps = [m for m in self.mcps if m.mcp_id != mcp_id]
        self.updated_at = datetime.now()
    
    def get_mcp(self, mcp_id: str) -> Optional[MCPReference]:
        """Get an MCP reference by ID."""
        return next((m for m in self.mcps if m.mcp_id == mcp_id), None)
    
    def get_mcps_by_tier(self, tier: str) -> List[MCPReference]:
        """Get all MCPs for a specific tier."""
        return [m for m in self.mcps if m.tier == tier]
    
    def get_required_mcps(self) -> List[MCPReference]:
        """Get all required MCPs."""
        return [m for m in self.mcps if m.required]
    
    def get_fallback_mcps(self) -> List[MCPReference]:
        """Get all fallback MCPs."""
        return [m for m in self.mcps if m.fallback]
    
    def get_sorted_mcps(self) -> List[MCPReference]:
        """Get MCPs sorted by priority."""
        return sorted(self.mcps, key=lambda m: m.priority)
    
    def increment_execution(self, success: bool = True) -> None:
        """Increment execution counters."""
        self.execution_count += 1
        if success:
            self.success_count += 1
        else:
            self.failure_count += 1
    
    def get_success_rate(self) -> float:
        """Calculate success rate."""
        if self.execution_count == 0:
            return 0.0
        return self.success_count / self.execution_count
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "composition_id": self.composition_id,
            "name": self.name,
            "description": self.description,
            "mcps": [
                {
                    "mcp_id": m.mcp_id,
                    "tier": m.tier,
                    "priority": m.priority,
                    "weight": m.weight,
                    "fallback": m.fallback,
                    "required": m.required,
                    "timeout_ms": m.timeout_ms,
                    "retry_count": m.retry_count,
                    "metadata": m.metadata
                }
                for m in self.mcps
            ],
            "strategy": self.strategy.value,
            "conflict_resolution": self.conflict_resolution.value,
            "version": self.version,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "merge_responses": self.merge_responses,
            "deduplicate": self.deduplicate,
            "max_response_length": self.max_response_length,
            "min_confidence": self.min_confidence,
            "require_sources": self.require_sources,
            "tags": self.tags,
            "metadata": self.metadata,
            "is_active": self.is_active,
            "execution_count": self.execution_count,
            "success_count": self.success_count,
            "failure_count": self.failure_count,
            "success_rate": self.get_success_rate()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Composition":
        """Create from dictionary."""
        mcps = [
            MCPReference(
                mcp_id=m["mcp_id"],
                tier=m["tier"],
                priority=m.get("priority", 1),
                weight=m.get("weight", 1.0),
                fallback=m.get("fallback", False),
                required=m.get("required", True),
                timeout_ms=m.get("timeout_ms", 30000),
                retry_count=m.get("retry_count", 3),
                metadata=m.get("metadata", {})
            )
            for m in data["mcps"]
        ]
        
        return cls(
            composition_id=data["composition_id"],
            name=data["name"],
            description=data["description"],
            mcps=mcps,
            strategy=CompositionStrategy(data["strategy"]),
            conflict_resolution=ConflictResolution(data["conflict_resolution"]),
            version=data.get("version", "1.0.0"),
            created_at=datetime.fromisoformat(data["created_at"]) if isinstance(data.get("created_at"), str) else data.get("created_at", datetime.now()),
            updated_at=datetime.fromisoformat(data["updated_at"]) if isinstance(data.get("updated_at"), str) else data.get("updated_at", datetime.now()),
            merge_responses=data.get("merge_responses", True),
            deduplicate=data.get("deduplicate", True),
            max_response_length=data.get("max_response_length", 10000),
            min_confidence=data.get("min_confidence", 0.5),
            require_sources=data.get("require_sources", True),
            tags=data.get("tags", []),
            metadata=data.get("metadata", {}),
            is_active=data.get("is_active", True),
            execution_count=data.get("execution_count", 0),
            success_count=data.get("success_count", 0),
            failure_count=data.get("failure_count", 0)
        )
