"""
Tests for Roadmap Generation Engine
===================================

Unit tests for intelligent roadmap generation.
"""

import pytest
from datetime import date, timedelta
import sys
from pathlib import Path

# Add service root to path
service_root = str(Path(__file__).parent.parent.parent)
if service_root not in sys.path:
    sys.path.insert(0, service_root)

from domain.services.roadmap_generator import (
    RoadmapGenerator,
    RoadmapGenerationRequest,
    RoadmapGenerationResult,
    RoadmapStrategy
)
from domain.entities.feature import Feature, FeaturePriority, FeatureStatus
from domain.entities.roadmap import Roadmap, Sprint, Release


@pytest.fixture
def generator():
    """Create roadmap generator instance."""
    return RoadmapGenerator()


@pytest.fixture
def sample_features():
    """Create sample features for testing."""
    return [
        Feature(
            id="feat-1",
            title="User Authentication",
            description="Implement user login and signup",
            priority=FeaturePriority.HIGH,
            estimated_effort=13.0,
            status=FeatureStatus.DRAFT
        ),
        Feature(
            id="feat-2",
            title="Payment Processing",
            description="Integrate payment gateway",
            priority=FeaturePriority.CRITICAL,
            estimated_effort=21.0,
            status=FeatureStatus.DRAFT
        ),
        Feature(
            id="feat-3",
            title="Admin Dashboard",
            description="Build admin control panel",
            priority=FeaturePriority.MEDIUM,
            estimated_effort=8.0,
            status=FeatureStatus.DRAFT
        ),
        Feature(
            id="feat-4",
            title="Email Notifications",
            description="Send email notifications",
            priority=FeaturePriority.LOW,
            estimated_effort=5.0,
            status=FeatureStatus.DRAFT
        )
    ]


