"""
Integration tests for Workflow Integration - Phase 3 Day 3
Tests integration between Memory Agent and all 4 workflows.
"""

import pytest
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

from services.memory_agent.domain.entities.memory_context import (
    MemoryContext,
    WorkflowResult,
    WorkflowType
)
from services.memory_agent.domain.services.context_manager import ContextManager
from services.memory_agent.domain.services.artifact_linker import ArtifactLinker
from services.memory_agent.infrastructure.integrations.workflow_integration import (
    WorkflowIntegrationHelper
)


@pytest.fixture
def context_manager():
    """Create ContextManager instance for testing."""
    return ContextManager(redis_client=None)  # Use local cache


@pytest.fixture
def artifact_linker():
    """Create ArtifactLinker instance for testing."""
    return ArtifactLinker()


@pytest.fixture
def workflow_helper(context_manager, artifact_linker):
    """Create WorkflowIntegrationHelper instance for testing."""
    return WorkflowIntegrationHelper(
        context_manager=context_manager,
        artifact_linker=artifact_linker
    )


class TestWorkflowAIntegration:
    """Test Workflow A (Feature Decomposition) integration."""
    
    @pytest.mark.asyncio
    async def test_store_workflow_a_result(self, workflow_helper):
        """Test storing Workflow A result with artifacts."""
        workflow_id = "wf_a_test_001"
        feature_breakdown = {
            "feature_id": "feat_001",
            "user_stories": 10,
            "technical_tasks": 25,
            "total_story_points": 45
        }
        prompts_used = ["prompt_decomp_001", "prompt_decomp_002"]
        documents_generated = ["doc_breakdown_001"]
        duration_ms = 2500.0
        
        result = await workflow_helper.store_workflow_a_result(
            workflow_id=workflow_id,
            feature_breakdown=feature_breakdown,
            prompts_used=prompts_used,
            documents_generated=documents_generated,
            duration_ms=duration_ms
        )
        
        # Verify result was stored
        assert result.workflow_id == workflow_id
        assert result.workflow_type == WorkflowType.WORKFLOW_A
        assert result.success is True
        assert result.duration_ms == duration_ms
        assert "llm-gateway" in result.services_called
        
        # Verify context was created
        context = await workflow_helper.get_workflow_context(workflow_id)
        assert context is not None
        
        # Verify artifacts were linked
        assert len(context.linked_prompts) == 2
        assert len(context.linked_documents) == 1
        assert "prompt_decomp_001" in context.linked_prompts
        assert "doc_breakdown_001" in context.linked_documents
    
    @pytest.mark.asyncio
    async def test_workflow_a_with_parent(self, workflow_helper):
        """Test Workflow A with parent workflow."""
        parent_id = "parent_orch_001"
        workflow_id = "wf_a_child_001"
        
        result = await workflow_helper.store_workflow_a_result(
            workflow_id=workflow_id,
            feature_breakdown={"test": "data"},
            prompts_used=[],
            documents_generated=[],
            duration_ms=1000.0,
            parent_workflow_id=parent_id
        )
        
        # Verify parent linkage
        context = await workflow_helper.get_workflow_context(workflow_id)
        assert context.parent_workflow_id == parent_id


