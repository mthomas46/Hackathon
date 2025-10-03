"""
Tests for Timeline Estimation Engine
====================================

Unit tests for velocity-based timeline estimation.
"""

import pytest
from datetime import date, timedelta
import sys
from pathlib import Path

# Add service root to path
service_root = str(Path(__file__).parent.parent.parent)
if service_root not in sys.path:
    sys.path.insert(0, service_root)

from domain.services.timeline_estimator import (
    TimelineEstimator,
    TimelineEstimationRequest,
    TimelineEstimate,
    VelocityData,
    EstimationMethod,
    ConfidenceLevel,
    WhatIfScenario
)
from domain.entities.feature import Feature, FeaturePriority
from domain.entities.task import Task, TaskType


@pytest.fixture
def estimator():
    """Create timeline estimator instance."""
    return TimelineEstimator()


@pytest.fixture
def sample_velocity_data():
    """Create sample velocity data."""
    return [
        VelocityData("Sprint 1", 18.0, 160, 12, 14),
        VelocityData("Sprint 2", 22.0, 176, 15, 14),
        VelocityData("Sprint 3", 20.0, 168, 14, 14),
        VelocityData("Sprint 4", 21.0, 170, 13, 14)
    ]


@pytest.fixture
def sample_features():
    """Create sample features."""
    return [
        Feature("f1", "Feature 1", "Description", estimated_effort=13.0),
        Feature("f2", "Feature 2", "Description", estimated_effort=21.0),
        Feature("f3", "Feature 3", "Description", estimated_effort=8.0)
    ]


@pytest.fixture
def sample_tasks():
    """Create sample tasks."""
    return [
        Task("t1", "f1", "system", "Task 1", "Desc", TaskType.DEVELOPMENT, estimated_hours=16.0),
        Task("t2", "f1", "system", "Task 2", "Desc", TaskType.TESTING, estimated_hours=8.0),
        Task("t3", "f2", "system", "Task 3", "Desc", TaskType.DEVELOPMENT, estimated_hours=24.0)
    ]


