"""
Integration tests for Context Aggregation & Search - Phase 3 Day 4
Tests aggregation, synthesis, and search functionality.
"""

import pytest
from datetime import datetime, timedelta

from services.memory_agent.domain.entities.memory_context import (
    MemoryContext,
    WorkflowResult,
    ArtifactLink,
    WorkflowType
)
from services.memory_agent.domain.services.context_aggregator import ContextAggregator
from services.memory_agent.domain.services.context_search import ContextSearch


@pytest.fixture
def context_aggregator():
    """Create ContextAggregator instance for testing."""
    return ContextAggregator()


@pytest.fixture
def context_search():
    """Create ContextSearch instance for testing."""
    return ContextSearch()


@pytest.fixture
def sample_contexts():
    """Create sample contexts for testing."""
    contexts = []
    
    # Workflow A context
    ctx_a = MemoryContext(
        context_id="ctx_a_001",
        workflow_id="wf_a_001",
        parent_workflow_id="parent_001",
        workflow_type=WorkflowType.WORKFLOW_A
    )
    ctx_a.link_document("doc_a_001")
    ctx_a.link_prompt("prompt_a_001")
    result_a = WorkflowResult(
        result_id="res_a_001",
        workflow_id="wf_a_001",
        workflow_type=WorkflowType.WORKFLOW_A,
        result_data={"features": 10},
        success=True,
        duration_ms=2500.0,
        services_called=["llm-gateway", "prompt-store"]
    )
    ctx_a.add_workflow_result(result_a)
    contexts.append(ctx_a)
    
    # Workflow B context
    ctx_b = MemoryContext(
        context_id="ctx_b_001",
        workflow_id="wf_b_001",
        parent_workflow_id="parent_001",
        workflow_type=WorkflowType.WORKFLOW_B
    )
    ctx_b.link_document("doc_b_001")
    ctx_b.link_document("doc_b_002")
    result_b = WorkflowResult(
        result_id="res_b_001",
        workflow_id="wf_b_001",
        workflow_type=WorkflowType.WORKFLOW_B,
        result_data={"sources": 50},
        success=True,
        duration_ms=3500.0,
        services_called=["doc-store", "source-agent"]
    )
    ctx_b.add_workflow_result(result_b)
    contexts.append(ctx_b)
    
    # Workflow C context
    ctx_c = MemoryContext(
        context_id="ctx_c_001",
        workflow_id="wf_c_001",
        parent_workflow_id="parent_001",
        workflow_type=WorkflowType.WORKFLOW_C
    )
    ctx_c.link_user("user_001")
    result_c = WorkflowResult(
        result_id="res_c_001",
        workflow_id="wf_c_001",
        workflow_type=WorkflowType.WORKFLOW_C,
        result_data={"duration_days": 90},
        success=True,
        duration_ms=4000.0,
        services_called=["project-simulation", "analysis-service"]
    )
    ctx_c.add_workflow_result(result_c)
    contexts.append(ctx_c)
    
    # Workflow D context (with failure)
    ctx_d = MemoryContext(
        context_id="ctx_d_001",
        workflow_id="wf_d_001",
        parent_workflow_id="parent_001",
        workflow_type=WorkflowType.WORKFLOW_D
    )
    ctx_d.link_user("user_001")
    ctx_d.link_user("user_002")
    result_d = WorkflowResult(
        result_id="res_d_001",
        workflow_id="wf_d_001",
        workflow_type=WorkflowType.WORKFLOW_D,
        result_data={},
        success=False,
        error_message="Test error",
        duration_ms=1000.0,
        services_called=["user-store"]
    )
    ctx_d.add_workflow_result(result_d)
    contexts.append(ctx_d)
    
    return contexts


