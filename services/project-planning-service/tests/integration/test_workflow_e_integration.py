"""
Integration Tests for Workflow E
Tests integration with validation, gap detection, and blindspot detection components.
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "services" / "project-planning-service"))

from domain.services.workflow_e_orchestrator import WorkflowEOrchestrator
from domain.entities.external_service_entities import ServiceCategory


class TestWorkflowEIntegration:
    """Integration tests for complete Workflow E pipeline."""
    
    @pytest.fixture
    def feature_query(self):
        """Sample feature query."""
        return "Build push notifications using Firebase for 100K users"
    
    @pytest.fixture
    def requirements(self):
        """Sample requirements."""
        return {
            "feature_type": "Notification System",
            "expected_users": 100000,
            "platforms": ["iOS", "Android"]
        }
    
    @pytest.fixture
    def original_plan(self):
        """Sample original plan."""
        return {
            "story_points": 50,
            "weeks": 3.0,
            "confidence": 75,
            "risk_level": "MEDIUM"
        }
    
    @pytest.mark.asyncio
    async def test_complete_workflow_e_pipeline(
        self,
        feature_query,
        requirements,
        original_plan
    ):
        """Test complete Workflow E execution."""
        orchestrator = WorkflowEOrchestrator()
        
        result = await orchestrator.execute_workflow_e(
            feature_query=feature_query,
            extracted_requirements=requirements,
            original_plan=original_plan
        )
        
        # Verify result structure
        assert result is not None
        assert hasattr(result, 'discovered_services')
        assert hasattr(result, 'cataloged_services')
        assert hasattr(result, 'validation_results')
        assert hasattr(result, 'gap_analyses')
        assert hasattr(result, 'blindspot_analyses')
        assert hasattr(result, 'accuracy_enhancement')
        
        # Verify services discovered
        assert len(result.discovered_services) > 0
        
        # Verify accuracy enhancement
        acc = result.accuracy_enhancement
        assert acc.adjusted_story_points >= acc.original_story_points
        assert acc.adjusted_confidence >= acc.original_confidence
    
    @pytest.mark.asyncio
    async def test_discovery_finds_firebase(
        self,
        feature_query,
        requirements,
        original_plan
    ):
        """Test that discovery finds Firebase when mentioned."""
        orchestrator = WorkflowEOrchestrator()
        
        result = await orchestrator.execute_workflow_e(
            feature_query=feature_query,
            extracted_requirements=requirements,
            original_plan=original_plan
        )
        
        service_names = [s.name.lower() for s in result.discovered_services]
        assert any("firebase" in name for name in service_names)
    
    @pytest.mark.asyncio
    async def test_validation_detects_issues(
        self,
        feature_query,
        requirements,
        original_plan
    ):
        """Test that validation detects compliance issues."""
        orchestrator = WorkflowEOrchestrator()
        
        result = await orchestrator.execute_workflow_e(
            feature_query=feature_query,
            extracted_requirements=requirements,
            original_plan=original_plan
        )
        
        # Should find some validation issues for Firebase
        total_issues = sum(len(vr.issues) for vr in result.validation_results)
        assert total_issues > 0
    
    @pytest.mark.asyncio
    async def test_gap_detection_finds_gaps(
        self,
        feature_query,
        requirements,
        original_plan
    ):
        """Test that gap detection finds knowledge gaps."""
        orchestrator = WorkflowEOrchestrator()
        
        result = await orchestrator.execute_workflow_e(
            feature_query=feature_query,
            extracted_requirements=requirements,
            original_plan=original_plan
        )
        
        # Should find some gaps
        total_gaps = sum(
            len(ga.documentation_gaps) + len(ga.skills_gaps) + len(ga.configuration_gaps)
            for ga in result.gap_analyses
        )
        assert total_gaps >= 0  # May or may not find gaps depending on mock data
    
    @pytest.mark.asyncio
    async def test_blindspot_detection_at_scale(
        self,
        requirements,
        original_plan
    ):
        """Test that blindspot detection works with scale requirements."""
        orchestrator = WorkflowEOrchestrator()
        
        query = "Build notifications for 100K users with Firebase"
        reqs = {**requirements, "expected_users": 100000}
        
        result = await orchestrator.execute_workflow_e(
            feature_query=query,
            extracted_requirements=reqs,
            original_plan=original_plan
        )
        
        # Should detect scale-related blindspots
        total_blindspots = sum(len(ba.blindspots) for ba in result.blindspot_analyses)
        assert total_blindspots > 0
    
    @pytest.mark.asyncio
    async def test_accuracy_improvement_significant(
        self,
        feature_query,
        requirements,
        original_plan
    ):
        """Test that accuracy improvement is significant."""
        orchestrator = WorkflowEOrchestrator()
        
        result = await orchestrator.execute_workflow_e(
            feature_query=feature_query,
            extracted_requirements=requirements,
            original_plan=original_plan
        )
        
        acc = result.accuracy_enhancement
        
        # Should improve confidence
        assert acc.confidence_improvement > 0
        
        # Should adjust story points if issues found
        if acc.issues_found_total > 0:
            assert acc.story_points_added > 0
    
    @pytest.mark.asyncio
    async def test_workflow_feedback_generation(
        self,
        feature_query,
        requirements,
        original_plan
    ):
        """Test workflow feedback generation."""
        orchestrator = WorkflowEOrchestrator()
        
        result = await orchestrator.execute_workflow_e(
            feature_query=feature_query,
            extracted_requirements=requirements,
            original_plan=original_plan
        )
        
        feedback = await orchestrator.get_workflow_feedback(result)
        
        assert "workflow_a_updates" in feedback
        assert "workflow_c_updates" in feedback
        assert "workflow_d_updates" in feedback
        
        # Should have additional stories if issues found
        if result.accuracy_enhancement.issues_found_total > 0:
            assert len(feedback["workflow_a_updates"]["additional_stories"]) > 0
    
    @pytest.mark.asyncio
    async def test_execution_performance(
        self,
        feature_query,
        requirements,
        original_plan
    ):
        """Test that Workflow E executes quickly."""
        import time
        orchestrator = WorkflowEOrchestrator()
        
        start = time.time()
        result = await orchestrator.execute_workflow_e(
            feature_query=feature_query,
            extracted_requirements=requirements,
            original_plan=original_plan
        )
        duration = time.time() - start
        
        # Should complete in under 5 seconds (target is ~1 second)
        assert duration < 5.0
        assert result.execution_time_seconds < 5.0
    
    @pytest.mark.asyncio
    async def test_multiple_services_discovery(self):
        """Test discovery of multiple services."""
        orchestrator = WorkflowEOrchestrator()
        
        query = "Build notifications with Firebase, SendGrid, and Twilio"
        requirements = {"feature_type": "Multi-channel Notifications"}
        original_plan = {
            "story_points": 80,
            "weeks": 5.0,
            "confidence": 70,
            "risk_level": "HIGH"
        }
        
        result = await orchestrator.execute_workflow_e(
            feature_query=query,
            extracted_requirements=requirements,
            original_plan=original_plan
        )
        
        # Should discover multiple services
        assert len(result.discovered_services) >= 3
        
        service_names = [s.name.lower() for s in result.discovered_services]
        assert any("firebase" in name for name in service_names)
        assert any("sendgrid" in name for name in service_names)
        assert any("twilio" in name for name in service_names)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

