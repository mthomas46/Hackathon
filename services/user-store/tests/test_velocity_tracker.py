"""
Tests for Team Velocity Tracker Service
=======================================

Unit tests for velocity tracking, trend analysis, and forecasting.
"""

import pytest
from datetime import date, timedelta
import sys
from pathlib import Path

# Add service root to path
service_root = str(Path(__file__).parent.parent)
if service_root not in sys.path:
    sys.path.insert(0, service_root)

from domain.services.velocity_tracker import (
    VelocityTracker,
    VelocityTrend,
    SprintMetrics,
    VelocityForecast
)


@pytest.fixture
def tracker():
    """Create a velocity tracker instance."""
    return VelocityTracker()


@pytest.fixture
def sample_sprints(tracker):
    """Create sample sprint data."""
    team_id = "team-1"
    base_date = date(2025, 1, 1)
    
    sprints = []
    for i in range(6):
        start = base_date + timedelta(days=i * 14)
        end = start + timedelta(days=13)
        
        # Simulate improving velocity
        planned = 20.0 + i
        completed = 16.0 + i * 1.5
        
        sprint = tracker.record_sprint(
            team_id=team_id,
            sprint_name=f"Sprint {i+1}",
            start_date=start,
            end_date=end,
            planned_story_points=planned,
            completed_story_points=completed,
            planned_tasks=10 + i,
            completed_tasks=8 + i,
            total_hours_spent=120.0 + i * 10
        )
        sprints.append(sprint)
    
    return team_id, sprints