class TestRoadmapGenerator:
    """Test suite for Roadmap Generator."""
    
    def test_generator_initialization(self, generator):
        """Test generator initialization."""
        assert generator.default_sprint_duration == 14
        assert generator.default_capacity_per_sprint == 40
    
    def test_generate_sprint_based_roadmap(self, generator, sample_features):
        """Test sprint-based roadmap generation."""
        request = RoadmapGenerationRequest(
            features=sample_features,
            team_id="team-1",
            start_date=date(2025, 1, 1),
            strategy=RoadmapStrategy.SPRINT_BASED,
            velocity=20.0
        )
        
        result = generator.generate_roadmap(request)
        
        assert isinstance(result, RoadmapGenerationResult)
        assert result.roadmap is not None
        assert len(result.sprints) > 0
        assert result.roadmap.id == "roadmap-team-1"
    
    def test_generate_release_based_roadmap(self, generator, sample_features):
        """Test release-based roadmap generation."""
        request = RoadmapGenerationRequest(
            features=sample_features,
            team_id="team-1",
            start_date=date(2025, 1, 1),
            strategy=RoadmapStrategy.RELEASE_BASED,
            velocity=20.0
        )
        
        result = generator.generate_roadmap(request)
        
        assert isinstance(result, RoadmapGenerationResult)
        assert len(result.releases) > 0
    
    def test_prioritize_features(self, generator):
        """Test feature prioritization."""
        features = [
            Feature("f1", "Feature 1", "Description", priority=FeaturePriority.LOW),
            Feature("f2", "Feature 2", "Description", priority=FeaturePriority.CRITICAL),
            Feature("f3", "Feature 3", "Description", priority=FeaturePriority.HIGH),
            Feature("f4", "Feature 4", "Description", priority=FeaturePriority.MEDIUM),
        ]
        
        sorted_features = generator._prioritize_features(features)
        
        # Critical should be first
        assert sorted_features[0].priority == FeaturePriority.CRITICAL
        # Low should be last
        assert sorted_features[-1].priority == FeaturePriority.LOW
    
    def test_estimate_total_effort(self, generator, sample_features):
        """Test total effort estimation."""
        total_effort = generator._estimate_total_effort(sample_features)
        
        # Sum: 13 + 21 + 8 + 5 = 47
        assert total_effort == 47.0
    
    def test_sprint_allocation(self, generator, sample_features):
        """Test feature allocation to sprints."""
        request = RoadmapGenerationRequest(
            features=sample_features,
            team_id="team-1",
            start_date=date(2025, 1, 1),
            strategy=RoadmapStrategy.SPRINT_BASED,
            velocity=20.0
        )
        
        result = generator.generate_roadmap(request)
        
        # Check sprints are created
        assert len(result.sprints) >= 3  # Need at least 3 sprints for 47 points @ 20/sprint
        
        # Check features are allocated
        total_allocated = sum(sprint.allocated for sprint in result.sprints)
        assert total_allocated <= 47.0
    
    def test_unscheduled_features(self, generator):
        """Test handling of features that don't fit."""
        # Create many large features
        large_features = [
            Feature(f"feat-{i}", f"Feature {i}", "Description", estimated_effort=50.0)
            for i in range(10)
        ]
        
        request = RoadmapGenerationRequest(
            features=large_features,
            team_id="team-1",
            start_date=date(2025, 1, 1),
            target_date=date(2025, 2, 1),  # Only 1 month
            strategy=RoadmapStrategy.SPRINT_BASED,
            velocity=20.0
        )
        
        result = generator.generate_roadmap(request)
        
        # Some features should not fit
        assert len(result.unscheduled_features) > 0
        assert not result.is_feasible()
    
    def test_target_date_warning(self, generator, sample_features):
        """Test warning when target date is exceeded."""
        request = RoadmapGenerationRequest(
            features=sample_features,
            team_id="team-1",
            start_date=date(2025, 1, 1),
            target_date=date(2025, 1, 15),  # Only 2 weeks
            strategy=RoadmapStrategy.SPRINT_BASED,
            velocity=20.0
        )
        
        result = generator.generate_roadmap(request)
        
        # Should have warning about exceeding target
        assert len(result.warnings) > 0
        assert any("exceeds target" in w for w in result.warnings)
    
    def test_recommendations_generation(self, generator, sample_features):
        """Test recommendation generation."""
        request = RoadmapGenerationRequest(
            features=sample_features,
            team_id="team-1",
            start_date=date(2025, 1, 1),
            target_date=date(2025, 1, 20),  # Tight deadline
            strategy=RoadmapStrategy.SPRINT_BASED,
            velocity=20.0
        )
        
        result = generator.generate_roadmap(request)
        
        # Should have recommendations
        assert len(result.recommendations) > 0
    
    def test_confidence_calculation(self, generator, sample_features):
        """Test confidence score calculation."""
        # Feasible roadmap should have high confidence
        request1 = RoadmapGenerationRequest(
            features=sample_features,
            team_id="team-1",
            start_date=date(2025, 1, 1),
            strategy=RoadmapStrategy.SPRINT_BASED,
            velocity=20.0
        )
        
        result1 = generator.generate_roadmap(request1)
        
        assert 0.0 <= result1.confidence <= 1.0
        assert result1.confidence >= 0.5  # Should be reasonably confident
    
    def test_sprint_dates(self, generator, sample_features):
        """Test sprint date calculations."""
        request = RoadmapGenerationRequest(
            features=sample_features,
            team_id="team-1",
            start_date=date(2025, 1, 1),
            strategy=RoadmapStrategy.SPRINT_BASED,
            sprint_duration_weeks=2,
            velocity=20.0
        )
        
        result = generator.generate_roadmap(request)
        
        # Check sprint dates are sequential
        for i in range(len(result.sprints) - 1):
            current_sprint = result.sprints[i]
            next_sprint = result.sprints[i + 1]
            
            # Current sprint end + 1 day should be next sprint start
            expected_next_start = current_sprint.end_date + timedelta(days=1)
            assert next_sprint.start_date == expected_next_start
    
    def test_release_grouping(self, generator, sample_features):
        """Test grouping sprints into releases."""
        request = RoadmapGenerationRequest(
            features=sample_features,
            team_id="team-1",
            start_date=date(2025, 1, 1),
            strategy=RoadmapStrategy.SPRINT_BASED,
            velocity=20.0
        )
        
        result = generator.generate_roadmap(request)
        
        # Should have releases
        assert len(result.releases) > 0
        
        # Releases are created from sprints
        # In sprint-based mode, features are in sprints, not directly in releases
        assert len(result.sprints) > 0
    
    def test_validation_no_features(self, generator):
        """Test validation with no features."""
        request = RoadmapGenerationRequest(
            features=[],
            team_id="team-1",
            start_date=date(2025, 1, 1)
        )
        
        with pytest.raises(ValueError, match="At least one feature required"):
            generator.generate_roadmap(request)
    
    def test_validation_invalid_sprint_duration(self, generator, sample_features):
        """Test validation with invalid sprint duration."""
        request = RoadmapGenerationRequest(
            features=sample_features,
            team_id="team-1",
            start_date=date(2025, 1, 1),
            sprint_duration_weeks=0
        )
        
        with pytest.raises(ValueError, match="Sprint duration must be positive"):
            generator.generate_roadmap(request)
    
    def test_validation_invalid_dates(self, generator, sample_features):
        """Test validation with invalid dates."""
        request = RoadmapGenerationRequest(
            features=sample_features,
            team_id="team-1",
            start_date=date(2025, 2, 1),
            target_date=date(2025, 1, 1)  # Before start date
        )
        
        with pytest.raises(ValueError, match="Target date must be after start date"):
            generator.generate_roadmap(request)
    
    def test_validation_invalid_velocity(self, generator, sample_features):
        """Test validation with invalid velocity."""
        request = RoadmapGenerationRequest(
            features=sample_features,
            team_id="team-1",
            start_date=date(2025, 1, 1),
            velocity=-10.0
        )
        
        with pytest.raises(ValueError, match="Velocity must be positive"):
            generator.generate_roadmap(request)
    
    def test_completion_date(self, generator, sample_features):
        """Test completion date calculation."""
        request = RoadmapGenerationRequest(
            features=sample_features,
            team_id="team-1",
            start_date=date(2025, 1, 1),
            strategy=RoadmapStrategy.SPRINT_BASED,
            velocity=20.0
        )
        
        result = generator.generate_roadmap(request)
        
        completion_date = result.completion_date()
        assert completion_date is not None
        assert completion_date > request.start_date
    
    def test_default_velocity(self, generator, sample_features):
        """Test roadmap generation without explicit velocity."""
        request = RoadmapGenerationRequest(
            features=sample_features,
            team_id="team-1",
            start_date=date(2025, 1, 1),
            strategy=RoadmapStrategy.SPRINT_BASED
            # No velocity specified
        )
        
        result = generator.generate_roadmap(request)
        
        # Should still generate roadmap with default velocity
        assert result.roadmap is not None
        assert len(result.sprints) > 0
    
    def test_feature_dependencies(self, generator):
        """Test handling of features with dependencies."""
        features = [
            Feature("feat-1", "Feature 1", "Desc", dependencies=[], estimated_effort=10.0),
            Feature("feat-2", "Feature 2", "Desc", dependencies=["feat-1"], estimated_effort=10.0),
            Feature("feat-3", "Feature 3", "Desc", dependencies=["feat-1", "feat-2"], estimated_effort=10.0)
        ]
        
        sorted_features = generator._prioritize_features(features)
        
        # Feature with no dependencies should come first
        assert sorted_features[0].id == "feat-1"


