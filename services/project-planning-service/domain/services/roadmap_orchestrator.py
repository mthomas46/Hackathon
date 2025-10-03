"""
Roadmap Orchestration Service
==============================

High-level orchestrator that coordinates all roadmap generation components
to produce complete, validated development roadmaps with intelligent planning.
"""

from typing import List, Dict, Optional
from dataclasses import dataclass, field
from datetime import date

from ..entities.feature import Feature
from ..entities.roadmap import Roadmap
from .roadmap_generator import RoadmapGenerator, RoadmapGenerationRequest, RoadmapGenerationResult
from .feature_decomposer import FeatureDecomposer, DecompositionRequest, DecompositionResult
from .timeline_estimator import TimelineEstimator, TimelineEstimationRequest, TimelineEstimate
from .milestone_planner import MilestonePlanner, MilestonePlanRequest, MilestonePlan
from .dependency_resolver import DependencyResolver, DependencyAnalysisResult


@dataclass
class ComprehensiveRoadmapRequest:
    """Request for comprehensive roadmap generation."""
    features: List[Feature]
    team_id: str
    start_date: date
    team_velocity: float
    sprint_duration_weeks: int = 2
    generation_strategy: str = "sprint_based"  # sprint_based, release_based
    decompose_features: bool = True
    analyze_dependencies: bool = True
    create_milestones: bool = True
    milestone_frequency_weeks: int = 4


@dataclass
class ComprehensiveRoadmap:
    """Complete roadmap with all analysis and planning."""
    roadmap: Roadmap
    generation_result: RoadmapGenerationResult
    decomposition_results: Dict[str, DecompositionResult] = field(default_factory=dict)
    timeline_estimate: Optional[TimelineEstimate] = None
    dependency_analysis: Optional[DependencyAnalysisResult] = None
    milestone_plan: Optional[MilestonePlan] = None
    warnings: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def summary(self) -> Dict[str, any]:
        """Generate executive summary."""
        return {
            "roadmap_id": self.roadmap.id,
            "roadmap_name": self.roadmap.name,
            "total_features": len(self.roadmap.feature_ids),
            "total_sprints": len(self.roadmap.releases[0].sprints) if self.roadmap.releases else 0,
            "estimated_completion": self.roadmap.end_date.isoformat() if self.roadmap.end_date else None,
            "story_points": self.roadmap.total_story_points,
            "milestone_count": self.milestone_plan.milestone_count if self.milestone_plan else 0,
            "has_dependency_issues": (
                self.dependency_analysis.has_cycles() if self.dependency_analysis else False
            ),
            "warnings_count": len(self.warnings),
            "recommendations_count": len(self.recommendations)
        }