class TestVelocityTracker:
    """Test suite for Velocity Tracker."""
    
    def test_tracker_initialization(self):
        """Test tracker initialization."""
        tracker = VelocityTracker()
        assert tracker.velocity_history == {}
    
    def test_record_sprint(self, tracker):
        """Test recording a sprint."""
        velocity = tracker.record_sprint(
            team_id="team-1",
            sprint_name="Sprint 1",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 14),
            planned_story_points=20.0,
            completed_story_points=18.0,
            planned_tasks=10,
            completed_tasks=9,
            total_hours_spent=120.0
        )
        
        assert velocity.team_id == "team-1"
        assert velocity.sprint_name == "Sprint 1"
        assert velocity.completed_story_points == 18.0
        assert velocity.completion_rate() == 0.9
    
    def test_get_velocity_history(self, sample_sprints):
        """Test retrieving velocity history."""
        team_id, sprints = sample_sprints
        tracker = VelocityTracker()
        
        # Re-add sprints to new tracker
        for sprint in sprints:
            tracker.velocity_history.setdefault(team_id, []).append(sprint)
        
        history = tracker.get_velocity_history(team_id)
        
        assert len(history) == 6
        # Should be most recent first
        assert history[0].sprint_name == "Sprint 6"
        assert history[-1].sprint_name == "Sprint 1"
    
    def test_get_velocity_history_with_limit(self, sample_sprints):
        """Test velocity history with limit."""
        team_id, sprints = sample_sprints
        tracker = VelocityTracker()
        
        for sprint in sprints:
            tracker.velocity_history.setdefault(team_id, []).append(sprint)
        
        history = tracker.get_velocity_history(team_id, limit=3)
        
        assert len(history) == 3
        assert history[0].sprint_name == "Sprint 6"
    
    def test_get_velocity_history_no_data(self, tracker):
        """Test velocity history with no data."""
        history = tracker.get_velocity_history("nonexistent-team")
        assert history == []
    
    def test_calculate_trend(self, sample_sprints):
        """Test trend calculation."""
        team_id, sprints = sample_sprints
        tracker = VelocityTracker()
        
        for sprint in sprints:
            tracker.velocity_history.setdefault(team_id, []).append(sprint)
        
        trend = tracker.calculate_trend(team_id)
        
        assert trend is not None
        assert trend.team_id == team_id
        assert trend.sprints_analyzed == 6
        assert trend.avg_velocity > 0
        assert trend.trend_direction in ['increasing', 'decreasing', 'stable']
    
    def test_calculate_trend_increasing(self, tracker):
        """Test detection of increasing trend."""
        team_id = "team-1"
        base_date = date(2025, 1, 1)
        
        # Create clearly increasing velocity
        for i in range(6):
            start = base_date + timedelta(days=i * 14)
            end = start + timedelta(days=13)
            
            tracker.record_sprint(
                team_id=team_id,
                sprint_name=f"Sprint {i+1}",
                start_date=start,
                end_date=end,
                planned_story_points=20.0,
                completed_story_points=10.0 + i * 3.0,  # Clearly increasing
                planned_tasks=10,
                completed_tasks=8,
                total_hours_spent=120.0
            )
        
        trend = tracker.calculate_trend(team_id)
        
        assert trend.trend_direction == 'increasing'
        assert trend.trend_percentage > 0
    
    def test_calculate_trend_insufficient_data(self, tracker):
        """Test trend calculation with insufficient data."""
        tracker.record_sprint(
            team_id="team-1",
            sprint_name="Sprint 1",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 14),
            planned_story_points=20.0,
            completed_story_points=18.0,
            planned_tasks=10,
            completed_tasks=9,
            total_hours_spent=120.0
        )
        
        trend = tracker.calculate_trend("team-1")
        
        # Need at least 2 sprints
        assert trend is None
    
    def test_get_sprint_metrics(self, sample_sprints):
        """Test getting sprint metrics."""
        team_id, sprints = sample_sprints
        tracker = VelocityTracker()
        
        for sprint in sprints:
            tracker.velocity_history.setdefault(team_id, []).append(sprint)
        
        metrics = tracker.get_sprint_metrics(team_id, "Sprint 1")
        
        assert metrics is not None
        assert metrics.sprint_name == "Sprint 1"
        assert metrics.velocity > 0
        assert metrics.completion_rate > 0
        assert metrics.hours_per_point > 0
    
    def test_get_sprint_metrics_not_found(self, tracker):
        """Test getting metrics for non-existent sprint."""
        metrics = tracker.get_sprint_metrics("team-1", "Sprint 99")
        assert metrics is None
    
    def test_forecast_velocity(self, sample_sprints):
        """Test velocity forecasting."""
        team_id, sprints = sample_sprints
        tracker = VelocityTracker()
        
        for sprint in sprints:
            tracker.velocity_history.setdefault(team_id, []).append(sprint)
        
        forecast = tracker.forecast_velocity(team_id)
        
        assert forecast is not None
        assert forecast.predicted_velocity > 0
        assert forecast.confidence_interval[0] < forecast.predicted_velocity
        assert forecast.confidence_interval[1] > forecast.predicted_velocity
        assert len(forecast.assumptions) > 0
    
    def test_forecast_velocity_insufficient_data(self, tracker):
        """Test forecasting with insufficient data."""
        tracker.record_sprint(
            team_id="team-1",
            sprint_name="Sprint 1",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 14),
            planned_story_points=20.0,
            completed_story_points=18.0,
            planned_tasks=10,
            completed_tasks=9,
            total_hours_spent=120.0
        )
        
        forecast = tracker.forecast_velocity("team-1")
        
        # Need at least 3 sprints
        assert forecast is None
    
    def test_calculate_capacity_from_velocity(self, sample_sprints):
        """Test capacity calculation from velocity."""
        team_id, sprints = sample_sprints
        tracker = VelocityTracker()
        
        for sprint in sprints:
            tracker.velocity_history.setdefault(team_id, []).append(sprint)
        
        capacity = tracker.calculate_capacity_from_velocity(team_id, 50.0)
        
        assert capacity is not None
        assert 'target_story_points' in capacity
        assert capacity['target_story_points'] == 50.0
        assert 'sprints_needed' in capacity
        assert 'sprints_with_buffer' in capacity
        assert capacity['sprints_with_buffer'] >= capacity['sprints_needed']
    
    def test_calculate_capacity_no_data(self, tracker):
        """Test capacity calculation with no data."""
        capacity = tracker.calculate_capacity_from_velocity("team-1", 50.0)
        assert capacity is None
    
    def test_compare_sprints(self, sample_sprints):
        """Test sprint comparison."""
        team_id, sprints = sample_sprints
        tracker = VelocityTracker()
        
        for sprint in sprints:
            tracker.velocity_history.setdefault(team_id, []).append(sprint)
        
        comparison = tracker.compare_sprints(team_id, "Sprint 1", "Sprint 6")
        
        assert comparison is not None
        assert 'velocity_change' in comparison
        assert 'velocity_change_percentage' in comparison
        assert 'completion_rate_change' in comparison
        assert comparison['sprint1'] == "Sprint 1"
        assert comparison['sprint2'] == "Sprint 6"
    
    def test_compare_sprints_not_found(self, tracker):
        """Test comparing non-existent sprints."""
        comparison = tracker.compare_sprints("team-1", "Sprint 1", "Sprint 99")
        assert comparison is None
    
    def test_get_team_performance_summary(self, sample_sprints):
        """Test team performance summary."""
        team_id, sprints = sample_sprints
        tracker = VelocityTracker()
        
        for sprint in sprints:
            tracker.velocity_history.setdefault(team_id, []).append(sprint)
        
        summary = tracker.get_team_performance_summary(team_id)
        
        assert summary is not None
        assert summary['team_id'] == team_id
        assert summary['sprints_analyzed'] == 6
        assert summary['total_story_points_completed'] > 0
        assert summary['successful_sprints'] >= 0
        assert summary['trend'] is not None
        assert summary['forecast'] is not None
    
    def test_get_team_performance_summary_no_data(self, tracker):
        """Test performance summary with no data."""
        summary = tracker.get_team_performance_summary("team-1")
        assert summary is None


