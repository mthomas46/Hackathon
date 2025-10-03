"""
Roadmap Generation Engine
=========================

Automatically generates comprehensive development roadmaps from feature lists,
integrating with all Phase 1-3 services for intelligent planning.
"""

from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import date, timedelta
from enum import Enum

from ..entities.feature import Feature, FeatureStatus, FeaturePriority
from ..entities.task import Task, TaskType, TaskStatus
from ..entities.roadmap import Roadmap, Release, Sprint, ReleaseStatus


class RoadmapStrategy(Enum):
    """Strategy for organizing roadmap."""
    SPRINT_BASED = "sprint_based"  # Organize by 2-week sprints
    RELEASE_BASED = "release_based"  # Organize by releases
    MILESTONE_BASED = "milestone_based"  # Organize by milestones
    CONTINUOUS = "continuous"  # Continuous delivery


@dataclass
class RoadmapGenerationRequest:
    """Request for roadmap generation."""
    features: List[Feature]
    team_id: str
    start_date: date
    target_date: Optional[date] = None
    strategy: RoadmapStrategy = RoadmapStrategy.SPRINT_BASED
    sprint_duration_weeks: int = 2
    velocity: Optional[float] = None  # Story points per sprint
    constraints: Dict[str, any] = field(default_factory=dict)


@dataclass
class RoadmapGenerationResult:
    """Result of roadmap generation."""
    roadmap: Roadmap
    releases: List[Release]
    sprints: List[Sprint]
    unscheduled_features: List[Feature]
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    confidence: float = 0.0  # 0-1, confidence in timeline
    
    def is_feasible(self) -> bool:
        """Check if roadmap is feasible within constraints."""
        return len(self.unscheduled_features) == 0
    
    def completion_date(self) -> Optional[date]:
        """Get estimated completion date."""
        if not self.sprints:
            return None
        return max(sprint.end_date for sprint in self.sprints)