class TestWorkflowBIntegration:
    """Test Workflow B (Historical Context) integration."""
    
    @pytest.mark.asyncio
    async def test_store_workflow_b_result(self, workflow_helper):
        """Test storing Workflow B result with artifacts."""
        workflow_id = "wf_b_test_001"
        historical_context = {
            "total_sources": 50,
            "relevance_score": 0.85,
            "jira_tickets": 12,
            "confluence_pages": 8
        }
        documents_retrieved = ["doc_hist_001", "doc_hist_002"]
        jira_tickets = ["PROJ-123", "PROJ-456"]
        confluence_pages = ["page_001", "page_002"]
        duration_ms = 3500.0
        
        result = await workflow_helper.store_workflow_b_result(
            workflow_id=workflow_id,
            historical_context=historical_context,
            documents_retrieved=documents_retrieved,
            jira_tickets=jira_tickets,
            confluence_pages=confluence_pages,
            duration_ms=duration_ms
        )
        
        # Verify result was stored
        assert result.workflow_id == workflow_id
        assert result.workflow_type == WorkflowType.WORKFLOW_B
        assert result.success is True
        assert "source-agent" in result.services_called
        
        # Verify context
        context = await workflow_helper.get_workflow_context(workflow_id)
        assert context is not None
        
        # Verify artifacts (docs + custom artifacts for Jira/Confluence)
        all_artifacts = context.get_all_artifacts()
        assert len(all_artifacts) >= 6  # 2 docs + 2 jira + 2 confluence
        
        # Verify document links
        assert len(context.linked_documents) == 2
    
    @pytest.mark.asyncio
    async def test_workflow_b_custom_artifacts(self, workflow_helper):
        """Test that Jira and Confluence artifacts are properly linked."""
        workflow_id = "wf_b_artifacts_001"
        
        await workflow_helper.store_workflow_b_result(
            workflow_id=workflow_id,
            historical_context={},
            documents_retrieved=[],
            jira_tickets=["PROJ-789"],
            confluence_pages=["page_003"],
            duration_ms=2000.0
        )
        
        context = await workflow_helper.get_workflow_context(workflow_id)
        artifacts = context.get_all_artifacts()
        
        # Find Jira and Confluence artifacts
        jira_artifacts = [a for a in artifacts if a.artifact_type == "jira_ticket"]
        confluence_artifacts = [a for a in artifacts if a.artifact_type == "confluence_page"]
        
        assert len(jira_artifacts) == 1
        assert len(confluence_artifacts) == 1
        assert "PROJ-789" in jira_artifacts[0].artifact_id


class TestWorkflowCIntegration:
    """Test Workflow C (Timeline Analysis) integration."""
    
    @pytest.mark.asyncio
    async def test_store_workflow_c_result(self, workflow_helper):
        """Test storing Workflow C result with artifacts."""
        workflow_id = "wf_c_test_001"
        timeline_analysis = {
            "estimated_duration_days": 90,
            "estimated_sprints": 9,
            "confidence_score": 0.78,
            "risks": 3
        }
        simulation_results = ["sim_001", "sim_002"]
        reports_generated = ["report_001"]
        duration_ms = 4000.0
        
        result = await workflow_helper.store_workflow_c_result(
            workflow_id=workflow_id,
            timeline_analysis=timeline_analysis,
            simulation_results=simulation_results,
            reports_generated=reports_generated,
            duration_ms=duration_ms
        )
        
        # Verify result
        assert result.workflow_id == workflow_id
        assert result.workflow_type == WorkflowType.WORKFLOW_C
        assert result.success is True
        assert "project-simulation" in result.services_called
        
        # Verify context
        context = await workflow_helper.get_workflow_context(workflow_id)
        assert context is not None
        
        # Verify artifacts
        all_artifacts = context.get_all_artifacts()
        assert len(all_artifacts) >= 3  # 2 simulations + 1 report
        
        # Verify simulation artifacts
        sim_artifacts = [a for a in all_artifacts if a.artifact_type == "simulation"]
        assert len(sim_artifacts) == 2


class TestWorkflowDIntegration:
    """Test Workflow D (Skills Matching) integration."""
    
    @pytest.mark.asyncio
    async def test_store_workflow_d_result(self, workflow_helper):
        """Test storing Workflow D result with artifacts."""
        workflow_id = "wf_d_test_001"
        skills_matching = {
            "team_size": 5,
            "skill_gaps": 2,
            "readiness_score": 0.85,
            "allocations": 15
        }
        team_members = ["user_alice", "user_bob", "user_charlie"]
        allocations = [
            {"member_id": "user_alice", "task_id": "task_001"},
            {"member_id": "user_bob", "task_id": "task_002"}
        ]
        duration_ms = 1500.0
        
        result = await workflow_helper.store_workflow_d_result(
            workflow_id=workflow_id,
            skills_matching=skills_matching,
            team_members=team_members,
            allocations=allocations,
            duration_ms=duration_ms
        )
        
        # Verify result
        assert result.workflow_id == workflow_id
        assert result.workflow_type == WorkflowType.WORKFLOW_D
        assert result.success is True
        assert "user-store" in result.services_called
        
        # Verify context
        context = await workflow_helper.get_workflow_context(workflow_id)
        assert context is not None
        
        # Verify user links
        assert len(context.linked_users) == 3
        assert "user_alice" in context.linked_users
        
        # Verify allocation artifacts
        allocation_artifacts = [a for a in context.get_all_artifacts() if a.artifact_type == "allocation"]
        assert len(allocation_artifacts) == 2


