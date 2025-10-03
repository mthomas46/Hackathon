"""
Milestone Planning Engine
=========================

Automatically generates balanced milestones from features and sprints,
with progress tracking and velocity-based adjustments.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum

from ..entities.feature import Feature, FeatureStatus
from ..entities.roadmap import Sprint


class MilestoneType(Enum):
    """Type of milestone."""
    SPRINT = "sprint"  # Sprint-based milestone
    RELEASE = "release"  # Release milestone
    PHASE = "phase"  # Project phase milestone
    DELIVERABLE = "deliverable"  # Key deliverable milestone


@dataclass
class Milestone:
    """Project milestone."""
    id: str
    name: str
    description: str
    milestone_type: MilestoneType
    target_date: date
    feature_ids: List[str] = field(default_factory=list)
    completed: bool = False
    completion_date: Optional[date] = None
    story_points: float = 0.0
    
    def is_overdue(self, current_date: date) -> bool:
        """Check if milestone is overdue."""
        return not self.completed and current_date > self.target_date
    
    def days_until(self, current_date: date) -> int:
        """Calculate days until milestone (negative if past)."""
        return (self.target_date - current_date).days


@dataclass
class MilestonePlanRequest:
    """Request for milestone planning."""
    features: List[Feature]
    sprints: List[Sprint]
    start_date: date
    milestone_frequency_weeks: int = 4  # Create milestone every N weeks
    min_features_per_milestone: int = 2
    max_features_per_milestone: int = 8
    strategy: str = "balanced"  # balanced, sprint_based, value_based


@dataclass
class MilestonePlan:
    """Generated milestone plan."""
    milestones: List[Milestone]
    total_story_points: float
    estimated_completion_date: date
    milestone_count: int
    
    def get_next_milestone(self, current_date: date) -> Optional[Milestone]:
        """Get next upcoming milestone."""
        upcoming = [m for m in self.milestones if not m.completed and m.target_date >= current_date]
        return min(upcoming, key=lambda m: m.target_date) if upcoming else None
    
    def completion_percentage(self) -> float:
        """Calculate overall completion percentage."""
        if not self.milestones:
            return 0.0
        completed = sum(1 for m in self.milestones if m.completed)
        return (completed / len(self.milestones)) * 100


class MilestonePlanner:
    """
    Intelligent milestone planning engine.
    
    Generates balanced milestones that:
    - Group related features
    - Balance workload
    - Align with sprints
    - Track progress
    """
    
    def __init__(self):
        """Initialize milestone planner."""
        self.default_milestone_weeks = 4
    
    def generate_milestones(
        self,
        request: MilestonePlanRequest
    ) -> MilestonePlan:
        """
        Generate milestone plan from features and sprints.
        
        Args:
            request: Milestone planning request
            
        Returns:
            MilestonePlan with generated milestones
        """
        if request.strategy == "sprint_based":
            milestones = self._generate_sprint_based_milestones(request)
        elif request.strategy == "value_based":
            milestones = self._generate_value_based_milestones(request)
        else:  # balanced
            milestones = self._generate_balanced_milestones(request)
        
        # Calculate totals
        total_points = sum(m.story_points for m in milestones)
        completion_date = milestones[-1].target_date if milestones else request.start_date
        
        return MilestonePlan(
            milestones=milestones,
            total_story_points=total_points,
            estimated_completion_date=completion_date,
            milestone_count=len(milestones)
        )
    
    def _generate_balanced_milestones(
        self,
        request: MilestonePlanRequest
    ) -> List[Milestone]:
        """Generate balanced milestones with even distribution of work."""
        milestones = []
        
        # Calculate milestone frequency
        milestone_frequency_days = request.milestone_frequency_weeks * 7
        
        # Group features into milestones
        current_features = []
        current_points = 0.0
        milestone_num = 1
        current_date = request.start_date
        
        # Sort features by priority (if available)
        sorted_features = sorted(
            request.features,
            key=lambda f: (f.priority.value if hasattr(f, 'priority') and f.priority else 'medium',
                          -(f.estimated_effort if f.estimated_effort else 0))
        )
        
        for feature in sorted_features:
            effort = feature.estimated_effort if feature.estimated_effort else 5.0
            
            # Check if we should create a milestone
            should_create = (
                len(current_features) >= request.max_features_per_milestone or
                (len(current_features) >= request.min_features_per_milestone and
                 current_points + effort > 20.0)  # ~2 sprints worth
            )
            
            if should_create and current_features:
                # Create milestone
                milestone = Milestone(
                    id=f"milestone-{milestone_num}",
                    name=f"Milestone {milestone_num}",
                    description=f"Complete {len(current_features)} features",
                    milestone_type=MilestoneType.PHASE,
                    target_date=current_date,
                    feature_ids=[f.id for f in current_features],
                    story_points=current_points
                )
                milestones.append(milestone)
                
                # Reset for next milestone
                current_features = []
                current_points = 0.0
                milestone_num += 1
                current_date += timedelta(days=milestone_frequency_days)
            
            # Add feature to current group
            current_features.append(feature)
            current_points += effort
        
        # Add remaining features as final milestone
        if current_features:
            milestone = Milestone(
                id=f"milestone-{milestone_num}",
                name=f"Milestone {milestone_num} (Final)",
                description=f"Complete final {len(current_features)} features",
                milestone_type=MilestoneType.DELIVERABLE,
                target_date=current_date,
                feature_ids=[f.id for f in current_features],
                story_points=current_points
            )
            milestones.append(milestone)
        
        return milestones
    
    def _generate_sprint_based_milestones(
        self,
        request: MilestonePlanRequest
    ) -> List[Milestone]:
        """Generate milestones aligned with sprints."""
        milestones = []
        
        if not request.sprints:
            # Fall back to balanced if no sprints
            return self._generate_balanced_milestones(request)
        
        # Group sprints into milestones
        sprints_per_milestone = request.milestone_frequency_weeks // 2  # Assuming 2-week sprints
        sprints_per_milestone = max(1, sprints_per_milestone)
        
        for i in range(0, len(request.sprints), sprints_per_milestone):
            sprint_group = request.sprints[i:i + sprints_per_milestone]
            milestone_num = (i // sprints_per_milestone) + 1
            
            # Collect features from these sprints
            feature_ids = []
            total_points = 0.0
            
            for sprint in sprint_group:
                feature_ids.extend(sprint.feature_ids)
                total_points += sprint.allocated
            
            milestone = Milestone(
                id=f"milestone-{milestone_num}",
                name=f"Sprint Milestone {milestone_num}",
                description=f"Complete sprints {sprint_group[0].name} through {sprint_group[-1].name}",
                milestone_type=MilestoneType.SPRINT,
                target_date=sprint_group[-1].end_date,
                feature_ids=feature_ids,
                story_points=total_points
            )
            milestones.append(milestone)
        
        return milestones
    
    def _generate_value_based_milestones(
        self,
        request: MilestonePlanRequest
    ) -> List[Milestone]:
        """Generate milestones prioritizing high-value features."""
        # Similar to balanced but group by priority
        milestones = []
        
        # Group features by priority
        priority_groups = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
        for feature in request.features:
            priority = feature.priority.value if hasattr(feature, 'priority') and feature.priority else 'medium'
            priority_groups[priority].append(feature)
        
        milestone_num = 1
        current_date = request.start_date
        milestone_frequency_days = request.milestone_frequency_weeks * 7
        
        # Create milestones for each priority level
        for priority in ['critical', 'high', 'medium', 'low']:
            features = priority_groups[priority]
            if not features:
                continue
            
            total_points = sum(f.estimated_effort if f.estimated_effort else 5.0 for f in features)
            
            milestone = Milestone(
                id=f"milestone-{milestone_num}",
                name=f"Milestone {milestone_num}: {priority.title()} Priority",
                description=f"Complete {len(features)} {priority} priority features",
                milestone_type=MilestoneType.DELIVERABLE,
                target_date=current_date,
                feature_ids=[f.id for f in features],
                story_points=total_points
            )
            milestones.append(milestone)
            
            milestone_num += 1
            current_date += timedelta(days=milestone_frequency_days)
        
        return milestones
    
    def track_milestone_progress(
        self,
        milestone: Milestone,
        features: List[Feature]
    ) -> float:
        """
        Track progress towards milestone completion.
        
        Args:
            milestone: Milestone to track
            features: All features in project
            
        Returns:
            Progress percentage (0-100)
        """
        if not milestone.feature_ids:
            return 100.0 if milestone.completed else 0.0
        
        # Find features for this milestone
        milestone_features = [f for f in features if f.id in milestone.feature_ids]
        
        if not milestone_features:
            return 0.0
        
        # Count completed features
        completed = sum(
            1 for f in milestone_features 
            if f.status == FeatureStatus.COMPLETED
        )
        
        return (completed / len(milestone_features)) * 100
    
    def adjust_milestone_dates(
        self,
        milestone_plan: MilestonePlan,
        actual_velocity: float,
        planned_velocity: float
    ) -> MilestonePlan:
        """
        Adjust milestone dates based on actual vs planned velocity.
        
        Args:
            milestone_plan: Original milestone plan
            actual_velocity: Actual team velocity
            planned_velocity: Planned velocity
            
        Returns:
            Adjusted milestone plan
        """
        if planned_velocity == 0 or actual_velocity == planned_velocity:
            return milestone_plan
        
        # Calculate adjustment factor
        velocity_ratio = planned_velocity / actual_velocity
        
        # Adjust all incomplete milestones
        adjusted_milestones = []
        
        for milestone in milestone_plan.milestones:
            if milestone.completed:
                adjusted_milestones.append(milestone)
            else:
                # Calculate days to adjust
                original_days = (milestone.target_date - milestone_plan.milestones[0].target_date).days
                adjusted_days = int(original_days * velocity_ratio)
                
                adjusted_milestone = Milestone(
                    id=milestone.id,
                    name=milestone.name,
                    description=milestone.description,
                    milestone_type=milestone.milestone_type,
                    target_date=milestone_plan.milestones[0].target_date + timedelta(days=adjusted_days),
                    feature_ids=milestone.feature_ids.copy(),
                    completed=milestone.completed,
                    completion_date=milestone.completion_date,
                    story_points=milestone.story_points
                )
                adjusted_milestones.append(adjusted_milestone)
        
        return MilestonePlan(
            milestones=adjusted_milestones,
            total_story_points=milestone_plan.total_story_points,
            estimated_completion_date=adjusted_milestones[-1].target_date if adjusted_milestones else milestone_plan.estimated_completion_date,
            milestone_count=len(adjusted_milestones)
        )
    
    def suggest_milestone_names(
        self,
        milestone: Milestone,
        features: List[Feature]
    ) -> List[str]:
        """
        Suggest meaningful names for milestone based on features.
        
        Args:
            milestone: Milestone to name
            features: Features in milestone
            
        Returns:
            List of suggested names
        """
        milestone_features = [f for f in features if f.id in milestone.feature_ids]
        
        if not milestone_features:
            return [milestone.name]
        
        suggestions = []
        
        # Theme-based names
        if len(milestone_features) <= 3:
            # Use feature names
            feature_names = [f.title for f in milestone_features[:3]]
            suggestions.append(" + ".join(feature_names))
        
        # Value-based names
        suggestions.append(f"{len(milestone_features)} Feature Release")
        
        # Date-based names
        month_name = milestone.target_date.strftime("%B %Y")
        suggestions.append(f"{month_name} Release")
        
        # Versioning
        milestone_num = int(milestone.id.split('-')[-1]) if '-' in milestone.id else 1
        suggestions.append(f"v{milestone_num}.0 Release")
        
        return suggestions

