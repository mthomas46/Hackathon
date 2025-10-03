"""
Tests for Milestone Planning Engine
===================================

Unit tests for milestone generation and tracking.
"""

import pytest
from datetime import date, timedelta
import sys
from pathlib import Path

# Add service root to path
service_root = str(Path(__file__).parent.parent.parent)
if service_root not in sys.path:
    sys.path.insert(0, service_root)

from domain.services.milestone_planner import (
    MilestonePlanner,
    MilestonePlanRequest,
    MilestonePlan,
    Milestone,
    MilestoneType
)
from domain.entities.feature import Feature, FeaturePriority, FeatureStatus
from domain.entities.roadmap import Sprint


@pytest.fixture
def planner():
    """Create milestone planner instance."""
    return MilestonePlanner()


@pytest.fixture
def sample_features():
    """Create sample features."""
    return [
        Feature("f1", "Authentication", "User auth", priority=FeaturePriority.HIGH, estimated_effort=13.0),
        Feature("f2", "Payment", "Payment system", priority=FeaturePriority.CRITICAL, estimated_effort=21.0),
        Feature("f3", "Dashboard", "Admin dashboard", priority=FeaturePriority.MEDIUM, estimated_effort=8.0),
        Feature("f4", "Reports", "Reporting", priority=FeaturePriority.LOW, estimated_effort=5.0)
    ]


@pytest.fixture
def sample_sprints():
    """Create sample sprints."""
    start = date(2025, 1, 1)
    sprints = []
    for i in range(6):
        sprint = Sprint(
            id=f"sprint-{i+1}",
            name=f"Sprint {i+1}",
            start_date=start + timedelta(days=i*14),
            end_date=start + timedelta(days=(i+1)*14-1),
            capacity=20.0,
            allocated=18.0,
            feature_ids=[f"f{i+1}"] if i < 4 else []
        )
        sprints.append(sprint)
    return sprints


class TestMilestonePlanner:
    """Test suite for Milestone Planner."""
    
    def test_planner_initialization(self, planner):
        """Test planner initialization."""
        assert planner is not None
        assert planner.default_milestone_weeks == 4
    
    def test_generate_balanced_milestones(self, planner, sample_features):
        """Test balanced milestone generation."""
        request = MilestonePlanRequest(
            features=sample_features,
            sprints=[],
            start_date=date(2025, 1, 1),
            strategy="balanced"
        )
        
        plan = planner.generate_milestones(request)
        
        assert isinstance(plan, MilestonePlan)
        assert len(plan.milestones) > 0
        assert plan.milestone_count == len(plan.milestones)
    
    def test_generate_sprint_based_milestones(self, planner, sample_features, sample_sprints):
        """Test sprint-based milestone generation."""
        request = MilestonePlanRequest(
            features=sample_features,
            sprints=sample_sprints,
            start_date=date(2025, 1, 1),
            strategy="sprint_based"
        )
        
        plan = planner.generate_milestones(request)
        
        assert len(plan.milestones) > 0
        # Should have milestones aligned with sprints
        for milestone in plan.milestones:
            assert milestone.milestone_type == MilestoneType.SPRINT
    
    def test_generate_value_based_milestones(self, planner, sample_features):
        """Test value-based milestone generation."""
        request = MilestonePlanRequest(
            features=sample_features,
            sprints=[],
            start_date=date(2025, 1, 1),
            strategy="value_based"
        )
        
        plan = planner.generate_milestones(request)
        
        assert len(plan.milestones) > 0
        # Should have milestones for different priority levels
        assert plan.total_story_points > 0
    
    def test_milestone_contains_features(self, planner, sample_features):
        """Test that milestones contain features."""
        request = MilestonePlanRequest(
            features=sample_features,
            sprints=[],
            start_date=date(2025, 1, 1)
        )
        
        plan = planner.generate_milestones(request)
        
        # All features should be in some milestone
        all_feature_ids = set()
        for milestone in plan.milestones:
            all_feature_ids.update(milestone.feature_ids)
        
        expected_ids = {f.id for f in sample_features}
        assert all_feature_ids == expected_ids
    
    def test_milestone_frequency(self, planner, sample_features):
        """Test milestone frequency setting."""
        request = MilestonePlanRequest(
            features=sample_features,
            sprints=[],
            start_date=date(2025, 1, 1),
            milestone_frequency_weeks=2
        )
        
        plan = planner.generate_milestones(request)
        
        # Check that milestones are spaced appropriately
        if len(plan.milestones) > 1:
            first = plan.milestones[0]
            second = plan.milestones[1]
            days_between = (second.target_date - first.target_date).days
            assert days_between >= 14  # At least 2 weeks
    
    def test_track_milestone_progress(self, planner):
        """Test milestone progress tracking."""
        features = [
            Feature("f1", "F1", "D", status=FeatureStatus.COMPLETED),
            Feature("f2", "F2", "D", status=FeatureStatus.IN_PROGRESS),
            Feature("f3", "F3", "D", status=FeatureStatus.DRAFT)
        ]
        
        milestone = Milestone(
            id="m1",
            name="Milestone 1",
            description="Test",
            milestone_type=MilestoneType.PHASE,
            target_date=date(2025, 2, 1),
            feature_ids=["f1", "f2", "f3"]
        )
        
        progress = planner.track_milestone_progress(milestone, features)
        
        # 1 of 3 completed = 33.33%
        assert progress == pytest.approx(33.33, abs=0.1)
    
    def test_adjust_milestone_dates(self, planner, sample_features):
        """Test milestone date adjustment based on velocity."""
        request = MilestonePlanRequest(
            features=sample_features,
            sprints=[],
            start_date=date(2025, 1, 1)
        )
        
        original_plan = planner.generate_milestones(request)
        
        # Team is going slower (actual=10, planned=20)
        adjusted_plan = planner.adjust_milestone_dates(
            original_plan,
            actual_velocity=10.0,
            planned_velocity=20.0
        )
        
        # Dates should be pushed out
        if len(original_plan.milestones) > 0:
            original_last = original_plan.milestones[-1].target_date
            adjusted_last = adjusted_plan.milestones[-1].target_date
            assert adjusted_last >= original_last
    
    def test_suggest_milestone_names(self, planner):
        """Test milestone name suggestions."""
        features = [
            Feature("f1", "Authentication", "Desc"),
            Feature("f2", "Payment", "Desc")
        ]
        
        milestone = Milestone(
            id="milestone-1",
            name="Milestone 1",
            description="Test",
            milestone_type=MilestoneType.PHASE,
            target_date=date(2025, 2, 1),
            feature_ids=["f1", "f2"]
        )
        
        suggestions = planner.suggest_milestone_names(milestone, features)
        
        assert len(suggestions) > 0
        # Should include feature-based suggestion
        assert any("Authentication" in s for s in suggestions)