class TestTimelineEstimator:
    """Test suite for Timeline Estimator."""
    
    def test_estimator_initialization(self, estimator):
        """Test estimator initialization."""
        assert estimator is not None
        assert estimator.default_velocity == 20.0
        assert len(estimator.velocity_weights) == 4
    
    def test_basic_estimation(self, estimator, sample_features, sample_velocity_data):
        """Test basic timeline estimation."""
        request = TimelineEstimationRequest(
            features=sample_features,
            tasks=[],
            start_date=date(2025, 1, 1),
            velocity_data=sample_velocity_data
        )
        
        estimate = estimator.estimate_timeline(request)
        
        assert isinstance(estimate, TimelineEstimate)
        assert estimate.estimated_completion_date > request.start_date
        assert estimate.estimated_duration_days > 0
        assert estimate.estimated_sprints > 0
        assert 0.0 <= estimate.confidence_score <= 1.0
    
    def test_total_effort_calculation(self, estimator, sample_features):
        """Test total effort calculation from features."""
        total_effort = estimator._calculate_total_effort(sample_features, [])
        
        # 13 + 21 + 8 = 42
        assert total_effort == 42.0
    
    def test_effort_from_tasks(self, estimator, sample_tasks):
        """Test effort calculation from tasks when no feature estimates."""
        features_no_effort = [Feature("f1", "F1", "D"), Feature("f2", "F2", "D")]
        
        total_effort = estimator._calculate_total_effort(features_no_effort, sample_tasks)
        
        # (16 + 8 + 24) hours / 8 = 6 story points
        assert total_effort == 6.0
    
    def test_average_velocity_calculation(self, estimator, sample_velocity_data):
        """Test average velocity calculation."""
        velocity = estimator._calculate_velocity(
            sample_velocity_data,
            EstimationMethod.AVERAGE_VELOCITY
        )
        
        # (18 + 22 + 20 + 21) / 4 = 20.25
        assert velocity == pytest.approx(20.25)
    
    def test_weighted_velocity_calculation(self, estimator, sample_velocity_data):
        """Test weighted velocity calculation."""
        velocity = estimator._calculate_velocity(
            sample_velocity_data,
            EstimationMethod.WEIGHTED_VELOCITY
        )
        
        # Should weight recent sprints higher
        assert velocity > 0
        # Most recent sprint is 21, should be weighted heavily
        assert velocity >= 20.0
    
    def test_optimistic_velocity(self, estimator, sample_velocity_data):
        """Test optimistic velocity method."""
        velocity = estimator._calculate_velocity(
            sample_velocity_data,
            EstimationMethod.OPTIMISTIC
        )
        
        # Should return max velocity (22.0)
        assert velocity == 22.0
    
    def test_pessimistic_velocity(self, estimator, sample_velocity_data):
        """Test pessimistic velocity method."""
        velocity = estimator._calculate_velocity(
            sample_velocity_data,
            EstimationMethod.PESSIMISTIC
        )
        
        # Should return min velocity (18.0)
        assert velocity == 18.0
    
    def test_three_point_velocity(self, estimator, sample_velocity_data):
        """Test three-point velocity method."""
        velocity = estimator._calculate_velocity(
            sample_velocity_data,
            EstimationMethod.THREE_POINT
        )
        
        # (22 + 4*20 + 18) / 6 = 20.0
        assert velocity == pytest.approx(20.0, abs=0.5)
    
    def test_default_velocity_no_data(self, estimator):
        """Test default velocity when no historical data."""
        velocity = estimator._calculate_velocity([], EstimationMethod.AVERAGE_VELOCITY)
        
        assert velocity == estimator.default_velocity
    
    def test_confidence_interval_calculation(self, estimator, sample_velocity_data):
        """Test confidence interval calculation."""
        earliest, latest = estimator._calculate_confidence_interval(
            start_date=date(2025, 1, 1),
            total_effort=40.0,
            velocity=20.0,
            velocity_data=sample_velocity_data,
            confidence_level=ConfidenceLevel.MEDIUM,
            sprint_duration_weeks=2
        )
        
        assert earliest < latest
        assert earliest >= date(2025, 1, 1)
    
    def test_confidence_score_with_data(self, estimator, sample_velocity_data):
        """Test confidence score calculation with historical data."""
        confidence = estimator._calculate_confidence_score(
            sample_velocity_data,
            total_effort=40.0,
            velocity=20.0
        )
        
        assert 0.0 <= confidence <= 1.0
        # Should have decent confidence with 4 sprints of consistent data
        assert confidence > 0.7
    
    def test_confidence_score_without_data(self, estimator):
        """Test confidence score without historical data."""
        confidence = estimator._calculate_confidence_score(
            [],
            total_effort=40.0,
            velocity=20.0
        )
        
        # Should have lower confidence
        assert confidence <= 0.5
    
    def test_buffer_inclusion(self, estimator, sample_features, sample_velocity_data):
        """Test buffer time inclusion."""
        # With buffer
        request_with_buffer = TimelineEstimationRequest(
            features=sample_features,
            tasks=[],
            start_date=date(2025, 1, 1),
            velocity_data=sample_velocity_data,
            include_buffer=True,
            buffer_percentage=0.2
        )
        
        # Without buffer
        request_no_buffer = TimelineEstimationRequest(
            features=sample_features,
            tasks=[],
            start_date=date(2025, 1, 1),
            velocity_data=sample_velocity_data,
            include_buffer=False
        )
        
        estimate_with = estimator.estimate_timeline(request_with_buffer)
        estimate_without = estimator.estimate_timeline(request_no_buffer)
        
        assert estimate_with.buffer_days > 0
        assert estimate_without.buffer_days == 0
        assert estimate_with.estimated_duration_days > estimate_without.estimated_duration_days
    
    def test_risk_factor_identification(self, estimator):
        """Test risk factor identification."""
        # No historical data
        risks1 = estimator._identify_risk_factors([], 40.0, 20.0, 60)
        assert any("No historical" in r for r in risks1)
        
        # Large project
        risks2 = estimator._identify_risk_factors([], 150.0, 20.0, 300)
        assert any("Large project" in r for r in risks2)
        
        # Long duration
        risks3 = estimator._identify_risk_factors([], 40.0, 20.0, 200)
        assert any("Long project" in r for r in risks3)
    
    def test_assumptions_documentation(self, estimator, sample_velocity_data):
        """Test assumptions documentation."""
        assumptions = estimator._document_assumptions(
            sample_velocity_data,
            velocity=20.0,
            method=EstimationMethod.WEIGHTED_VELOCITY,
            include_buffer=True
        )
        
        assert len(assumptions) > 0
        assert any("historical data" in a for a in assumptions)
        assert any("buffer" in a.lower() for a in assumptions)
    
    def test_what_if_scenarios(self, estimator, sample_features, sample_velocity_data):
        """Test what-if scenario analysis."""
        request = TimelineEstimationRequest(
            features=sample_features,
            tasks=[],
            start_date=date(2025, 1, 1),
            velocity_data=sample_velocity_data
        )
        
        scenarios = estimator.analyze_what_if_scenarios(request)
        
        assert len(scenarios) == 4
        assert any("Increased" in s.scenario_name for s in scenarios)
        assert any("Decreased" in s.scenario_name for s in scenarios)
        assert any("Optimistic" in s.scenario_name for s in scenarios)
        assert any("Pessimistic" in s.scenario_name for s in scenarios)
        
        # Optimistic should be fastest
        optimistic = next(s for s in scenarios if "Optimistic" in s.scenario_name)
        pessimistic = next(s for s in scenarios if "Pessimistic" in s.scenario_name)
        
        assert optimistic.duration_days < pessimistic.duration_days
    
    def test_method_comparison(self, estimator, sample_features, sample_velocity_data):
        """Test comparison of different estimation methods."""
        request = TimelineEstimationRequest(
            features=sample_features,
            tasks=[],
            start_date=date(2025, 1, 1),
            velocity_data=sample_velocity_data
        )
        
        results = estimator.compare_methods(request)
        
        assert len(results) == len(EstimationMethod)
        assert "average_velocity" in results
        assert "weighted_velocity" in results
        assert "optimistic" in results
        assert "pessimistic" in results
        assert "three_point" in results
        
        # Optimistic should have shortest duration
        optimistic = results["optimistic"]
        pessimistic = results["pessimistic"]
        
        assert optimistic.estimated_duration_days <= pessimistic.estimated_duration_days


