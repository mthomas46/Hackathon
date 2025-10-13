"""
Document management endpoints.

Provides access to stored documents.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, validator, Field

from ...storage import get_database
from ...storage.repositories import DocumentRepository

logger = logging.getLogger(__name__)

router = APIRouter()


class DocumentResponse(BaseModel):
    """Document response model."""
    id: str
    service_name: str
    file_path: str
    original_format: str
    created_at: str
    updated_at: str
    is_latest: bool
    word_count: int


class DocumentListResponse(BaseModel):
    """Document list response."""
    documents: List[DocumentResponse]
    total: int
    limit: int
    offset: int
    has_next: bool
    has_previous: bool


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List documents",
    description="Query and list documents with filters"
)
async def list_documents(
    service: Optional[str] = Query(None, description="Filter by service name", max_length=100),
    limit: int = Query(50, ge=1, le=500, description="Maximum results"),
    offset: int = Query(0, ge=0, le=10000, description="Pagination offset")
):
    """
    List documents with optional filtering.
    
    Args:
        service: Optional service name filter
        limit: Maximum number of results
        offset: Pagination offset
    
    Returns:
        List of documents matching criteria
    """
    db = get_database()
    
    # Validate service name if provided
    if service:
        from ...utils.validation import validate_service_name
        try:
            service = validate_service_name(service)
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    
    async with db.session() as session:
        repo = DocumentRepository(session)
        
        if service:
            documents = await repo.get_by_service(service, limit=limit, offset=offset)
            total = await repo.count_by_service(service)
        else:
            documents = await repo.get_all(limit=limit, offset=offset)
            total = await repo.count()
        
        has_next = (offset + limit) < total
        has_previous = offset > 0
        
        return DocumentListResponse(
            documents=[
                DocumentResponse(
                    id=str(doc.id),
                    service_name=doc.service_name,
                    file_path=doc.file_path,
                    original_format=doc.original_format,
                    created_at=doc.created_at.isoformat(),
                    updated_at=doc.updated_at.isoformat(),
                    is_latest=doc.is_latest,
                    word_count=getattr(doc.metadata, "word_count", 0)
                )
                for doc in documents
            ],
            total=total,
            limit=limit,
            offset=offset,
            has_next=has_next,
            has_previous=has_previous
        )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document",
    description="Get document by ID"
)
async def get_document(document_id: UUID):
    """
    Get document by ID.
    
    Args:
        document_id: Document UUID
    
    Returns:
        Document details
    """
    db = get_database()
    
    async with db.session() as session:
        repo = DocumentRepository(session)
        doc = await repo.get_by_id(document_id)
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentResponse(
            id=str(doc.id),
            service_name=doc.service_name,
            file_path=doc.file_path,
            original_format=doc.original_format,
            created_at=doc.created_at.isoformat(),
            updated_at=doc.updated_at.isoformat(),
            is_latest=doc.is_latest,
            word_count=getattr(doc.metadata, "word_count", 0)
        )