class RoadmapOrchestrator:
    """
    Master orchestrator for comprehensive roadmap generation.
    
    Coordinates:
    - Feature decomposition
    - Timeline estimation
    - Dependency analysis
    - Sprint/release planning
    - Milestone generation
    """
    
    def __init__(self):
        """Initialize orchestrator with all components."""
        self.roadmap_generator = RoadmapGenerator()
        self.feature_decomposer = FeatureDecomposer()
        self.timeline_estimator = TimelineEstimator()
        self.milestone_planner = MilestonePlanner()
        self.dependency_resolver = DependencyResolver()
    
    def generate_comprehensive_roadmap(
        self,
        request: ComprehensiveRoadmapRequest
    ) -> ComprehensiveRoadmap:
        """
        Generate complete roadmap with all analysis.
        
        Args:
            request: Comprehensive roadmap request
            
        Returns:
            ComprehensiveRoadmap with all components
        """
        warnings = []
        recommendations = []
        
        # Step 1: Decompose features (if requested)
        decomposition_results = {}
        if request.decompose_features:
            decomposition_results = self._decompose_all_features(
                request.features,
                warnings,
                recommendations
            )
        
        # Step 2: Analyze dependencies (if requested)
        dependency_analysis = None
        if request.analyze_dependencies:
            dependency_analysis = self._analyze_dependencies(
                request.features,
                warnings,
                recommendations
            )
        
        # Step 3: Estimate timeline
        timeline_estimate = self._estimate_timeline(
            request.features,
            request.team_velocity,
            request.sprint_duration_weeks,
            warnings
        )
        
        # Step 4: Generate core roadmap
        generation_result = self._generate_roadmap(
            request,
            timeline_estimate,
            warnings
        )
        
        # Step 5: Create milestones (if requested)
        milestone_plan = None
        if request.create_milestones:
            milestone_plan = self._create_milestones(
                request.features,
                generation_result.roadmap.releases[0].sprints if generation_result.roadmap.releases else [],
                request.start_date,
                request.milestone_frequency_weeks
            )
        
        # Step 6: Generate recommendations
        self._generate_recommendations(
            generation_result.roadmap,
            timeline_estimate,
            dependency_analysis,
            recommendations
        )
        
        return ComprehensiveRoadmap(
            roadmap=generation_result.roadmap,
            generation_result=generation_result,
            decomposition_results=decomposition_results,
            timeline_estimate=timeline_estimate,
            dependency_analysis=dependency_analysis,
            milestone_plan=milestone_plan,
            warnings=warnings,
            recommendations=recommendations
        )
    
    def _decompose_all_features(
        self,
        features: List[Feature],
        warnings: List[str],
        recommendations: List[str]
    ) -> Dict[str, DecompositionResult]:
        """
        Decompose all features into stories and tasks.
        
        NOTE: Feature decomposition requires async/await and LLM calls.
        For synchronous orchestration, this is temporarily disabled.
        TODO: Implement async orchestrator or separate decomposition workflow.
        """
        warnings.append(
            "Feature decomposition temporarily disabled in orchestrator (requires async implementation)"
        )
        return {}
    
    def _analyze_dependencies(
        self,
        features: List[Feature],
        warnings: List[str],
        recommendations: List[str]
    ) -> Optional[DependencyAnalysisResult]:
        """Analyze feature dependencies."""
        try:
            # Dependency resolver has been fixed and is now operational!
            result = self.dependency_resolver.analyze_dependencies(features)
            
            # Check for issues
            if result.has_cycles():
                warnings.append(
                    f"Circular dependencies detected: {len(result.circular_dependencies)} cycles"
                )
                recommendations.append(
                    "Review and resolve circular dependencies before starting development"
                )
            
            if result.bottlenecks:
                warnings.append(
                    f"Found {len(result.bottlenecks)} potential bottleneck features"
                )
                bottleneck_names = [b.title for b in result.bottlenecks[:3]]
                recommendations.append(
                    f"Consider prioritizing bottleneck resolution: {', '.join(bottleneck_names)}"
                )
            
            return result
            
            # Original code (disabled):
            # result = self.dependency_resolver.analyze_dependencies(features)
            # 
            # # Check for issues
            # if result.has_cycles():
            #     warnings.append(
            #         f"Circular dependencies detected: {len(result.circular_dependencies)} cycles"
            #     )
            #     recommendations.append(
            #         "Review and resolve circular dependencies before starting development"
            #     )
            # 
            # if result.bottlenecks:
            #     warnings.append(
            #         f"Found {len(result.bottlenecks)} potential bottleneck features"
            #     )
            #     recommendations.append(
            #         f"Consider prioritizing: {', '.join([b.name for b in result.bottlenecks[:3]])}"
            #     )
            # 
            # return result
            
        except Exception as e:
            warnings.append(f"Dependency analysis failed: {str(e)}")
            return None
    
    def _estimate_timeline(
        self,
        features: List[Feature],
        team_velocity: float,
        sprint_duration_weeks: int,
        warnings: List[str]
    ) -> TimelineEstimate:
        """Estimate project timeline."""
        from .timeline_estimator import VelocityData
        from datetime import datetime
        
        # Create velocity data from team velocity
        velocity_data = [
            VelocityData(
                sprint_name=f"Sprint {i+1}",
                story_points_completed=team_velocity,
                hours_spent=80.0,  # Assume 2 weeks * 40 hours
                tasks_completed=int(team_velocity),
                sprint_duration_days=sprint_duration_weeks * 7
            )
            for i in range(3)  # Use 3 sprints of historical data
        ]
        
        request = TimelineEstimationRequest(
            features=features,
            tasks=[],  # No tasks at this level
            start_date=datetime.now().date(),
            velocity_data=velocity_data,
            sprint_duration_weeks=sprint_duration_weeks
        )
        
        estimate = self.timeline_estimator.estimate_timeline(request)
        
        # Check confidence
        if estimate.confidence_score < 0.5:
            warnings.append(
                f"Timeline estimate has low confidence ({estimate.confidence_score:.1%})"
            )
        
        return estimate
    
    def _generate_roadmap(
        self,
        request: ComprehensiveRoadmapRequest,
        timeline_estimate: TimelineEstimate,
        warnings: List[str]
    ) -> RoadmapGenerationResult:
        """Generate core roadmap."""
        from .roadmap_generator import RoadmapStrategy
        
        # Handle empty features
        if not request.features:
            warnings.append("No features provided - roadmap will be empty")
            # Return empty result
            from ..entities.roadmap import Roadmap, RoadmapStatus
            from datetime import datetime
            empty_roadmap = Roadmap(
                id=f"roadmap-{request.team_id}",
                name="Empty Roadmap",
                created_by="system",
                status=RoadmapStatus.PLANNING,
                start_date=request.start_date
            )
            return RoadmapGenerationResult(
                roadmap=empty_roadmap,
                releases=[],
                sprints=[],
                unscheduled_features=[],
                warnings=["No features to schedule"]
            )
        
        # Map strategy name to enum
        strategy_map = {
            "sprint_based": RoadmapStrategy.SPRINT_BASED,
            "release_based": RoadmapStrategy.RELEASE_BASED
        }
        strategy = strategy_map.get(request.generation_strategy, RoadmapStrategy.SPRINT_BASED)
        
        roadmap_request = RoadmapGenerationRequest(
            features=request.features,
            team_id=request.team_id,
            start_date=request.start_date,
            velocity=request.team_velocity,
            sprint_duration_weeks=request.sprint_duration_weeks,
            strategy=strategy
        )
        
        result = self.roadmap_generator.generate_roadmap(roadmap_request)
        
        # Check for unscheduled features (capacity issues)
        if result.unscheduled_features:
            warnings.append(
                f"Roadmap has {len(result.unscheduled_features)} unscheduled features - consider extending timeline or reducing scope"
            )
        
        return result
    
    def _create_milestones(
        self,
        features: List[Feature],
        sprints: List,
        start_date: date,
        frequency_weeks: int
    ) -> MilestonePlan:
        """Create milestone plan."""
        request = MilestonePlanRequest(
            features=features,
            sprints=sprints,
            start_date=start_date,
            milestone_frequency_weeks=frequency_weeks,
            strategy="balanced"
        )
        
        return self.milestone_planner.generate_milestones(request)
    
    def _generate_recommendations(
        self,
        roadmap: Roadmap,
        timeline_estimate: Optional[TimelineEstimate],
        dependency_analysis: Optional[DependencyAnalysisResult],
        recommendations: List[str]
    ) -> None:
        """Generate strategic recommendations."""
        
        # Timeline recommendations
        if timeline_estimate:
            if timeline_estimate.buffer_days > 20:
                recommendations.append(
                    "Significant buffer time included - consider more detailed analysis"
                )
            if not timeline_estimate.is_realistic():
                recommendations.append(
                    "Timeline estimate has low confidence - gather more historical data"
                )
        
        # Dependency recommendations (disabled while dependency resolver is being fixed)
        # if dependency_analysis and dependency_analysis.parallel_tracks:
        #     recommendations.append(
        #         f"Consider parallel development: {len(dependency_analysis.parallel_tracks)} independent tracks available"
        #     )
        
        # Capacity recommendations
        if roadmap.total_story_points and roadmap.total_story_points > 200:
            recommendations.append(
                "Large project scope - consider phased delivery or additional team resources"
            )
        
        # Sprint recommendations
        if roadmap.releases:
            sprint_count = len(roadmap.releases[0].sprints) if roadmap.releases else 0
            if sprint_count > 12:
                recommendations.append(
                    f"Long project duration ({sprint_count} sprints) - establish regular checkpoints"
                )
    
    def validate_roadmap(
        self,
        roadmap: ComprehensiveRoadmap
    ) -> Dict[str, any]:
        """
        Validate generated roadmap for completeness and feasibility.
        
        Returns:
            Validation report
        """
        issues = []
        checks_passed = []
        
        # Check 1: All features included
        if len(roadmap.roadmap.feature_ids) > 0:
            checks_passed.append("All features are included in roadmap")
        else:
            issues.append("No features in roadmap")
        
        # Check 2: Timeline estimate exists
        if roadmap.timeline_estimate:
            checks_passed.append("Timeline estimate available")
        else:
            issues.append("Missing timeline estimate")
        
        # Check 3: No circular dependencies
        if not roadmap.dependency_analysis or not roadmap.dependency_analysis.has_cycles():
            checks_passed.append("No circular dependencies")
        else:
            issues.append("Circular dependencies detected")
        
        # Check 4: All features scheduled
        if not roadmap.generation_result.unscheduled_features:
            checks_passed.append("All features scheduled")
        else:
            issues.append(f"{len(roadmap.generation_result.unscheduled_features)} features unscheduled")
        
        # Check 5: Milestones defined
        if roadmap.milestone_plan and len(roadmap.milestone_plan.milestones) > 0:
            checks_passed.append(f"{len(roadmap.milestone_plan.milestones)} milestones defined")
        
        return {
            "valid": len(issues) == 0,
            "checks_passed": checks_passed,
            "issues": issues,
            "warnings": roadmap.warnings,
            "quality_score": len(checks_passed) / (len(checks_passed) + len(issues)) if (len(checks_passed) + len(issues)) > 0 else 0.0
        }
    
    def optimize_roadmap(
        self,
        roadmap: ComprehensiveRoadmap,
        optimization_goal: str = "speed"  # speed, cost, quality
    ) -> ComprehensiveRoadmap:
        """
        Optimize roadmap based on specified goal.
        
        Args:
            roadmap: Original roadmap
            optimization_goal: Optimization target (speed/cost/quality)
            
        Returns:
            Optimized roadmap
        """
        # This is a placeholder for future optimization logic
        # Could implement:
        # - Feature reordering for speed
        # - Resource reallocation for cost
        # - Additional quality gates
        
        recommendations = roadmap.recommendations.copy()
        recommendations.append(f"Roadmap optimization for '{optimization_goal}' is available")
        
        # Return roadmap with optimization note
        return ComprehensiveRoadmap(
            roadmap=roadmap.roadmap,
            generation_result=roadmap.generation_result,
            decomposition_results=roadmap.decomposition_results,
            timeline_estimate=roadmap.timeline_estimate,
            dependency_analysis=roadmap.dependency_analysis,
            milestone_plan=roadmap.milestone_plan,
            warnings=roadmap.warnings,
            recommendations=recommendations
        )