class TestVelocityTrend:
    """Test suite for VelocityTrend."""
    
    def test_velocity_trend_creation(self):
        """Test velocity trend creation."""
        trend = VelocityTrend(
            team_id="team-1",
            sprints_analyzed=6,
            avg_velocity=20.0,
            avg_completion_rate=0.85,
            trend_direction='increasing',
            trend_percentage=15.0,
            volatility=0.15,
            most_recent_velocity=23.0,
            predicted_next_sprint=24.0,
            confidence_level='high'
        )
        
        assert trend.team_id == "team-1"
        assert trend.is_improving()
        assert trend.is_reliable()
        assert not trend.is_stable()
    
    def test_trend_is_stable(self):
        """Test stable trend detection."""
        trend = VelocityTrend(
            team_id="team-1",
            sprints_analyzed=6,
            avg_velocity=20.0,
            avg_completion_rate=0.85,
            trend_direction='stable',
            trend_percentage=2.0,
            volatility=0.1,
            most_recent_velocity=20.5,
            predicted_next_sprint=20.0,
            confidence_level='high'
        )
        
        assert trend.is_stable()
        assert not trend.is_improving()
    
    def test_trend_is_reliable(self):
        """Test reliability detection."""
        reliable_trend = VelocityTrend(
            team_id="team-1",
            sprints_analyzed=6,
            avg_velocity=20.0,
            avg_completion_rate=0.85,
            trend_direction='stable',
            trend_percentage=0.0,
            volatility=0.2,  # Below 0.3 threshold
            most_recent_velocity=20.0,
            predicted_next_sprint=20.0,
            confidence_level='high'
        )
        
        unreliable_trend = VelocityTrend(
            team_id="team-1",
            sprints_analyzed=6,
            avg_velocity=20.0,
            avg_completion_rate=0.85,
            trend_direction='stable',
            trend_percentage=0.0,
            volatility=0.5,  # Above 0.3 threshold
            most_recent_velocity=20.0,
            predicted_next_sprint=20.0,
            confidence_level='low'
        )
        
        assert reliable_trend.is_reliable()
        assert not unreliable_trend.is_reliable()


