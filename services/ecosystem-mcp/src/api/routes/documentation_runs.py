"""
Documentation Run Management API Routes

Provides endpoints for managing documentation generation runs:
- Create and track runs
- Browse run history
- View generated documents
- Export documents
- Real-time progress tracking
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID
import zipfile
from io import BytesIO

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ...storage import get_database
from ...services.documentation.run_manager import DocumentationRunManager
from ...services.documentation.adaptive_orchestrator import AdaptiveDocumentationOrchestrator

logger = logging.getLogger(__name__)
router = APIRouter()


# ==========================================
# Background Task Functions
# ==========================================

async def _generate_documentation_background(
    run_id: str,
    service_name: str,
    template_name: str,
    category: str,
    config: dict
):
    """
    Background task to generate documentation for a run.
    
    This is called automatically when a run is created (Solution #2).
    """
    try:
        logger.info(f"📚 Starting background generation for run {run_id}")
        
        # Update status to running
        db = get_database()
        async with db.session() as session:
            from ...storage.models_documentation import DocumentationRunModel
            from sqlalchemy import select, update
            
            await session.execute(
                update(DocumentationRunModel)
                .where(DocumentationRunModel.id == run_id)
                .values(status="running", started_at=datetime.utcnow())
            )
            await session.commit()
        
        # Generate documentation with timeout
        import asyncio
        orchestrator = AdaptiveDocumentationOrchestrator()
        
        try:
            # 5 minute timeout for generation
            async with asyncio.timeout(300):
                result = await orchestrator.generate_adaptive_documentation(
                    service_name=service_name,
                    template_name=template_name,
                    category=category,
                    config=config,
                    run_id=run_id  # Pass existing run_id!
                )
        except asyncio.TimeoutError:
            logger.error(f"⏱️  Documentation generation timed out after 5 minutes for run {run_id}")
            raise TimeoutError("Documentation generation exceeded 5 minute timeout")
        
        # Update run with results
        # NOTE: total_artifacts and total_words are already updated by the repository
        # during artifact creation. DO NOT overwrite them here!
        async with db.session() as session:
            await session.execute(
                update(DocumentationRunModel)
                .where(DocumentationRunModel.id == run_id)
                .values(
                    status="completed",
                    completed_at=datetime.utcnow(),
                    passes_completed=config.get("passes", 1)
                    # ✅ REMOVED: total_artifacts and total_words
                    # These are maintained by DocumentationRunRepository.add_artifact()
                )
            )
            await session.commit()
        
        logger.info(f"✅ Background generation completed for run {run_id}")
    
    except Exception as e:
        logger.error(f"❌ Background generation failed for run {run_id}: {e}", exc_info=True)
        
        # Update run as failed
        try:
            db = get_database()
            async with db.session() as session:
                from ...storage.models_documentation import DocumentationRunModel
                from sqlalchemy import update
                
                await session.execute(
                    update(DocumentationRunModel)
                    .where(DocumentationRunModel.id == run_id)
                    .values(
                        status="failed",
                        completed_at=datetime.utcnow()
                        # Note: error_details column doesn't exist in model
                        # Error is logged instead
                    )
                )
                await session.commit()
                logger.info(f"Marked run {run_id} as failed: {str(e)}")
        except Exception as update_err:
            logger.error(f"Failed to update run status: {update_err}")


# ==========================================
# Request/Response Models
# ==========================================

class CreateRunRequest(BaseModel):
    """Request to create a new documentation run."""
    name: str = Field(..., min_length=1, max_length=255)
    description: str = Field("", max_length=1000)
    source_directory: str
    output_format: str = Field("markdown", pattern="^(markdown|html|pdf)$")
    response_size: Optional[str] = Field(None, pattern="^(S|M|L|XL)$")
    tier: Optional[str] = Field(None, pattern="^(desktop|docker|auto)$")
    num_passes: int = Field(3, ge=1, le=10)
    questions_per_pass: int = Field(5, ge=1, le=20)
    created_by: Optional[str] = None
    metadata: Optional[dict] = None


class CreateRunResponse(BaseModel):
    """Response after creating a run."""
    run_id: str
    name: str
    status: str
    message: str


class RunSummaryResponse(BaseModel):
    """Summary of a documentation run."""
    id: str
    name: str
    description: str
    status: str
    source_directory: str
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    total_documents: int
    successful_documents: int
    failed_documents: int
    created_by: Optional[str]
    created_at: datetime


class RunDetailResponse(BaseModel):
    """Detailed information about a run."""
    id: str
    name: str
    description: str
    status: str
    source_directory: str
    output_format: str
    response_size: Optional[str]
    tier: Optional[str]
    num_passes: int
    questions_per_pass: int
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[int]
    total_documents: int
    successful_documents: int
    failed_documents: int
    output_directory: Optional[str]
    created_by: Optional[str]
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None  # Additional metadata including sections


class RunProgressResponse(BaseModel):
    """Real-time progress of a run."""
    run_id: str
    current_pass: int
    total_passes: int
    current_question: int
    total_questions: int
    current_operation: str
    progress_percentage: float
    documents_generated: int
    documents_failed: int
    estimated_time_remaining_seconds: Optional[int]
    updated_at: datetime


class GeneratedDocumentResponse(BaseModel):
    """Information about a generated document."""
    id: str
    run_id: str
    title: str
    filename: str
    content_hash: str
    content_size: int
    pass_number: Optional[int]
    question: Optional[str]
    status: str
    generation_time_seconds: Optional[float]
    word_count: Optional[int]
    created_at: datetime


class DocumentContentResponse(BaseModel):
    """Full content of a generated document."""
    id: str
    title: str
    filename: str
    content: str
    content_size: int
    word_count: Optional[int]
    created_at: datetime


class RunStatsResponse(BaseModel):
    """Statistics for a run."""
    total_docs: int
    successful_docs: int
    failed_docs: int
    avg_generation_time: Optional[float]
    total_content_size: int
    total_word_count: int


# ==========================================
# Endpoints
# ==========================================

@router.post("/runs", response_model=CreateRunResponse)
async def create_documentation_run(
    request: CreateRunRequest,
    background_tasks: BackgroundTasks
):
    """
    Create a new documentation generation run and start processing.
    
    The run is created in 'pending' status and immediately queued for
    background processing. The worker will pick it up automatically.
    
    Auto-start can be disabled by setting auto_start=false in request.
    """
    try:
        db = get_database()
        async with db.session() as session:
            manager = DocumentationRunManager(session)
            
            # Build metadata dict FIRST (so we can use it in config)
            metadata = request.metadata or {}
            logger.info(f"📍 Received metadata: {metadata}")
            
            # Extract transparency_mode BEFORE updating metadata
            transparency_mode = metadata.get("transparency_mode", "normal")
            logger.info(f"📍 Transparency mode: {transparency_mode}")
            
            # ✨ CRITICAL FIX: Extract service_name from multiple possible sources
            # The UI may pass it in metadata OR as service_filter
            service_name_from_metadata = metadata.get("service_name")
            service_name_from_filter = metadata.get("service_filter")
            service_name_from_path = request.source_directory.split("/")[-1] if request.source_directory else None
            
            service_name = (
                service_name_from_metadata or 
                service_name_from_filter or 
                service_name_from_path or
                "unknown"
            )
            
            logger.info(f"🔍 Service Name Resolution:")
            logger.info(f"   - From metadata: {service_name_from_metadata}")
            logger.info(f"   - From filter: {service_name_from_filter}")
            logger.info(f"   - From path: {service_name_from_path}")
            logger.info(f"   ✅ Final: {service_name}")
            
            # ✅ VALIDATION: Check if service has documents in database
            if service_name and service_name != "unknown":
                try:
                    from ...storage.chromadb_client import get_chroma_client
                    chroma = get_chroma_client()
                    
                    # Quick check: try to get documents for this service
                    test_results = await chroma.query_embeddings(
                        query_embedding=[0.0] * 384,  # Dummy embedding
                        n_results=1,
                        where={"service": service_name}
                    )
                    
                    doc_count = len(test_results.get("ids", [[]])[0]) if test_results else 0
                    
                    if doc_count == 0:
                        logger.warning(f"⚠️ No documents found for service '{service_name}' in ChromaDB")
                        logger.warning(f"   Generation may produce 'I don't have enough information' responses")
                        logger.warning(f"   Consider ingesting the repository first")
                    else:
                        logger.info(f"✅ Service '{service_name}' has documents in database")
                        
                except Exception as e:
                    logger.warning(f"⚠️ Could not validate service documents: {e}")
                    # Don't fail hard - validation is advisory only
            
            metadata.update({
                "name": request.name,
                "description": request.description,
                "created_by": request.created_by,
                # Add template/service info if available
                "template_name": metadata.get("template_name", "api_reference"),
                "service_name": service_name,  # Use resolved service name
                "category": metadata.get("category", "backend")
            })
            
            # Build config dict from request parameters + metadata
            config = {
                "output_format": request.output_format,
                "response_size": request.response_size,
                "tier": request.tier,
                "passes": request.num_passes,
                "questions_per_pass": request.questions_per_pass,
                "transparency_mode": transparency_mode  # Use extracted value
            }
            logger.info(f"📍 Final config: {config}")
            
            run = await manager.create_run(
                repo_path=request.source_directory,
                config=config,
                metadata=metadata
            )
            
            # ✅ SOLUTION #2: Auto-start generation in background
            # Note: The worker (Solution #1) will also pick this up if background task fails
            auto_start = metadata.get("auto_start", True)
            if auto_start:
                logger.info(f"🚀 Auto-starting documentation generation for run {run.id}")
                background_tasks.add_task(
                    _generate_documentation_background,
                    str(run.id),
                    service_name,  # Use resolved service_name variable
                    metadata.get("template_name", "api_reference"),
                    metadata.get("category", "backend"),
                    config
                )
            
            return CreateRunResponse(
                run_id=str(run.id),
                name=request.name,
                status="pending",
                message=f"Documentation run '{request.name}' created and queued for processing"
            )
    
    except Exception as e:
        logger.error(f"Failed to create documentation run: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs", response_model=List[RunSummaryResponse])
async def list_documentation_runs(
    status: Optional[str] = Query(None, pattern="^(pending|running|completed|failed|cancelled)$"),
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """
    List documentation runs with optional filtering.
    
    Parameters:
    - status: Filter by run status
    - limit: Maximum results to return
    - offset: Pagination offset
    """
    try:
        db = get_database()
        async with db.session() as session:
            manager = DocumentationRunManager(session)
            
            runs = await manager.list_runs(
                status=status,
                limit=limit,
                offset=offset
            )
            
            # Convert runs to response format
            result = []
            for run in runs:
                # Extract metadata safely
                metadata = run.metadata if hasattr(run, 'metadata') and isinstance(run.metadata, dict) else {}
                config = run.config if hasattr(run, 'config') and isinstance(run.config, dict) else {}
                
                # Calculate duration if completed
                duration_seconds = None
                if run.completed_at and run.started_at:
                    duration_seconds = int((run.completed_at - run.started_at).total_seconds())
                
                result.append(RunSummaryResponse(
                    id=str(run.id),
                    name=metadata.get("name", "Unknown"),
                    description=metadata.get("description", ""),
                    status=run.status,
                    source_directory=run.repo_id or metadata.get("source_directory", ""),
                    started_at=run.started_at,
                    completed_at=run.completed_at,
                    duration_seconds=duration_seconds,
                    total_documents=run.total_artifacts or 0,
                    successful_documents=run.total_artifacts or 0,
                    failed_documents=0,
                    created_by=metadata.get("created_by"),
                    created_at=run.created_at
                ))
            
            return result
    
    except Exception as e:
        logger.error(f"Failed to list documentation runs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}", response_model=RunDetailResponse)
async def get_documentation_run(run_id: str):
    """Get detailed information about a specific run."""
    try:
        db = get_database()
        async with db.session() as session:
            from sqlalchemy import select
            from ...storage.models_documentation import DocumentationRunModel
            
            # Get run directly from database
            query = select(DocumentationRunModel).filter(DocumentationRunModel.id == UUID(run_id))
            result = await session.execute(query)
            run = result.scalar_one_or_none()
            
            if not run:
                raise HTTPException(status_code=404, detail="Run not found")
            
            # Calculate duration if completed
            duration_seconds = None
            if run.completed_at and run.started_at:
                duration_seconds = int((run.completed_at - run.started_at).total_seconds())
            
            # Extract metadata fields
            metadata = run.metadata if hasattr(run, 'metadata') and isinstance(run.metadata, dict) else {}
            
            # Get artifacts to extract sections
            from ...storage.models_documentation import DocumentationArtifactModel
            query_artifacts = select(DocumentationArtifactModel).filter(
                DocumentationArtifactModel.run_id == UUID(run_id)
            )
            result_artifacts = await session.execute(query_artifacts)
            artifacts = result_artifacts.scalars().all()
            
            # Extract section information from artifacts
            sections_info = []
            for artifact in artifacts:
                sections_info.append({
                    "title": artifact.title,
                    "type": artifact.artifact_type,
                    "word_count": artifact.word_count
                })
            
            # Enhanced metadata with run_id and sections
            enhanced_metadata = metadata.copy() if metadata else {}
            enhanced_metadata.update({
                "run_id": str(run.id),
                "sections": sections_info,
                "total_sections": len(sections_info)
            })
            
            return RunDetailResponse(
                id=str(run.id),
                name=metadata.get("name", "Unknown"),
                description=metadata.get("description", ""),
                status=run.status,
                source_directory=run.repo_id or metadata.get("source_directory", ""),
                output_format=run.config.get("output_format", "markdown") if run.config else "markdown",
                response_size=run.config.get("response_size") if run.config else None,
                tier=run.config.get("tier") if run.config else None,
                num_passes=run.total_passes,
                questions_per_pass=run.config.get("questions_per_pass", 0) if run.config else 0,
                started_at=run.started_at,
                completed_at=run.completed_at,
                duration_seconds=duration_seconds,
                total_documents=run.total_artifacts,
                successful_documents=run.total_artifacts,  # Assuming all successful for now
                failed_documents=0,
                output_directory=run.output_path,
                created_by=metadata.get("created_by"),
                created_at=run.created_at,
                updated_at=run.updated_at,
                metadata=enhanced_metadata  # Include enhanced metadata with sections
            )
    
    except ValueError as e:
        logger.error(f"ValueError getting run {run_id}: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail=f"Invalid run ID: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get documentation run {run_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}/progress", response_model=Optional[RunProgressResponse])
async def get_run_progress(run_id: str):
    """Get real-time progress for a running documentation generation."""
    try:
        db = get_database()
        async with db.session() as session:
            manager = DocumentationRunManager(session)
            
            progress = await manager.get_run_progress(UUID(run_id))
            
            if not progress:
                return None
            
            return RunProgressResponse(
                run_id=str(progress["run_id"]),
                current_pass=progress["current_pass"],
                total_passes=progress["total_passes"],
                current_question=progress["current_question"],
                total_questions=progress["total_questions"],
                current_operation=progress["current_operation"],
                progress_percentage=float(progress["progress_percentage"]),
                documents_generated=progress["documents_generated"],
                documents_failed=progress["documents_failed"],
                estimated_time_remaining_seconds=progress.get("estimated_time_remaining_seconds"),
                updated_at=progress["updated_at"]
            )
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID")
    except Exception as e:
        logger.error(f"Failed to get run progress: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/runs/{run_id}/start")
async def start_documentation_run(
    run_id: str,
    background_tasks: BackgroundTasks
):
    """
    ✅ SOLUTION #3: Manually start/restart a pending or failed documentation run.
    
    This endpoint allows you to:
    - Start a run that was created with auto_start=false
    - Retry a failed run
    - Restart a cancelled run
    
    The run must be in 'pending', 'failed', or 'cancelled' status.
    """
    try:
        db = get_database()
        async with db.session() as session:
            from ...storage.models_documentation import DocumentationRunModel
            from sqlalchemy import select
            
            # Get the run
            query = select(DocumentationRunModel).filter(
                DocumentationRunModel.id == run_id
            )
            result = await session.execute(query)
            run = result.scalar_one_or_none()
            
            if not run:
                raise HTTPException(status_code=404, detail="Run not found")
            
            # Check if run can be started
            if run.status == "running":
                raise HTTPException(
                    status_code=400,
                    detail="Run is already running"
                )
            elif run.status == "completed":
                raise HTTPException(
                    status_code=400,
                    detail="Run already completed. Create a new run to regenerate."
                )
            
            # Extract metadata for generation
            metadata = run.metadata or {}
            service_name = metadata.get("service_name", run.repo_id or "unknown")
            template_name = metadata.get("template_name", "api_reference")
            category = metadata.get("category", "backend")
            config = run.config or {}
            
            logger.info(f"🚀 Manually starting documentation run {run_id}")
            
            # Start generation in background
            background_tasks.add_task(
                _generate_documentation_background,
                str(run.id),
                service_name,
                template_name,
                category,
                config
            )
            
            return {
                "success": True,
                "run_id": str(run.id),
                "status": "pending",
                "message": f"Documentation generation started for run {run_id}"
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to start documentation run: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}/documents", response_model=List[GeneratedDocumentResponse])
async def get_run_documents(
    run_id: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Get all documents/artifacts generated by a specific run."""
    try:
        db = get_database()
        async with db.session() as session:
            manager = DocumentationRunManager(session)
            
            # Get artifacts for this run
            artifacts = await manager.get_artifacts(UUID(run_id))
            
            # Apply pagination
            paginated_artifacts = artifacts[offset:offset+limit]
            
            return [
                GeneratedDocumentResponse(
                    id=str(artifact.id),
                    run_id=str(artifact.run_id),
                    title=artifact.title,
                    filename=f"{artifact.artifact_type}_{artifact.pass_number}.md",
                    content_hash=str(hash(artifact.content)),  # Simple hash for now
                    content_size=len(artifact.content),
                    pass_number=artifact.pass_number,
                    question=None,  # Not stored in artifacts model
                    status="completed",  # Artifacts are completed by definition
                    generation_time_seconds=None,  # Not tracked per artifact
                    word_count=artifact.word_count,
                    created_at=artifact.created_at
                )
                for artifact in paginated_artifacts
            ]
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID")
    except Exception as e:
        logger.error(f"Failed to get run documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/documents/{document_id}", response_model=DocumentContentResponse)
async def get_document_content(document_id: str):
    """Get the full content of a generated document."""
    try:
        db = get_database()
        async with db.session() as session:
            # Use DocumentationArtifactModel instead of non-existent generated_documents table
            from src.storage.models_documentation import DocumentationArtifactModel
            from sqlalchemy import select
            
            query = select(DocumentationArtifactModel).filter(
                DocumentationArtifactModel.id == UUID(document_id)
            )
            result = await session.execute(query)
            artifact = result.scalar_one_or_none()
            
            if not artifact:
                raise HTTPException(status_code=404, detail="Document not found")
            
            return DocumentContentResponse(
                id=str(artifact.id),
                title=artifact.title,
                filename=f"{artifact.artifact_type}_{artifact.pass_number}.md",
                content=artifact.content,
                content_size=len(artifact.content),
                word_count=artifact.word_count,
                created_at=artifact.created_at
            )
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get document content: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}/export/zip")
async def export_run_as_zip(run_id: str):
    """
    Export all documents from a run as a ZIP file.
    
    Returns a downloadable ZIP archive containing all generated documents.
    """
    try:
        db = get_database()
        async with db.session() as session:
            manager = DocumentationRunManager(session)
            
            # Get run details
            run = await manager.get_run(UUID(run_id))
            if not run:
                raise HTTPException(status_code=404, detail="Run not found")
            
            # Get all artifacts
            artifacts = await manager.get_artifacts(UUID(run_id))
            
            if not artifacts:
                raise HTTPException(status_code=404, detail="No documents found for this run")
            
            # Create ZIP file in memory
            zip_buffer = BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add README with run metadata
                # Extract metadata safely
                metadata = run.metadata if hasattr(run, 'metadata') and isinstance(run.metadata, dict) else {}
                config = run.config if hasattr(run, 'config') and isinstance(run.config, dict) else {}
                
                readme_content = f"""# Documentation Run: {metadata.get('name', 'Unknown')}

{metadata.get('description', 'No description')}

## Run Information
- Run ID: {run.id}
- Status: {run.status}
- Started: {run.started_at if run.started_at else 'N/A'}
- Completed: {run.completed_at if run.completed_at else 'N/A'}
- Duration: {int((run.completed_at - run.started_at).total_seconds()) if run.completed_at and run.started_at else 0} seconds
- Total Documents: {run.total_artifacts}

## Configuration
- Source: {run.repo_id or 'N/A'}
- Format: {config.get('output_format', 'markdown')}
- Response Size: {config.get('response_size', 'Default')}
- Tier: {config.get('tier', 'Auto')}
- Passes: {run.total_passes}
- Questions per Pass: {config.get('questions_per_pass', 0)}

## Generated Documents
{len(artifacts)} documents included in this archive.
"""
                zip_file.writestr("README.md", readme_content)
                
                # Add each artifact
                for idx, artifact in enumerate(artifacts, 1):
                    filename = f"{idx}_{artifact.artifact_type}_{artifact.title.replace(' ', '_').replace('/', '_')}.md"
                    zip_file.writestr(filename, artifact.content)
            
            # Prepare response
            zip_buffer.seek(0)
            
            return StreamingResponse(
                zip_buffer,
                media_type="application/zip",
                headers={
                    "Content-Disposition": f"attachment; filename=run_{str(run.id)[:8]}_documents.zip"
                }
            )
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to export run as ZIP: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/runs/{run_id}")
async def delete_documentation_run(run_id: str):
    """
    Delete a documentation run and all its generated documents.
    
    Warning: This action is irreversible!
    """
    try:
        db = get_database()
        async with db.session() as session:
            manager = DocumentationRunManager(session)
            
            # Check if run exists
            run = await manager.get_run(UUID(run_id))
            if not run:
                raise HTTPException(status_code=404, detail="Run not found")
            
            # Delete the run
            await manager.delete_run(UUID(run_id))
            
            return {
                "message": f"Successfully deleted run '{run['name']}' and all its documents",
                "run_id": run_id
            }
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete run: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