class TestOrchestrationIntegration:
    """Test orchestration workflow integration."""
    
    @pytest.mark.asyncio
    async def test_store_orchestration_result(self, workflow_helper):
        """Test storing orchestration result."""
        workflow_id = "orch_test_001"
        orchestration_data = {
            "total_workflows": 4,
            "successful": 4,
            "failed": 0,
            "total_duration_ms": 10000.0
        }
        child_workflow_ids = ["wf_a_001", "wf_b_001", "wf_c_001", "wf_d_001"]
        duration_ms = 12000.0
        
        result = await workflow_helper.store_orchestration_result(
            workflow_id=workflow_id,
            orchestration_data=orchestration_data,
            child_workflow_ids=child_workflow_ids,
            duration_ms=duration_ms
        )
        
        # Verify result
        assert result.workflow_id == workflow_id
        assert result.workflow_type == WorkflowType.ORCHESTRATION
        assert result.success is True
        
        # Verify context
        context = await workflow_helper.get_workflow_context(workflow_id)
        assert context is not None
        
        # Verify child workflow links
        child_artifacts = [a for a in context.get_all_artifacts() if a.artifact_type == "workflow"]
        assert len(child_artifacts) == 4
    
    @pytest.mark.asyncio
    async def test_aggregated_results(self, workflow_helper):
        """Test getting aggregated results from child workflows."""
        parent_id = "orch_agg_001"
        
        # Store parent workflow
        await workflow_helper.store_orchestration_result(
            workflow_id=parent_id,
            orchestration_data={},
            child_workflow_ids=["child_1", "child_2"],
            duration_ms=5000.0
        )
        
        # Store child workflows
        await workflow_helper.store_workflow_a_result(
            workflow_id="child_1",
            feature_breakdown={"test": "data1"},
            prompts_used=[],
            documents_generated=[],
            duration_ms=1000.0,
            parent_workflow_id=parent_id
        )
        
        await workflow_helper.store_workflow_b_result(
            workflow_id="child_2",
            historical_context={"test": "data2"},
            documents_retrieved=[],
            jira_tickets=[],
            confluence_pages=[],
            duration_ms=2000.0,
            parent_workflow_id=parent_id
        )
        
        # Get aggregated results
        aggregated = await workflow_helper.get_aggregated_results(parent_id)
        
        assert aggregated["parent_workflow_id"] == parent_id
        assert aggregated["total_child_workflows"] == 2
        assert aggregated["successful_workflows"] == 2


class TestWorkflowHelperUtilities:
    """Test utility methods of WorkflowIntegrationHelper."""
    
    @pytest.mark.asyncio
    async def test_track_service_call(self, workflow_helper, context_manager):
        """Test tracking service calls."""
        workflow_id = "wf_track_001"
        
        # Create context
        await context_manager.create_context(
            workflow_id=workflow_id,
            workflow_type=WorkflowType.WORKFLOW_A
        )
        
        # Track service call
        await workflow_helper.track_service_call(
            workflow_id=workflow_id,
            service_name="llm-gateway",
            operation="generate",
            duration_ms=500.0,
            success=True
        )
        
        # Verify tracking
        context = await workflow_helper.get_workflow_context(workflow_id)
        assert "service_calls" in context.metadata
        assert len(context.metadata["service_calls"]) == 1
        assert context.metadata["service_calls"][0]["service"] == "llm-gateway"
    
    @pytest.mark.asyncio
    async def test_link_workflow_artifacts(self, workflow_helper, context_manager):
        """Test bulk linking of artifacts."""
        workflow_id = "wf_bulk_001"
        
        # Create context
        await context_manager.create_context(
            workflow_id=workflow_id,
            workflow_type=WorkflowType.ORCHESTRATION
        )
        
        # Bulk link artifacts
        total_linked = await workflow_helper.link_workflow_artifacts(
            workflow_id=workflow_id,
            documents=["doc_1", "doc_2"],
            prompts=["prompt_1"],
            users=["user_1", "user_2", "user_3"]
        )
        
        assert total_linked == 6  # 2 + 1 + 3
        
        # Verify links
        context = await workflow_helper.get_workflow_context(workflow_id)
        assert len(context.linked_documents) == 2
        assert len(context.linked_prompts) == 1
        assert len(context.linked_users) == 3
    
    @pytest.mark.asyncio
    async def test_get_synthesized_context(self, workflow_helper):
        """Test getting synthesized context view."""
        workflow_id = "wf_synth_001"
        
        # Store workflow result
        await workflow_helper.store_workflow_a_result(
            workflow_id=workflow_id,
            feature_breakdown={"test": "synthesis"},
            prompts_used=["prompt_1"],
            documents_generated=["doc_1"],
            duration_ms=1000.0
        )
        
        # Get synthesized view
        synthesized = await workflow_helper.get_synthesized_context(workflow_id)
        
        assert synthesized["workflow_id"] == workflow_id
        assert "success_rate" in synthesized
        assert "total_artifacts" in synthesized