class TestSprintMetrics:
    """Test suite for SprintMetrics."""
    
    def test_sprint_metrics_creation(self):
        """Test sprint metrics creation."""
        metrics = SprintMetrics(
            sprint_name="Sprint 1",
            team_id="team-1",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 14),
            planned_story_points=20.0,
            completed_story_points=18.0,
            planned_tasks=10,
            completed_tasks=9,
            total_hours_spent=120.0,
            completion_rate=0.9,
            velocity=18.0,
            hours_per_point=6.67,
            team_size=5,
            capacity_utilization=0.75
        )
        
        assert metrics.sprint_name == "Sprint 1"
        assert metrics.velocity == 18.0
        assert metrics.sprint_duration_days() == 13
    
    def test_is_successful(self):
        """Test sprint success detection."""
        successful = SprintMetrics(
            sprint_name="Sprint 1",
            team_id="team-1",
            start_date=date(2025, 1, 1),
            end_date=date(2025, 1, 14),
            planned_story_points=20.0,
            completed_story_points=18.0,
            planned_tasks=10,
            completed_tasks=9,
            total_hours_spent=120.0,
            completion_rate=0.9,
            velocity=18.0,
            hours_per_point=6.67,
            team_size=5,
            capacity_utilization=0.75
        )
        
        unsuccessful = SprintMetrics(
            sprint_name="Sprint 2",
            team_id="team-1",
            start_date=date(2025, 1, 15),
            end_date=date(2025, 1, 28),
            planned_story_points=20.0,
            completed_story_points=12.0,
            planned_tasks=10,
            completed_tasks=6,
            total_hours_spent=120.0,
            completion_rate=0.6,
            velocity=12.0,
            hours_per_point=10.0,
            team_size=5,
            capacity_utilization=0.75
        )
        
        assert successful.is_successful()
        assert not unsuccessful.is_successful()


class TestVelocityForecast:
    """Test suite for VelocityForecast."""
    
    def test_forecast_creation(self):
        """Test forecast creation."""
        forecast = VelocityForecast(
            team_id="team-1",
            forecast_sprints=1,
            predicted_velocity=20.0,
            confidence_interval=(18.0, 22.0),
            based_on_sprints=6,
            assumptions=["Team stable", "No disruptions"]
        )
        
        assert forecast.team_id == "team-1"
        assert forecast.predicted_velocity == 20.0
        assert len(forecast.assumptions) == 2
    
    def test_within_range(self):
        """Test checking if actual velocity is within range."""
        forecast = VelocityForecast(
            team_id="team-1",
            forecast_sprints=1,
            predicted_velocity=20.0,
            confidence_interval=(18.0, 22.0),
            based_on_sprints=6,
            assumptions=[]
        )
        
        assert forecast.within_range(19.0)
        assert forecast.within_range(18.0)
        assert forecast.within_range(22.0)
        assert not forecast.within_range(17.0)
        assert not forecast.within_range(23.0)


class TestIntegration:
    """Integration tests for velocity tracking."""
    
    def test_full_velocity_tracking_workflow(self, tracker):
        """Test complete velocity tracking workflow."""
        team_id = "team-1"
        
        # Record multiple sprints
        for i in range(6):
            start = date(2025, 1, 1) + timedelta(days=i * 14)
            end = start + timedelta(days=13)
            
            tracker.record_sprint(
                team_id=team_id,
                sprint_name=f"Sprint {i+1}",
                start_date=start,
                end_date=end,
                planned_story_points=20.0,
                completed_story_points=18.0 + i * 0.5,
                planned_tasks=10,
                completed_tasks=9,
                total_hours_spent=120.0
            )
        
        # Get history
        history = tracker.get_velocity_history(team_id)
        assert len(history) == 6
        
        # Calculate trend
        trend = tracker.calculate_trend(team_id)
        assert trend is not None
        assert trend.sprints_analyzed == 6
        
        # Forecast
        forecast = tracker.forecast_velocity(team_id)
        assert forecast is not None
        
        # Capacity calculation
        capacity = tracker.calculate_capacity_from_velocity(team_id, 100.0)
        assert capacity is not None
        
        # Performance summary
        summary = tracker.get_team_performance_summary(team_id)
        assert summary is not None
        assert summary['trend'] == trend
        assert summary['forecast'] == forecast


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

