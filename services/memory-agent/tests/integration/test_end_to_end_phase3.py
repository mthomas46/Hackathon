"""
End-to-End Integration Tests - Phase 3 Day 5
Comprehensive tests for complete Memory Agent Phase 3 functionality.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from services.memory_agent.domain.entities.memory_context import (
    MemoryContext,
    WorkflowResult,
    ArtifactLink,
    WorkflowType
)
from services.memory_agent.domain.services.context_manager import ContextManager
from services.memory_agent.domain.services.artifact_linker import ArtifactLinker
from services.memory_agent.domain.services.context_aggregator import ContextAggregator
from services.memory_agent.domain.services.context_search import ContextSearch
from services.memory_agent.infrastructure.integrations.workflow_integration import (
    WorkflowIntegrationHelper
)


@pytest.fixture
def full_stack():
    """Create complete Phase 3 stack for testing."""
    context_manager = ContextManager(redis_client=None)
    artifact_linker = ArtifactLinker()
    context_aggregator = ContextAggregator()
    context_search = ContextSearch()
    workflow_helper = WorkflowIntegrationHelper(context_manager, artifact_linker)
    
    return {
        "context_manager": context_manager,
        "artifact_linker": artifact_linker,
        "context_aggregator": context_aggregator,
        "context_search": context_search,
        "workflow_helper": workflow_helper
    }


class TestCompleteRoadmapGeneration:
    """Test complete roadmap generation workflow end-to-end."""
    
    @pytest.mark.asyncio
    async def test_complete_roadmap_workflow_e2e(self, full_stack):
        """
        Test complete Enhanced Roadmap v2.0 workflow from start to finish.
        
        This test simulates:
        1. User submits natural language query
        2. Orchestrator creates parent workflow
        3. All 4 workflows (A, B, C, D) execute in parallel
        4. Results are stored in Memory Agent
        5. Artifacts are linked automatically
        6. Results are aggregated
        7. Insights are extracted
        8. Recommendations are generated
        """
        helper = full_stack["workflow_helper"]
        aggregator = full_stack["context_aggregator"]
        search = full_stack["context_search"]
        
        # Step 1: Create orchestration workflow
        parent_id = "orch_e2e_001"
        await helper.store_orchestration_result(
            workflow_id=parent_id,
            orchestration_data={
                "query": "Build user authentication system for mobile app",
                "team_id": "mobile-team-01",
                "priority": "high"
            },
            child_workflow_ids=["wf_a_e2e", "wf_b_e2e", "wf_c_e2e", "wf_d_e2e"],
            duration_ms=15000.0
        )
        
        # Step 2: Execute Workflow A (Feature Decomposition)
        await helper.store_workflow_a_result(
            workflow_id="wf_a_e2e",
            feature_breakdown={
                "feature_id": "auth_system",
                "user_stories": 8,
                "technical_tasks": 20,
                "total_story_points": 45,
                "complexity": "medium"
            },
            prompts_used=["prompt_decomp_001", "prompt_decomp_002"],
            documents_generated=["doc_auth_breakdown"],
            duration_ms=2500.0,
            parent_workflow_id=parent_id
        )
        
        # Step 3: Execute Workflow B (Historical Context)
        await helper.store_workflow_b_result(
            workflow_id="wf_b_e2e",
            historical_context={
                "total_sources": 45,
                "relevance_score": 0.85,
                "similar_features": 3
            },
            documents_retrieved=["doc_hist_auth_001", "doc_hist_auth_002"],
            jira_tickets=["AUTH-123", "AUTH-456"],
            confluence_pages=["page_auth_patterns"],
            duration_ms=3500.0,
            parent_workflow_id=parent_id
        )
        
        # Step 3: Execute Workflow C (Timeline Analysis)
        await helper.store_workflow_c_result(
            workflow_id="wf_c_e2e",
            timeline_analysis={
                "estimated_duration_days": 60,
                "estimated_sprints": 6,
                "confidence_score": 0.78,
                "critical_path": 45
            },
            simulation_results=["sim_auth_001"],
            reports_generated=["report_timeline_auth"],
            duration_ms=4000.0,
            parent_workflow_id=parent_id
        )
        
        # Step 4: Execute Workflow D (Skills Matching)
        await helper.store_workflow_d_result(
            workflow_id="wf_d_e2e",
            skills_matching={
                "team_size": 5,
                "skill_gaps": 1,
                "readiness_score": 0.9,
                "allocations": 12
            },
            team_members=["user_alice", "user_bob", "user_charlie"],
            allocations=[
                {"member_id": "user_alice", "task_id": "task_backend"},
                {"member_id": "user_bob", "task_id": "task_frontend"}
            ],
            duration_ms=1500.0,
            parent_workflow_id=parent_id
        )
        
        # Step 5: Retrieve all contexts
        parent_context = await helper.get_workflow_context(parent_id)
        child_contexts = []
        for wf_id in ["wf_a_e2e", "wf_b_e2e", "wf_c_e2e", "wf_d_e2e"]:
            ctx = await helper.get_workflow_context(wf_id)
            if ctx:
                child_contexts.append(ctx)
        
        # Verify all workflows created
        assert parent_context is not None
        assert len(child_contexts) == 4
        
        # Step 6: Aggregate results
        aggregated = await helper.get_aggregated_results(parent_id)
        
        assert aggregated["total_child_workflows"] == 4
        assert aggregated["successful_workflows"] == 4
        assert aggregated["failed_workflows"] == 0
        
        # Step 7: Get synthesized context
        synthesized = await helper.get_synthesized_context(parent_id)
        
        assert synthesized["workflow_id"] == parent_id
        assert synthesized["total_workflows"] >= 5  # Parent + 4 children
        assert synthesized["successful_workflows"] == 5
        
        # Step 8: Aggregate all child contexts
        all_aggregated = await aggregator.aggregate_parallel_workflows(child_contexts)
        
        assert all_aggregated["total_workflows"] == 4
        assert all_aggregated["overall_success_rate"] == 1.0  # All succeeded
        assert all_aggregated["total_artifacts"] > 0
        
        # Step 9: Extract insights
        insights = await aggregator.extract_key_insights(all_aggregated)
        
        assert len(insights) > 0
        insights_text = " ".join(insights)
        assert "success" in insights_text.lower()
        
        # Step 10: Search for similar roadmaps
        similar = await search.find_similar_contexts(
            parent_context,
            child_contexts,
            similarity_threshold=0.0,
            limit=5
        )
        
        # Should find some similarity
        assert isinstance(similar, list)
        
        # Verify complete traceability
        assert parent_context.total_workflows > 0
        assert all_aggregated["total_artifacts"] >= 10  # Should have many artifacts


class TestPerformanceAndScalability:
    """Test performance and scalability of Phase 3 components."""
    
    @pytest.mark.asyncio
    async def test_large_scale_aggregation(self, full_stack):
        """Test aggregation with many workflows."""
        aggregator = full_stack["context_aggregator"]
        
        # Create 50 mock contexts
        contexts = []
        for i in range(50):
            ctx = MemoryContext(
                context_id=f"ctx_perf_{i}",
                workflow_id=f"wf_perf_{i}",
                parent_workflow_id="parent_perf",
                workflow_type=WorkflowType.WORKFLOW_A if i % 2 == 0 else WorkflowType.WORKFLOW_B
            )
            
            result = WorkflowResult(
                result_id=f"res_perf_{i}",
                workflow_id=f"wf_perf_{i}",
                workflow_type=ctx.workflow_type,
                result_data={"iteration": i},
                success=True,
                duration_ms=1000.0 + (i * 10)
            )
            ctx.add_workflow_result(result)
            contexts.append(ctx)
        
        # Aggregate - should complete quickly
        start = datetime.utcnow()
        aggregated = await aggregator.aggregate_parallel_workflows(contexts)
        duration = (datetime.utcnow() - start).total_seconds()
        
        assert aggregated["total_workflows"] == 50
        assert duration < 1.0  # Should complete in under 1 second
    
    @pytest.mark.asyncio
    async def test_similarity_search_performance(self, full_stack):
        """Test similarity search performance with many contexts."""
        search = full_stack["context_search"]
        
        # Create 100 mock contexts
        contexts = []
        for i in range(100):
            ctx = MemoryContext(
                context_id=f"ctx_sim_{i}",
                workflow_id=f"wf_sim_{i}",
                parent_workflow_id=None,
                workflow_type=WorkflowType.WORKFLOW_A
            )
            contexts.append(ctx)
        
        target = contexts[0]
        candidates = contexts[1:]
        
        # Search - should complete quickly
        start = datetime.utcnow()
        similar = await search.find_similar_contexts(
            target,
            candidates,
            similarity_threshold=0.0,
            limit=10
        )
        duration = (datetime.utcnow() - start).total_seconds()
        
        assert len(similar) <= 10
        assert duration < 2.0  # Should complete in under 2 seconds


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    @pytest.mark.asyncio
    async def test_empty_context_handling(self, full_stack):
        """Test handling of empty contexts."""
        aggregator = full_stack["context_aggregator"]
        
        # Aggregate empty list
        aggregated = await aggregator.aggregate_parallel_workflows([])
        
        assert aggregated["total_workflows"] == 0
        assert aggregated["overall_success_rate"] == 0.0
        assert len(aggregated["insights"]) == 0
    
    @pytest.mark.asyncio
    async def test_failed_workflow_handling(self, full_stack):
        """Test handling of failed workflows."""
        helper = full_stack["workflow_helper"]
        context_manager = full_stack["context_manager"]
        
        # Store failed workflow
        await context_manager.store_workflow_result(
            workflow_id="wf_failed_001",
            workflow_type=WorkflowType.WORKFLOW_A,
            result_data={},
            success=False,
            error_message="Simulated failure",
            duration_ms=500.0
        )
        
        # Retrieve and verify
        context = await helper.get_workflow_context("wf_failed_001")
        
        assert context is not None
        assert context.failed_workflows == 1
        assert context.success_rate == 0.0
    
    @pytest.mark.asyncio
    async def test_missing_artifacts_handling(self, full_stack):
        """Test handling of missing artifact links."""
        artifact_linker = full_stack["artifact_linker"]
        
        ctx = MemoryContext(
            context_id="ctx_missing",
            workflow_id="wf_missing",
            parent_workflow_id=None,
            workflow_type=WorkflowType.WORKFLOW_A
        )
        
        # Try to remove non-existent artifact
        removed = await artifact_linker.remove_artifact_link(ctx, "nonexistent")
        
        assert removed is False


class TestDataIntegrity:
    """Test data integrity and consistency."""
    
    @pytest.mark.asyncio
    async def test_context_versioning(self, full_stack):
        """Test that context versioning works correctly."""
        context_manager = full_stack["context_manager"]
        
        # Create context
        ctx = await context_manager.create_context(
            workflow_id="wf_version_001",
            workflow_type=WorkflowType.WORKFLOW_A
        )
        
        initial_version = ctx.version
        
        # Store result (should increment version)
        await context_manager.store_workflow_result(
            workflow_id="wf_version_001",
            workflow_type=WorkflowType.WORKFLOW_A,
            result_data={"test": "data"},
            success=True,
            duration_ms=1000.0
        )
        
        # Retrieve updated context
        updated_ctx = await context_manager.get_context("wf_version_001")
        
        assert updated_ctx.version > initial_version
    
    @pytest.mark.asyncio
    async def test_artifact_deduplication(self, full_stack):
        """Test that artifacts are deduplicated properly."""
        aggregator = full_stack["context_aggregator"]
        
        # Create contexts with overlapping artifacts
        ctx1 = MemoryContext(
            context_id="ctx_dedup_1",
            workflow_id="wf_dedup_1",
            parent_workflow_id=None,
            workflow_type=WorkflowType.WORKFLOW_A
        )
        ctx1.link_document("doc_shared")
        ctx1.link_document("doc_1")
        
        ctx2 = MemoryContext(
            context_id="ctx_dedup_2",
            workflow_id="wf_dedup_2",
            parent_workflow_id=None,
            workflow_type=WorkflowType.WORKFLOW_B
        )
        ctx2.link_document("doc_shared")  # Duplicate
        ctx2.link_document("doc_2")
        
        # Aggregate
        aggregated = await aggregator.aggregate_parallel_workflows([ctx1, ctx2])
        
        # Should deduplicate doc_shared
        assert len(aggregated["documents"]) == 3  # doc_shared, doc_1, doc_2
        assert "doc_shared" in aggregated["documents"]
        assert aggregated["documents"].count("doc_shared") == 1


class TestComprehensiveFeatures:
    """Test comprehensive Phase 3 features."""
    
    @pytest.mark.asyncio
    async def test_complete_artifact_lifecycle(self, full_stack):
        """Test complete artifact lifecycle: create, link, retrieve, remove."""
        context_manager = full_stack["context_manager"]
        artifact_linker = full_stack["artifact_linker"]
        
        # Create context
        ctx = await context_manager.create_context(
            workflow_id="wf_artifact_lifecycle",
            workflow_type=WorkflowType.WORKFLOW_A
        )
        
        # Link various artifacts
        await artifact_linker.link_document(ctx, "doc_lifecycle_001", validate=False)
        await artifact_linker.link_prompt(ctx, "prompt_lifecycle_001", validate=False)
        await artifact_linker.link_user(ctx, "user_lifecycle_001", validate=False)
        
        # Verify links
        all_artifacts = await artifact_linker.get_all_artifacts(ctx)
        assert len(all_artifacts) == 3
        
        # Get cross-references
        cross_refs = await artifact_linker.get_cross_references(ctx)
        assert len(cross_refs["documents"]) == 1
        assert len(cross_refs["prompts"]) == 1
        assert len(cross_refs["users"]) == 1
        
        # Remove artifact
        removed = await artifact_linker.remove_artifact_link(ctx, "doc_lifecycle_001")
        assert removed is True
        
        # Verify removal
        all_artifacts_after = await artifact_linker.get_all_artifacts(ctx)
        assert len(all_artifacts_after) == 2
    
    @pytest.mark.asyncio
    async def test_pattern_identification_accuracy(self, full_stack):
        """Test pattern identification across workflows."""
        aggregator = full_stack["context_aggregator"]
        
        # Create contexts with clear patterns
        contexts = []
        for i in range(10):
            ctx = MemoryContext(
                context_id=f"ctx_pattern_{i}",
                workflow_id=f"wf_pattern_{i}",
                parent_workflow_id=None,
                workflow_type=WorkflowType.WORKFLOW_A
            )
            
            # All use same service
            result = WorkflowResult(
                result_id=f"res_pattern_{i}",
                workflow_id=f"wf_pattern_{i}",
                workflow_type=WorkflowType.WORKFLOW_A,
                result_data={},
                success=True,
                duration_ms=1000.0 + (i * 100),
                services_called=["llm-gateway", "prompt-store"]  # Common services
            )
            ctx.add_workflow_result(result)
            contexts.append(ctx)
        
        # Identify patterns
        patterns = await aggregator.identify_patterns(contexts)
        
        # Should identify common services
        assert "common_services" in patterns
        assert "llm-gateway" in patterns["common_services"]
        assert "prompt-store" in patterns["common_services"]
        
        # Should have timing patterns
        assert "timing_patterns" in patterns
        assert "workflow_a" in patterns["timing_patterns"]


class TestPhase3Integration:
    """Test integration of all Phase 3 components together."""
    
    @pytest.mark.asyncio
    async def test_all_services_working_together(self, full_stack):
        """Test that all Phase 3 services work together seamlessly."""
        # Get all services
        context_manager = full_stack["context_manager"]
        artifact_linker = full_stack["artifact_linker"]
        context_aggregator = full_stack["context_aggregator"]
        context_search = full_stack["context_search"]
        workflow_helper = full_stack["workflow_helper"]
        
        # Create parent workflow
        parent_id = "integration_parent"
        await workflow_helper.store_orchestration_result(
            workflow_id=parent_id,
            orchestration_data={"test": "integration"},
            child_workflow_ids=["child_1", "child_2"],
            duration_ms=5000.0
        )
        
        # Create child workflows
        for i in [1, 2]:
            await workflow_helper.store_workflow_a_result(
                workflow_id=f"child_{i}",
                feature_breakdown={"test": f"child{i}"},
                prompts_used=[f"prompt_{i}"],
                documents_generated=[f"doc_{i}"],
                duration_ms=2000.0,
                parent_workflow_id=parent_id
            )
        
        # Test ContextManager
        parent_ctx = await context_manager.get_context(parent_id)
        assert parent_ctx is not None
        
        # Test ArtifactLinker
        all_artifacts = await artifact_linker.get_all_artifacts(parent_ctx)
        assert len(all_artifacts) >= 1
        
        # Test ContextAggregator
        child_contexts = []
        for i in [1, 2]:
            ctx = await context_manager.get_context(f"child_{i}")
            if ctx:
                child_contexts.append(ctx)
        
        aggregated = await context_aggregator.aggregate_parallel_workflows(child_contexts)
        assert aggregated["total_workflows"] == 2
        
        # Test ContextSearch
        recent = await context_search.search_recent(
            child_contexts,
            hours=24,
            limit=10
        )
        assert len(recent) == 2
        
        # Test WorkflowIntegrationHelper
        synthesized = await workflow_helper.get_synthesized_context(parent_id)
        assert synthesized["workflow_id"] == parent_id
        
        # All services working! ✅

