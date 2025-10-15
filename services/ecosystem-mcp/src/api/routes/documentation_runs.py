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
from typing import List, Optional
from uuid import UUID
import zipfile
from io import BytesIO

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ...storage import get_database
from ...services.documentation.run_manager import DocumentationRunManager

logger = logging.getLogger(__name__)
router = APIRouter()


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
async def create_documentation_run(request: CreateRunRequest):
    """
    Create a new documentation generation run.
    
    This initializes a run but doesn't start generation.
    Use the dashboard or start the generation process to begin.
    """
    try:
        db = get_database()
        async with db.session() as session:
            manager = DocumentationRunManager(session)
            
            run_id = await manager.create_run(
                name=request.name,
                description=request.description,
                source_directory=request.source_directory,
                output_format=request.output_format,
                response_size=request.response_size,
                tier=request.tier,
                num_passes=request.num_passes,
                questions_per_pass=request.questions_per_pass,
                created_by=request.created_by,
                metadata=request.metadata
            )
            
            return CreateRunResponse(
                run_id=str(run_id),
                name=request.name,
                status="pending",
                message=f"Documentation run '{request.name}' created successfully"
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
            
            return [
                RunSummaryResponse(
                    id=str(run["id"]),
                    name=run["name"],
                    description=run["description"] or "",
                    status=run["status"],
                    source_directory=run["source_directory"],
                    started_at=run.get("started_at"),
                    completed_at=run.get("completed_at"),
                    duration_seconds=run.get("duration_seconds"),
                    total_documents=run.get("total_documents", 0),
                    successful_documents=run.get("successful_documents", 0),
                    failed_documents=run.get("failed_documents", 0),
                    created_by=run.get("created_by"),
                    created_at=run["created_at"]
                )
                for run in runs
            ]
    
    except Exception as e:
        logger.error(f"Failed to list documentation runs: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/runs/{run_id}", response_model=RunDetailResponse)
async def get_documentation_run(run_id: str):
    """Get detailed information about a specific run."""
    try:
        db = get_database()
        async with db.session() as session:
            manager = DocumentationRunManager(session)
            
            run = await manager.get_run(UUID(run_id))
            
            if not run:
                raise HTTPException(status_code=404, detail="Run not found")
            
            return RunDetailResponse(
                id=str(run["id"]),
                name=run["name"],
                description=run["description"] or "",
                status=run["status"],
                source_directory=run["source_directory"],
                output_format=run["output_format"],
                response_size=run.get("response_size"),
                tier=run.get("tier"),
                num_passes=run["num_passes"],
                questions_per_pass=run["questions_per_pass"],
                started_at=run.get("started_at"),
                completed_at=run.get("completed_at"),
                duration_seconds=run.get("duration_seconds"),
                total_documents=run.get("total_documents", 0),
                successful_documents=run.get("successful_documents", 0),
                failed_documents=run.get("failed_documents", 0),
                output_directory=run.get("output_directory"),
                created_by=run.get("created_by"),
                created_at=run["created_at"],
                updated_at=run["updated_at"]
            )
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid run ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get documentation run: {e}", exc_info=True)
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


@router.get("/runs/{run_id}/documents", response_model=List[GeneratedDocumentResponse])
async def get_run_documents(
    run_id: str,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
):
    """Get all documents generated by a specific run."""
    try:
        db = get_database()
        async with db.session() as session:
            manager = DocumentationRunManager(session)
            
            documents = await manager.get_run_documents(
                UUID(run_id),
                limit=limit,
                offset=offset
            )
            
            return [
                GeneratedDocumentResponse(
                    id=str(doc["id"]),
                    run_id=str(doc["run_id"]),
                    title=doc["title"],
                    filename=doc["filename"],
                    content_hash=doc["content_hash"],
                    content_size=doc["content_size"],
                    pass_number=doc.get("pass_number"),
                    question=doc.get("question"),
                    status=doc["status"],
                    generation_time_seconds=doc.get("generation_time_seconds"),
                    word_count=doc.get("word_count"),
                    created_at=doc["created_at"]
                )
                for doc in documents
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
            query = """
                SELECT id, title, filename, content, content_size, word_count, created_at
                FROM generated_documents
                WHERE id = :doc_id
            """
            
            from sqlalchemy import text
            result = await session.execute(text(query), {"doc_id": UUID(document_id)})
            row = result.fetchone()
            
            if not row:
                raise HTTPException(status_code=404, detail="Document not found")
            
            return DocumentContentResponse(
                id=str(row[0]),
                title=row[1],
                filename=row[2],
                content=row[3],
                content_size=row[4],
                word_count=row[5],
                created_at=row[6]
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
            
            # Get all documents
            documents = await manager.get_run_documents(UUID(run_id), limit=1000, offset=0)
            
            if not documents:
                raise HTTPException(status_code=404, detail="No documents found for this run")
            
            # Create ZIP file in memory
            zip_buffer = BytesIO()
            
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                # Add README with run metadata
                readme_content = f"""# Documentation Run: {run['name']}

{run['description']}

## Run Information
- Status: {run['status']}
- Started: {run.get('started_at', 'N/A')}
- Completed: {run.get('completed_at', 'N/A')}
- Duration: {run.get('duration_seconds', 0)} seconds
- Total Documents: {run.get('total_documents', 0)}
- Successful: {run.get('successful_documents', 0)}
- Failed: {run.get('failed_documents', 0)}

## Configuration
- Source: {run['source_directory']}
- Format: {run['output_format']}
- Response Size: {run.get('response_size', 'Default')}
- Tier: {run.get('tier', 'Auto')}
- Passes: {run['num_passes']}
- Questions per Pass: {run['questions_per_pass']}

## Generated Documents
{len(documents)} documents included in this archive.
"""
                zip_file.writestr("README.md", readme_content)
                
                # Add each document
                for doc in documents:
                    filename = doc["filename"]
                    content = doc["content"]
                    zip_file.writestr(filename, content)
            
            # Prepare response
            zip_buffer.seek(0)
            
            return StreamingResponse(
                zip_buffer,
                media_type="application/zip",
                headers={
                    "Content-Disposition": f"attachment; filename={run['name'].replace(' ', '_')}_documents.zip"
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

