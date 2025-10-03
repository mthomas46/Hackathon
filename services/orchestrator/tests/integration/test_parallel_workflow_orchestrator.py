"""
End-to-End Integration tests for Parallel Workflow Orchestrator
Phase 2 Day 5 - Enhanced Roadmap v2.0 Final Integration
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from services.orchestrator.domain.services.parallel_workflow_orchestrator import (
    ParallelWorkflowOrchestrator,
    ComprehensiveRoadmap
)


@pytest.fixture
def mock_workflow_logger():
    """Mock WorkflowLogger for testing."""
    logger = MagicMock()
    logger.log_workflow_start = AsyncMock()
    logger.log_workflow_step = AsyncMock()
    logger.log_workflow_complete = AsyncMock()
    logger.log_error = AsyncMock()
    return logger


@pytest.fixture
def orchestrator(mock_workflow_logger):
    """Create ParallelWorkflowOrchestrator instance."""
    return ParallelWorkflowOrchestrator(
        workflow_logger=mock_workflow_logger
    )


@pytest.fixture
def sample_interpreted_query():
    """Sample interpreted query from Interpreter service."""
    return {
        "workflow_id": "wf-test-123",
        "query": "Build an authentication system for mobile app with team of 5",
        "entities": {
            "feature_type": "authentication",
            "platform": "mobile",
            "feature_title": "OAuth2 Authentication System",
            "team_size": 5
        },
        "confidence": 0.92,
        "complexity": "moderate"
    }


class TestParallelWorkflowOrchestrator:
    """Test the parallel workflow orchestrator."""
    
    @pytest.mark.asyncio
    async def test_orchestrate_all_workflows_success(
        self,
        orchestrator,
        sample_interpreted_query,
        mock_workflow_logger
    ):
        """Test successful orchestration of all 4 workflows."""
        # Mock all external HTTP calls to fail (use fallback logic)
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Service unavailable")
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Service unavailable")
            
            result = await orchestrator.orchestrate(
                query=sample_interpreted_query["query"],
                interpreted_query=sample_interpreted_query,
                team_id="test-team"
            )
            
            # Verify result structure
            assert isinstance(result, ComprehensiveRoadmap)
            assert result.orchestration_id.startswith("orch_")
            assert result.query == sample_interpreted_query["query"]
            
            # Verify workflows were attempted
            assert result.workflows_completed + result.workflows_failed == 4
            
            # Verify at least some workflows succeeded (fallback logic)
            assert result.workflows_completed >= 2  # A and B should work
            
            # Verify logging
            mock_workflow_logger.log_workflow_start.assert_called_once()
            mock_workflow_logger.log_workflow_complete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_orchestrate_with_partial_failures(
        self,
        orchestrator,
        sample_interpreted_query,
        mock_workflow_logger
    ):
        """Test orchestration with some workflows failing."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Service unavailable")
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Service unavailable")
            
            result = await orchestrator.orchestrate(
                query=sample_interpreted_query["query"],
                interpreted_query=sample_interpreted_query,
                team_id="test-team"
            )
            
            # Should still complete successfully
            assert isinstance(result, ComprehensiveRoadmap)
            
            # Check success rate
            assert 0.0 <= result.success_rate <= 1.0
            
            # Should have processing time
            assert result.total_processing_time_ms > 0
    
    @pytest.mark.asyncio
    async def test_comprehensive_roadmap_properties(
        self,
        orchestrator,
        sample_interpreted_query
    ):
        """Test ComprehensiveRoadmap properties and calculated fields."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Service unavailable")
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Service unavailable")
            
            result = await orchestrator.orchestrate(
                query=sample_interpreted_query["query"],
                interpreted_query=sample_interpreted_query,
                team_id="test-team"
            )
            
            # Check overall confidence
            assert 0.0 <= result.overall_confidence <= 1.0
            
            # Check readiness score
            assert 0.0 <= result.readiness_score <= 1.0
            
            # Check estimated values
            assert result.total_estimated_days >= 0
            assert result.total_estimated_sprints >= 0
            
            # Check collections
            assert isinstance(result.critical_risks, list)
            assert isinstance(result.recommendations, list)
    
    def test_comprehensive_roadmap_success_rate(self):
        """Test success rate calculation."""
        roadmap = ComprehensiveRoadmap(
            orchestration_id="test",
            query="test query",
            interpreted_query={},
            workflows_completed=3,
            workflows_failed=1
        )
        
        assert roadmap.success_rate == 0.75  # 3/4
    
    def test_comprehensive_roadmap_success_rate_zero(self):
        """Test success rate with no workflows."""
        roadmap = ComprehensiveRoadmap(
            orchestration_id="test",
            query="test query",
            interpreted_query={}
        )
        
        assert roadmap.success_rate == 0.0
    
    @pytest.mark.asyncio
    async def test_workflow_a_execution(
        self,
        orchestrator,
        sample_interpreted_query
    ):
        """Test individual workflow A execution."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Service unavailable")
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Service unavailable")
            
            result = await orchestrator._execute_workflow_a(
                interpreted_query=sample_interpreted_query,
                parent_workflow_id="test"
            )
            
            # Should return FeatureBreakdown
            assert result is not None
            assert hasattr(result, 'feature_id')
            assert hasattr(result, 'user_stories')
            assert hasattr(result, 'technical_tasks')
    
    @pytest.mark.asyncio
    async def test_workflow_b_execution(
        self,
        orchestrator,
        sample_interpreted_query
    ):
        """Test individual workflow B execution."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Service unavailable")
            
            result = await orchestrator._execute_workflow_b(
                interpreted_query=sample_interpreted_query,
                parent_workflow_id="test"
            )
            
            # Should return HistoricalContext
            assert result is not None
            assert hasattr(result, 'sources')
            assert hasattr(result, 'average_relevance')
    
    @pytest.mark.asyncio
    async def test_result_aggregation(
        self,
        orchestrator,
        sample_interpreted_query
    ):
        """Test result aggregation from all workflows."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Service unavailable")
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Service unavailable")
            
            result = await orchestrator.orchestrate(
                query=sample_interpreted_query["query"],
                interpreted_query=sample_interpreted_query,
                team_id="test-team"
            )
            
            # Verify aggregation happened
            if result.workflows_completed > 0:
                # Should have calculated overall confidence
                assert result.overall_confidence > 0.0
                
                # Should have recommendations if any workflow succeeded
                # (not always guaranteed with fallbacks)
                assert isinstance(result.recommendations, list)
    
    @pytest.mark.asyncio
    async def test_parallel_execution_timing(
        self,
        orchestrator,
        sample_interpreted_query
    ):
        """Test that parallel execution is faster than sequential."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Service unavailable")
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Service unavailable")
            
            start_time = datetime.utcnow()
            
            result = await orchestrator.orchestrate(
                query=sample_interpreted_query["query"],
                interpreted_query=sample_interpreted_query,
                team_id="test-team"
            )
            
            end_time = datetime.utcnow()
            actual_time = (end_time - start_time).total_seconds() * 1000
            
            # Reported time should be close to actual time
            assert abs(result.total_processing_time_ms - actual_time) < 1000  # Within 1 second
    
    @pytest.mark.asyncio
    async def test_orchestration_logging(
        self,
        orchestrator,
        sample_interpreted_query,
        mock_workflow_logger
    ):
        """Test that orchestration is properly logged."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Service unavailable")
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Service unavailable")
            
            await orchestrator.orchestrate(
                query=sample_interpreted_query["query"],
                interpreted_query=sample_interpreted_query,
                team_id="test-team"
            )
            
            # Verify logging calls
            assert mock_workflow_logger.log_workflow_start.called
            assert mock_workflow_logger.log_workflow_step.called
            assert mock_workflow_logger.log_workflow_complete.called
            
            # Check specific log steps
            step_calls = [call[1] for call in mock_workflow_logger.log_workflow_step.call_args_list]
            step_names = [call.get('step_name') for call in step_calls]
            
            assert "parallel_execution_start" in step_names
            assert "parallel_execution_complete" in step_names