class TestMilestone:
    """Test suite for Milestone dataclass."""
    
    def test_milestone_creation(self):
        """Test milestone creation."""
        milestone = Milestone(
            id="m1",
            name="Milestone 1",
            description="First milestone",
            milestone_type=MilestoneType.PHASE,
            target_date=date(2025, 3, 1),
            feature_ids=["f1", "f2"],
            story_points=25.0
        )
        
        assert milestone.id == "m1"
        assert milestone.name == "Milestone 1"
        assert not milestone.completed
        assert milestone.story_points == 25.0
    
    def test_is_overdue(self):
        """Test overdue detection."""
        milestone = Milestone(
            id="m1",
            name="Test",
            description="Test",
            milestone_type=MilestoneType.PHASE,
            target_date=date(2025, 1, 1),
            completed=False
        )
        
        # Overdue if current date is past target
        assert milestone.is_overdue(date(2025, 1, 15))
        assert not milestone.is_overdue(date(2024, 12, 15))
    
    def test_completed_not_overdue(self):
        """Test that completed milestones are not overdue."""
        milestone = Milestone(
            id="m1",
            name="Test",
            description="Test",
            milestone_type=MilestoneType.PHASE,
            target_date=date(2025, 1, 1),
            completed=True
        )
        
        # Never overdue if completed
        assert not milestone.is_overdue(date(2025, 2, 1))
    
    def test_days_until(self):
        """Test days until calculation."""
        milestone = Milestone(
            id="m1",
            name="Test",
            description="Test",
            milestone_type=MilestoneType.PHASE,
            target_date=date(2025, 2, 1)
        )
        
        assert milestone.days_until(date(2025, 1, 1)) == 31
        assert milestone.days_until(date(2025, 2, 1)) == 0
        assert milestone.days_until(date(2025, 3, 1)) < 0


class TestMilestonePlan:
    """Test suite for MilestonePlan dataclass."""
    
    def test_get_next_milestone(self):
        """Test getting next milestone."""
        milestones = [
            Milestone("m1", "M1", "Desc", MilestoneType.PHASE, date(2025, 1, 15), completed=True),
            Milestone("m2", "M2", "Desc", MilestoneType.PHASE, date(2025, 2, 1)),
            Milestone("m3", "M3", "Desc", MilestoneType.PHASE, date(2025, 3, 1))
        ]
        
        plan = MilestonePlan(
            milestones=milestones,
            total_story_points=50.0,
            estimated_completion_date=date(2025, 3, 1),
            milestone_count=3
        )
        
        next_milestone = plan.get_next_milestone(date(2025, 1, 20))
        
        assert next_milestone is not None
        assert next_milestone.id == "m2"
    
    def test_completion_percentage(self):
        """Test completion percentage calculation."""
        milestones = [
            Milestone("m1", "M1", "Desc", MilestoneType.PHASE, date(2025, 1, 1), completed=True),
            Milestone("m2", "M2", "Desc", MilestoneType.PHASE, date(2025, 2, 1), completed=True),
            Milestone("m3", "M3", "Desc", MilestoneType.PHASE, date(2025, 3, 1), completed=False)
        ]
        
        plan = MilestonePlan(
            milestones=milestones,
            total_story_points=50.0,
            estimated_completion_date=date(2025, 3, 1),
            milestone_count=3
        )
        
        # 2 of 3 completed = 66.67%
        assert plan.completion_percentage() == pytest.approx(66.67, abs=0.1)
    
    def test_no_milestones_completion(self):
        """Test completion percentage with no milestones."""
        plan = MilestonePlan(
            milestones=[],
            total_story_points=0.0,
            estimated_completion_date=date(2025, 1, 1),
            milestone_count=0
        )
        
        assert plan.completion_percentage() == 0.0


class TestMilestoneStrategies:
    """Test different milestone generation strategies."""
    
    def test_balanced_vs_value_based(self, planner, sample_features):
        """Compare balanced and value-based strategies."""
        request_balanced = MilestonePlanRequest(
            features=sample_features,
            sprints=[],
            start_date=date(2025, 1, 1),
            strategy="balanced"
        )
        
        request_value = MilestonePlanRequest(
            features=sample_features,
            sprints=[],
            start_date=date(2025, 1, 1),
            strategy="value_based"
        )
        
        plan_balanced = planner.generate_milestones(request_balanced)
        plan_value = planner.generate_milestones(request_value)
        
        # Both should have milestones
        assert len(plan_balanced.milestones) > 0
        assert len(plan_value.milestones) > 0
        
        # Total points should be the same
        assert plan_balanced.total_story_points == plan_value.total_story_points


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

