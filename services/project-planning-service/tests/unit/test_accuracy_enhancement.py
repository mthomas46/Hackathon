"""
Unit Tests for Accuracy Enhancement Engine - Phase 9
"""

import pytest
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root / "services" / "project-planning-service"))

from domain.services.accuracy_enhancement_engine import AccuracyEnhancementEngine
from domain.entities.external_service_entities import (
    ExternalServiceMatch,
    ServiceCatalogEntry,
    ComplianceValidationResult,
    KnowledgeGapAnalysis,
    BlindspotAnalysis,
    ValidationIssue,
    KnowledgeGap,
    DevelopmentBlindspot,
    IssueSeverity,
    DiscoveryMethod,
    ServiceCategory
)


class TestAccuracyEnhancementEngine:
    """Test suite for Accuracy Enhancement Engine."""
    
    @pytest.fixture
    def engine(self):
        """Create accuracy enhancement engine instance."""
        return AccuracyEnhancementEngine()
    
    @pytest.fixture
    def sample_original_plan(self):
        """Sample original plan."""
        return {
            "story_points": 68,
            "weeks": 4.0,
            "confidence": 78,
            "risk_level": "MEDIUM"
        }
    
    @pytest.fixture
    def sample_discovered_services(self):
        """Sample discovered services."""
        return [
            ExternalServiceMatch(
                service_id="firebase-fcm",
                name="Firebase FCM",
                relevance_score=0.98,
                discovery_methods=[DiscoveryMethod.EXPLICIT_MENTION],
                initial_category=ServiceCategory.DIRECT
            )
        ]
    
    @pytest.fixture
    def sample_validation_results(self):
        """Sample validation results with issues."""
        return [
            ComplianceValidationResult(
                service_id="firebase-fcm",
                service_name="Firebase FCM",
                api_compliant=False,
                security_compliant=True,
                version_compatible=True,
                rate_limits_sufficient=False,
                issues=[
                    ValidationIssue(
                        severity=IssueSeverity.HIGH,
                        category="rate_limits",
                        issue="Rate limit insufficient",
                        impact="Cannot meet requirements",
                        detection_method="Rate limit analysis",
                        remediation="Implement queue",
                        story_points_to_add=8,
                        timeline_impact_days=1.0,
                        sprint="Sprint 1"
                    )
                ],
                total_story_points_to_add=8,
                total_timeline_impact_days=1.0,
                validation_confidence=0.95
            )
        ]
    
    def test_confidence_boost_calculation(self, engine):
        """Test confidence boost calculation."""
        validation_results = [
            ComplianceValidationResult(
                service_id="test",
                service_name="Test Service",
                api_compliant=True,
                security_compliant=True,
                version_compatible=True,
                rate_limits_sufficient=True,
                issues=[],
                total_story_points_to_add=0,
                total_timeline_impact_days=0.0,
                validation_confidence=1.0
            )
        ]
        
        gap_analyses = []
        blindspot_analyses = []
        
        boost = engine._calculate_confidence_boost(
            validation_results,
            gap_analyses,
            blindspot_analyses
        )
        
        assert boost >= 0
        assert boost <= 25  # Capped at 25
    
    def test_risk_reduction_calculation(self, engine):
        """Test risk reduction calculation."""
        validation_results = [
            ComplianceValidationResult(
                service_id="test",
                service_name="Test Service",
                api_compliant=False,
                security_compliant=True,
                version_compatible=True,
                rate_limits_sufficient=False,
                issues=[
                    ValidationIssue(
                        severity=IssueSeverity.CRITICAL,
                        category="api",
                        issue="Critical issue",
                        impact="High impact",
                        detection_method="Analysis",
                        remediation="Fix it",
                        story_points_to_add=5,
                        timeline_impact_days=1.0,
                        sprint="Sprint 1"
                    )
                ],
                total_story_points_to_add=5,
                total_timeline_impact_days=1.0,
                validation_confidence=0.9
            )
        ]
        
        gap_analyses = []
        blindspot_analyses = [
            BlindspotAnalysis(
                service_id="test",
                service_name="Test Service",
                blindspots=[
                    DevelopmentBlindspot(
                        blindspot_type="hidden_dependency",
                        severity=IssueSeverity.HIGH,
                        description="Hidden dep",
                        why_missed="Not documented",
                        impact="Big impact",
                        detection_method="Analysis",
                        story_points_to_add=3,
                        timeline_impact_days=0.5,
                        mitigation="Add it",
                        sprint="Sprint 1"
                    )
                ],
                severity_distribution={"critical": 0, "high": 1, "medium": 0, "low": 0},
                total_story_points_missed=3,
                total_timeline_impact_days=0.5,
                detection_confidence=0.95
            )
        ]
        
        risk_level, risk_reduction = engine._calculate_risk_reduction(
            validation_results,
            gap_analyses,
            blindspot_analyses
        )
        
        assert risk_level in ["LOW", "MEDIUM", "HIGH"]
        assert 0.0 <= risk_reduction <= 100.0
    
    @pytest.mark.asyncio
    async def test_enhance_accuracy_increases_story_points(
        self,
        engine,
        sample_original_plan,
        sample_discovered_services,
        sample_validation_results
    ):
        """Test that accuracy enhancement increases story points."""
        result = await engine.enhance_accuracy(
            original_plan=sample_original_plan,
            discovered_services=sample_discovered_services,
            cataloged_services=[],
            validation_results=sample_validation_results,
            gap_analyses=[],
            blindspot_analyses=[],
            execution_time=0.5
        )
        
        acc = result.accuracy_enhancement
        
        assert acc.adjusted_story_points > acc.original_story_points
        assert acc.story_points_added > 0
    
    @pytest.mark.asyncio
    async def test_enhance_accuracy_improves_confidence(
        self,
        engine,
        sample_original_plan,
        sample_discovered_services,
        sample_validation_results
    ):
        """Test that accuracy enhancement improves confidence."""
        result = await engine.enhance_accuracy(
            original_plan=sample_original_plan,
            discovered_services=sample_discovered_services,
            cataloged_services=[],
            validation_results=sample_validation_results,
            gap_analyses=[],
            blindspot_analyses=[],
            execution_time=0.5
        )
        
        acc = result.accuracy_enhancement
        
        assert acc.adjusted_confidence >= acc.original_confidence
        assert acc.confidence_improvement >= 0
    
    @pytest.mark.asyncio
    async def test_enhance_accuracy_adjusts_timeline(
        self,
        engine,
        sample_original_plan,
        sample_discovered_services,
        sample_validation_results
    ):
        """Test that accuracy enhancement adjusts timeline."""
        result = await engine.enhance_accuracy(
            original_plan=sample_original_plan,
            discovered_services=sample_discovered_services,
            cataloged_services=[],
            validation_results=sample_validation_results,
            gap_analyses=[],
            blindspot_analyses=[],
            execution_time=0.5
        )
        
        acc = result.accuracy_enhancement
        
        assert acc.adjusted_weeks >= acc.original_weeks
        assert acc.weeks_added >= 0
    
    @pytest.mark.asyncio
    async def test_workflow_feedback_generation(
        self,
        engine,
        sample_original_plan,
        sample_discovered_services,
        sample_validation_results
    ):
        """Test workflow feedback generation."""
        result = await engine.enhance_accuracy(
            original_plan=sample_original_plan,
            discovered_services=sample_discovered_services,
            cataloged_services=[],
            validation_results=sample_validation_results,
            gap_analyses=[],
            blindspot_analyses=[],
            execution_time=0.5
        )
        
        feedback = await engine.generate_workflow_feedback(result)
        
        assert "workflow_a_updates" in feedback
        assert "workflow_c_updates" in feedback
        assert "workflow_d_updates" in feedback
        
        assert "additional_stories" in feedback["workflow_a_updates"]
        assert "timeline_adjustments" in feedback["workflow_c_updates"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

