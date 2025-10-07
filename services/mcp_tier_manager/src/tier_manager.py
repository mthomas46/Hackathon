"""
Tier Management System for 5-Tier Hierarchical MCP.

Implements:
- Client Tier: User/session-specific context
- Project Tier: Project-specific knowledge
- Company Tier: Organization-wide knowledge  
- Team Tier: Team/department knowledge
- Ecosystem Tier: Industry/domain knowledge
"""

import uuid
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger(__name__)


# ============================================================================
# Enumerations
# ============================================================================

class TierType(Enum):
    """Types of MCP tiers in hierarchy."""
    CLIENT = "client"
    PROJECT = "project"
    COMPANY = "company"
    TEAM = "team"
    ECOSYSTEM = "ecosystem"


class InheritancePolicy(Enum):
    """Inheritance policies for tiers."""
    AUTO = "auto"  # Automatically inherit from parent
    EXPLICIT_ONLY = "explicit_only"  # Only inherit when explicitly requested
    SELECTIVE = "selective"  # Inherit based on tags/filters


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class TierConfig:
    """Configuration for a tier."""
    name: str
    tier_type: TierType
    parent_tier_id: Optional[str] = None
    max_size_mb: int = 1000
    retention_days: int = 90
    allow_inheritance: bool = True
    inheritance_policy: InheritancePolicy = InheritancePolicy.AUTO


