"""
Team Velocity Tracker Service
=============================

Tracks team velocity across sprints, calculates trends, and provides
forecasting for capacity planning and roadmap estimation.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import date, timedelta
import statistics

from ..models.team_capacity import TeamVelocity, TeamMember, TaskAssignment


@dataclass
class VelocityTrend:
    """Represents velocity trend analysis."""
    team_id: str
    sprints_analyzed: int
    avg_velocity: float  # Average story points per sprint
    avg_completion_rate: float  # Average completion percentage
    trend_direction: str  # 'increasing', 'decreasing', 'stable'
    trend_percentage: float  # Percentage change
    volatility: float  # Standard deviation / mean
    most_recent_velocity: float
    predicted_next_sprint: float
    confidence_level: str  # 'high', 'medium', 'low'
    
    def is_improving(self) -> bool:
        """Check if team velocity is improving."""
        return self.trend_direction == 'increasing'
    
    def is_stable(self) -> bool:
        """Check if team velocity is stable."""
        return self.trend_direction == 'stable'
    
    def is_reliable(self) -> bool:
        """Check if velocity is reliable (low volatility)."""
        return self.volatility < 0.3  # Less than 30% variance


@dataclass
class SprintMetrics:
    """Detailed metrics for a single sprint."""
    sprint_name: str
    team_id: str
    start_date: date
    end_date: date
    planned_story_points: float
    completed_story_points: float
    planned_tasks: int
    completed_tasks: int
    total_hours_spent: float
    completion_rate: float
    velocity: float  # Completed story points
    hours_per_point: float
    team_size: int
    capacity_utilization: float  # Percentage of available capacity used
    
    def sprint_duration_days(self) -> int:
        """Calculate sprint duration in days."""
        return (self.end_date - self.start_date).days
    
    def is_successful(self, threshold: float = 0.8) -> bool:
        """Check if sprint met success threshold."""
        return self.completion_rate >= threshold


@dataclass
class VelocityForecast:
    """Forecast for future sprint velocity."""
    team_id: str
    forecast_sprints: int
    predicted_velocity: float
    confidence_interval: Tuple[float, float]  # (lower, upper)
    based_on_sprints: int
    assumptions: List[str] = field(default_factory=list)
    
    def within_range(self, actual_velocity: float) -> bool:
        """Check if actual velocity falls within predicted range."""
        return self.confidence_interval[0] <= actual_velocity <= self.confidence_interval[1]


class VelocityTracker:
    """
    Team velocity tracking and analysis service.
    
    Provides:
    - Velocity history tracking
    - Trend analysis
    - Performance forecasting
    - Sprint metrics
    - Capacity planning insights
    """
    
    def __init__(self):
        """Initialize velocity tracker."""
        self.velocity_history: Dict[str, List[TeamVelocity]] = {}  # team_id -> velocities
    
    def record_sprint(
        self,
        team_id: str,
        sprint_name: str,
        start_date: date,
        end_date: date,
        planned_story_points: float,
        completed_story_points: float,
        planned_tasks: int,
        completed_tasks: int,
        total_hours_spent: float
    ) -> TeamVelocity:
        """
        Record velocity for a completed sprint.
        
        Args:
            team_id: Team identifier
            sprint_name: Sprint name/identifier
            start_date: Sprint start date
            end_date: Sprint end date
            planned_story_points: Story points planned
            completed_story_points: Story points completed
            planned_tasks: Number of tasks planned
            completed_tasks: Number of tasks completed
            total_hours_spent: Total hours worked
            
        Returns:
            TeamVelocity record
        """
        velocity = TeamVelocity(
            team_id=team_id,
            sprint_name=sprint_name,
            start_date=start_date,
            end_date=end_date,
            planned_story_points=int(planned_story_points),
            completed_story_points=int(completed_story_points),
            tasks_planned=planned_tasks,
            tasks_completed=completed_tasks,
            actual_hours=total_hours_spent
        )
        
        # Store in history
        if team_id not in self.velocity_history:
            self.velocity_history[team_id] = []
        self.velocity_history[team_id].append(velocity)
        
        # Sort by start date
        self.velocity_history[team_id].sort(key=lambda v: v.start_date)
        
        return velocity
    
    def get_velocity_history(
        self,
        team_id: str,
        limit: Optional[int] = None
    ) -> List[TeamVelocity]:
        """
        Get velocity history for a team.
        
        Args:
            team_id: Team identifier
            limit: Optional limit on number of recent sprints
            
        Returns:
            List of TeamVelocity records (most recent first)
        """
        if team_id not in self.velocity_history:
            return []
        
        history = list(reversed(self.velocity_history[team_id]))  # Most recent first
        
        if limit:
            history = history[:limit]
        
        return history
    
    def calculate_trend(
        self,
        team_id: str,
        lookback_sprints: int = 6
    ) -> Optional[VelocityTrend]:
        """
        Calculate velocity trend for a team.
        
        Args:
            team_id: Team identifier
            lookback_sprints: Number of recent sprints to analyze
            
        Returns:
            VelocityTrend or None if insufficient data
        """
        history = self.get_velocity_history(team_id, limit=lookback_sprints)
        
        if len(history) < 2:
            return None  # Need at least 2 sprints for trend
        
        velocities = [float(v.completed_story_points) for v in history]
        completion_rates = [
            v.completed_story_points / v.planned_story_points if v.planned_story_points > 0 else 0.0
            for v in history
        ]
        
        # Calculate statistics
        avg_velocity = statistics.mean(velocities)
        avg_completion_rate = statistics.mean(completion_rates)
        
        # Calculate trend
        recent_avg = statistics.mean(velocities[:3]) if len(velocities) >= 3 else velocities[0]
        older_avg = statistics.mean(velocities[-3:]) if len(velocities) >= 3 else velocities[-1]
        
        if recent_avg > older_avg * 1.1:  # 10% improvement
            trend_direction = 'increasing'
        elif recent_avg < older_avg * 0.9:  # 10% decline
            trend_direction = 'decreasing'
        else:
            trend_direction = 'stable'
        
        trend_percentage = ((recent_avg - older_avg) / older_avg * 100) if older_avg > 0 else 0
        
        # Calculate volatility
        volatility = (
            statistics.stdev(velocities) / avg_velocity
            if len(velocities) > 1 and avg_velocity > 0
            else 0
        )
        
        # Predict next sprint (simple moving average)
        if len(velocities) >= 3:
            predicted = statistics.mean(velocities[:3])
        else:
            predicted = avg_velocity
        
        # Determine confidence level
        if len(history) >= 6 and volatility < 0.2:
            confidence = 'high'
        elif len(history) >= 3 and volatility < 0.4:
            confidence = 'medium'
        else:
            confidence = 'low'
        
        return VelocityTrend(
            team_id=team_id,
            sprints_analyzed=len(history),
            avg_velocity=round(avg_velocity, 2),
            avg_completion_rate=round(avg_completion_rate, 2),
            trend_direction=trend_direction,
            trend_percentage=round(trend_percentage, 2),
            volatility=round(volatility, 2),
            most_recent_velocity=round(velocities[0], 2),
            predicted_next_sprint=round(predicted, 2),
            confidence_level=confidence
        )
    
    def get_sprint_metrics(
        self,
        team_id: str,
        sprint_name: str
    ) -> Optional[SprintMetrics]:
        """
        Get detailed metrics for a specific sprint.
        
        Args:
            team_id: Team identifier
            sprint_name: Sprint name
            
        Returns:
            SprintMetrics or None if not found
        """
        if team_id not in self.velocity_history:
            return None
        
        # Find sprint
        sprint = next(
            (v for v in self.velocity_history[team_id] if v.sprint_name == sprint_name),
            None
        )
        
        if not sprint:
            return None
        
        # Calculate metrics
        completion_rate = (
            sprint.completed_story_points / sprint.planned_story_points
            if sprint.planned_story_points > 0 else 0.0
        )
        hours_per_point = (
            sprint.actual_hours / sprint.completed_story_points
            if sprint.completed_story_points > 0 else 0.0
        )
        
        return SprintMetrics(
            sprint_name=sprint.sprint_name,
            team_id=team_id,
            start_date=sprint.start_date,
            end_date=sprint.end_date,
            planned_story_points=float(sprint.planned_story_points),
            completed_story_points=float(sprint.completed_story_points),
            planned_tasks=sprint.tasks_planned,
            completed_tasks=sprint.tasks_completed,
            total_hours_spent=sprint.actual_hours,
            completion_rate=completion_rate,
            velocity=float(sprint.completed_story_points),
            hours_per_point=hours_per_point,
            team_size=0,  # Would need team member data
            capacity_utilization=0.0  # Would need capacity data
        )
    
    def forecast_velocity(
        self,
        team_id: str,
        forecast_sprints: int = 1,
        confidence_level: float = 0.9
    ) -> Optional[VelocityForecast]:
        """
        Forecast velocity for future sprints.
        
        Args:
            team_id: Team identifier
            forecast_sprints: Number of sprints to forecast
            confidence_level: Confidence level (e.g., 0.9 for 90%)
            
        Returns:
            VelocityForecast or None if insufficient data
        """
        history = self.get_velocity_history(team_id, limit=10)
        
        if len(history) < 3:
            return None  # Need at least 3 sprints for forecasting
        
        velocities = [float(v.completed_story_points) for v in history]
        
        # Simple moving average for prediction
        predicted = statistics.mean(velocities[:5] if len(velocities) >= 5 else velocities)
        
        # Calculate confidence interval
        if len(velocities) > 1:
            stdev = statistics.stdev(velocities)
        else:
            stdev = predicted * 0.2  # Assume 20% variance
        
        # Use 1.96 for 95% confidence, 1.645 for 90%
        z_score = 1.96 if confidence_level >= 0.95 else 1.645
        margin = z_score * stdev
        
        confidence_interval = (
            max(0, predicted - margin),
            predicted + margin
        )
        
        assumptions = [
            "Team composition remains stable",
            "Work complexity similar to recent sprints",
            "No major external disruptions",
            f"Based on last {len(history)} sprints"
        ]
        
        return VelocityForecast(
            team_id=team_id,
            forecast_sprints=forecast_sprints,
            predicted_velocity=round(predicted, 2),
            confidence_interval=(
                round(confidence_interval[0], 2),
                round(confidence_interval[1], 2)
            ),
            based_on_sprints=len(history),
            assumptions=assumptions
        )
    
    def calculate_capacity_from_velocity(
        self,
        team_id: str,
        target_story_points: float
    ) -> Optional[Dict[str, float]]:
        """
        Calculate how many sprints needed for target story points.
        
        Args:
            team_id: Team identifier
            target_story_points: Target story points to complete
            
        Returns:
            Dictionary with capacity calculations
        """
        trend = self.calculate_trend(team_id)
        
        if not trend or trend.avg_velocity <= 0:
            return None
        
        sprints_needed = target_story_points / trend.predicted_next_sprint
        
        # Adjust for reliability
        if trend.volatility > 0.3:  # High volatility
            buffer = 1.2  # 20% buffer
        elif trend.volatility > 0.2:  # Medium volatility
            buffer = 1.1  # 10% buffer
        else:
            buffer = 1.05  # 5% buffer
        
        adjusted_sprints = sprints_needed * buffer
        
        return {
            'target_story_points': target_story_points,
            'avg_velocity': trend.avg_velocity,
            'predicted_velocity': trend.predicted_next_sprint,
            'sprints_needed': round(sprints_needed, 1),
            'sprints_with_buffer': round(adjusted_sprints, 1),
            'buffer_percentage': round((buffer - 1) * 100, 1),
            'confidence': trend.confidence_level,
            'volatility': trend.volatility
        }
    
    def compare_sprints(
        self,
        team_id: str,
        sprint1_name: str,
        sprint2_name: str
    ) -> Optional[Dict[str, any]]:
        """
        Compare two sprints.
        
        Args:
            team_id: Team identifier
            sprint1_name: First sprint name
            sprint2_name: Second sprint name
            
        Returns:
            Comparison dictionary or None
        """
        metrics1 = self.get_sprint_metrics(team_id, sprint1_name)
        metrics2 = self.get_sprint_metrics(team_id, sprint2_name)
        
        if not metrics1 or not metrics2:
            return None
        
        velocity_change = metrics2.velocity - metrics1.velocity
        velocity_change_pct = (
            (velocity_change / metrics1.velocity * 100)
            if metrics1.velocity > 0 else 0
        )
        
        completion_change = metrics2.completion_rate - metrics1.completion_rate
        
        hours_per_point_change = metrics2.hours_per_point - metrics1.hours_per_point
        
        return {
            'sprint1': sprint1_name,
            'sprint2': sprint2_name,
            'velocity_change': round(velocity_change, 2),
            'velocity_change_percentage': round(velocity_change_pct, 2),
            'completion_rate_change': round(completion_change, 2),
            'hours_per_point_change': round(hours_per_point_change, 2),
            'sprint1_metrics': metrics1,
            'sprint2_metrics': metrics2
        }
    
    def get_team_performance_summary(
        self,
        team_id: str,
        lookback_sprints: int = 6
    ) -> Optional[Dict[str, any]]:
        """
        Get comprehensive team performance summary.
        
        Args:
            team_id: Team identifier
            lookback_sprints: Number of sprints to analyze
            
        Returns:
            Performance summary dictionary
        """
        history = self.get_velocity_history(team_id, limit=lookback_sprints)
        
        if not history:
            return None
        
        trend = self.calculate_trend(team_id, lookback_sprints)
        forecast = self.forecast_velocity(team_id)
        
        # Calculate additional metrics
        total_points_completed = sum(float(v.completed_story_points) for v in history)
        total_points_planned = sum(float(v.planned_story_points) for v in history)
        
        # Calculate successful sprints (>= 80% completion)
        successful_sprints = sum(
            1 for v in history 
            if v.planned_story_points > 0 and 
            (v.completed_story_points / v.planned_story_points) >= 0.8
        )
        success_rate = successful_sprints / len(history) if history else 0
        
        return {
            'team_id': team_id,
            'sprints_analyzed': len(history),
            'total_story_points_completed': round(total_points_completed, 2),
            'total_story_points_planned': round(total_points_planned, 2),
            'overall_completion_rate': round(total_points_completed / total_points_planned, 2) if total_points_planned > 0 else 0,
            'successful_sprints': successful_sprints,
            'success_rate': round(success_rate, 2),
            'trend': trend,
            'forecast': forecast,
            'most_recent_sprint': history[0].sprint_name if history else None
        }

