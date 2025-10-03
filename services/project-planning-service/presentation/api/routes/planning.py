"""
Planning API Routes
===================

API endpoints for feature planning, analysis, and roadmap generation.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
import uuid
import time
from datetime import datetime

from ....domain.entities.feature import Feature, FeatureStatus, FeaturePriority
from ....domain.entities.task import Task, TaskStatus, TaskType
from ....infrastructure.database import get_db
from ....infrastructure.repositories.feature_repository import FeatureRepository
from ....infrastructure.repositories.task_repository import TaskRepository
from ....infrastructure.integrations.log_collector_client import get_log_client
from ....infrastructure.integrations.interpreter_client import InterpreterClient
from ....infrastructure.integrations.llm_gateway_client import LLMGatewayClient
from ....infrastructure.integrations.user_store_client import UserStoreClient


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class AnalyzeFeatureRequest(BaseModel):
    """Request to analyze a feature description."""
    title: str = Field(..., description="Feature title")
    description: str = Field(..., description="Feature description")
    context: Optional[Dict[str, Any]] = Field(default=None, description="Additional context")
    user_id: Optional[str] = Field(default=None, description="User making the request")


class AnalyzeFeatureResponse(BaseModel):
    """Response from feature analysis."""
    feature_id: str
    analysis: Dict[str, Any]
    complexity_score: float
    story_points: float
    estimated_duration_days: float
    risks: Dict[str, Any]
    user_stories: List[Dict[str, Any]]
    technical_requirements: Dict[str, Any]


class DecomposeFeatureRequest(BaseModel):
    """Request to decompose a feature into tasks."""
    feature_id: str = Field(..., description="Feature ID to decompose")
    decomposition_level: str = Field(default="detailed", description="Decomposition level")
    assign_automatically: bool = Field(default=False, description="Auto-assign tasks")
    team_id: Optional[str] = Field(default=None, description="Team to assign from")


class DecomposeFeatureResponse(BaseModel):
    """Response from feature decomposition."""
    feature_id: str
    user_stories: List[Dict[str, Any]]
    tasks: List[Dict[str, Any]]
    total_story_points: float
    estimated_duration_days: float


class AllocateResourcesRequest(BaseModel):
    """Request to allocate team resources to tasks."""
    task_ids: List[str] = Field(..., description="Task IDs to allocate")
    team_id: Optional[str] = Field(default=None, description="Team ID")
    allocation_strategy: str = Field(default="skills_based", description="Allocation strategy")


class AllocateResourcesResponse(BaseModel):
    """Response from resource allocation."""
    allocations: List[Dict[str, Any]]
    unallocated_tasks: List[str]
    team_capacity_remaining: Dict[str, float]


# ============================================================================
# ROUTER SETUP
# ============================================================================

router = APIRouter(prefix="/api/v1/planning", tags=["planning"])


# Initialize clients (will be properly injected in production)
log_client = get_log_client()
interpreter_client = InterpreterClient(log_client=log_client)
llm_client = LLMGatewayClient(log_client=log_client)
user_store_client = UserStoreClient(log_client=log_client)


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/analyze", response_model=AnalyzeFeatureResponse)
async def analyze_feature(
    request: AnalyzeFeatureRequest,
    db: Session = Depends(get_db)
):
    """
    Analyze a feature description using AI to extract requirements,
    estimate complexity, and identify risks.
    
    This endpoint performs comprehensive AI-powered analysis including:
    - Feature decomposition into user stories
    - Complexity and effort estimation
    - Risk assessment
    - Technical requirements extraction
    """
    start_time = time.time()
    
    try:
        # Log request
        await log_client.log_business_event(
            "feature_analysis_started",
            {"title": request.title},
            user_id=request.user_id
        )
        
        # Step 1: Create feature entity
        feature = Feature(
            id=str(uuid.uuid4()),
            title=request.title,
            description=request.description,
            status=FeatureStatus.DRAFT,
            priority=FeaturePriority.MEDIUM,
            created_by=request.user_id or "system"
        )
        
        # Step 2: Analyze with Interpreter
        analysis_result = await interpreter_client.analyze_feature_description(
            request.description,
            context=request.context
        )
        
        # Step 3: Estimate complexity with LLM Gateway
        complexity_result = await llm_client.analyze_feature_complexity(
            request.description,
            technical_context=request.context
        )
        
        # Step 4: Assess risks
        risk_result = await llm_client.assess_risk(
            request.description,
            project_context=request.context
        )
        
        # Step 5: Generate user stories
        user_stories = await llm_client.generate_user_stories(
            request.description,
            persona=request.context.get("persona") if request.context else None
        )
        
        # Step 6: Extract technical requirements
        tech_requirements = await interpreter_client.extract_technical_requirements(
            request.description
        )
        
        # Step 7: Update feature with analysis results
        feature.estimated_effort = complexity_result.get("story_points", 5)
        feature.technical_complexity = complexity_result.get("complexity_score", 5)
        feature.ai_analysis = {
            "interpreter_analysis": analysis_result,
            "complexity_analysis": complexity_result,
            "generated_at": datetime.utcnow().isoformat()
        }
        feature.risk_assessment = risk_result
        feature.update_status(FeatureStatus.ANALYZED)
        
        # Step 8: Persist feature
        feature_repo = FeatureRepository(db)
        feature_repo.create(feature)
        db.commit()
        
        # Calculate duration
        duration_ms = (time.time() - start_time) * 1000
        
        # Log completion
        await log_client.log_feature_analysis(
            feature.id,
            "comprehensive_analysis",
            {
                "story_points": feature.estimated_effort,
                "complexity_score": feature.technical_complexity,
                "user_stories_count": len(user_stories),
                "risks_identified": len(risk_result.get("technical_risks", []))
            },
            duration_ms
        )
        
        await log_client.log_business_event(
            "feature_analysis_completed",
            {
                "feature_id": feature.id,
                "title": request.title,
                "story_points": feature.estimated_effort,
                "duration_ms": duration_ms
            },
            user_id=request.user_id
        )
        
        # Return response
        return AnalyzeFeatureResponse(
            feature_id=feature.id,
            analysis=analysis_result,
            complexity_score=complexity_result.get("complexity_score", 5),
            story_points=complexity_result.get("story_points", 5),
            estimated_duration_days=complexity_result.get("estimated_days", 5),
            risks=risk_result,
            user_stories=user_stories,
            technical_requirements=tech_requirements
        )
        
    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        
        await log_client.log_error(
            f"Feature analysis failed: {str(e)}",
            context={
                "title": request.title,
                "error": str(e),
                "duration_ms": duration_ms
            },
            user_id=request.user_id
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Feature analysis failed: {str(e)}"
        )


@router.post("/decompose", response_model=DecomposeFeatureResponse)
async def decompose_feature(
    request: DecomposeFeatureRequest,
    db: Session = Depends(get_db)
):
    """
    Decompose a feature into detailed tasks and user stories.
    
    This endpoint breaks down a high-level feature into:
    - User stories with acceptance criteria
    - Implementation tasks
    - Testing tasks
    - Documentation tasks
    
    Optionally assigns tasks to team members based on skills and capacity.
    """
    start_time = time.time()
    
    try:
        # Retrieve feature
        feature_repo = FeatureRepository(db)
        feature = feature_repo.get_by_id(request.feature_id)
        
        if not feature:
            raise HTTPException(status_code=404, detail="Feature not found")
        
        # Log decomposition start
        await log_client.log_business_event(
            "feature_decomposition_started",
            {
                "feature_id": feature.id,
                "title": feature.title,
                "decomposition_level": request.decomposition_level
            }
        )
        
        # Decompose with Interpreter
        decomposition_result = await interpreter_client.decompose_feature(
            feature.description,
            decomposition_level=request.decomposition_level,
            context={
                "feature_id": feature.id,
                "priority": feature.priority.value,
                "estimated_effort": feature.estimated_effort
            }
        )
        
        # Create tasks from decomposition
        task_repo = TaskRepository(db)
        created_tasks = []
        total_story_points = 0
        
        for task_data in decomposition_result.get("tasks", []):
            task = Task(
                id=str(uuid.uuid4()),
                title=task_data.get("title", "Unnamed Task"),
                description=task_data.get("description", ""),
                task_type=TaskType(task_data.get("type", "development")),
                status=TaskStatus.TODO,
                feature_id=feature.id,
                estimated_hours=task_data.get("estimated_hours"),
                story_points=task_data.get("story_points", 1),
                created_by="system"
            )
            
            task_repo.create(task)
            created_tasks.append(task.to_dict())
            total_story_points += task.story_points or 0
        
        # Auto-assign if requested
        allocations = []
        if request.assign_automatically:
            for task in created_tasks:
                task_obj = Task(**{k: v for k, v in task.items() if k != 'can_start'})
                
                # Find best assignee
                required_skills = task.get("tags", [])
                assignee = await user_store_client.find_best_assignee(
                    required_skills=required_skills,
                    estimated_hours=task.get("estimated_hours", 8),
                    team_id=request.team_id
                )
                
                if assignee:
                    # Assign task
                    task_obj.assign_to(assignee["user_id"], "system")
                    task_repo.update(task_obj)
                    
                    # Allocate capacity
                    await user_store_client.allocate_capacity(
                        assignee["user_id"],
                        task["id"],
                        task.get("estimated_hours", 8)
                    )
                    
                    allocations.append({
                        "task_id": task["id"],
                        "assigned_to": assignee["user_id"],
                        "assignee_name": assignee["name"],
                        "match_score": assignee["total_score"]
                    })
        
        db.commit()
        
        # Calculate estimated duration
        estimated_duration = total_story_points * 1.5  # Rough estimate: 1.5 days per story point
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Log completion
        await log_client.log_business_event(
            "feature_decomposition_completed",
            {
                "feature_id": feature.id,
                "tasks_created": len(created_tasks),
                "total_story_points": total_story_points,
                "auto_assigned": len(allocations),
                "duration_ms": duration_ms
            }
        )
        
        return DecomposeFeatureResponse(
            feature_id=feature.id,
            user_stories=decomposition_result.get("user_stories", []),
            tasks=created_tasks,
            total_story_points=total_story_points,
            estimated_duration_days=estimated_duration
        )
        
    except HTTPException:
        raise
    except Exception as e:
        await log_client.log_error(
            f"Feature decomposition failed: {str(e)}",
            context={
                "feature_id": request.feature_id,
                "error": str(e)
            }
        )
        
        raise HTTPException(
            status_code=500,
            detail=f"Feature decomposition failed: {str(e)}"
        )


@router.get("/features/{feature_id}")
async def get_feature(
    feature_id: str,
    db: Session = Depends(get_db)
):
    """Get feature details by ID."""
    feature_repo = FeatureRepository(db)
    feature = feature_repo.get_by_id(feature_id)
    
    if not feature:
        raise HTTPException(status_code=404, detail="Feature not found")
    
    return feature.to_dict()


@router.get("/features")
async def list_features(
    status: Optional[str] = Query(default=None),
    priority: Optional[str] = Query(default=None),
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db)
):
    """List features with optional filtering."""
    feature_repo = FeatureRepository(db)
    
    if status:
        features = feature_repo.find_by_status(FeatureStatus(status))
    elif priority:
        features = feature_repo.find_by_priority(FeaturePriority(priority))
    else:
        features = feature_repo.list_all(limit=limit, offset=offset)
    
    return {
        "features": [f.to_dict() for f in features],
        "count": len(features),
        "limit": limit,
        "offset": offset
    }


@router.get("/tasks")
async def list_tasks(
    feature_id: Optional[str] = Query(default=None),
    assigned_to: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    db: Session = Depends(get_db)
):
    """List tasks with optional filtering."""
    task_repo = TaskRepository(db)
    
    if feature_id:
        tasks = task_repo.find_by_feature(feature_id)
    elif assigned_to:
        tasks = task_repo.find_by_assignee(assigned_to)
    elif status:
        tasks = task_repo.find_by_status(TaskStatus(status))
    else:
        # Return recent tasks
        tasks = []  # Would implement pagination
    
    return {
        "tasks": [t.to_dict() for t in tasks],
        "count": len(tasks)
    }