@dataclass
class Tier:
    """Represents a single tier in the hierarchy."""
    tier_id: str
    name: str
    tier_type: TierType
    parent_tier_id: Optional[str] = None
    status: str = "active"
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    config: Optional[TierConfig] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KnowledgeItem:
    """A piece of knowledge stored in a tier."""
    item_id: str
    tier_id: str
    content: str
    relevance: float = 1.0
    token_count: int = 0
    tags: List[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InheritanceResult:
    """Result of inheritance operation."""
    success: bool
    items_inherited: int
    levels_inherited: int = 1
    errors: List[str] = field(default_factory=list)


@dataclass
class QueryResult:
    """Result from a single tier query."""
    tier_id: str
    tier_type: TierType
    content: str
    relevance: float
    token_count: int
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CascadeResult:
    """Result of cascading query across tiers."""
    query: str
    tiers_searched: int
    results: List[QueryResult]
    total_tokens: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TierStatistics:
    """Statistics for a tier."""
    tier_id: str
    tier_type: TierType
    knowledge_count: int
    size_mb: float
    created_at: datetime
    last_updated: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TierAccessControl:
    """Access control for a tier."""
    tier_id: str
    user_id: str
    role: str  # admin, write, read
    granted_at: datetime = field(default_factory=datetime.now)


# ============================================================================
# Tier Manager
# ============================================================================

class TierManager:
    """
    Manages the 5-tier hierarchical MCP system.
    
    Tier Hierarchy:
        Ecosystem (industry-wide)
            ↓
        Company (organization-wide)
            ↓
        Team (team/department)
            ↓
        Project (project-specific)
            ↓
        Client (user-specific)
    """
    
    # Valid parent-child relationships
    VALID_HIERARCHY = {
        TierType.CLIENT: [TierType.PROJECT],
        TierType.PROJECT: [TierType.COMPANY, TierType.TEAM],
        TierType.TEAM: [TierType.COMPANY],
        TierType.COMPANY: [TierType.ECOSYSTEM],
        TierType.ECOSYSTEM: [],  # Top level, no parent
    }
    
    def __init__(self):
        """Initialize tier manager."""
        self._tiers: Dict[str, Tier] = {}
        self._knowledge: Dict[str, List[KnowledgeItem]] = defaultdict(list)
        self._access_control: Dict[str, List[TierAccessControl]] = defaultdict(list)
        self._tier_children: Dict[str, List[str]] = defaultdict(list)
        
        logger.info("TierManager initialized")
    
    # ========================================================================
    # Tier Creation & Management
    # ========================================================================
    
    def create_tier(self, config: TierConfig) -> Tier:
        """
        Create a new tier.
        
        Args:
            config: Tier configuration
        
        Returns:
            Created Tier instance
        
        Raises:
            ValueError: If tier already exists or hierarchy is invalid
        """
        # Check for duplicate name
        if any(t.name == config.name for t in self._tiers.values()):
            raise ValueError(f"Tier with name '{config.name}' already exists")
        
        # Validate parent relationship if provided
        if config.parent_tier_id:
            self._validate_hierarchy(config.tier_type, config.parent_tier_id)
        
        # Create tier
        tier_id = f"tier_{uuid.uuid4().hex[:12]}"
        tier = Tier(
            tier_id=tier_id,
            name=config.name,
            tier_type=config.tier_type,
            parent_tier_id=config.parent_tier_id,
            config=config
        )
        
        self._tiers[tier_id] = tier
        
        # Track parent-child relationship
        if config.parent_tier_id:
            self._tier_children[config.parent_tier_id].append(tier_id)
        
        logger.info(f"Created tier: {config.name} ({config.tier_type.value})")
        
        # Auto-inherit if policy allows
        if config.parent_tier_id and config.inheritance_policy == InheritancePolicy.AUTO:
            self.inherit_from_parent(tier_id)
        
        return tier
    
    def _validate_hierarchy(self, tier_type: TierType, parent_id: str):
        """Validate tier hierarchy."""
        if parent_id not in self._tiers:
            raise ValueError(f"Parent tier not found: {parent_id}")
        
        parent = self._tiers[parent_id]
        valid_parents = self.VALID_HIERARCHY.get(tier_type, [])
        
        if parent.tier_type not in valid_parents:
            raise ValueError(
                f"Invalid parent: {tier_type.value} cannot be child of {parent.tier_type.value}"
            )
    
    def get_tier(self, tier_id: str) -> Optional[Tier]:
        """Get tier by ID."""
        return self._tiers.get(tier_id)
    
    def get_tier_children(self, tier_id: str) -> List[str]:
        """Get child tier IDs."""
        return self._tier_children.get(tier_id, [])
    
    def delete_tier(self, tier_id: str):
        """Delete a tier."""
        if tier_id not in self._tiers:
            raise ValueError(f"Tier not found: {tier_id}")
        
        # Check for children
        if self._tier_children.get(tier_id):
            raise ValueError(f"Tier {tier_id} has children and cannot be deleted")
        
        # Remove tier
        tier = self._tiers[tier_id]
        del self._tiers[tier_id]
        
        # Clean up parent's children list
        if tier.parent_tier_id:
            self._tier_children[tier.parent_tier_id].remove(tier_id)
        
        # Clean up knowledge
        if tier_id in self._knowledge:
            del self._knowledge[tier_id]
        
        logger.info(f"Deleted tier: {tier_id}")
    
    def update_tier_parent(self, tier_id: str, new_parent_id: str):
        """Update tier's parent (with circular dependency check)."""
        if tier_id not in self._tiers:
            raise ValueError(f"Tier not found: {tier_id}")
        
        # Check for circular dependency
        if self._would_create_cycle(tier_id, new_parent_id):
            raise ValueError("Circular dependency detected")
        
        tier = self._tiers[tier_id]
        
        # Remove from old parent's children
        if tier.parent_tier_id:
            self._tier_children[tier.parent_tier_id].remove(tier_id)
        
        # Validate new hierarchy
        self._validate_hierarchy(tier.tier_type, new_parent_id)
        
        # Update parent
        tier.parent_tier_id = new_parent_id
        self._tier_children[new_parent_id].append(tier_id)
        tier.updated_at = datetime.now()
    
    def _would_create_cycle(self, tier_id: str, new_parent_id: str) -> bool:
        """Check if setting parent would create circular dependency."""
        current_id = new_parent_id
        visited = set()
        
        while current_id:
            if current_id == tier_id:
                return True
            if current_id in visited:
                return False
            
            visited.add(current_id)
            tier = self._tiers.get(current_id)
            current_id = tier.parent_tier_id if tier else None
        
        return False
    
    # ========================================================================
    # Knowledge Management
    # ========================================================================
    
    def add_knowledge(
        self,
        tier_id: str,
        content: str,
        relevance: float = 1.0,
        tags: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> KnowledgeItem:
        """Add knowledge to a tier."""
        if tier_id not in self._tiers:
            raise ValueError(f"Tier not found: {tier_id}")
        
        tier = self._tiers[tier_id]
        
        # Check size limit
        content_size_mb = len(content.encode('utf-8')) / (1024 * 1024)
        current_size = self._get_tier_size_mb(tier_id)
        
        if tier.config and (current_size + content_size_mb) > tier.config.max_size_mb:
            raise ValueError(
                f"Adding content exceeds maximum size limit of {tier.config.max_size_mb}MB"
            )
        
        # Create knowledge item
        item = KnowledgeItem(
            item_id=f"know_{uuid.uuid4().hex[:12]}",
            tier_id=tier_id,
            content=content,
            relevance=relevance,
            token_count=len(content.split()),  # Simple token count
            tags=tags or [],
            metadata=metadata or {}
        )
        
        self._knowledge[tier_id].append(item)
        tier.updated_at = datetime.now()
        
        return item
    
    def get_tier_knowledge(self, tier_id: str) -> List[KnowledgeItem]:
        """Get all knowledge items for a tier."""
        return self._knowledge.get(tier_id, [])
    
    def _get_tier_size_mb(self, tier_id: str) -> float:
        """Calculate tier size in MB."""
        items = self._knowledge.get(tier_id, [])
        total_bytes = sum(len(item.content.encode('utf-8')) for item in items)
        return total_bytes / (1024 * 1024)
    
    # ========================================================================
    # Inheritance
    # ========================================================================
    
    def inherit_from_parent(
        self,
        tier_id: str,
        filter_tags: List[str] = None
    ) -> InheritanceResult:
        """Inherit knowledge from parent tier."""
        if tier_id not in self._tiers:
            raise ValueError(f"Tier not found: {tier_id}")
        
        tier = self._tiers[tier_id]
        
        if not tier.parent_tier_id:
            return InheritanceResult(success=True, items_inherited=0)
        
        # Get parent knowledge
        parent_knowledge = self._knowledge.get(tier.parent_tier_id, [])
        
        # Filter if tags provided
        if filter_tags:
            parent_knowledge = [
                item for item in parent_knowledge
                if any(tag in item.tags for tag in filter_tags)
            ]
        
        # Copy to child (simplified - in production would be references)
        for item in parent_knowledge:
            self.add_knowledge(
                tier_id=tier_id,
                content=item.content,
                relevance=item.relevance * 0.9,  # Slightly reduce relevance
                tags=item.tags,
                metadata={**item.metadata, "inherited_from": tier.parent_tier_id}
            )
        
        return InheritanceResult(
            success=True,
            items_inherited=len(parent_knowledge)
        )
    
    def inherit_cascading(
        self,
        tier_id: str,
        max_levels: int = 3
    ) -> InheritanceResult:
        """Inherit knowledge cascading through multiple ancestor levels."""
        if tier_id not in self._tiers:
            raise ValueError(f"Tier not found: {tier_id}")
        
        total_inherited = 0
        levels = 0
        current_id = self._tiers[tier_id].parent_tier_id
        
        while current_id and levels < max_levels:
            # Get ancestor knowledge
            ancestor_knowledge = self._knowledge.get(current_id, [])
            
            # Add to tier with decreasing relevance
            relevance_factor = 0.9 ** (levels + 1)
            for item in ancestor_knowledge:
                self.add_knowledge(
                    tier_id=tier_id,
                    content=item.content,
                    relevance=item.relevance * relevance_factor,
                    tags=item.tags,
                    metadata={**item.metadata, "inherited_from": current_id, "level": levels + 1}
                )
                total_inherited += 1
            
            # Move to next ancestor
            current_id = self._tiers[current_id].parent_tier_id
            levels += 1
        
        return InheritanceResult(
            success=True,
            items_inherited=total_inherited,
            levels_inherited=levels
        )
    
    # ========================================================================
    # Cascade Query
    # ========================================================================
    
    def cascade_query(
        self,
        query: str,
        starting_tier_id: str,
        max_tiers: int = 5,
        max_tokens: int = 4000
    ) -> CascadeResult:
        """Execute cascading query across tiers."""
        if starting_tier_id not in self._tiers:
            raise ValueError(f"Tier not found: {starting_tier_id}")
        
        results: List[QueryResult] = []
        tiers_searched = 0
        total_tokens = 0
        
        # Start with current tier and move up hierarchy
        current_id = starting_tier_id
        visited = set()
        
        while current_id and tiers_searched < max_tiers and total_tokens < max_tokens:
            if current_id in visited:
                break
            
            visited.add(current_id)
            tier = self._tiers[current_id]
            
            # Search tier knowledge
            tier_knowledge = self._knowledge.get(current_id, [])
            for item in tier_knowledge:
                # Simple relevance check (in production would use vector search)
                if query.lower() in item.content.lower():
                    if total_tokens + item.token_count <= max_tokens:
                        results.append(QueryResult(
                            tier_id=current_id,
                            tier_type=tier.tier_type,
                            content=item.content,
                            relevance=item.relevance,
                            token_count=item.token_count
                        ))
                        total_tokens += item.token_count
            
            tiers_searched += 1
            current_id = tier.parent_tier_id
        
        # Sort by tier proximity (closer tiers first) and relevance
        results.sort(key=lambda r: (
            list(TierType).index(r.tier_type),
            -r.relevance
        ))
        
        return CascadeResult(
            query=query,
            tiers_searched=tiers_searched,
            results=results,
            total_tokens=total_tokens
        )
    
    # ========================================================================
    # Access Control
    # ========================================================================
    
    def add_user_access(self, tier_id: str, user_id: str, role: str):
        """Add user access to tier."""
        if tier_id not in self._tiers:
            raise ValueError(f"Tier not found: {tier_id}")
        
        access = TierAccessControl(
            tier_id=tier_id,
            user_id=user_id,
            role=role
        )
        self._access_control[tier_id].append(access)
    
    def has_access(self, tier_id: str, user_id: str) -> bool:
        """Check if user has access to tier."""
        access_list = self._access_control.get(tier_id, [])
        return any(ac.user_id == user_id for ac in access_list)
    
    def can_write(self, tier_id: str, user_id: str) -> bool:
        """Check if user can write to tier."""
        access_list = self._access_control.get(tier_id, [])
        user_access = [ac for ac in access_list if ac.user_id == user_id]
        return any(ac.role in ["admin", "write"] for ac in user_access)
    
    # ========================================================================
    # Statistics
    # ========================================================================
    
    def get_tier_stats(self, tier_id: str) -> TierStatistics:
        """Get statistics for a tier."""
        if tier_id not in self._tiers:
            raise ValueError(f"Tier not found: {tier_id}")
        
        tier = self._tiers[tier_id]
        knowledge = self._knowledge.get(tier_id, [])
        
        return TierStatistics(
            tier_id=tier_id,
            tier_type=tier.tier_type,
            knowledge_count=len(knowledge),
            size_mb=self._get_tier_size_mb(tier_id),
            created_at=tier.created_at,
            last_updated=tier.updated_at
        )
    
    def get_all_tiers_overview(self) -> List[Dict[str, Any]]:
        """Get overview of all tiers."""
        return [
            {
                "tier_id": tier.tier_id,
                "name": tier.name,
                "tier_type": tier.tier_type.value,
                "status": tier.status,
                "knowledge_count": len(self._knowledge.get(tier.tier_id, [])),
                "created_at": tier.created_at.isoformat()
            }
            for tier in self._tiers.values()
        ]

