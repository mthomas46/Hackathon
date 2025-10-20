"""
Discovery API Routes

Endpoints for repository discovery and processing plan generation.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
import uuid

from ...services.discovery import get_discovery_engine
from ...storage import get_database
from ...storage.models_discovery import ProcessingPlanModel, SubJobModel, FileClassificationModel
from ...utils.host_path_resolver import validate_ingestion_path

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/discovery", tags=["Discovery"])


# Pydantic models for API
class DiscoveryScanRequest(BaseModel):
    """Request to scan repository and create processing plan."""
    repo_path: str = Field(..., description="Path to repository")
    resolve_host_path: bool = Field(default=False, description="Whether to resolve host path to container path")
    save_to_db: bool = Field(default=True, description="Whether to save plan to database")


class SubJobInfo(BaseModel):
    """Sub-job information."""
    id: str
    name: str
    file_count: int
    priority: int
    estimated_minutes: float


class ProcessingPlanSummary(BaseModel):
    """Processing plan summary."""
    plan_id: str
    repo_path: str
    total_files: int
    total_size_mb: float
    sub_jobs: int
    estimated_time_minutes: float
    max_parallelization: int
    sub_job_details: List[SubJobInfo]


class DiscoveryScanResponse(BaseModel):
    """Response from discovery scan."""
    success: bool
    plan_id: str
    summary: ProcessingPlanSummary
    saved_to_db: bool


class ProcessingPlanListItem(BaseModel):
    """Processing plan list item."""
    id: str
    repo_path: str
    total_files: int
    total_size_mb: float
    status: str
    created_at: str
    sub_jobs_count: int


@router.post(
    "/scan",
    response_model=DiscoveryScanResponse,
    summary="Scan repository and create processing plan",
    description="Analyzes repository structure and creates an intelligent processing plan with sub-jobs"
)
async def scan_repository(
    request: DiscoveryScanRequest = Body(...),
    db: AsyncSession = Depends(get_database)
) -> DiscoveryScanResponse:
    """
    Scan repository and create processing plan.
    
    This endpoint:
    1. Scans the repository structure
    2. Classifies files by importance
    3. Creates an optimized processing plan
    4. Optionally saves the plan to database
    
    Returns processing plan with sub-jobs for parallel execution.
    """
    try:
        logger.info(f"🔍 Discovery scan requested for: {request.repo_path}")
        
        # Validate and resolve path
        repo_path = request.repo_path
        if request.resolve_host_path:
            is_valid, message, resolved = validate_ingestion_path(repo_path)
            if not is_valid:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Path validation failed: {message}"
                )
            repo_path = resolved.container_path
            logger.info(f"  ✅ Resolved path: {repo_path}")
        
        # Verify path exists
        path_obj = Path(repo_path)
        if not path_obj.exists():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Repository path does not exist: {repo_path}"
            )
        
        if not path_obj.is_dir():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Repository path is not a directory: {repo_path}"
            )
        
        # Run discovery
        engine = get_discovery_engine()
        plan = await engine.discover(repo_path)
        summary = engine.get_plan_summary(plan)
        
        plan_id = str(uuid.uuid4())
        
        # Save to database if requested
        saved = False
        if request.save_to_db:
            async with db.session() as session:
                # Create processing plan record
                plan_model = ProcessingPlanModel(
                    id=plan_id,
                    repo_path=plan.repo_path,
                    total_files=plan.total_files,
                    total_size_mb=plan.total_size_mb,
                    estimated_time_minutes=plan.estimated_total_time_minutes,
                    max_parallelization=plan.max_parallelization,
                    processing_order=plan.processing_order,
                    status="ready"
                )
                session.add(plan_model)
                
                # Create sub-job records
                for sub_job in plan.sub_jobs:
                    sub_job_model = SubJobModel(
                        plan_id=plan_id,
                        sub_job_id=sub_job.sub_job_id,
                        sub_job_name=sub_job.sub_job_name,
                        file_count=len(sub_job.files),
                        priority=sub_job.priority,
                        estimated_time_minutes=sub_job.estimated_time_minutes,
                        dependencies=sub_job.dependencies,
                        status="pending"
                    )
                    session.add(sub_job_model)
                    
                    # Create file classification records
                    for classified_file in sub_job.files:
                        file_model = FileClassificationModel(
                            plan_id=plan_id,
                            file_path=str(classified_file.file_info.path),
                            relative_path=classified_file.file_info.relative_path,
                            size_bytes=classified_file.file_info.size_bytes,
                            extension=classified_file.file_info.extension,
                            language=classified_file.file_info.language,
                            is_code=classified_file.file_info.is_code,
                            is_test=classified_file.file_info.is_test,
                            is_doc=classified_file.file_info.is_doc,
                            is_config=classified_file.file_info.is_config,
                            importance_level=classified_file.importance_level.value,
                            importance_score=classified_file.importance_score,
                            priority=classified_file.priority,
                            sub_job_id=sub_job.sub_job_id
                        )
                        session.add(file_model)
                
                await session.commit()
                saved = True
                logger.info(f"  ✅ Saved processing plan to database: {plan_id}")
        
        # Build response
        response = DiscoveryScanResponse(
            success=True,
            plan_id=plan_id,
            summary=ProcessingPlanSummary(
                plan_id=plan_id,
                repo_path=summary["repo_path"],
                total_files=summary["total_files"],
                total_size_mb=summary["total_size_mb"],
                sub_jobs=summary["sub_jobs"],
                estimated_time_minutes=summary["estimated_time_minutes"],
                max_parallelization=summary["max_parallelization"],
                sub_job_details=[
                    SubJobInfo(
                        id=sj["id"],
                        name=sj["name"],
                        file_count=sj["files"],
                        priority=sj["priority"],
                        estimated_minutes=sj["estimated_minutes"]
                    )
                    for sj in summary["sub_job_details"]
                ]
            ),
            saved_to_db=saved
        )
        
        logger.info(f"✅ Discovery scan complete: {summary['total_files']} files, {summary['sub_jobs']} sub-jobs")
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Discovery scan failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Discovery scan failed: {str(e)}"
        )


@router.get(
    "/plans",
    response_model=List[ProcessingPlanListItem],
    summary="List processing plans",
    description="Get list of all processing plans in database"
)
async def list_processing_plans(
    limit: int = 100,
    offset: int = 0,
    status_filter: Optional[str] = None,
    db: AsyncSession = Depends(get_database)
) -> List[ProcessingPlanListItem]:
    """List processing plans."""
    try:
        from sqlalchemy import select, func
        
        async with db.session() as session:
            # Build query
            query = select(
                ProcessingPlanModel,
                func.count(SubJobModel.id).label("sub_jobs_count")
            ).outerjoin(SubJobModel).group_by(ProcessingPlanModel.id)
            
            if status_filter:
                query = query.where(ProcessingPlanModel.status == status_filter)
            
            query = query.order_by(ProcessingPlanModel.created_at.desc())
            query = query.limit(limit).offset(offset)
            
            result = await session.execute(query)
            rows = result.all()
            
            plans = []
            for plan, sub_jobs_count in rows:
                plans.append(ProcessingPlanListItem(
                    id=str(plan.id),
                    repo_path=plan.repo_path,
                    total_files=plan.total_files,
                    total_size_mb=plan.total_size_mb,
                    status=plan.status,
                    created_at=plan.created_at.isoformat(),
                    sub_jobs_count=sub_jobs_count
                ))
            
            return plans
            
    except Exception as e:
        logger.error(f"Failed to list processing plans: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list processing plans: {str(e)}"
        )


@router.get(
    "/plans/{plan_id}",
    summary="Get processing plan details",
    description="Get detailed information about a specific processing plan"
)
async def get_processing_plan(
    plan_id: str,
    db: AsyncSession = Depends(get_database)
) -> Dict[str, Any]:
    """Get processing plan details."""
    try:
        from sqlalchemy import select
        
        async with db.session() as session:
            # Get plan
            result = await session.execute(
                select(ProcessingPlanModel).where(ProcessingPlanModel.id == plan_id)
            )
            plan = result.scalar_one_or_none()
            
            if not plan:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Processing plan not found: {plan_id}"
                )
            
            # Get sub-jobs
            result = await session.execute(
                select(SubJobModel).where(SubJobModel.plan_id == plan_id).order_by(SubJobModel.priority)
            )
            sub_jobs = result.scalars().all()
            
            return {
                "id": str(plan.id),
                "repo_path": plan.repo_path,
                "total_files": plan.total_files,
                "total_size_mb": plan.total_size_mb,
                "estimated_time_minutes": plan.estimated_time_minutes,
                "max_parallelization": plan.max_parallelization,
                "processing_order": plan.processing_order,
                "status": plan.status,
                "created_at": plan.created_at.isoformat(),
                "updated_at": plan.updated_at.isoformat(),
                "sub_jobs": [
                    {
                        "id": str(sj.id),
                        "sub_job_id": sj.sub_job_id,
                        "sub_job_name": sj.sub_job_name,
                        "file_count": sj.file_count,
                        "priority": sj.priority,
                        "estimated_time_minutes": sj.estimated_time_minutes,
                        "status": sj.status,
                        "processed_files": sj.processed_files,
                        "failed_files": sj.failed_files,
                        "skipped_files": sj.skipped_files
                    }
                    for sj in sub_jobs
                ]
            }
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get processing plan: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get processing plan: {str(e)}"
        )

