"""
Unit Tests for Feature Entity
==============================

Tests for the Feature domain entity including validation, state transitions,
and business logic.
"""

import pytest
from datetime import datetime
import sys
from pathlib import Path

# Add service root to path
service_root = str(Path(__file__).parent.parent.parent)
if service_root not in sys.path:
    sys.path.insert(0, service_root)

from domain.entities.feature import (
    Feature,
    FeatureStatus,
    FeaturePriority
)


class TestFeatureEntity:
    """Test suite for Feature entity."""
    
    def test_create_feature_with_required_fields(self):
        """Test creating a feature with only required fields."""
        feature = Feature(
            id="test-feature-1",
            title="User Authentication",
            description="Implement secure user authentication system",
            created_by="test-user"
        )
        
        assert feature.id == "test-feature-1"
        assert feature.title == "User Authentication"
        assert feature.description == "Implement secure user authentication system"
        assert feature.status == FeatureStatus.DRAFT
        assert feature.priority == FeaturePriority.MEDIUM
        assert feature.created_by == "test-user"
        assert isinstance(feature.created_at, datetime)
        assert isinstance(feature.updated_at, datetime)
    
    def test_create_feature_with_empty_title_raises_error(self):
        """Test that creating a feature with empty title raises ValueError."""
        with pytest.raises(ValueError, match="Feature title cannot be empty"):
            Feature(
                id="test-feature-1",
                title="",
                description="Some description",
                created_by="test-user"
            )
    
    def test_create_feature_with_empty_description_raises_error(self):
        """Test that creating a feature with empty description raises ValueError."""
        with pytest.raises(ValueError, match="Feature description cannot be empty"):
            Feature(
                id="test-feature-1",
                title="Valid Title",
                description="",
                created_by="test-user"
            )
    
    def test_update_status(self):
        """Test updating feature status."""
        feature = Feature(
            id="test-feature-1",
            title="Test Feature",
            description="Description",
            created_by="test-user"
        )
        
        original_updated_at = feature.updated_at
        
        # Small delay to ensure timestamp changes
        import time
        time.sleep(0.01)
        
        feature.update_status(FeatureStatus.ANALYZED)
        
        assert feature.status == FeatureStatus.ANALYZED
        assert feature.updated_at > original_updated_at
    
    def test_add_acceptance_criterion(self):
        """Test adding acceptance criteria."""
        feature = Feature(
            id="test-feature-1",
            title="Test Feature",
            description="Description",
            created_by="test-user"
        )
        
        feature.add_acceptance_criterion("User can log in with email and password")
        feature.add_acceptance_criterion("User receives error message on invalid credentials")
        
        assert len(feature.acceptance_criteria) == 2
        assert "User can log in with email and password" in feature.acceptance_criteria
    
    def test_add_empty_acceptance_criterion_ignored(self):
        """Test that empty acceptance criteria are not added."""
        feature = Feature(
            id="test-feature-1",
            title="Test Feature",
            description="Description",
            created_by="test-user"
        )
        
        feature.add_acceptance_criterion("  ")
        
        assert len(feature.acceptance_criteria) == 0
    
    def test_set_estimated_effort(self):
        """Test setting estimated effort."""
        feature = Feature(
            id="test-feature-1",
            title="Test Feature",
            description="Description",
            created_by="test-user"
        )
        
        feature.set_estimated_effort(8.0)
        
        assert feature.estimated_effort == 8.0
    
    def test_set_negative_effort_raises_error(self):
        """Test that setting negative effort raises ValueError."""
        feature = Feature(
            id="test-feature-1",
            title="Test Feature",
            description="Description",
            created_by="test-user"
        )
        
        with pytest.raises(ValueError, match="Effort cannot be negative"):
            feature.set_estimated_effort(-5.0)
    
    def test_add_dependency(self):
        """Test adding feature dependencies."""
        feature = Feature(
            id="test-feature-1",
            title="Test Feature",
            description="Description",
            created_by="test-user"
        )
        
        feature.add_dependency("feature-2")
        feature.add_dependency("feature-3")
        
        assert len(feature.dependencies) == 2
        assert "feature-2" in feature.dependencies
        assert "feature-3" in feature.dependencies
    
    def test_add_duplicate_dependency_ignored(self):
        """Test that adding duplicate dependencies is prevented."""
        feature = Feature(
            id="test-feature-1",
            title="Test Feature",
            description="Description",
            created_by="test-user"
        )
        
        feature.add_dependency("feature-2")
        feature.add_dependency("feature-2")
        
        assert len(feature.dependencies) == 1
    
    def test_update_ai_analysis(self):
        """Test updating AI analysis results."""
        feature = Feature(
            id="test-feature-1",
            title="Test Feature",
            description="Description",
            created_by="test-user"
        )
        
        analysis_data = {
            "complexity": "high",
            "estimated_lines_of_code": 500,
            "technologies": ["Python", "FastAPI"]
        }
        
        feature.update_ai_analysis(analysis_data)
        
        assert feature.ai_analysis["complexity"] == "high"
        assert feature.ai_analysis["estimated_lines_of_code"] == 500
    
    def test_assess_risk(self):
        """Test risk assessment."""
        feature = Feature(
            id="test-feature-1",
            title="Test Feature",
            description="Description",
            created_by="test-user"
        )
        
        risk_data = {
            "overall_risk": "medium",
            "technical_risks": ["Integration complexity"],
            "mitigation": "Phased rollout"
        }
        
        feature.assess_risk(risk_data)
        
        assert feature.risk_assessment["overall_risk"] == "medium"
        assert len(feature.risk_assessment["technical_risks"]) == 1
    
    def test_is_ready_for_planning(self):
        """Test ready for planning property."""
        feature = Feature(
            id="test-feature-1",
            title="Test Feature",
            description="Description",
            created_by="test-user"
        )
        
        # Initially not ready (no acceptance criteria)
        assert not feature.is_ready_for_planning
        
        # Add acceptance criteria
        feature.add_acceptance_criterion("Criterion 1")
        
        # Now ready
        assert feature.is_ready_for_planning
    
    def test_completion_percentage(self):
        """Test completion percentage calculation."""
        feature = Feature(
            id="test-feature-1",
            title="Test Feature",
            description="Description",
            created_by="test-user"
        )
        
        # No acceptance criteria means 0% complete regardless of status
        assert feature.completion_percentage == 0.0
        
        # Add acceptance criteria
        feature.add_acceptance_criterion("Criterion 1")
        
        # Now status-based completion applies
        assert feature.completion_percentage == 0.1  # DRAFT status
        
        feature.update_status(FeatureStatus.IN_PROGRESS)
        assert feature.completion_percentage == 0.7
        
        feature.update_status(FeatureStatus.COMPLETED)
        assert feature.completion_percentage == 1.0
    
    def test_to_dict(self):
        """Test converting feature to dictionary."""
        feature = Feature(
            id="test-feature-1",
            title="Test Feature",
            description="Description",
            status=FeatureStatus.ANALYZED,
            priority=FeaturePriority.HIGH,
            created_by="test-user"
        )
        
        feature.add_acceptance_criterion("Criterion 1")
        feature.set_estimated_effort(5.0)
        
        feature_dict = feature.to_dict()
        
        assert feature_dict["id"] == "test-feature-1"
        assert feature_dict["title"] == "Test Feature"
        assert feature_dict["status"] == "analyzed"
        assert feature_dict["priority"] == "high"
        assert feature_dict["estimated_effort"] == 5.0
        assert len(feature_dict["acceptance_criteria"]) == 1
        assert "created_at" in feature_dict
        assert "updated_at" in feature_dict
        assert "is_ready_for_planning" in feature_dict
        assert "completion_percentage" in feature_dict


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

