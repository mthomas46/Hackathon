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

router = APIRouter()
logger = logging.getLogger(__name__)


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
        
        # 1. Get or create analysis
        analysis_engine = AnalysisEngine()
        
        # Check if analysis exists
        stmt = select(AnalysisResultModel).where(
            AnalysisResultModel.repo_path == request.repo_path
        ).order_by(desc(AnalysisResultModel.created_at)).limit(1)
        result = await session.execute(stmt)
        analysis_record = result.scalar_one_or_none()
        
        if not analysis_record:
            logger.info("   No existing analysis found, running analysis...")
            analysis_report = await analysis_engine.analyze_repository(request.repo_path)
            
            # Store analysis
            analysis_record = AnalysisResultModel(
                repo_path=request.repo_path,
                analysis_data=analysis_report.to_dict()
            )
            session.add(analysis_record)
            await session.commit()
        else:
            logger.info("   Using existing analysis")
            # Reconstruct analysis report from stored data
            from ...services.analysis.analysis_engine import AnalysisReport
            analysis_report = AnalysisReport(**analysis_record.analysis_data)
        
        # 2. Configure documentation generation
        config = DocConfig(
            passes=[PassType(p) for p in request.passes] if request.passes else None,
            output_formats=request.output_formats,
            include_diagrams=request.include_diagrams,
            include_examples=request.include_examples,
            validate_between_passes=request.validate_between_passes,
            min_quality_score=request.min_quality_score
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