class TestRoadmapGenerationResult:
    """Test suite for RoadmapGenerationResult."""
    
    def test_is_feasible(self):
        """Test feasibility check."""
        roadmap = Roadmap(
            id="roadmap-1",
            name="Test Roadmap",
            created_by="test",
            description="Test",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 1)
        )
        
        # Feasible (no unscheduled features)
        result1 = RoadmapGenerationResult(
            roadmap=roadmap,
            releases=[],
            sprints=[],
            unscheduled_features=[]
        )
        assert result1.is_feasible()
        
        # Not feasible (has unscheduled features)
        result2 = RoadmapGenerationResult(
            roadmap=roadmap,
            releases=[],
            sprints=[],
            unscheduled_features=[Feature("f1", "F1", "Desc")]
        )
        assert not result2.is_feasible()
    
    def test_completion_date(self):
        """Test completion date calculation."""
        roadmap = Roadmap(
            id="roadmap-1",
            name="Test",
            created_by="test",
            description="Test",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 1)
        )
        
        sprint1 = Sprint(
            id="sprint-1",
            name="Sprint 1",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 14),
            capacity=20.0,
            allocated=0.0
        )
        
        sprint2 = Sprint(
            id="sprint-2",
            name="Sprint 2",
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 28),
            capacity=20.0,
            allocated=0.0
        )
        
        result = RoadmapGenerationResult(
            roadmap=roadmap,
            releases=[],
            sprints=[sprint1, sprint2],
            unscheduled_features=[]
        )
        
        assert result.completion_date() == date(2025, 1, 28)
    
    def test_completion_date_no_sprints(self):
        """Test completion date with no sprints."""
        roadmap = Roadmap(
            id="roadmap-1",
            name="Test",
            created_by="test",
            description="Test",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 3, 1)
        )
        
        result = RoadmapGenerationResult(
            roadmap=roadmap,
            releases=[],
            sprints=[],
            unscheduled_features=[]
        )
        
        assert result.completion_date() is None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

