"""
Roadmap Orchestration API Routes
=================================

REST API endpoints for comprehensive roadmap generation and management.
"""

from fastapi import APIRouter, HTTPException, status
from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field

from ..domain.services.roadmap_orchestrator import (
    RoadmapOrchestrator,
    ComprehensiveRoadmapRequest,
    ComprehensiveRoadmap
)
from ..domain.entities.feature import Feature, FeaturePriority


# Request/Response Models
class FeatureRequest(BaseModel):
    """Feature input for roadmap generation."""
    id: str
    title: str
    description: str
    priority: Optional[str] = "medium"
    estimated_effort: Optional[float] = None
    dependencies: List[str] = Field(default_factory=list)


class RoadmapGenerationRequest(BaseModel):
    """Request to generate comprehensive roadmap."""
    features: List[FeatureRequest]
    team_id: str
    start_date: date
    team_velocity: float = 20.0
    sprint_duration_weeks: int = 2
    generation_strategy: str = "sprint_based"
    decompose_features: bool = False  # Disabled (requires async)
    analyze_dependencies: bool = False  # Disabled (known issue)
    create_milestones: bool = True
    milestone_frequency_weeks: int = 4


class MilestoneResponse(BaseModel):
    """Milestone information."""
    id: str
    name: str
    description: str
    milestone_type: str
    target_date: date
    feature_ids: List[str]
    completed: bool
    story_points: float


class RoadmapResponse(BaseModel):
    """Comprehensive roadmap response."""
    roadmap_id: str
    roadmap_name: str
    start_date: Optional[date]
    end_date: Optional[date]
    total_features: int
    total_sprints: int
    estimated_completion: Optional[date]
    story_points: Optional[float]
    milestone_count: int
    milestones: List[MilestoneResponse]
    warnings: List[str]
    recommendations: List[str]
    confidence_score: Optional[float]


class ValidationResponse(BaseModel):
    """Roadmap validation result."""
    valid: bool
    quality_score: float
    checks_passed: List[str]
    issues: List[str]
    warnings: List[str]


# Create router
router = APIRouter(prefix="/roadmap", tags=["Roadmap Orchestration"])

# Initialize orchestrator
orchestrator = RoadmapOrchestrator()


@router.post("/generate", response_model=RoadmapResponse, status_code=status.HTTP_201_CREATED)
async def generate_roadmap(request: RoadmapGenerationRequest):
    """
    Generate comprehensive development roadmap.
    
    **Features:**
    - Intelligent sprint/release planning
    - Timeline estimation with confidence intervals
    - Milestone generation and tracking
    - Warnings and recommendations
    
    **Example Request:**
    ```json
    {
        "features": [
            {
                "id": "f1",
                "title": "User Authentication",
                "description": "Implement login and registration",
                "priority": "high",
                "estimated_effort": 13.0
            }
        ],
        "team_id": "team-alpha",
        "start_date": "2025-01-01",
        "team_velocity": 20.0,
        "create_milestones": true
    }
    ```
    """
    try:
        # Convert request features to domain entities
        features = []
        for f_req in request.features:
            priority = FeaturePriority[f_req.priority.upper()] if f_req.priority else FeaturePriority.MEDIUM
            feature = Feature(
                id=f_req.id,
                title=f_req.title,
                description=f_req.description,
                priority=priority,
                estimated_effort=f_req.estimated_effort,
                dependencies=f_req.dependencies
            )
            features.append(feature)
        
        # Create orchestrator request
        orch_request = ComprehensiveRoadmapRequest(
            features=features,
            team_id=request.team_id,
            start_date=request.start_date,
            team_velocity=request.team_velocity,
            sprint_duration_weeks=request.sprint_duration_weeks,
            generation_strategy=request.generation_strategy,
            decompose_features=request.decompose_features,
            analyze_dependencies=request.analyze_dependencies,
            create_milestones=request.create_milestones,
            milestone_frequency_weeks=request.milestone_frequency_weeks
        )
        
        # Generate roadmap
        result = orchestrator.generate_comprehensive_roadmap(orch_request)
        
        # Convert milestones to response format
        milestones = []
        if result.milestone_plan:
            for m in result.milestone_plan.milestones:
                milestones.append(MilestoneResponse(
                    id=m.id,
                    name=m.name,
                    description=m.description,
                    milestone_type=m.milestone_type.value,
                    target_date=m.target_date,
                    feature_ids=m.feature_ids,
                    completed=m.completed,
                    story_points=m.story_points
                ))
        
        # Build response
        summary = result.summary()
        response = RoadmapResponse(
            roadmap_id=result.roadmap.id,
            roadmap_name=result.roadmap.name,
            start_date=result.roadmap.start_date,
            end_date=result.roadmap.end_date,
            total_features=summary["total_features"],
            total_sprints=summary["total_sprints"],
            estimated_completion=result.roadmap.end_date,
            story_points=result.roadmap.total_story_points,
            milestone_count=summary["milestone_count"],
            milestones=milestones,
            warnings=result.warnings,
            recommendations=result.recommendations,
            confidence_score=result.generation_result.confidence if result.generation_result else None
        )
        
        return response
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate roadmap: {str(e)}"
        )