class TestEndToEndWorkflow:
    """End-to-end test of complete workflow execution."""
    
    @pytest.mark.asyncio
    async def test_complete_roadmap_workflow(self, workflow_helper):
        """Test complete roadmap generation workflow with all 4 workflows."""
        parent_id = "orch_complete_001"
        
        # Step 1: Store orchestration workflow
        await workflow_helper.store_orchestration_result(
            workflow_id=parent_id,
            orchestration_data={"query": "Build authentication system"},
            child_workflow_ids=["wf_a_001", "wf_b_001", "wf_c_001", "wf_d_001"],
            duration_ms=15000.0
        )
        
        # Step 2: Store Workflow A (Feature Decomposition)
        await workflow_helper.store_workflow_a_result(
            workflow_id="wf_a_001",
            feature_breakdown={
                "features": 1,
                "user_stories": 8,
                "tasks": 20
            },
            prompts_used=["prompt_decomp_001", "prompt_decomp_002"],
            documents_generated=["doc_breakdown_001"],
            duration_ms=2500.0,
            parent_workflow_id=parent_id
        )
        
        # Step 3: Store Workflow B (Historical Context)
        await workflow_helper.store_workflow_b_result(
            workflow_id="wf_b_001",
            historical_context={"sources": 45, "relevance": 0.85},
            documents_retrieved=["doc_hist_001", "doc_hist_002"],
            jira_tickets=["AUTH-123"],
            confluence_pages=["page_auth_001"],
            duration_ms=3500.0,
            parent_workflow_id=parent_id
        )
        
        # Step 4: Store Workflow C (Timeline Analysis)
        await workflow_helper.store_workflow_c_result(
            workflow_id="wf_c_001",
            timeline_analysis={"duration_days": 60, "sprints": 6},
            simulation_results=["sim_001"],
            reports_generated=["report_timeline_001"],
            duration_ms=4000.0,
            parent_workflow_id=parent_id
        )
        
        # Step 5: Store Workflow D (Skills Matching)
        await workflow_helper.store_workflow_d_result(
            workflow_id="wf_d_001",
            skills_matching={"readiness": 0.9, "gaps": 1},
            team_members=["user_alice", "user_bob"],
            allocations=[{"member_id": "user_alice", "task_id": "task_001"}],
            duration_ms=1500.0,
            parent_workflow_id=parent_id
        )
        
        # Verify complete workflow
        parent_context = await workflow_helper.get_workflow_context(parent_id)
        assert parent_context is not None
        
        # Get aggregated results
        aggregated = await workflow_helper.get_aggregated_results(parent_id)
        assert aggregated["total_child_workflows"] == 4
        assert aggregated["successful_workflows"] == 4
        assert aggregated["failed_workflows"] == 0
        
        # Get synthesized context
        synthesized = await workflow_helper.get_synthesized_context(parent_id)
        assert synthesized["total_workflows"] >= 5  # Parent + 4 children
        
        # Verify all artifact types are present
        assert aggregated["total_artifacts"] > 0

