"""
Unit tests for Tier Management System.

Tests the 5-tier hierarchical MCP system:
- Client tier (user-specific)
- Project tier (project-specific)
- Company tier (organization-wide)
- Team tier (team/department)
- Ecosystem tier (industry-wide)
"""

import pytest
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

# Add services directory to path
services_path = Path(__file__).parent.parent.parent / "services"
sys.path.insert(0, str(services_path))

from mcp_tier_manager.src.tier_manager import (
    TierManager,
    Tier,
    TierConfig,
    TierType,
    InheritancePolicy,
    CascadeResult,
    TierAccessControl,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def tier_manager():
    """Create a TierManager instance."""
    return TierManager()


@pytest.fixture
def sample_tier_config():
    """Create sample tier configuration."""
    return TierConfig(
        name="test_client",
        tier_type=TierType.CLIENT,
        max_size_mb=100,
        retention_days=30,
        allow_inheritance=True
    )


# ============================================================================
# Tier Creation Tests
# ============================================================================

class TestTierCreation:
    """Test tier creation and management."""
    
    def test_create_client_tier(self, tier_manager, sample_tier_config):
        """Test creating a client tier."""
        tier = tier_manager.create_tier(sample_tier_config)
        
        assert tier is not None
        assert tier.name == "test_client"
        assert tier.tier_type == TierType.CLIENT
        assert tier.status == "active"
        assert tier.created_at is not None
    
    def test_create_all_tier_types(self, tier_manager):
        """Test creating all 5 tier types."""
        tier_types = [
            TierType.CLIENT,
            TierType.PROJECT,
            TierType.COMPANY,
            TierType.TEAM,
            TierType.ECOSYSTEM
        ]
        
        tiers = []
        for tier_type in tier_types:
            config = TierConfig(
                name=f"test_{tier_type.value}",
                tier_type=tier_type
            )
            tier = tier_manager.create_tier(config)
            tiers.append(tier)
        
        assert len(tiers) == 5
        assert all(tier.status == "active" for tier in tiers)
    
    def test_create_tier_with_parent(self, tier_manager):
        """Test creating tier with parent relationship."""
        # Create parent (project)
        project_config = TierConfig(
            name="parent_project",
            tier_type=TierType.PROJECT
        )
        project_tier = tier_manager.create_tier(project_config)
        
        # Create child (client)
        client_config = TierConfig(
            name="child_client",
            tier_type=TierType.CLIENT,
            parent_tier_id=project_tier.tier_id
        )
        client_tier = tier_manager.create_tier(client_config)
        
        assert client_tier.parent_tier_id == project_tier.tier_id
        assert client_tier.tier_id in tier_manager.get_tier_children(project_tier.tier_id)
    
    def test_cannot_create_duplicate_tier(self, tier_manager, sample_tier_config):
        """Test that duplicate tier names are rejected."""
        tier_manager.create_tier(sample_tier_config)
        
        with pytest.raises(ValueError, match="already exists"):
            tier_manager.create_tier(sample_tier_config)
    
    def test_tier_hierarchy_validation(self, tier_manager):
        """Test that tier hierarchy is validated."""
        # Client can only be child of Project
        # Should fail: Client as child of Ecosystem
        ecosystem_tier = tier_manager.create_tier(
            TierConfig(name="eco", tier_type=TierType.ECOSYSTEM)
        )
        
        with pytest.raises(ValueError, match="Invalid parent"):
            tier_manager.create_tier(
                TierConfig(
                    name="client",
                    tier_type=TierType.CLIENT,
                    parent_tier_id=ecosystem_tier.tier_id
                )
            )


# ============================================================================
# Tier Inheritance Tests
# ============================================================================

class TestTierInheritance:
    """Test tier inheritance mechanisms."""
    
    def test_inherit_from_parent(self, tier_manager):
        """Test inheriting knowledge from parent tier."""
        # Create parent with knowledge
        parent = tier_manager.create_tier(
            TierConfig(name="parent_project", tier_type=TierType.PROJECT)
        )
        tier_manager.add_knowledge(parent.tier_id, "parent knowledge")
        
        # Create child
        child = tier_manager.create_tier(
            TierConfig(
                name="child_client",
                tier_type=TierType.CLIENT,
                parent_tier_id=parent.tier_id
            )
        )
        
        # Inherit from parent
        result = tier_manager.inherit_from_parent(child.tier_id)
        
        assert result.success is True
        assert result.items_inherited > 0
    
    def test_selective_inheritance(self, tier_manager):
        """Test selective pattern inheritance."""
        parent = tier_manager.create_tier(
            TierConfig(name="parent", tier_type=TierType.PROJECT)
        )
        
        # Add multiple patterns to parent
        tier_manager.add_knowledge(parent.tier_id, "pattern1", tags=["critical"])
        tier_manager.add_knowledge(parent.tier_id, "pattern2", tags=["optional"])
        
        child = tier_manager.create_tier(
            TierConfig(
                name="child",
                tier_type=TierType.CLIENT,
                parent_tier_id=parent.tier_id
            )
        )
        
        # Inherit only critical patterns
        result = tier_manager.inherit_from_parent(
            child.tier_id,
            filter_tags=["critical"]
        )
        
        assert result.items_inherited == 1
    
    def test_cascading_inheritance(self, tier_manager):
        """Test inheritance cascading through multiple levels."""
        # Create hierarchy: Ecosystem -> Company -> Project -> Client
        ecosystem = tier_manager.create_tier(
            TierConfig(name="eco", tier_type=TierType.ECOSYSTEM)
        )
        tier_manager.add_knowledge(ecosystem.tier_id, "eco knowledge")
        
        company = tier_manager.create_tier(
            TierConfig(
                name="company",
                tier_type=TierType.COMPANY,
                parent_tier_id=ecosystem.tier_id
            )
        )
        
        project = tier_manager.create_tier(
            TierConfig(
                name="project",
                tier_type=TierType.PROJECT,
                parent_tier_id=company.tier_id
            )
        )
        
        client = tier_manager.create_tier(
            TierConfig(
                name="client",
                tier_type=TierType.CLIENT,
                parent_tier_id=project.tier_id
            )
        )
        
        # Inherit cascading from all ancestors
        result = tier_manager.inherit_cascading(client.tier_id, max_levels=3)
        
        assert result.success is True
        assert result.levels_inherited == 3
    
    def test_inheritance_policy(self, tier_manager):
        """Test different inheritance policies."""
        parent = tier_manager.create_tier(
            TierConfig(
                name="parent",
                tier_type=TierType.PROJECT,
                inheritance_policy=InheritancePolicy.EXPLICIT_ONLY
            )
        )
        
        child = tier_manager.create_tier(
            TierConfig(
                name="child",
                tier_type=TierType.CLIENT,
                parent_tier_id=parent.tier_id
            )
        )
        
        # Should not auto-inherit with EXPLICIT_ONLY policy
        knowledge = tier_manager.get_tier_knowledge(child.tier_id)
        assert len(knowledge) == 0


# ============================================================================
# Cascade Query Tests
# ============================================================================

class TestCascadeQuery:
    """Test cascading queries across tiers."""
    
    def test_cascade_single_tier(self, tier_manager):
        """Test query on single tier without cascading."""
        tier = tier_manager.create_tier(
            TierConfig(name="client", tier_type=TierType.CLIENT)
        )
        tier_manager.add_knowledge(tier.tier_id, "client-specific info")
        
        result = tier_manager.cascade_query(
            query="info",
            starting_tier_id=tier.tier_id,
            max_tiers=1
        )
        
        assert result.tiers_searched == 1
        assert len(result.results) > 0
        assert all(r.tier_id == tier.tier_id for r in result.results)
    
    def test_cascade_up_hierarchy(self, tier_manager):
        """Test cascading query up the hierarchy."""
        # Create hierarchy
        project = tier_manager.create_tier(
            TierConfig(name="project", tier_type=TierType.PROJECT)
        )
        tier_manager.add_knowledge(project.tier_id, "project knowledge")
        
        client = tier_manager.create_tier(
            TierConfig(
                name="client",
                tier_type=TierType.CLIENT,
                parent_tier_id=project.tier_id
            )
        )
        tier_manager.add_knowledge(client.tier_id, "client knowledge")
        
        # Query starting from client, cascade to project
        result = tier_manager.cascade_query(
            query="knowledge",
            starting_tier_id=client.tier_id,
            max_tiers=2
        )
        
        assert result.tiers_searched == 2
        assert len(result.results) >= 2
        # Should have results from both tiers
        tier_ids = {r.tier_id for r in result.results}
        assert client.tier_id in tier_ids
        assert project.tier_id in tier_ids
    
    def test_cascade_with_token_budget(self, tier_manager):
        """Test cascading with token budget constraints."""
        tier = tier_manager.create_tier(
            TierConfig(name="client", tier_type=TierType.CLIENT)
        )
        
        # Add multiple items
        for i in range(10):
            tier_manager.add_knowledge(tier.tier_id, f"knowledge item {i}")
        
        result = tier_manager.cascade_query(
            query="knowledge",
            starting_tier_id=tier.tier_id,
            max_tokens=1000
        )
        
        # Total tokens should not exceed budget
        total_tokens = sum(r.token_count for r in result.results)
        assert total_tokens <= 1000
    
    def test_cascade_prioritization(self, tier_manager):
        """Test that cascading prioritizes by tier proximity."""
        # Create 3-level hierarchy
        company = tier_manager.create_tier(
            TierConfig(name="company", tier_type=TierType.COMPANY)
        )
        tier_manager.add_knowledge(company.tier_id, "company info", relevance=0.5)
        
        project = tier_manager.create_tier(
            TierConfig(
                name="project",
                tier_type=TierType.PROJECT,
                parent_tier_id=company.tier_id
            )
        )
        tier_manager.add_knowledge(project.tier_id, "project info", relevance=0.7)
        
        client = tier_manager.create_tier(
            TierConfig(
                name="client",
                tier_type=TierType.CLIENT,
                parent_tier_id=project.tier_id
            )
        )
        tier_manager.add_knowledge(client.tier_id, "client info", relevance=0.9)
        
        result = tier_manager.cascade_query(
            query="info",
            starting_tier_id=client.tier_id,
            max_tiers=3
        )
        
        # Results should be ordered by proximity (client first)
        assert result.results[0].tier_type == TierType.CLIENT


# ============================================================================
# Tier Access Control Tests
# ============================================================================

class TestTierAccessControl:
    """Test tier isolation and access control."""
    
    def test_tier_isolation(self, tier_manager):
        """Test that tiers are isolated from each other."""
        tier1 = tier_manager.create_tier(
            TierConfig(name="client1", tier_type=TierType.CLIENT)
        )
        tier2 = tier_manager.create_tier(
            TierConfig(name="client2", tier_type=TierType.CLIENT)
        )
        
        tier_manager.add_knowledge(tier1.tier_id, "tier1 secret")
        
        # tier2 should not have access to tier1's knowledge
        knowledge = tier_manager.get_tier_knowledge(tier2.tier_id)
        assert len(knowledge) == 0
    
    def test_access_control_user(self, tier_manager):
        """Test user-based access control."""
        tier = tier_manager.create_tier(
            TierConfig(name="client", tier_type=TierType.CLIENT)
        )
        
        # Add access control
        tier_manager.add_user_access(tier.tier_id, user_id="user123", role="read")
        
        # User should have access
        assert tier_manager.has_access(tier.tier_id, user_id="user123")
        
        # Other user should not
        assert not tier_manager.has_access(tier.tier_id, user_id="user456")
    
    def test_access_control_roles(self, tier_manager):
        """Test role-based access control."""
        tier = tier_manager.create_tier(
            TierConfig(name="project", tier_type=TierType.PROJECT)
        )
        
        tier_manager.add_user_access(tier.tier_id, user_id="user1", role="admin")
        tier_manager.add_user_access(tier.tier_id, user_id="user2", role="read")
        
        # Admin can write
        assert tier_manager.can_write(tier.tier_id, user_id="user1")
        
        # Read-only cannot write
        assert not tier_manager.can_write(tier.tier_id, user_id="user2")


# ============================================================================
# Tier Statistics Tests
# ============================================================================

class TestTierStatistics:
    """Test tier statistics and metrics."""
    
    def test_get_tier_stats(self, tier_manager):
        """Test getting tier statistics."""
        tier = tier_manager.create_tier(
            TierConfig(name="client", tier_type=TierType.CLIENT)
        )
        
        # Add some knowledge
        for i in range(5):
            tier_manager.add_knowledge(tier.tier_id, f"item {i}")
        
        stats = tier_manager.get_tier_stats(tier.tier_id)
        
        assert stats.knowledge_count == 5
        assert stats.size_mb > 0
        assert stats.created_at is not None
    
    def test_get_all_tiers_overview(self, tier_manager):
        """Test getting overview of all tiers."""
        # Create multiple tiers
        for tier_type in TierType:
            tier_manager.create_tier(
                TierConfig(
                    name=f"test_{tier_type.value}",
                    tier_type=tier_type
                )
            )
        
        overview = tier_manager.get_all_tiers_overview()
        
        assert len(overview) == 5  # 5 tier types
        assert all("tier_type" in tier for tier in overview)


# ============================================================================
# Edge Cases and Error Handling
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""
    
    def test_query_nonexistent_tier(self, tier_manager):
        """Test querying nonexistent tier."""
        with pytest.raises(ValueError, match="Tier not found"):
            tier_manager.cascade_query(
                query="test",
                starting_tier_id="nonexistent_id"
            )
    
    def test_circular_inheritance(self, tier_manager):
        """Test that circular inheritance is prevented."""
        tier1 = tier_manager.create_tier(
            TierConfig(name="tier1", tier_type=TierType.PROJECT)
        )
        tier2 = tier_manager.create_tier(
            TierConfig(
                name="tier2",
                tier_type=TierType.CLIENT,
                parent_tier_id=tier1.tier_id
            )
        )
        
        # Should not allow tier1 to become child of tier2
        with pytest.raises(ValueError, match="Circular"):
            tier_manager.update_tier_parent(tier1.tier_id, tier2.tier_id)
    
    def test_delete_tier_with_children(self, tier_manager):
        """Test deleting tier with children."""
        parent = tier_manager.create_tier(
            TierConfig(name="parent", tier_type=TierType.PROJECT)
        )
        child = tier_manager.create_tier(
            TierConfig(
                name="child",
                tier_type=TierType.CLIENT,
                parent_tier_id=parent.tier_id
            )
        )
        
        # Should not allow deletion of parent with children
        with pytest.raises(ValueError, match="has children"):
            tier_manager.delete_tier(parent.tier_id)
    
    def test_tier_size_limit(self, tier_manager):
        """Test tier size limit enforcement."""
        tier = tier_manager.create_tier(
            TierConfig(
                name="client",
                tier_type=TierType.CLIENT,
                max_size_mb=1  # 1MB limit
            )
        )
        
        # Try to add knowledge exceeding limit
        large_content = "x" * (2 * 1024 * 1024)  # 2MB of data
        
        with pytest.raises(ValueError, match="exceeds maximum size"):
            tier_manager.add_knowledge(tier.tier_id, large_content)