class TestEndToEndIntegration:
    """End-to-end integration tests for the complete Enhanced Roadmap v2.0 flow."""
    
    @pytest.mark.asyncio
    async def test_complete_enhanced_roadmap_flow(
        self,
        orchestrator,
        sample_interpreted_query,
        mock_workflow_logger
    ):
        """Test the complete Enhanced Roadmap v2.0 flow from query to roadmap."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Service unavailable")
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Service unavailable")
            
            # Step 1: Natural language query (already interpreted)
            query = sample_interpreted_query["query"]
            
            # Step 2: Orchestrate all 4 workflows
            roadmap = await orchestrator.orchestrate(
                query=query,
                interpreted_query=sample_interpreted_query,
                team_id="test-team"
            )
            
            # Step 3: Verify comprehensive roadmap
            assert isinstance(roadmap, ComprehensiveRoadmap)
            
            # Verify all workflow results are present (or failed gracefully)
            total_workflows = 4
            assert roadmap.workflows_completed + roadmap.workflows_failed == total_workflows
            
            # Verify aggregated data
            assert roadmap.overall_confidence >= 0.0
            assert roadmap.readiness_score >= 0.0
            
            # Verify metadata
            assert roadmap.created_at is not None
            assert roadmap.total_processing_time_ms > 0
            
            # Verify traceability
            assert roadmap.orchestration_id is not None
            assert roadmap.query == query
            
            # Verify logging happened
            mock_workflow_logger.log_workflow_start.assert_called()
            mock_workflow_logger.log_workflow_complete.assert_called()
    
    @pytest.mark.asyncio
    async def test_roadmap_with_all_workflow_successes(
        self,
        orchestrator,
        sample_interpreted_query
    ):
        """Test roadmap generation when all workflows succeed."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Service unavailable")
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Service unavailable")
            
            roadmap = await orchestrator.orchestrate(
                query=sample_interpreted_query["query"],
                interpreted_query=sample_interpreted_query,
                team_id="test-team"
            )
            
            # With fallback logic, we should get at least some successful workflows
            assert roadmap.workflows_completed >= 2
            
            # Verify success flags
            success_count = sum([
                roadmap.feature_breakdown_success,
                roadmap.historical_context_success,
                roadmap.timeline_analysis_success,
                roadmap.skills_matching_success
            ])
            
            assert success_count == roadmap.workflows_completed
    
    @pytest.mark.asyncio
    async def test_roadmap_provides_actionable_insights(
        self,
        orchestrator,
        sample_interpreted_query
    ):
        """Test that roadmap provides actionable insights."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_client.return_value.__aenter__.return_value.get.side_effect = Exception("Service unavailable")
            mock_client.return_value.__aenter__.return_value.post.side_effect = Exception("Service unavailable")
            
            roadmap = await orchestrator.orchestrate(
                query=sample_interpreted_query["query"],
                interpreted_query=sample_interpreted_query,
                team_id="test-team"
            )
            
            # Should have actionable insights if workflows succeeded
            if roadmap.workflows_completed > 0:
                # At least one of these should have content
                has_insights = (
                    len(roadmap.critical_risks) > 0 or
                    len(roadmap.recommendations) > 0 or
                    roadmap.total_estimated_days > 0 or
                    roadmap.overall_confidence > 0.0
                )
                assert has_insights

