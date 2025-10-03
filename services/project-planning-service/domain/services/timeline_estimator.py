"""
Timeline Estimation Engine
==========================

Velocity-based timeline prediction with confidence intervals,
buffer recommendations, and what-if scenario analysis.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum
import statistics

from ..entities.feature import Feature
from ..entities.task import Task


class EstimationMethod(Enum):
    """Method for timeline estimation."""
    AVERAGE_VELOCITY = "average_velocity"  # Use average velocity
    WEIGHTED_VELOCITY = "weighted_velocity"  # Weight recent sprints higher
    OPTIMISTIC = "optimistic"  # Best case scenario
    PESSIMISTIC = "pessimistic"  # Worst case scenario
    THREE_POINT = "three_point"  # PERT estimation (optimistic + 4*likely + pessimistic) / 6


class ConfidenceLevel(Enum):
    """Confidence level for estimates."""
    LOW = "low"  # 50% confidence
    MEDIUM = "medium"  # 75% confidence
    HIGH = "high"  # 90% confidence
    VERY_HIGH = "very_high"  # 95% confidence


@dataclass
class VelocityData:
    """Historical velocity data."""
    sprint_name: str
    story_points_completed: float
    hours_spent: float
    tasks_completed: int
    sprint_duration_days: int


@dataclass
class TimelineEstimationRequest:
    """Request for timeline estimation."""
    features: List[Feature]
    tasks: List[Task]
    start_date: date
    velocity_data: List[VelocityData] = field(default_factory=list)
    method: EstimationMethod = EstimationMethod.WEIGHTED_VELOCITY
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    sprint_duration_weeks: int = 2
    include_buffer: bool = True
    buffer_percentage: float = 0.2  # 20% buffer by default


@dataclass
class TimelineEstimate:
    """Timeline estimation result."""
    estimated_completion_date: date
    estimated_duration_days: int
    estimated_sprints: int
    confidence_score: float  # 0-1
    confidence_interval: Tuple[date, date]  # (earliest, latest)
    velocity_used: float  # Story points per sprint
    total_effort: float  # Story points
    buffer_days: int
    risk_factors: List[str] = field(default_factory=list)
    assumptions: List[str] = field(default_factory=list)
    
    def is_realistic(self) -> bool:
        """Check if estimate seems realistic."""
        return self.confidence_score >= 0.5
    
    def variance_days(self) -> int:
        """Calculate variance between best and worst case."""
        earliest, latest = self.confidence_interval
        return (latest - earliest).days


@dataclass
class WhatIfScenario:
    """What-if scenario analysis."""
    scenario_name: str
    velocity_multiplier: float  # e.g., 1.2 = 20% faster
    estimated_completion: date
    duration_days: int
    description: str


class TimelineEstimator:
    """
    Velocity-based timeline estimation engine.
    
    Provides:
    - Realistic timeline predictions
    - Confidence intervals
    - Buffer recommendations
    - What-if scenario analysis
    - Risk assessment
    """
    
    def __init__(self):
        """Initialize timeline estimator."""
        self.default_velocity = 20.0  # Story points per sprint
        self.velocity_weights = [0.5, 0.3, 0.15, 0.05]  # Weight recent sprints higher
    
    def estimate_timeline(
        self,
        request: TimelineEstimationRequest
    ) -> TimelineEstimate:
        """
        Estimate project timeline based on velocity data.
        
        Args:
            request: Timeline estimation request
            
        Returns:
            TimelineEstimate with predictions and confidence intervals
        """
        # Calculate total effort
        total_effort = self._calculate_total_effort(request.features, request.tasks)
        
        # Determine velocity to use
        velocity = self._calculate_velocity(request.velocity_data, request.method)
        
        # Calculate base timeline
        sprints_needed = max(1, total_effort / velocity)
        duration_days = int(sprints_needed * request.sprint_duration_weeks * 7)
        
        # Add buffer if requested
        buffer_days = 0
        if request.include_buffer:
            buffer_days = int(duration_days * request.buffer_percentage)
            duration_days += buffer_days
        
        # Calculate completion date
        completion_date = request.start_date + timedelta(days=duration_days)
        
        # Calculate confidence interval
        confidence_interval = self._calculate_confidence_interval(
            request.start_date,
            total_effort,
            velocity,
            request.velocity_data,
            request.confidence_level,
            request.sprint_duration_weeks
        )
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence_score(
            request.velocity_data,
            total_effort,
            velocity
        )
        
        # Identify risk factors
        risk_factors = self._identify_risk_factors(
            request.velocity_data,
            total_effort,
            velocity,
            duration_days
        )
        
        # Document assumptions
        assumptions = self._document_assumptions(
            request.velocity_data,
            velocity,
            request.method,
            request.include_buffer
        )
        
        return TimelineEstimate(
            estimated_completion_date=completion_date,
            estimated_duration_days=duration_days,
            estimated_sprints=int(sprints_needed),
            confidence_score=confidence_score,
            confidence_interval=confidence_interval,
            velocity_used=velocity,
            total_effort=total_effort,
            buffer_days=buffer_days,
            risk_factors=risk_factors,
            assumptions=assumptions
        )
    
    def _calculate_total_effort(
        self,
        features: List[Feature],
        tasks: List[Task]
    ) -> float:
        """Calculate total effort in story points."""
        # Sum feature estimates
        feature_effort = sum(
            f.estimated_effort if f.estimated_effort else 0.0
            for f in features
        )
        
        # If no feature estimates, calculate from tasks (8 hours = 1 story point)
        if feature_effort == 0.0 and tasks:
            task_hours = sum(
                t.estimated_hours if t.estimated_hours else 0.0
                for t in tasks
            )
            feature_effort = task_hours / 8.0
        
        return max(1.0, feature_effort)  # At least 1 story point
    
    def _calculate_velocity(
        self,
        velocity_data: List[VelocityData],
        method: EstimationMethod
    ) -> float:
        """Calculate velocity based on historical data and method."""
        if not velocity_data:
            return self.default_velocity
        
        velocities = [v.story_points_completed for v in velocity_data]
        
        if method == EstimationMethod.AVERAGE_VELOCITY:
            return statistics.mean(velocities)
        
        elif method == EstimationMethod.WEIGHTED_VELOCITY:
            # Weight recent sprints more heavily
            weighted_sum = 0.0
            weight_sum = 0.0
            
            for i, velocity_item in enumerate(reversed(velocity_data)):
                weight = self.velocity_weights[min(i, len(self.velocity_weights) - 1)]
                weighted_sum += velocity_item.story_points_completed * weight
                weight_sum += weight
            
            return weighted_sum / weight_sum if weight_sum > 0 else self.default_velocity
        
        elif method == EstimationMethod.OPTIMISTIC:
            return max(velocities)
        
        elif method == EstimationMethod.PESSIMISTIC:
            return min(velocities)
        
        elif method == EstimationMethod.THREE_POINT:
            optimistic = max(velocities)
            pessimistic = min(velocities)
            likely = statistics.median(velocities)
            return (optimistic + 4 * likely + pessimistic) / 6
        
        else:
            return self.default_velocity
    
    def _calculate_confidence_interval(
        self,
        start_date: date,
        total_effort: float,
        velocity: float,
        velocity_data: List[VelocityData],
        confidence_level: ConfidenceLevel,
        sprint_duration_weeks: int
    ) -> Tuple[date, date]:
        """Calculate confidence interval for completion date."""
        if not velocity_data:
            # Without historical data, use wider intervals
            base_days = int((total_effort / velocity) * sprint_duration_weeks * 7)
            margin = int(base_days * 0.3)  # ±30%
            earliest = start_date + timedelta(days=base_days - margin)
            latest = start_date + timedelta(days=base_days + margin)
            return (earliest, latest)
        
        # Calculate velocity variance
        velocities = [v.story_points_completed for v in velocity_data]
        if len(velocities) > 1:
            velocity_std = statistics.stdev(velocities)
        else:
            velocity_std = velocity * 0.2  # Assume 20% variance
        
        # Determine margin based on confidence level
        confidence_multiplier = {
            ConfidenceLevel.LOW: 0.674,  # 50% confidence (0.5 std dev)
            ConfidenceLevel.MEDIUM: 1.15,  # 75% confidence (~1.15 std dev)
            ConfidenceLevel.HIGH: 1.645,  # 90% confidence
            ConfidenceLevel.VERY_HIGH: 1.96  # 95% confidence
        }
        
        multiplier = confidence_multiplier.get(confidence_level, 1.15)
        
        # Calculate date range
        base_days = int((total_effort / velocity) * sprint_duration_weeks * 7)
        
        # Optimistic (faster velocity)
        optimistic_velocity = velocity + (velocity_std * multiplier)
        optimistic_days = int((total_effort / optimistic_velocity) * sprint_duration_weeks * 7)
        earliest = start_date + timedelta(days=optimistic_days)
        
        # Pessimistic (slower velocity)
        pessimistic_velocity = max(1.0, velocity - (velocity_std * multiplier))
        pessimistic_days = int((total_effort / pessimistic_velocity) * sprint_duration_weeks * 7)
        latest = start_date + timedelta(days=pessimistic_days)
        
        return (earliest, latest)
    
    def _calculate_confidence_score(
        self,
        velocity_data: List[VelocityData],
        total_effort: float,
        velocity: float
    ) -> float:
        """Calculate confidence score (0-1) for the estimate."""
        confidence = 1.0
        
        # Reduce confidence if no historical data
        if not velocity_data:
            confidence *= 0.5
        elif len(velocity_data) < 3:
            confidence *= 0.7
        
        # Reduce confidence if velocity is inconsistent
        if velocity_data and len(velocity_data) > 1:
            velocities = [v.story_points_completed for v in velocity_data]
            velocity_std = statistics.stdev(velocities)
            coefficient_of_variation = velocity_std / statistics.mean(velocities)
            
            if coefficient_of_variation > 0.5:  # High variance
                confidence *= 0.6
            elif coefficient_of_variation > 0.3:
                confidence *= 0.8
        
        # Reduce confidence for very large projects
        if total_effort > 100:
            confidence *= 0.8
        elif total_effort > 50:
            confidence *= 0.9
        
        return max(0.0, min(confidence, 1.0))
    
    def _identify_risk_factors(
        self,
        velocity_data: List[VelocityData],
        total_effort: float,
        velocity: float,
        duration_days: int
    ) -> List[str]:
        """Identify risk factors that could affect timeline."""
        risks = []
        
        # Insufficient historical data
        if not velocity_data:
            risks.append("No historical velocity data - estimate based on assumptions")
        elif len(velocity_data) < 3:
            risks.append(f"Limited velocity data ({len(velocity_data)} sprints) - estimate may be unreliable")
        
        # High velocity variance
        if velocity_data and len(velocity_data) > 1:
            velocities = [v.story_points_completed for v in velocity_data]
            velocity_std = statistics.stdev(velocities)
            if velocity_std / statistics.mean(velocities) > 0.3:
                risks.append("High velocity variance - team performance inconsistent")
        
        # Large project
        if total_effort > 100:
            risks.append("Large project (>100 points) - higher uncertainty in estimates")
        
        # Long duration
        if duration_days > 180:  # > 6 months
            risks.append("Long project duration - increased risk of scope changes")
        
        # Low velocity
        if velocity < 10:
            risks.append("Low team velocity - consider increasing team capacity")
        
        return risks
    
    def _document_assumptions(
        self,
        velocity_data: List[VelocityData],
        velocity: float,
        method: EstimationMethod,
        include_buffer: bool
    ) -> List[str]:
        """Document assumptions made in estimation."""
        assumptions = []
        
        # Velocity assumptions
        if velocity_data:
            assumptions.append(
                f"Based on {len(velocity_data)} sprint(s) of historical data"
            )
            assumptions.append(
                f"Using {method.value} method with velocity of {velocity:.1f} points/sprint"
            )
        else:
            assumptions.append(
                f"No historical data - using default velocity of {velocity:.1f} points/sprint"
            )
        
        # Team assumptions
        assumptions.append("Team capacity remains stable")
        assumptions.append("No major scope changes")
        assumptions.append("No team member turnover")
        
        # Buffer assumptions
        if include_buffer:
            assumptions.append("Includes buffer time for unknowns and risks")
        else:
            assumptions.append("No buffer included - timeline is optimistic")
        
        return assumptions
    
    def analyze_what_if_scenarios(
        self,
        request: TimelineEstimationRequest
    ) -> List[WhatIfScenario]:
        """
        Analyze what-if scenarios with different velocity assumptions.
        
        Args:
            request: Timeline estimation request
            
        Returns:
            List of what-if scenarios
        """
        base_estimate = self.estimate_timeline(request)
        scenarios = []
        
        # Scenario 1: Team works 20% faster
        scenarios.append(self._create_scenario(
            "Increased Velocity (+20%)",
            1.2,
            request,
            "Team increases velocity through improved processes or additional resources"
        ))
        
        # Scenario 2: Team works 20% slower
        scenarios.append(self._create_scenario(
            "Decreased Velocity (-20%)",
            0.8,
            request,
            "Team velocity decreases due to interruptions, complexity, or technical debt"
        ))
        
        # Scenario 3: Optimistic (50% faster)
        scenarios.append(self._create_scenario(
            "Optimistic (+50%)",
            1.5,
            request,
            "Best case scenario with perfect conditions and no blockers"
        ))
        
        # Scenario 4: Pessimistic (50% slower)
        scenarios.append(self._create_scenario(
            "Pessimistic (-50%)",
            0.5,
            request,
            "Worst case scenario with significant challenges and blockers"
        ))
        
        return scenarios
    
    def _create_scenario(
        self,
        name: str,
        multiplier: float,
        request: TimelineEstimationRequest,
        description: str
    ) -> WhatIfScenario:
        """Create a what-if scenario with adjusted velocity."""
        # Adjust velocity data
        adjusted_velocity_data = [
            VelocityData(
                sprint_name=v.sprint_name,
                story_points_completed=v.story_points_completed * multiplier,
                hours_spent=v.hours_spent,
                tasks_completed=v.tasks_completed,
                sprint_duration_days=v.sprint_duration_days
            )
            for v in request.velocity_data
        ]
        
        # Create adjusted request
        adjusted_request = TimelineEstimationRequest(
            features=request.features,
            tasks=request.tasks,
            start_date=request.start_date,
            velocity_data=adjusted_velocity_data,
            method=request.method,
            confidence_level=request.confidence_level,
            sprint_duration_weeks=request.sprint_duration_weeks,
            include_buffer=request.include_buffer,
            buffer_percentage=request.buffer_percentage
        )
        
        # Estimate with adjusted velocity
        estimate = self.estimate_timeline(adjusted_request)
        
        return WhatIfScenario(
            scenario_name=name,
            velocity_multiplier=multiplier,
            estimated_completion=estimate.estimated_completion_date,
            duration_days=estimate.estimated_duration_days,
            description=description
        )
    
    def compare_methods(
        self,
        request: TimelineEstimationRequest
    ) -> Dict[str, TimelineEstimate]:
        """
        Compare different estimation methods.
        
        Args:
            request: Timeline estimation request
            
        Returns:
            Dictionary mapping method names to estimates
        """
        results = {}
        
        for method in EstimationMethod:
            method_request = TimelineEstimationRequest(
                features=request.features,
                tasks=request.tasks,
                start_date=request.start_date,
                velocity_data=request.velocity_data,
                method=method,
                confidence_level=request.confidence_level,
                sprint_duration_weeks=request.sprint_duration_weeks,
                include_buffer=request.include_buffer,
                buffer_percentage=request.buffer_percentage
            )
            
            estimate = self.estimate_timeline(method_request)
            results[method.value] = estimate
        
        return results