class TestContextAggregator:
    """Test Context Aggregator service."""
    
    @pytest.mark.asyncio
    async def test_aggregate_parallel_workflows(self, context_aggregator, sample_contexts):
        """Test aggregating parallel workflow results."""
        aggregated = await context_aggregator.aggregate_parallel_workflows(sample_contexts)
        
        # Verify structure
        assert "aggregation_timestamp" in aggregated
        assert "total_workflows" in aggregated
        assert "overall_success_rate" in aggregated
        
        # Verify counts
        assert aggregated["total_workflows"] == 4
        assert aggregated["total_artifacts"] > 0
        
        # Verify workflow types
        assert len(aggregated["workflow_types"]) == 4
        assert WorkflowType.WORKFLOW_A.value in aggregated["workflow_types"]
        
        # Verify artifacts
        assert len(aggregated["documents"]) == 3  # doc_a_001, doc_b_001, doc_b_002
        assert len(aggregated["prompts"]) == 1   # prompt_a_001
        assert len(aggregated["users"]) == 2     # user_001, user_002 (deduplicated)
        
        # Verify services
        assert len(aggregated["services_called"]) > 0
        assert "llm-gateway" in aggregated["services_called"]
    
    @pytest.mark.asyncio
    async def test_aggregate_empty_workflows(self, context_aggregator):
        """Test aggregating empty list."""
        aggregated = await context_aggregator.aggregate_parallel_workflows([])
        
        assert aggregated["total_workflows"] == 0
        assert aggregated["overall_success_rate"] == 0.0
        assert len(aggregated["documents"]) == 0
    
    @pytest.mark.asyncio
    async def test_create_unified_view(self, context_aggregator, sample_contexts):
        """Test creating unified view from workflow results."""
        # Extract all workflow results
        all_results = []
        for context in sample_contexts:
            all_results.extend(context.workflow_results.values())
        
        unified = await context_aggregator.create_unified_view(all_results)
        
        # Verify structure
        assert "created_at" in unified
        assert "total_results" in unified
        assert "successful_results" in unified
        assert "failed_results" in unified
        
        # Verify counts
        assert unified["total_results"] == 4
        assert unified["successful_results"] == 3
        assert unified["failed_results"] == 1
        
        # Verify timeline
        assert len(unified["timeline"]) == 4
        assert all("workflow_id" in item for item in unified["timeline"])
        
        # Verify performance metrics
        assert "performance_metrics" in unified
        assert "fastest_ms" in unified["performance_metrics"]
        assert "slowest_ms" in unified["performance_metrics"]
        
        # Verify error summary
        assert len(unified["error_summary"]) == 1
        assert unified["error_summary"][0]["error"] == "Test error"
    
    @pytest.mark.asyncio
    async def test_extract_key_insights(self, context_aggregator, sample_contexts):
        """Test extracting key insights."""
        aggregated = await context_aggregator.aggregate_parallel_workflows(sample_contexts)
        insights = await context_aggregator.extract_key_insights(aggregated)
        
        # Verify insights generated
        assert len(insights) > 0
        assert isinstance(insights, list)
        assert all(isinstance(insight, str) for insight in insights)
        
        # Check for typical insight patterns
        insights_text = " ".join(insights)
        assert any(word in insights_text.lower() for word in ["success", "artifact", "service", "duration"])
    
    @pytest.mark.asyncio
    async def test_synthesize_recommendations(self, context_aggregator, sample_contexts):
        """Test synthesizing recommendations."""
        aggregated = await context_aggregator.aggregate_parallel_workflows(sample_contexts)
        
        all_results = []
        for context in sample_contexts:
            all_results.extend(context.workflow_results.values())
        unified = await context_aggregator.create_unified_view(all_results)
        
        recommendations = await context_aggregator.synthesize_recommendations(
            aggregated,
            unified
        )
        
        # Verify recommendations generated
        assert len(recommendations) > 0
        assert isinstance(recommendations, list)
        assert all(isinstance(rec, str) for rec in recommendations)
        
        # Should recommend investigating failure
        recommendations_text = " ".join(recommendations)
        assert "failed" in recommendations_text.lower() or "investigate" in recommendations_text.lower()
    
    @pytest.mark.asyncio
    async def test_identify_patterns(self, context_aggregator, sample_contexts):
        """Test identifying patterns across workflows."""
        patterns = await context_aggregator.identify_patterns(sample_contexts)
        
        # Verify structure
        assert "common_services" in patterns
        assert "frequent_artifacts" in patterns
        assert "timing_patterns" in patterns
        assert "success_patterns" in patterns
        
        # Verify patterns found
        assert isinstance(patterns["common_services"], list)
        assert isinstance(patterns["frequent_artifacts"], list)
        assert isinstance(patterns["timing_patterns"], dict)
        assert isinstance(patterns["success_patterns"], dict)