@router.post("/validate", response_model=ValidationResponse)
async def validate_roadmap(request: RoadmapGenerationRequest):
    """
    Validate roadmap generation request and get quality assessment.
    
    Performs validation without full generation to quickly assess:
    - Feature completeness
    - Team capacity alignment
    - Timeline feasibility
    - Potential issues
    """
    try:
        # Generate roadmap (needed for validation)
        features = []
        for f_req in request.features:
            priority = FeaturePriority[f_req.priority.upper()] if f_req.priority else FeaturePriority.MEDIUM
            feature = Feature(
                id=f_req.id,
                title=f_req.title,
                description=f_req.description,
                priority=priority,
                estimated_effort=f_req.estimated_effort,
                dependencies=f_req.dependencies
            )
            features.append(feature)
        
        orch_request = ComprehensiveRoadmapRequest(
            features=features,
            team_id=request.team_id,
            start_date=request.start_date,
            team_velocity=request.team_velocity,
            sprint_duration_weeks=request.sprint_duration_weeks,
            generation_strategy=request.generation_strategy,
            decompose_features=False,  # Skip for validation
            analyze_dependencies=False,  # Skip for validation
            create_milestones=request.create_milestones,
            milestone_frequency_weeks=request.milestone_frequency_weeks
        )
        
        result = orchestrator.generate_comprehensive_roadmap(orch_request)
        validation = orchestrator.validate_roadmap(result)
        
        return ValidationResponse(
            valid=validation["valid"],
            quality_score=validation["quality_score"],
            checks_passed=validation["checks_passed"],
            issues=validation["issues"],
            warnings=validation.get("warnings", [])
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """
    Health check endpoint for roadmap orchestration service.
    
    Returns service status and component availability.
    """
    try:
        # Test orchestrator initialization
        test_orch = RoadmapOrchestrator()
        
        return {
            "status": "healthy",
            "service": "roadmap-orchestration",
            "components": {
                "roadmap_generator": "available",
                "timeline_estimator": "available",
                "milestone_planner": "available",
                "feature_decomposer": "disabled (requires async)",
                "dependency_resolver": "disabled (known issue)"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


@router.get("/strategies")
async def get_generation_strategies():
    """
    Get available roadmap generation strategies.
    
    Returns information about supported strategies and their characteristics.
    """
    return {
        "strategies": [
            {
                "id": "sprint_based",
                "name": "Sprint-Based Planning",
                "description": "Organize features into fixed-length sprints",
                "best_for": "Agile teams with regular sprint cadence",
                "characteristics": [
                    "Predictable sprint boundaries",
                    "Even workload distribution",
                    "Easy capacity planning"
                ]
            },
            {
                "id": "release_based",
                "name": "Release-Based Planning",
                "description": "Group features into major releases",
                "best_for": "Projects with defined release milestones",
                "characteristics": [
                    "Feature grouping by release",
                    "Milestone-driven planning",
                    "Flexible sprint allocation"
                ]
            }
        ],
        "milestone_strategies": [
            {
                "id": "balanced",
                "name": "Balanced Milestones",
                "description": "Even distribution of work across milestones"
            },
            {
                "id": "sprint_based",
                "name": "Sprint-Aligned Milestones",
                "description": "Milestones aligned with sprint boundaries"
            },
            {
                "id": "value_based",
                "name": "Value-Based Milestones",
                "description": "Milestones grouped by priority/value"
            }
        ]
    }

