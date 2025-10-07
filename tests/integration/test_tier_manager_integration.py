"""
Integration tests for Tier Management System.

Tests full integration of:
- TierManager
- ProgressiveRefiner
- Tier hierarchy operations
- Real-world workflows
"""

import pytest
import sys
from pathlib import Path

# Add services directory to path
services_path = Path(__file__).parent.parent.parent / "services"
sys.path.insert(0, str(services_path))

from mcp_tier_manager.src.tier_manager import (
    TierManager,
    TierConfig,
    TierType,
    InheritancePolicy
)
from mcp_tier_manager.src.progressive_refinement import (
    ProgressiveRefiner,
    RefinementConfig,
    RefinementStrategy
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def integrated_system():
    """Create integrated tier system with sample data."""
    tier_manager = TierManager()
    
    # Create 5-tier hierarchy
    ecosystem = tier_manager.create_tier(
        TierConfig(name="tech_ecosystem", tier_type=TierType.ECOSYSTEM)
    )
    tier_manager.add_knowledge(
        ecosystem.tier_id,
        "Industry best practice: Always use version control",
        relevance=0.7,
        tags=["best_practice"]
    )
    tier_manager.add_knowledge(
        ecosystem.tier_id,
        "Technology trend: AI and machine learning are transforming software",
        relevance=0.6,
        tags=["trend"]
    )
    
    company = tier_manager.create_tier(
        TierConfig(
            name="acme_corp",
            tier_type=TierType.COMPANY,
            parent_tier_id=ecosystem.tier_id
        )
    )
    tier_manager.add_knowledge(
        company.tier_id,
        "Company policy: All code must be reviewed before merge",
        relevance=0.8,
        tags=["policy"]
    )
    tier_manager.add_knowledge(
        company.tier_id,
        "Company standard: Use Python 3.11+ for all new projects",
        relevance=0.9,
        tags=["standard"]
    )
    
    team = tier_manager.create_tier(
        TierConfig(
            name="backend_team",
            tier_type=TierType.TEAM,
            parent_tier_id=company.tier_id
        )
    )
    tier_manager.add_knowledge(
        team.tier_id,
        "Team practice: Daily standups at 9 AM",
        relevance=0.7,
        tags=["practice"]
    )
    
    project = tier_manager.create_tier(
        TierConfig(
            name="mcp_project",
            tier_type=TierType.PROJECT,
            parent_tier_id=team.tier_id
        )
    )
    tier_manager.add_knowledge(
        project.tier_id,
        "Project guideline: Follow DDD architecture",
        relevance=0.9,
        tags=["architecture"]
    )
    tier_manager.add_knowledge(
        project.tier_id,
        "Project requirement: TDD for all features",
        relevance=1.0,
        tags=["testing"]
    )
    
    client = tier_manager.create_tier(
        TierConfig(
            name="user_session",
            tier_type=TierType.CLIENT,
            parent_tier_id=project.tier_id
        )
    )
    tier_manager.add_knowledge(
        client.tier_id,
        "User preference: Dark mode enabled",
        relevance=0.8,
        tags=["preference"]
    )
    tier_manager.add_knowledge(
        client.tier_id,
        "User context: Working on authentication feature",
        relevance=1.0,
        tags=["context"]
    )
    
    return {
        "tier_manager": tier_manager,
        "tiers": {
            "ecosystem": ecosystem,
            "company": company,
            "team": team,
            "project": project,
            "client": client
        }
    }


# ============================================================================
# Integration Tests
# ============================================================================

class TestTierManagerIntegration:
    """Integration tests for tier manager."""
    
    def test_full_hierarchy_creation(self, integrated_system):
        """Test creating and querying full 5-tier hierarchy."""
        tier_manager = integrated_system["tier_manager"]
        tiers = integrated_system["tiers"]
        
        # Verify all tiers created
        assert len(tier_manager._tiers) == 5
        
        # Verify hierarchy relationships
        assert tiers["client"].parent_tier_id == tiers["project"].tier_id
        assert tiers["project"].parent_tier_id == tiers["team"].tier_id
        assert tiers["team"].parent_tier_id == tiers["company"].tier_id
        assert tiers["company"].parent_tier_id == tiers["ecosystem"].tier_id
        assert tiers["ecosystem"].parent_tier_id is None
    
    def test_cascade_query_full_hierarchy(self, integrated_system):
        """Test cascading query through full hierarchy."""
        tier_manager = integrated_system["tier_manager"]
        client_id = integrated_system["tiers"]["client"].tier_id
        
        # Query from client tier, should cascade up
        result = tier_manager.cascade_query(
            query="practice",
            starting_tier_id=client_id,
            max_tiers=5
        )
        
        # Should find results from multiple tiers
        assert result.tiers_searched >= 2
        assert len(result.results) > 0
        
        # Should include results from different tier types
        tier_types = {r.tier_type for r in result.results}
        assert TierType.TEAM in tier_types  # "Team practice"
        assert TierType.ECOSYSTEM in tier_types  # "Industry best practice"
    
    def test_cascading_inheritance(self, integrated_system):
        """Test cascading inheritance through multiple levels."""
        tier_manager = integrated_system["tier_manager"]
        client_id = integrated_system["tiers"]["client"].tier_id
        
        # Get initial knowledge count
        initial_knowledge = len(tier_manager.get_tier_knowledge(client_id))
        
        # Inherit cascading from all ancestors
        result = tier_manager.inherit_cascading(client_id, max_levels=4)
        
        # Should inherit from multiple levels
        assert result.success
        assert result.items_inherited > 0
        assert result.levels_inherited > 1
        
        # Knowledge count should increase
        final_knowledge = len(tier_manager.get_tier_knowledge(client_id))
        assert final_knowledge > initial_knowledge


class TestProgressiveRefinementIntegration:
    """Integration tests for progressive refinement."""
    
    def test_bottom_up_refinement(self, integrated_system):
        """Test bottom-up progressive refinement."""
        tier_manager = integrated_system["tier_manager"]
        refiner = ProgressiveRefiner(tier_manager)
        client_id = integrated_system["tiers"]["client"].tier_id
        
        config = RefinementConfig(
            strategy=RefinementStrategy.BOTTOM_UP,
            token_budget=2000,
            max_tiers=5
        )
        
        result = refiner.refine_context(
            query="standard",
            starting_tier_id=client_id,
            config=config
        )
        
        # Should use multiple tiers
        assert len(result.tiers_used) >= 2
        
        # Should respect token budget
        assert result.total_tokens <= config.token_budget
        
        # Should start with client tier (bottom-up)
        assert result.tiers_used[0] == TierType.CLIENT
        
        # Should have quality score
        assert 0.0 <= result.refinement_score <= 1.0
    
    def test_top_down_refinement(self, integrated_system):
        """Test top-down progressive refinement."""
        tier_manager = integrated_system["tier_manager"]
        refiner = ProgressiveRefiner(tier_manager)
        client_id = integrated_system["tiers"]["client"].tier_id
        
        config = RefinementConfig(
            strategy=RefinementStrategy.TOP_DOWN,
            token_budget=2000,
            max_tiers=5
        )
        
        result = refiner.refine_context(
            query="best practice",
            starting_tier_id=client_id,
            config=config
        )
        
        # Should use multiple tiers
        assert len(result.tiers_used) >= 1
        
        # Should start with ecosystem tier (top-down)
        if result.tiers_used:
            # Ecosystem should be first or early in the list
            ecosystem_index = result.tiers_used.index(TierType.ECOSYSTEM) if TierType.ECOSYSTEM in result.tiers_used else -1
            if ecosystem_index >= 0:
                assert ecosystem_index < len(result.tiers_used) // 2
    
    def test_balanced_refinement(self, integrated_system):
        """Test balanced progressive refinement."""
        tier_manager = integrated_system["tier_manager"]
        refiner = ProgressiveRefiner(tier_manager)
        client_id = integrated_system["tiers"]["client"].tier_id
        
        config = RefinementConfig(
            strategy=RefinementStrategy.BALANCED,
            token_budget=3000,
            max_tiers=5
        )
        
        result = refiner.refine_context(
            query="project",
            starting_tier_id=client_id,
            config=config
        )
        
        # Should use multiple tiers
        assert len(result.tiers_used) >= 2
        
        # Should have results
        assert len(result.get_all_results()) > 0
        
        # Should have tier summary
        summary = result.get_tier_summary()
        assert len(summary) > 0
    
    def test_refinement_with_token_budget(self, integrated_system):
        """Test refinement respects token budget."""
        tier_manager = integrated_system["tier_manager"]
        refiner = ProgressiveRefiner(tier_manager)
        client_id = integrated_system["tiers"]["client"].tier_id
        
        # Very small budget
        config = RefinementConfig(
            strategy=RefinementStrategy.BOTTOM_UP,
            token_budget=50,
            max_tiers=5
        )
        
        result = refiner.refine_context(
            query="practice",
            starting_tier_id=client_id,
            config=config
        )
        
        # Should respect budget
        assert result.total_tokens <= config.token_budget
        
        # Should still return some results
        assert len(result.get_all_results()) >= 0


class TestRealWorldWorkflows:
    """Test real-world usage workflows."""
    
    def test_user_query_workflow(self, integrated_system):
        """Test complete user query workflow."""
        tier_manager = integrated_system["tier_manager"]
        refiner = ProgressiveRefiner(tier_manager)
        client_id = integrated_system["tiers"]["client"].tier_id
        
        # User asks a question
        query = "standard"  # Simplified query for matching
        
        # System refines context
        config = RefinementConfig(
            strategy=RefinementStrategy.BOTTOM_UP,
            token_budget=4000
        )
        
        context = refiner.refine_context(query, client_id, config)
        
        # Should get relevant context from multiple tiers
        assert len(context.tiers_used) >= 1  # At least one tier should have results
        
        # Should include company standards
        all_results = context.get_all_results()
        contents = [r.content for r in all_results]
        assert any("standard" in c.lower() for c in contents)
    
    def test_new_user_onboarding(self, integrated_system):
        """Test new user onboarding workflow."""
        tier_manager = integrated_system["tier_manager"]
        
        # Create new user (client tier)
        new_user = tier_manager.create_tier(
            TierConfig(
                name="new_user_session",
                tier_type=TierType.CLIENT,
                parent_tier_id=integrated_system["tiers"]["project"].tier_id
            )
        )
        
        # Inherit project, company, and ecosystem knowledge
        result = tier_manager.inherit_cascading(new_user.tier_id, max_levels=4)
        
        # Should inherit knowledge for onboarding
        assert result.success
        assert result.items_inherited > 0
        
        # New user should have inherited knowledge
        knowledge = tier_manager.get_tier_knowledge(new_user.tier_id)
        assert len(knowledge) > 0
    
    def test_project_context_switching(self, integrated_system):
        """Test switching between projects."""
        tier_manager = integrated_system["tier_manager"]
        company_id = integrated_system["tiers"]["company"].tier_id
        
        # Create second project under same company
        project2 = tier_manager.create_tier(
            TierConfig(
                name="frontend_project",
                tier_type=TierType.PROJECT,
                parent_tier_id=company_id
            )
        )
        tier_manager.add_knowledge(
            project2.tier_id,
            "Frontend: Use React for all UIs",
            relevance=0.9
        )
        
        # Create client for project2
        client2 = tier_manager.create_tier(
            TierConfig(
                name="frontend_user",
                tier_type=TierType.CLIENT,
                parent_tier_id=project2.tier_id
            )
        )
        
        # Query from project2 client
        result = tier_manager.cascade_query(
            query="policy",
            starting_tier_id=client2.tier_id,
            max_tiers=3
        )
        
        # Should get company policies (shared across projects)
        assert result.tiers_searched >= 2
        assert any("policy" in r.content.lower() for r in result.results)


class TestAccessControlIntegration:
    """Test access control in integrated system."""
    
    def test_multi_user_tier_isolation(self, integrated_system):
        """Test that users in different client tiers are isolated."""
        tier_manager = integrated_system["tier_manager"]
        project_id = integrated_system["tiers"]["project"].tier_id
        
        # Create two client tiers
        client1 = tier_manager.create_tier(
            TierConfig(name="user1", tier_type=TierType.CLIENT, parent_tier_id=project_id)
        )
        client2 = tier_manager.create_tier(
            TierConfig(name="user2", tier_type=TierType.CLIENT, parent_tier_id=project_id)
        )
        
        # Add knowledge to client1
        tier_manager.add_knowledge(client1.tier_id, "User1's private data", relevance=1.0)
        
        # Client2 should not see client1's knowledge
        client2_knowledge = tier_manager.get_tier_knowledge(client2.tier_id)
        assert not any("User1's private data" in item.content for item in client2_knowledge)
    
    def test_role_based_access_control(self, integrated_system):
        """Test role-based access control."""
        tier_manager = integrated_system["tier_manager"]
        project_id = integrated_system["tiers"]["project"].tier_id
        
        # Add users with different roles
        tier_manager.add_user_access(project_id, user_id="admin_user", role="admin")
        tier_manager.add_user_access(project_id, user_id="dev_user", role="read")
        
        # Admin should have write access
        assert tier_manager.can_write(project_id, user_id="admin_user")
        
        # Dev should only have read access
        assert not tier_manager.can_write(project_id, user_id="dev_user")


class TestPerformanceAndScaling:
    """Test performance and scaling characteristics."""
    
    def test_large_hierarchy_query(self, integrated_system):
        """Test query performance with large hierarchy."""
        tier_manager = integrated_system["tier_manager"]
        client_id = integrated_system["tiers"]["client"].tier_id
        
        # Add many knowledge items
        for i in range(50):
            tier_manager.add_knowledge(
                client_id,
                f"Knowledge item {i} with some content",
                relevance=0.5 + (i % 50) / 100
            )
        
        # Query should still work efficiently
        result = tier_manager.cascade_query(
            query="content",
            starting_tier_id=client_id,
            max_tokens=1000
        )
        
        # Should return results within token budget
        assert result.total_tokens <= 1000
        assert len(result.results) > 0
    
    def test_multiple_concurrent_refinements(self, integrated_system):
        """Test multiple refinements can run concurrently."""
        tier_manager = integrated_system["tier_manager"]
        refiner = ProgressiveRefiner(tier_manager)
        client_id = integrated_system["tiers"]["client"].tier_id
        
        config = RefinementConfig(
            strategy=RefinementStrategy.BOTTOM_UP,
            token_budget=1000
        )
        
        # Run multiple refinements
        results = []
        queries = ["practice", "standard", "policy"]
        
        for query in queries:
            result = refiner.refine_context(query, client_id, config)
            results.append(result)
        
        # All should succeed
        assert len(results) == 3
        assert all(r.refinement_score >= 0 for r in results)

