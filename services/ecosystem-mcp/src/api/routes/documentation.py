"""
API routes for documentation generation (Phase 4).
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...services.documentation import (
    get_doc_orchestrator,
    DocConfig,
    PassType,
    DocStatus,
    DocumentationSet
)
from ...services.analysis.analysis_engine import AnalysisEngine
from ...storage import get_session
from ...storage.models_documentation import DocumentationRunModel, DocumentationArtifactModel
from ...storage.models_analysis import AnalysisResultModel
from sqlalchemy import select, desc
from ...utils.enhanced_logging import create_pipeline_logger, log_execution_time

router = APIRouter()
logger = logging.getLogger(__name__)
pipeline_logger = create_pipeline_logger(__name__)


# ============================================================================
# Pydantic Models
# ============================================================================

class GenerateDocsRequest(BaseModel):
    """Request to generate documentation."""
    plan_id: str = Field(..., description="Processing plan ID")
    repo_path: str = Field(..., description="Repository path")
    
    # Configuration
    passes: Optional[List[str]] = Field(None, description="Pass types to execute")
    output_formats: Optional[List[str]] = Field(["markdown"], description="Output formats")
    include_diagrams: bool = Field(True, description="Include diagrams")
    include_examples: bool = Field(True, description="Include examples")
    validate_between_passes: bool = Field(True, description="Validate quality between passes")
    min_quality_score: float = Field(0.7, description="Minimum quality score", ge=0.0, le=1.0)
    skip_review: bool = Field(False, description="Skip automatic review queue for low-confidence artifacts")


class DocumentationRunResponse(BaseModel):
    """Documentation run response."""
    id: str
    plan_id: str
    repo_id: str
    status: str
    passes_completed: int
    total_passes: int
    current_pass: Optional[str]
    total_artifacts: int
    total_words: int
    overall_quality_score: Optional[float]
    started_at: str
    completed_at: Optional[str]
    output_path: Optional[str]


class ArtifactResponse(BaseModel):
    """Documentation artifact response."""
    id: str
    run_id: str
    artifact_type: str
    pass_number: int
    pass_type: str
    component_name: Optional[str]
    title: Optional[str]
    content: str
    format: str
    word_count: int
    quality_score: Optional[float]
    created_at: str


class PassResultResponse(BaseModel):
    """Pass result response."""
    pass_type: str
    status: str
    artifacts_count: int
    quality_score: float
    duration_seconds: float
    errors: List[str]


# ============================================================================
# API Endpoints
# ============================================================================

@router.post(
    "/documentation/generate",
    response_model=DocumentationRunResponse,
    summary="Generate Documentation",
    description="Start multi-pass documentation generation for a repository",
    tags=["Documentation"]
)
async def generate_documentation(
    request: GenerateDocsRequest,
    session: AsyncSession = Depends(get_session)
) -> DocumentationRunResponse:
    """
    Generate comprehensive documentation for a repository.
    
    Process:
    1. Load or run analysis (Phase 3)
    2. Execute multi-pass documentation generation
    3. Store artifacts in database
    4. Return run metadata
    """
    try:
        logger.info(f"📚 Documentation generation requested for plan {request.plan_id}")
        
        # 1. Get the processing plan with file classifications eagerly loaded
        from ...storage.models_discovery import ProcessingPlanModel
        from sqlalchemy.orm import selectinload
        
        stmt = select(ProcessingPlanModel).where(
            ProcessingPlanModel.id == request.plan_id
        ).options(selectinload(ProcessingPlanModel.file_classifications))
        result = await session.execute(stmt)
        plan = result.scalar_one_or_none()
        
        if not plan:
            raise HTTPException(status_code=404, detail=f"Processing plan {request.plan_id} not found")
        
        # 2. Get or create analysis
        analysis_engine = AnalysisEngine()
        
        # Check if analysis exists for this plan
        stmt = select(AnalysisResultModel).where(
            AnalysisResultModel.plan_id == request.plan_id
        ).order_by(desc(AnalysisResultModel.created_at)).limit(1)
        result = await session.execute(stmt)
        analysis_record = result.scalar_one_or_none()
        
        if not analysis_record:
            logger.info("   No existing analysis found, running analysis...")
            
            # Get files from plan's file classifications
            file_classifications = plan.file_classifications or []
            if not file_classifications:
                raise HTTPException(status_code=400, detail="Processing plan has no classified files")
            
            # Convert file classifications to file list for analysis
            files = [{
                "file_path": fc.file_path,
                "relative_path": fc.relative_path,
                "size_bytes": fc.size_bytes,
                "extension": fc.extension,
                "language": fc.language,
                "is_code": fc.is_code,
                "is_test": fc.is_test,
                "is_doc": fc.is_doc,
                "importance_level": fc.importance_level,
                "importance_score": fc.importance_score
            } for fc in file_classifications]
            
            logger.info(f"   Loaded {len(files)} files for analysis")
            
            # Run analysis
            pipeline_logger.log_step("Running analysis engine",
                plan_id=request.plan_id,
                files=len(files)
            )
            
            analysis_report = await analysis_engine.analyze(
                plan_id=request.plan_id,
                files=files,
                repo_path=request.repo_path
            )
            
            pipeline_logger.log_checkpoint("Analysis complete",
                files_analyzed=analysis_report.total_files,
                services_detected=analysis_report.total_services
            )
            
            # Generate repo_id
            repo_id = request.repo_path.replace("/", "_").replace("\\", "_")[-500:]
            
            # Ensure repository context exists (required for foreign key)
            from ...storage.models_analysis import RepositoryContextModel
            
            stmt_repo = select(RepositoryContextModel).where(
                RepositoryContextModel.repo_id == repo_id
            )
            result_repo = await session.execute(stmt_repo)
            repo_context = result_repo.scalar_one_or_none()
            
            if not repo_context:
                logger.info(f"   Creating repository context for {repo_id}...")
                repo_context = RepositoryContextModel(
                    repo_id=repo_id,
                    repo_name=repo_id.split("_")[-1] if "_" in repo_id else repo_id,
                    architecture_type="unknown",
                    service_count=1,
                    endpoint_count=0,
                    has_rest_api=False
                )
                session.add(repo_context)
                await session.flush()  # Flush to get the repo in DB before FK reference
                logger.info(f"   ✅ Repository context created")
            
            # Store analysis using proper field mapping
            logger.info(f"   Storing analysis results to database...")
            analysis_record = AnalysisResultModel(
                plan_id=request.plan_id,
                repo_id=repo_id,
                repo_path=request.repo_path,
                **analysis_report.to_model_kwargs()  # Use helper method for correct field mapping
            )
            session.add(analysis_record)
            await session.commit()
            logger.info(f"   ✅ Analysis complete and stored")
        else:
            logger.info("   Using existing analysis")
            # Reconstruct analysis report from stored model data
            from ...services.analysis.analysis_engine import (
                AnalysisReport,
                DependencyGraph,
                TechnologyStack,
                ArchitectureAnalysis,
                ServiceMap
            )
            
            # Reconstruct components from JSON fields
            dep_graph = DependencyGraph(**analysis_record.dependency_graph) if analysis_record.dependency_graph else None
            tech_stack = TechnologyStack(**analysis_record.technology_stack) if analysis_record.technology_stack else None
            arch = ArchitectureAnalysis(**analysis_record.architecture_analysis) if analysis_record.architecture_analysis else None
            svc_map = ServiceMap(**analysis_record.service_map) if analysis_record.service_map else None
            
            # Build AnalysisReport from model fields
            analysis_report = AnalysisReport(
                plan_id=analysis_record.plan_id,
                repo_path=analysis_record.repo_path,
                dependency_graph=dep_graph,
                technology_stack=tech_stack,
                architecture=arch,
                service_map=svc_map,
                total_files=analysis_record.total_files or 0,
                total_languages=analysis_record.total_languages or 0,
                total_frameworks=analysis_record.total_frameworks or 0,
                total_services=analysis_record.total_services or 1,
                modularity_score=analysis_record.modularity_score or 0.5,
                analysis_complete=analysis_record.analysis_complete,
                errors=analysis_record.errors or []
            )
            
            pipeline_logger.log_checkpoint("Loaded existing analysis",
                plan_id=analysis_record.plan_id,
                services=analysis_report.total_services
            )
        
        # 2. Configure documentation generation
        config = DocConfig(
            passes=[PassType(p) for p in request.passes] if request.passes else None,
            output_formats=request.output_formats,
            include_diagrams=request.include_diagrams,
            include_examples=request.include_examples,
            validate_between_passes=request.validate_between_passes,
            min_quality_score=request.min_quality_score,
            auto_queue_for_review=not request.skip_review  # Invert: skip_review=True means auto_queue=False
        )
        
        # 3. Generate documentation
        orchestrator = get_doc_orchestrator()
        doc_set: DocumentationSet = await orchestrator.generate_documentation(
            plan_id=request.plan_id,
            analysis_report=analysis_report,
            config=config
        )
        
        # 4. Store in database
        run_record = DocumentationRunModel(
            id=doc_set.run_id,
            plan_id=doc_set.plan_id,
            repo_id=doc_set.repo_id,
            passes_completed=len(doc_set.pass_results),
            total_passes=len(config.passes),
            status=doc_set.status.value,
            started_at=doc_set.started_at,
            completed_at=doc_set.completed_at,
            total_artifacts=doc_set.total_artifacts,
            total_words=doc_set.total_words,
            overall_quality_score=doc_set.overall_quality_score,
            output_path=doc_set.output_path,
            output_formats=request.output_formats,
            config={
                'passes': [p.value for p in config.passes],
                'validate_between_passes': config.validate_between_passes,
                'min_quality_score': config.min_quality_score
            }
        )
        session.add(run_record)
        
        # Store artifacts
        for pass_num, pass_result in enumerate(doc_set.pass_results, 1):
            for artifact in pass_result.artifacts:
                artifact_record = DocumentationArtifactModel(
                    run_id=doc_set.run_id,
                    artifact_type=artifact.get('type', 'unknown'),
                    pass_number=pass_num,
                    pass_type=pass_result.pass_type.value,
                    component_name=artifact.get('component_name'),
                    title=artifact.get('title'),
                    content=artifact.get('content', ''),
                    format=artifact.get('format', 'markdown'),
                    word_count=artifact.get('word_count', 0),
                    quality_score=pass_result.quality_score
                )
                session.add(artifact_record)
        
        await session.commit()
        
        logger.info(f"✅ Documentation generation complete: {doc_set.run_id}")
        
        return DocumentationRunResponse(
            id=str(run_record.id),
            plan_id=run_record.plan_id,
            repo_id=run_record.repo_id,
            status=run_record.status,
            passes_completed=run_record.passes_completed,
            total_passes=run_record.total_passes,
            current_pass=run_record.current_pass,
            total_artifacts=run_record.total_artifacts,
            total_words=run_record.total_words,
            overall_quality_score=run_record.overall_quality_score,
            started_at=run_record.started_at.isoformat(),
            completed_at=run_record.completed_at.isoformat() if run_record.completed_at else None,
            output_path=run_record.output_path
        )
    
    except Exception as e:
        logger.error(f"❌ Documentation generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Documentation generation failed: {str(e)}")


@router.get(
    "/documentation/runs",
    response_model=List[DocumentationRunResponse],
    summary="List Documentation Runs",
    description="List all documentation generation runs",
    tags=["Documentation"]
)
async def list_documentation_runs(
    limit: int = 50,
    offset: int = 0,
    status: Optional[str] = None,
    session: AsyncSession = Depends(get_session)
) -> List[DocumentationRunResponse]:
    """List documentation runs with pagination."""
    try:
        stmt = select(DocumentationRunModel).order_by(desc(DocumentationRunModel.created_at))
        
        if status:
            stmt = stmt.where(DocumentationRunModel.status == status)
        
        stmt = stmt.limit(limit).offset(offset)
        
        result = await session.execute(stmt)
        runs = result.scalars().all()
        
        return [
            DocumentationRunResponse(
                id=str(run.id),
                plan_id=run.plan_id,
                repo_id=run.repo_id,
                status=run.status,
                passes_completed=run.passes_completed,
                total_passes=run.total_passes,
                current_pass=run.current_pass,
                total_artifacts=run.total_artifacts,
                total_words=run.total_words,
                overall_quality_score=run.overall_quality_score,
                started_at=run.started_at.isoformat(),
                completed_at=run.completed_at.isoformat() if run.completed_at else None,
                output_path=run.output_path
            )
            for run in runs
        ]
    
    except Exception as e:
        logger.error(f"❌ Failed to list runs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list runs: {str(e)}")


@router.get(
    "/documentation/runs/{run_id}",
    response_model=DocumentationRunResponse,
    summary="Get Documentation Run",
    description="Get documentation run by ID",
    tags=["Documentation"]
)
async def get_documentation_run(
    run_id: str,
    session: AsyncSession = Depends(get_session)
) -> DocumentationRunResponse:
    """Get documentation run details."""
    try:
        from uuid import UUID
        run_uuid = UUID(run_id)
        
        stmt = select(DocumentationRunModel).where(DocumentationRunModel.id == run_uuid)
        result = await session.execute(stmt)
        run = result.scalar_one_or_none()
        
        if not run:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        
        return DocumentationRunResponse(
            id=str(run.id),
            plan_id=run.plan_id,
            repo_id=run.repo_id,
            status=run.status,
            passes_completed=run.passes_completed,
            total_passes=run.total_passes,
            current_pass=run.current_pass,
            total_artifacts=run.total_artifacts,
            total_words=run.total_words,
            overall_quality_score=run.overall_quality_score,
            started_at=run.started_at.isoformat(),
            completed_at=run.completed_at.isoformat() if run.completed_at else None,
            output_path=run.output_path
        )
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format")
    except Exception as e:
        logger.error(f"❌ Failed to get run: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get run: {str(e)}")


@router.get(
    "/documentation/runs/{run_id}/artifacts",
    response_model=List[ArtifactResponse],
    summary="Get Run Artifacts",
    description="Get all artifacts for a documentation run",
    tags=["Documentation"]
)
async def get_run_artifacts(
    run_id: str,
    artifact_type: Optional[str] = None,
    pass_type: Optional[str] = None,
    session: AsyncSession = Depends(get_session)
) -> List[ArtifactResponse]:
    """Get artifacts for a documentation run."""
    try:
        from uuid import UUID
        run_uuid = UUID(run_id)
        
        stmt = select(DocumentationArtifactModel).where(
            DocumentationArtifactModel.run_id == run_uuid
        ).order_by(DocumentationArtifactModel.pass_number)
        
        if artifact_type:
            stmt = stmt.where(DocumentationArtifactModel.artifact_type == artifact_type)
        if pass_type:
            stmt = stmt.where(DocumentationArtifactModel.pass_type == pass_type)
        
        result = await session.execute(stmt)
        artifacts = result.scalars().all()
        
        return [
            ArtifactResponse(
                id=str(artifact.id),
                run_id=str(artifact.run_id),
                artifact_type=artifact.artifact_type,
                pass_number=artifact.pass_number,
                pass_type=artifact.pass_type,
                component_name=artifact.component_name,
                title=artifact.title,
                content=artifact.content,
                format=artifact.format,
                word_count=artifact.word_count,
                quality_score=artifact.quality_score,
                created_at=artifact.created_at.isoformat()
            )
            for artifact in artifacts
        ]
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format")
    except Exception as e:
        logger.error(f"❌ Failed to get artifacts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get artifacts: {str(e)}")


@router.get(
    "/documentation/artifacts/{artifact_id}",
    response_model=ArtifactResponse,
    summary="Get Artifact",
    description="Get a single documentation artifact",
    tags=["Documentation"]
)
async def get_artifact(
    artifact_id: str,
    session: AsyncSession = Depends(get_session)
) -> ArtifactResponse:
    """Get a single artifact."""
    try:
        from uuid import UUID
        artifact_uuid = UUID(artifact_id)
        
        stmt = select(DocumentationArtifactModel).where(
            DocumentationArtifactModel.id == artifact_uuid
        )
        result = await session.execute(stmt)
        artifact = result.scalar_one_or_none()
        
        if not artifact:
            raise HTTPException(status_code=404, detail=f"Artifact {artifact_id} not found")
        
        return ArtifactResponse(
            id=str(artifact.id),
            run_id=str(artifact.run_id),
            artifact_type=artifact.artifact_type,
            pass_number=artifact.pass_number,
            pass_type=artifact.pass_type,
            component_name=artifact.component_name,
            title=artifact.title,
            content=artifact.content,
            format=artifact.format,
            word_count=artifact.word_count,
            quality_score=artifact.quality_score,
            created_at=artifact.created_at.isoformat()
        )
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid artifact ID format")
    except Exception as e:
        logger.error(f"❌ Failed to get artifact: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get artifact: {str(e)}")


@router.delete(
    "/documentation/runs/{run_id}",
    summary="Delete Documentation Run",
    description="Delete a documentation run and all its artifacts",
    tags=["Documentation"]
)
async def delete_documentation_run(
    run_id: str,
    session: AsyncSession = Depends(get_session)
) -> Dict:
    """Delete a documentation run."""
    try:
        from uuid import UUID
        run_uuid = UUID(run_id)
        
        stmt = select(DocumentationRunModel).where(DocumentationRunModel.id == run_uuid)
        result = await session.execute(stmt)
        run = result.scalar_one_or_none()
        
        if not run:
            raise HTTPException(status_code=404, detail=f"Run {run_id} not found")
        
        await session.delete(run)
        await session.commit()
        
        logger.info(f"🗑️ Deleted documentation run {run_id}")
        
        return {"success": True, "message": f"Run {run_id} deleted"}
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID format")
    except Exception as e:
        logger.error(f"❌ Failed to delete run: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to delete run: {str(e)}")

