"""
API endpoints for Multi-File Analysis (Phase 3).

Endpoints:
- POST /api/v1/analysis/run/{plan_id} - Run analysis for a processing plan
- GET /api/v1/analysis/reports/{plan_id} - Get full analysis report
- GET /api/v1/analysis/stack/{plan_id} - Get technology stack
- GET /api/v1/analysis/architecture/{plan_id} - Get architecture analysis
- GET /api/v1/analysis/services/{plan_id} - Get service map
- GET /api/v1/analysis/contexts - List repository contexts
- GET /api/v1/analysis/contexts/{repo_id} - Get repository context
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from ...storage.db import get_session
from ...storage.models_discovery import ProcessingPlanModel
from ...storage.models_analysis import (
    AnalysisResultModel,
    RepositoryContextModel,
    DetectedServiceModel
)
from ...services.analysis import get_analysis_engine

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class AnalysisRunRequest(BaseModel):
    """Request to run analysis."""
    force: bool = Field(False, description="Force re-analysis if already exists")


class AnalysisReportResponse(BaseModel):
    """Full analysis report response."""
    id: str
    plan_id: str
    repo_id: str
    repo_path: str
    analysis_complete: bool
    errors: List[str]
    
    # Summary
    total_files: int
    total_languages: int
    total_frameworks: int
    total_services: int
    modularity_score: float
    
    # Details
    dependency_graph: Optional[Dict] = None
    technology_stack: Optional[Dict] = None
    architecture_analysis: Optional[Dict] = None
    service_map: Optional[Dict] = None
    
    created_at: str
    updated_at: str


class TechnologyStackResponse(BaseModel):
    """Technology stack response."""
    languages: Dict[str, int]
    frameworks: Dict[str, List[str]]
    databases: List[str]
    tools: List[str]
    deployment_platforms: List[str]
    primary_language: Optional[str] = None


class ArchitectureResponse(BaseModel):
    """Architecture analysis response."""
    primary_pattern: Optional[Dict] = None
    secondary_patterns: List[Dict]
    layers: List[str]
    entry_points: List[str]
    modularity_score: float
    is_microservices: bool


class ServiceMapResponse(BaseModel):
    """Service map response."""
    services: List[Dict]
    dependencies: Dict[str, List[str]]
    service_count: int


class RepositoryContextResponse(BaseModel):
    """Repository context response."""
    id: str
    repo_id: str
    repo_name: Optional[str]
    
    # Technology
    languages: Dict[str, int]
    frameworks: Dict[str, List[str]]
    databases: List[str]
    
    # Architecture
    architecture_type: Optional[str]
    architecture_confidence: Optional[float]
    service_count: int
    layers: List[str]
    
    # Summary
    total_files: int
    modularity_score: Optional[float]
    brief_description: Optional[str]
    key_features: List[str]
    
    created_at: str


# ============================================================================
# Endpoints
# ============================================================================

@router.post(
    "/analysis/run/{plan_id}",
    response_model=AnalysisReportResponse,
    summary="Run analysis for a processing plan",
    description="Perform comprehensive multi-file analysis including dependencies, stack, architecture, and services"
)
async def run_analysis(
    plan_id: str,
    request: AnalysisRunRequest = AnalysisRunRequest(),
    session: AsyncSession = Depends(get_session)
):
    """Run analysis for a processing plan."""
    try:
        logger.info(f"🔬 Running analysis for plan {plan_id}")
        
        # 1. Check if plan exists
        result = await session.execute(
            select(ProcessingPlanModel).where(ProcessingPlanModel.id == plan_id)
        )
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise HTTPException(status_code=404, detail=f"Plan {plan_id} not found")
        
        # 2. Check if analysis already exists
        result = await session.execute(
            select(AnalysisResultModel).where(AnalysisResultModel.plan_id == plan_id)
        )
        existing = result.scalar_one_or_none()
        
        if existing and not request.force:
            logger.info(f"   ✅ Analysis already exists for plan {plan_id}")
            return AnalysisReportResponse(**existing.to_dict())
        
        # 3. Load files from plan
        files = plan.files or []
        if not files:
            raise HTTPException(status_code=400, detail="Plan has no files")
        
        repo_path = plan.repo_path
        
        # 4. Run analysis
        analysis_engine = get_analysis_engine()
        report = await analysis_engine.analyze(
            plan_id=plan_id,
            files=files,
            repo_path=repo_path
        )
        
        # 5. Generate repo_id (use repo_path as identifier)
        repo_id = repo_path.replace("/", "_").replace("\\", "_")[-500:]  # Truncate if needed
        
        # 6. Store repository context (if not exists)
        context_result = await session.execute(
            select(RepositoryContextModel).where(RepositoryContextModel.repo_id == repo_id)
        )
        context = context_result.scalar_one_or_none()
        
        if not context:
            context = RepositoryContextModel(
                repo_id=repo_id,
                repo_name=repo_path.split("/")[-1] if "/" in repo_path else repo_path,
                languages=report.technology_stack.languages if report.technology_stack else {},
                frameworks=report.technology_stack.frameworks if report.technology_stack else {},
                databases=report.technology_stack.databases if report.technology_stack else [],
                tools=report.technology_stack.tools if report.technology_stack else [],
                deployment_platforms=report.technology_stack.deployment if report.technology_stack else [],
                architecture_type=report.architecture.primary_pattern.name if report.architecture and report.architecture.primary_pattern else None,
                architecture_confidence=report.architecture.primary_pattern.confidence if report.architecture and report.architecture.primary_pattern else None,
                service_count=report.service_map.service_count if report.service_map else 1,
                layers=report.architecture.layers if report.architecture else [],
                total_files=report.total_files,
                modularity_score=report.modularity_score
            )
            session.add(context)
        
        # 7. Store detected services
        if report.service_map:
            for service in report.service_map.services:
                service_model = DetectedServiceModel(
                    repo_id=repo_id,
                    service_name=service.name,
                    root_path=service.root_path,
                    file_count=service.file_count,
                    entry_point=service.entry_point,
                    internal_dependencies=service.internal_dependencies,
                    external_dependencies=service.external_dependencies,
                    languages=service.languages,
                    frameworks=service.frameworks,
                    databases=service.databases,
                    has_api=service.has_api,
                    endpoints=service.endpoints,
                    has_dockerfile=service.has_dockerfile,
                    has_k8s_config=service.has_k8s_config
                )
                session.add(service_model)
        
        # 8. Store analysis result
        primary_lang = await analysis_engine.get_primary_language(report) if report.technology_stack else None
        is_microservices = await analysis_engine.is_microservices(report)
        
        analysis_result = AnalysisResultModel(
            plan_id=plan_id,
            repo_id=repo_id,
            repo_path=repo_path,
            analysis_complete=report.analysis_complete,
            errors=report.errors,
            has_dependency_graph=report.dependency_graph is not None,
            total_nodes=len(report.dependency_graph.nodes) if report.dependency_graph else 0,
            total_edges=len(report.dependency_graph.edges) if report.dependency_graph else 0,
            circular_dependencies=report.dependency_graph.circular_dependencies if report.dependency_graph else [],
            topological_order=report.dependency_graph.topological_order if report.dependency_graph else [],
            primary_language=primary_lang,
            total_languages=report.total_languages,
            total_frameworks=report.total_frameworks,
            total_databases=len(report.technology_stack.databases) if report.technology_stack else 0,
            primary_architecture=report.architecture.primary_pattern.name if report.architecture and report.architecture.primary_pattern else None,
            architecture_confidence=report.architecture.primary_pattern.confidence if report.architecture and report.architecture.primary_pattern else None,
            secondary_architectures=[p.name for p in report.architecture.secondary_patterns] if report.architecture else [],
            detected_layers=report.architecture.layers if report.architecture else [],
            total_services=report.total_services,
            is_microservices=is_microservices,
            service_dependencies=report.service_map.dependencies if report.service_map else {},
            total_files=report.total_files,
            modularity_score=report.modularity_score,
            dependency_graph=report.dependency_graph.to_dict() if report.dependency_graph else None,
            technology_stack=report.technology_stack.to_dict() if report.technology_stack else None,
            architecture_analysis=report.architecture.to_dict() if report.architecture else None,
            service_map=report.service_map.to_dict() if report.service_map else None
        )
        
        if existing:
            # Update existing
            for key, value in analysis_result.to_dict().items():
                if key not in ['id', 'created_at']:
                    setattr(existing, key, value)
            existing.updated_at = datetime.utcnow()
            await session.commit()
            logger.info(f"✅ Updated analysis for plan {plan_id}")
            return AnalysisReportResponse(**existing.to_dict())
        else:
            # Create new
            session.add(analysis_result)
            await session.commit()
            await session.refresh(analysis_result)
            logger.info(f"✅ Created analysis for plan {plan_id}")
            return AnalysisReportResponse(**analysis_result.to_dict())
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Analysis failed for plan {plan_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get(
    "/analysis/reports/{plan_id}",
    response_model=AnalysisReportResponse,
    summary="Get full analysis report",
    description="Retrieve complete analysis report for a processing plan"
)
async def get_analysis_report(
    plan_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get full analysis report."""
    try:
        result = await session.execute(
            select(AnalysisResultModel).where(AnalysisResultModel.plan_id == plan_id)
        )
        analysis = result.scalar_one_or_none()
        
        if not analysis:
            raise HTTPException(status_code=404, detail=f"Analysis not found for plan {plan_id}")
        
        return AnalysisReportResponse(**analysis.to_dict())
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get analysis report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/analysis/stack/{plan_id}",
    response_model=TechnologyStackResponse,
    summary="Get technology stack",
    description="Retrieve technology stack analysis"
)
async def get_technology_stack(
    plan_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get technology stack."""
    try:
        result = await session.execute(
            select(AnalysisResultModel).where(AnalysisResultModel.plan_id == plan_id)
        )
        analysis = result.scalar_one_or_none()
        
        if not analysis or not analysis.technology_stack:
            raise HTTPException(status_code=404, detail="Technology stack not found")
        
        stack = analysis.technology_stack
        return TechnologyStackResponse(
            languages=stack.get('languages', {}),
            frameworks=stack.get('frameworks', {}),
            databases=stack.get('databases', []),
            tools=stack.get('tools', []),
            deployment_platforms=stack.get('deployment', []),
            primary_language=analysis.primary_language
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get technology stack: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/analysis/architecture/{plan_id}",
    response_model=ArchitectureResponse,
    summary="Get architecture analysis",
    description="Retrieve architecture pattern analysis"
)
async def get_architecture(
    plan_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get architecture analysis."""
    try:
        result = await session.execute(
            select(AnalysisResultModel).where(AnalysisResultModel.plan_id == plan_id)
        )
        analysis = result.scalar_one_or_none()
        
        if not analysis or not analysis.architecture_analysis:
            raise HTTPException(status_code=404, detail="Architecture analysis not found")
        
        arch = analysis.architecture_analysis
        return ArchitectureResponse(
            primary_pattern=arch.get('primary_pattern'),
            secondary_patterns=arch.get('secondary_patterns', []),
            layers=arch.get('layers', []),
            entry_points=arch.get('entry_points', []),
            modularity_score=analysis.modularity_score or 0.5,
            is_microservices=analysis.is_microservices
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get architecture: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/analysis/services/{plan_id}",
    response_model=ServiceMapResponse,
    summary="Get service map",
    description="Retrieve detected services and dependencies"
)
async def get_service_map(
    plan_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get service map."""
    try:
        result = await session.execute(
            select(AnalysisResultModel).where(AnalysisResultModel.plan_id == plan_id)
        )
        analysis = result.scalar_one_or_none()
        
        if not analysis or not analysis.service_map:
            raise HTTPException(status_code=404, detail="Service map not found")
        
        service_map = analysis.service_map
        return ServiceMapResponse(
            services=service_map.get('services', []),
            dependencies=service_map.get('dependencies', {}),
            service_count=service_map.get('service_count', 1)
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get service map: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/analysis/contexts",
    response_model=List[RepositoryContextResponse],
    summary="List repository contexts",
    description="List all repository contexts with optional filtering"
)
async def list_contexts(
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    architecture_type: Optional[str] = Query(None, description="Filter by architecture type"),
    session: AsyncSession = Depends(get_session)
):
    """List repository contexts."""
    try:
        query = select(RepositoryContextModel)
        
        if architecture_type:
            query = query.where(RepositoryContextModel.architecture_type == architecture_type)
        
        query = query.order_by(desc(RepositoryContextModel.created_at)).limit(limit).offset(offset)
        
        result = await session.execute(query)
        contexts = result.scalars().all()
        
        return [RepositoryContextResponse(**ctx.to_dict()) for ctx in contexts]
    
    except Exception as e:
        logger.error(f"❌ Failed to list contexts: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/analysis/contexts/{repo_id}",
    response_model=RepositoryContextResponse,
    summary="Get repository context",
    description="Retrieve repository context by repo_id"
)
async def get_context(
    repo_id: str,
    session: AsyncSession = Depends(get_session)
):
    """Get repository context."""
    try:
        result = await session.execute(
            select(RepositoryContextModel).where(RepositoryContextModel.repo_id == repo_id)
        )
        context = result.scalar_one_or_none()
        
        if not context:
            raise HTTPException(status_code=404, detail=f"Context not found for repo {repo_id}")
        
        return RepositoryContextResponse(**context.to_dict())
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