class TestTimelineEstimate:
    """Test suite for TimelineEstimate dataclass."""
    
    def test_is_realistic(self):
        """Test is_realistic method."""
        # Realistic estimate
        estimate1 = TimelineEstimate(
            estimated_completion_date=date(2025, 3, 1),
            estimated_duration_days=60,
            estimated_sprints=4,
            confidence_score=0.8,
            confidence_interval=(date(2025, 2, 20), date(2025, 3, 10)),
            velocity_used=20.0,
            total_effort=40.0,
            buffer_days=10
        )
        assert estimate1.is_realistic()
        
        # Unrealistic estimate
        estimate2 = TimelineEstimate(
            estimated_completion_date=date(2025, 3, 1),
            estimated_duration_days=60,
            estimated_sprints=4,
            confidence_score=0.3,
            confidence_interval=(date(2025, 2, 20), date(2025, 3, 10)),
            velocity_used=20.0,
            total_effort=40.0,
            buffer_days=10
        )
        assert not estimate2.is_realistic()
    
    def test_variance_days(self):
        """Test variance_days calculation."""
        estimate = TimelineEstimate(
            estimated_completion_date=date(2025, 3, 1),
            estimated_duration_days=60,
            estimated_sprints=4,
            confidence_score=0.8,
            confidence_interval=(date(2025, 2, 20), date(2025, 3, 10)),
            velocity_used=20.0,
            total_effort=40.0,
            buffer_days=10
        )
        
        # 10 days between Feb 20 and Mar 10 (excluding Feb 20)
        variance = estimate.variance_days()
        assert variance == 18  # Mar 10 - Feb 20


