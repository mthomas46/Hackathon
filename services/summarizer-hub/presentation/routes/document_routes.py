"""Document API routes.

This module contains FastAPI routes for document operations.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional

from ..models.simulation_models import SummarizationRequest
from ...application.handlers.document_handler import DocumentHandler

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])
handler = DocumentHandler()


@router.post("/")
async def create_document(request: SummarizationRequest) -> dict:
    """Create a new document."""
    try:
        result = await handler.create_document(
            content=request.content,
            summary_type=request.summary_type,
            max_length=request.max_length,
            include_metadata=request.include_metadata,
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{document_id}")
async def get_document(document_id: str) -> dict:
    """Get a document by ID."""
    try:
        result = await handler.get_document(document_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/")
async def list_documents(
    limit: int = Query(50, description="Maximum number of documents to return"),
    offset: int = Query(0, description="Number of documents to skip"),
) -> dict:
    """List documents."""
    try:
        result = await handler.list_documents(limit=limit, offset=offset)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{document_id}")
async def update_document(document_id: str, request: SummarizationRequest) -> dict:
    """Update a document."""
    try:
        result = await handler.update_document(
            document_id=document_id,
            content=request.content,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{document_id}")
async def delete_document(document_id: str) -> dict:
    """Delete a document."""
    try:
        result = await handler.delete_document(document_id)
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