class RoadmapGenerator:
    """
    Intelligent roadmap generation engine.
    
    Generates comprehensive development roadmaps by:
    - Organizing features into sprints/releases
    - Calculating realistic timelines
    - Balancing workload
    - Identifying risks
    - Providing recommendations
    """
    
    def __init__(self):
        """Initialize roadmap generator."""
        self.default_sprint_duration = 14  # days
        self.default_capacity_per_sprint = 40  # hours
    
    def generate_roadmap(
        self,
        request: RoadmapGenerationRequest
    ) -> RoadmapGenerationResult:
        """
        Generate comprehensive roadmap from features.
        
        Args:
            request: Roadmap generation request
            
        Returns:
            RoadmapGenerationResult with roadmap and metadata
        """
        # Validate request
        self._validate_request(request)
        
        # Sort features by priority
        sorted_features = self._prioritize_features(request.features)
        
        # Estimate total effort
        total_effort = self._estimate_total_effort(sorted_features)
        
        # Calculate timeline
        if request.strategy == RoadmapStrategy.SPRINT_BASED:
            result = self._generate_sprint_based_roadmap(request, sorted_features, total_effort)
        elif request.strategy == RoadmapStrategy.RELEASE_BASED:
            result = self._generate_release_based_roadmap(request, sorted_features, total_effort)
        elif request.strategy == RoadmapStrategy.MILESTONE_BASED:
            result = self._generate_milestone_based_roadmap(request, sorted_features, total_effort)
        else:
            result = self._generate_continuous_roadmap(request, sorted_features, total_effort)
        
        # Add recommendations
        result.recommendations = self._generate_recommendations(result, request)
        
        # Calculate confidence
        result.confidence = self._calculate_confidence(result, request)
        
        return result
    
    def _validate_request(self, request: RoadmapGenerationRequest) -> None:
        """Validate roadmap generation request."""
        if not request.features:
            raise ValueError("At least one feature required")
        
        if request.sprint_duration_weeks <= 0:
            raise ValueError("Sprint duration must be positive")
        
        if request.target_date and request.target_date < request.start_date:
            raise ValueError("Target date must be after start date")
        
        if request.velocity is not None and request.velocity <= 0:
            raise ValueError("Velocity must be positive")
    
    def _prioritize_features(self, features: List[Feature]) -> List[Feature]:
        """
        Sort features by priority and dependencies.
        
        Priority order:
        1. CRITICAL features first
        2. HIGH priority features
        3. MEDIUM priority features
        4. LOW priority features
        """
        priority_order = {
            FeaturePriority.CRITICAL: 0,
            FeaturePriority.HIGH: 1,
            FeaturePriority.MEDIUM: 2,
            FeaturePriority.LOW: 3
        }
        
        return sorted(
            features,
            key=lambda f: (
                priority_order.get(f.priority, 99),
                len(f.dependencies),  # Fewer dependencies first
                -f.estimated_effort if f.estimated_effort else 0  # Larger first (within priority)
            )
        )
    
    def _estimate_total_effort(self, features: List[Feature]) -> float:
        """Calculate total effort for all features."""
        return sum(
            f.estimated_effort if f.estimated_effort else 0.0
            for f in features
        )
    
    def _generate_sprint_based_roadmap(
        self,
        request: RoadmapGenerationRequest,
        features: List[Feature],
        total_effort: float
    ) -> RoadmapGenerationResult:
        """Generate sprint-based roadmap."""
        # Calculate sprint parameters
        sprint_duration_days = request.sprint_duration_weeks * 7
        velocity = request.velocity if request.velocity else 20.0  # Default velocity
        
        # Calculate number of sprints needed
        sprints_needed = max(1, int(total_effort / velocity) + 1)
        
        # Create sprints
        sprints = []
        current_date = request.start_date
        
        for i in range(sprints_needed):
            sprint_start = current_date
            sprint_end = current_date + timedelta(days=sprint_duration_days - 1)
            
            sprint = Sprint(
                id=f"sprint-{i+1}",
                name=f"Sprint {i+1}",
                start_date=sprint_start,
                end_date=sprint_end,
                capacity=velocity,
                allocated=0.0
            )
            sprints.append(sprint)
            current_date = sprint_end + timedelta(days=1)
        
        # Allocate features to sprints
        scheduled_features = []
        unscheduled_features = []
        
        sprint_idx = 0
        for feature in features:
            effort = feature.estimated_effort if feature.estimated_effort else 5.0
            
            # Find sprint with capacity
            while sprint_idx < len(sprints):
                sprint = sprints[sprint_idx]
                remaining = sprint.capacity - sprint.allocated
                
                if remaining >= effort:
                    # Allocate to this sprint
                    sprint.allocated += effort
                    sprint.feature_ids.append(feature.id)
                    feature.roadmap_id = f"roadmap-{request.team_id}"
                    scheduled_features.append(feature)
                    break
                else:
                    # Move to next sprint
                    sprint_idx += 1
            else:
                # No sprint has capacity
                unscheduled_features.append(feature)
        
        # Create roadmap
        roadmap = Roadmap(
            id=f"roadmap-{request.team_id}",
            name=f"Development Roadmap - {request.team_id}",
            created_by="system",
            description="Auto-generated development roadmap",
            start_date=request.start_date,
            end_date=sprints[-1].end_date if sprints else request.start_date
        )
        
        # Create releases (group sprints)
        releases = self._group_sprints_into_releases(sprints, request.start_date)
        
        # Generate warnings
        warnings = []
        if unscheduled_features:
            warnings.append(f"{len(unscheduled_features)} features could not be scheduled")
        
        if request.target_date and roadmap.end_date > request.target_date:
            days_over = (roadmap.end_date - request.target_date).days
            warnings.append(f"Roadmap exceeds target date by {days_over} days")
        
        return RoadmapGenerationResult(
            roadmap=roadmap,
            releases=releases,
            sprints=sprints,
            unscheduled_features=unscheduled_features,
            warnings=warnings
        )
    
    def _generate_release_based_roadmap(
        self,
        request: RoadmapGenerationRequest,
        features: List[Feature],
        total_effort: float
    ) -> RoadmapGenerationResult:
        """Generate release-based roadmap (groups of features)."""
        # Group features into releases (every ~6 weeks worth of work)
        release_capacity = (request.velocity if request.velocity else 20.0) * 3  # 3 sprints
        
        releases = []
        current_date = request.start_date
        current_features = []
        current_effort = 0.0
        release_num = 1
        
        for feature in features:
            effort = feature.estimated_effort if feature.estimated_effort else 5.0
            
            if current_effort + effort > release_capacity and current_features:
                # Create release
                release_end = current_date + timedelta(weeks=6)
                release = Release(
                    id=f"release-{release_num}",
                    name=f"Release {release_num}",
                    version=f"v{release_num}.0.0",
                    planned_date=release_end,
                    feature_ids=[f.id for f in current_features],
                    status="planned"
                )
                releases.append(release)
                
                # Reset for next release
                current_date = release_end + timedelta(days=1)
                current_features = []
                current_effort = 0.0
                release_num += 1
            
            current_features.append(feature)
            current_effort += effort
        
        # Add remaining features to final release
        if current_features:
            release_end = current_date + timedelta(weeks=6)
            release = Release(
                id=f"release-{release_num}",
                name=f"Release {release_num}",
                description=f"v{release_num}.0.0",
                planned_release_date=release_end,
                feature_ids=[f.id for f in current_features],
                status=ReleaseStatus.PLANNED
            )
            releases.append(release)
        
        # Create roadmap
        roadmap = Roadmap(
            id=f"roadmap-{request.team_id}",
            name=f"Release Roadmap - {request.team_id}",
            created_by="system",
            description="Release-based development roadmap",
            start_date=request.start_date,
            end_date=releases[-1].planned_release_date if releases else request.start_date
        )
        
        # Convert releases to sprints for consistency
        sprints = self._releases_to_sprints(releases, request)
        
        return RoadmapGenerationResult(
            roadmap=roadmap,
            releases=releases,
            sprints=sprints,
            unscheduled_features=[],
            warnings=[]
        )
    
    def _generate_milestone_based_roadmap(
        self,
        request: RoadmapGenerationRequest,
        features: List[Feature],
        total_effort: float
    ) -> RoadmapGenerationResult:
        """Generate milestone-based roadmap."""
        # Similar to release-based but with shorter cycles
        return self._generate_release_based_roadmap(request, features, total_effort)
    
    def _generate_continuous_roadmap(
        self,
        request: RoadmapGenerationRequest,
        features: List[Feature],
        total_effort: float
    ) -> RoadmapGenerationResult:
        """Generate continuous delivery roadmap."""
        # All features in one continuous flow
        roadmap = Roadmap(
            id=f"roadmap-{request.team_id}",
            name=f"Continuous Delivery Roadmap - {request.team_id}",
            created_by="system",
            description="Continuous delivery roadmap",
            start_date=request.start_date,
            end_date=request.target_date if request.target_date else request.start_date + timedelta(weeks=12)
        )
        
        return RoadmapGenerationResult(
            roadmap=roadmap,
            releases=[],
            sprints=[],
            unscheduled_features=[],
            warnings=[]
        )
    
    def _group_sprints_into_releases(
        self,
        sprints: List[Sprint],
        start_date: date
    ) -> List[Release]:
        """Group sprints into releases (every 3 sprints = 1 release)."""
        releases = []
        sprints_per_release = 3
        
        for i in range(0, len(sprints), sprints_per_release):
            sprint_group = sprints[i:i + sprints_per_release]
            release_num = (i // sprints_per_release) + 1
            
            # Collect all features from sprints
            feature_ids = []
            for sprint in sprint_group:
                feature_ids.extend(sprint.feature_ids)
            
            release = Release(
                id=f"release-{release_num}",
                name=f"Release {release_num}",
                description=f"v{release_num}.0.0",
                planned_release_date=sprint_group[-1].end_date,
                feature_ids=feature_ids,
                status=ReleaseStatus.PLANNED
            )
            releases.append(release)
        
        return releases
    
    def _releases_to_sprints(
        self,
        releases: List[Release],
        request: RoadmapGenerationRequest
    ) -> List[Sprint]:
        """Convert releases to sprints for consistency."""
        sprints = []
        sprint_duration_days = request.sprint_duration_weeks * 7
        
        for release in releases:
            # Calculate how many sprints for this release
            release_start = releases[0].planned_release_date if releases.index(release) == 0 else releases[releases.index(release) - 1].planned_release_date
            sprints_in_release = 3  # Default 3 sprints per release
            
            for i in range(sprints_in_release):
                sprint_start = release_start + timedelta(days=i * sprint_duration_days)
                sprint_end = sprint_start + timedelta(days=sprint_duration_days - 1)
                
                sprint = Sprint(
                    id=f"sprint-{len(sprints) + 1}",
                    name=f"Sprint {len(sprints) + 1}",
                    start_date=sprint_start,
                    end_date=sprint_end,
                    capacity=request.velocity if request.velocity else 20.0,
                    allocated=0.0,
                    feature_ids=release.feature_ids if i == 0 else []
                )
                sprints.append(sprint)
        
        return sprints
    
    def _generate_recommendations(
        self,
        result: RoadmapGenerationResult,
        request: RoadmapGenerationRequest
    ) -> List[str]:
        """Generate recommendations for roadmap improvement."""
        recommendations = []
        
        # Check timeline feasibility
        if request.target_date and result.completion_date():
            days_difference = (result.completion_date() - request.target_date).days
            if days_difference > 0:
                recommendations.append(
                    f"Consider increasing team capacity or reducing scope by {days_difference} days"
                )
        
        # Check feature distribution
        if result.sprints:
            sprint_loads = [s.allocated / s.capacity for s in result.sprints]
            if sprint_loads and max(sprint_loads) > 0.9:
                recommendations.append("Some sprints are near capacity - consider buffering")
            
            if sprint_loads and min(sprint_loads) < 0.5:
                recommendations.append("Some sprints are underutilized - consider consolidation")
        
        # Check unscheduled features
        if result.unscheduled_features:
            recommendations.append(
                f"Add {len(result.unscheduled_features)} more sprints or reduce feature scope"
            )
        
        return recommendations
    
    def _calculate_confidence(
        self,
        result: RoadmapGenerationResult,
        request: RoadmapGenerationRequest
    ) -> float:
        """Calculate confidence in roadmap (0-1)."""
        confidence = 1.0
        
        # Reduce confidence for unscheduled features
        if result.unscheduled_features:
            penalty = len(result.unscheduled_features) / len(request.features)
            confidence -= penalty * 0.5
        
        # Reduce confidence if velocity not provided
        if request.velocity is None:
            confidence -= 0.2
        
        # Reduce confidence for tight deadlines
        if request.target_date and result.completion_date():
            days_available = (request.target_date - request.start_date).days
            days_needed = (result.completion_date() - request.start_date).days
            if days_needed > days_available:
                confidence -= 0.3
        
        return max(0.0, min(confidence, 1.0))