class TestContextSearch:
    """Test Context Search service."""
    
    @pytest.mark.asyncio
    async def test_search_by_workflow_type(self, context_search, sample_contexts):
        """Test searching by workflow type."""
        results = await context_search.search_by_workflow_type(
            sample_contexts,
            WorkflowType.WORKFLOW_A,
            limit=10
        )
        
        assert len(results) == 1
        assert results[0].workflow_type == WorkflowType.WORKFLOW_A
    
    @pytest.mark.asyncio
    async def test_search_by_date_range(self, context_search, sample_contexts):
        """Test searching by date range."""
        start_date = datetime.utcnow() - timedelta(hours=1)
        end_date = datetime.utcnow() + timedelta(hours=1)
        
        results = await context_search.search_by_date_range(
            sample_contexts,
            start_date,
            end_date,
            limit=10
        )
        
        # All sample contexts should be within range
        assert len(results) == 4
    
    @pytest.mark.asyncio
    async def test_search_by_success_rate(self, context_search, sample_contexts):
        """Test searching by success rate."""
        # Search for high success rate
        results = await context_search.search_by_success_rate(
            sample_contexts,
            min_success_rate=0.9,
            max_success_rate=1.0,
            limit=10
        )
        
        # Should find 3 successful workflows
        assert len(results) == 3
        assert all(ctx.success_rate >= 0.9 for ctx in results)
    
    @pytest.mark.asyncio
    async def test_search_by_artifacts(self, context_search, sample_contexts):
        """Test searching by artifact presence."""
        # Search for contexts with documents
        results = await context_search.search_by_artifacts(
            sample_contexts,
            has_documents=True,
            limit=10
        )
        
        # Should find contexts A and B
        assert len(results) == 2
        assert all(len(ctx.linked_documents) > 0 for ctx in results)
    
    @pytest.mark.asyncio
    async def test_find_similar_contexts(self, context_search, sample_contexts):
        """Test finding similar contexts."""
        target = sample_contexts[0]  # Workflow A
        candidates = sample_contexts[1:]  # Rest
        
        similar = await context_search.find_similar_contexts(
            target,
            candidates,
            similarity_threshold=0.0,  # Low threshold to get results
            limit=10
        )
        
        # Should find some similar contexts
        assert len(similar) > 0
        assert all("context" in item for item in similar)
        assert all("similarity_score" in item for item in similar)
        assert all("matching_criteria" in item for item in similar)
        
        # Scores should be between 0 and 1
        assert all(0.0 <= item["similarity_score"] <= 1.0 for item in similar)
    
    @pytest.mark.asyncio
    async def test_search_recent(self, context_search, sample_contexts):
        """Test searching recent contexts."""
        results = await context_search.search_recent(
            sample_contexts,
            hours=24,
            limit=10
        )
        
        # All sample contexts should be recent
        assert len(results) == 4
    
    @pytest.mark.asyncio
    async def test_search_by_parent(self, context_search, sample_contexts):
        """Test searching by parent workflow."""
        results = await context_search.search_by_parent(
            sample_contexts,
            parent_workflow_id="parent_001",
            limit=10
        )
        
        # All sample contexts have same parent
        assert len(results) == 4
        assert all(ctx.parent_workflow_id == "parent_001" for ctx in results)


class TestAggregationAndSearchIntegration:
    """Integration tests combining aggregation and search."""
    
    @pytest.mark.asyncio
    async def test_aggregate_then_search(
        self,
        context_aggregator,
        context_search,
        sample_contexts
    ):
        """Test aggregating then searching results."""
        # First aggregate
        aggregated = await context_aggregator.aggregate_parallel_workflows(sample_contexts)
        
        # Then search for successful workflows
        successful = await context_search.search_by_success_rate(
            sample_contexts,
            min_success_rate=1.0,
            limit=10
        )
        
        # Verify consistency
        assert aggregated["total_workflows"] == 4
        assert len(successful) == 3  # 3 with 100% success rate
    
    @pytest.mark.asyncio
    async def test_complete_analysis_workflow(
        self,
        context_aggregator,
        context_search,
        sample_contexts
    ):
        """Test complete analysis workflow."""
        # Step 1: Aggregate all workflows
        aggregated = await context_aggregator.aggregate_parallel_workflows(sample_contexts)
        
        # Step 2: Create unified view
        all_results = []
        for context in sample_contexts:
            all_results.extend(context.workflow_results.values())
        unified = await context_aggregator.create_unified_view(all_results)
        
        # Step 3: Extract insights
        insights = await context_aggregator.extract_key_insights(aggregated)
        
        # Step 4: Generate recommendations
        recommendations = await context_aggregator.synthesize_recommendations(
            aggregated,
            unified
        )
        
        # Step 5: Identify patterns
        patterns = await context_aggregator.identify_patterns(sample_contexts)
        
        # Step 6: Find similar contexts
        target = sample_contexts[0]
        similar = await context_search.find_similar_contexts(
            target,
            sample_contexts[1:],
            similarity_threshold=0.0,
            limit=5
        )
        
        # Verify complete analysis
        assert aggregated["total_workflows"] > 0
        assert unified["total_results"] > 0
        assert len(insights) > 0
        assert len(recommendations) > 0
        assert len(patterns) > 0
        assert len(similar) > 0