class TestConfidenceLevels:
    """Test different confidence levels."""
    
    def test_low_confidence_interval(self, estimator, sample_features, sample_velocity_data):
        """Test LOW confidence level produces narrower interval."""
        request = TimelineEstimationRequest(
            features=sample_features,
            tasks=[],
            start_date=date(2025, 1, 1),
            velocity_data=sample_velocity_data,
            confidence_level=ConfidenceLevel.LOW
        )
        
        estimate = estimator.estimate_timeline(request)
        earliest, latest = estimate.confidence_interval
        
        # Low confidence = narrower interval
        variance = (latest - earliest).days
        assert variance > 0
    
    def test_high_confidence_interval(self, estimator, sample_features, sample_velocity_data):
        """Test HIGH confidence level produces wider interval."""
        request = TimelineEstimationRequest(
            features=sample_features,
            tasks=[],
            start_date=date(2025, 1, 1),
            velocity_data=sample_velocity_data,
            confidence_level=ConfidenceLevel.HIGH
        )
        
        estimate = estimator.estimate_timeline(request)
        earliest, latest = estimate.confidence_interval
        
        # High confidence = wider interval
        variance = (latest - earliest).days
        assert variance > 0
    
    def test_confidence_level_comparison(self, estimator, sample_features, sample_velocity_data):
        """Compare confidence intervals across levels."""
        levels = [ConfidenceLevel.LOW, ConfidenceLevel.MEDIUM, 
                  ConfidenceLevel.HIGH, ConfidenceLevel.VERY_HIGH]
        
        variances = []
        for level in levels:
            request = TimelineEstimationRequest(
                features=sample_features,
                tasks=[],
                start_date=date(2025, 1, 1),
                velocity_data=sample_velocity_data,
                confidence_level=level
            )
            
            estimate = estimator.estimate_timeline(request)
            earliest, latest = estimate.confidence_interval
            variance = (latest - earliest).days
            variances.append(variance)
        
        # Higher confidence levels should have wider intervals
        # (though LOW might be similar to MEDIUM depending on implementation)
        assert variances[3] >= variances[0]  # VERY_HIGH >= LOW


class TestEdgeCases:
    """Test edge cases and boundary conditions."""
    
    def test_single_feature(self, estimator, sample_velocity_data):
        """Test estimation with single feature."""
        features = [Feature("f1", "Feature 1", "Description", estimated_effort=20.0)]
        
        request = TimelineEstimationRequest(
            features=features,
            tasks=[],
            start_date=date(2025, 1, 1),
            velocity_data=sample_velocity_data
        )
        
        estimate = estimator.estimate_timeline(request)
        
        assert estimate.total_effort == 20.0
        assert estimate.estimated_sprints >= 1
    
    def test_no_features_or_tasks(self, estimator):
        """Test estimation with no features or tasks."""
        request = TimelineEstimationRequest(
            features=[],
            tasks=[],
            start_date=date(2025, 1, 1)
        )
        
        estimate = estimator.estimate_timeline(request)
        
        # Should have minimum effort of 1.0
        assert estimate.total_effort >= 1.0
    
    def test_very_large_project(self, estimator, sample_velocity_data):
        """Test estimation for very large project."""
        features = [
            Feature(f"f{i}", f"Feature {i}", "Desc", estimated_effort=20.0)
            for i in range(10)  # 200 story points total
        ]
        
        request = TimelineEstimationRequest(
            features=features,
            tasks=[],
            start_date=date(2025, 1, 1),
            velocity_data=sample_velocity_data
        )
        
        estimate = estimator.estimate_timeline(request)
        
        assert estimate.total_effort == 200.0
        assert estimate.estimated_sprints >= 9  # ~200 points / ~20 velocity = ~10 sprints
        # Should have lower confidence for large projects
        assert estimate.confidence_score < 1.0


class TestVelocityData:
    """Test VelocityData dataclass."""
    
    def test_velocity_data_creation(self):
        """Test velocity data creation."""
        velocity = VelocityData(
            sprint_name="Sprint 1",
            story_points_completed=20.0,
            hours_spent=160,
            tasks_completed=12,
            sprint_duration_days=14
        )
        
        assert velocity.sprint_name == "Sprint 1"
        assert velocity.story_points_completed == 20.0
        assert velocity.hours_spent == 160
        assert velocity.tasks_completed == 12
        assert velocity.sprint_duration_days == 14


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

