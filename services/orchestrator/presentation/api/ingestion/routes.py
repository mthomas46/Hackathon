"""API Routes for Document Ingestion

Provides endpoints for:
- Starting document ingestion workflows
- Monitoring ingestion status
- Listing ingestion history
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional

from .dtos import (
    IngestRequest, IngestionStatusResponse, IngestionListResponse,
    DocumentMetadataResponse
)
from ....main import container

router = APIRouter()


@router.post("/ingest", response_model=dict)
async def start_ingestion(request: IngestRequest):
    """Start a document ingestion workflow."""
    try:
        from ....application.ingestion.commands import StartIngestionCommand
        command = StartIngestionCommand(
            source_url=request.source_url,
            source_type=request.source_type,
            parameters=request.parameters or {}
        )
        result = await container.start_ingestion_use_case.execute(command)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start ingestion: {str(e)}")


@router.get("/ingest/{ingestion_id}", response_model=IngestionStatusResponse)
async def get_ingestion_status(ingestion_id: str):
    """Get the status of a specific ingestion."""
    try:
        from ....application.ingestion.queries import GetIngestionStatusQuery
        query = GetIngestionStatusQuery(ingestion_id=ingestion_id)
        result = await container.get_ingestion_status_use_case.execute(query)
        if not result:
            raise HTTPException(status_code=404, detail="Ingestion not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get ingestion status: {str(e)}")


@router.get("/ingest", response_model=IngestionListResponse)
async def list_ingestions(
    status: Optional[str] = None,
    source_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """List ingestion workflows with optional filters."""
    try:
        from ....application.ingestion.queries import ListIngestionsQuery
        query = ListIngestionsQuery(
            status_filter=status,
            source_type_filter=source_type,
            limit=limit,
            offset=offset
        )
        result = await container.list_ingestions_use_case.execute(query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list ingestions: {str(e)}")


@router.get("/documents/{document_id}", response_model=DocumentMetadataResponse)
async def get_document_metadata(document_id: str):
    """Get metadata for a specific ingested document."""
    try:
        # This would typically use a dedicated query, but for now we'll use placeholder
        # In a full implementation, this would query the document store
        raise HTTPException(status_code=501, detail="Document metadata retrieval not yet implemented")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document metadata: {str(e)}")


@router.get("/sources", response_model=dict)
async def list_ingestion_sources():
    """List available ingestion sources and their capabilities."""
    try:
        # This would typically query available ingestion adapters/capabilities
        return {
            "sources": [
                {
                    "type": "github",
                    "name": "GitHub Repository",
                    "description": "Ingest code, issues, and pull requests from GitHub",
                    "supported_formats": ["markdown", "code", "issues", "pull_requests"]
                },
                {
                    "type": "gitlab",
                    "name": "GitLab Repository",
                    "description": "Ingest code, issues, and merge requests from GitLab",
                    "supported_formats": ["markdown", "code", "issues", "merge_requests"]
                },
                {
                    "type": "jira",
                    "name": "Jira Issues",
                    "description": "Ingest issues and project data from Jira",
                    "supported_formats": ["issues", "projects", "epics"]
                },
                {
                    "type": "confluence",
                    "name": "Confluence Pages",
                    "description": "Ingest documentation and knowledge base from Confluence",
                    "supported_formats": ["pages", "blogs", "spaces"]
                }
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list ingestion sources: {str(e)}")


@router.delete("/ingest/{ingestion_id}", response_model=dict)
async def cancel_ingestion(ingestion_id: str):
    """Cancel a running ingestion workflow."""
    try:
        # This would use a CancelIngestionUseCase in a full implementation
        raise HTTPException(status_code=501, detail="Ingestion cancellation not yet implemented")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cancel ingestion: {str(e)}")
