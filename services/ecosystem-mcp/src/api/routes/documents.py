"""
Document management endpoints.

Provides access to stored documents.
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Depends, Body
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
                    word_count=len(doc.normalized_content.split()) if doc.normalized_content else 0
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
            word_count=len(doc.normalized_content.split()) if doc.normalized_content else 0
        )


class BulkDeleteRequest(BaseModel):
    """Bulk delete request."""
    document_ids: List[UUID] = Field(..., description="List of document IDs to delete")


class BulkDeleteResponse(BaseModel):
    """Bulk delete response."""
    deleted: int
    success: bool
    message: str


@router.post(
    "/bulk-delete",
    response_model=BulkDeleteResponse,
    summary="Bulk delete documents",
    description="Delete multiple documents in a single transaction (Phase 3.2)"
)
async def bulk_delete_documents(
    request: BulkDeleteRequest = Body(...)
):
    """
    Bulk delete documents using Phase 3.2 bulk operations.
    
    Features:
    - Single database transaction
    - 10-50x faster than individual deletes
    - Atomic operation (all or nothing)
    
    Args:
        request: List of document IDs to delete
    
    Returns:
        Number of documents deleted
    """
    if not request.document_ids:
        raise HTTPException(status_code=400, detail="No document IDs provided")
    
    if len(request.document_ids) > 1000:
        raise HTTPException(
            status_code=400,
            detail="Too many documents. Maximum 1000 per request."
        )
    
    db = get_database()
    
    async with db.session() as session:
        repo = DocumentRepository(session)
        
        try:
            # Use Phase 3.2 bulk_delete method
            deleted_count = await repo.bulk_delete(request.document_ids)
            await session.commit()
            
            logger.info(f"Bulk deleted {deleted_count} documents")
            
            return BulkDeleteResponse(
                deleted=deleted_count,
                success=True,
                message=f"Successfully deleted {deleted_count} documents"
            )
        
        except Exception as e:
            await session.rollback()
            logger.error(f"Bulk delete failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Bulk delete failed: {str(e)}"
            )


class BulkUpdateRequest(BaseModel):
    """Bulk update request."""
    document_ids: List[UUID] = Field(..., description="List of document IDs to update")
    metadata: dict = Field(..., description="Metadata fields to update")


class BulkUpdateResponse(BaseModel):
    """Bulk update response."""
    updated: int
    success: bool
    message: str


@router.post(
    "/bulk-update",
    response_model=BulkUpdateResponse,
    summary="Bulk update document metadata",
    description="Update metadata for multiple documents in a single transaction (Phase 3.2)"
)
async def bulk_update_documents(
    request: BulkUpdateRequest = Body(...)
):
    """
    Bulk update document metadata using Phase 3.2 bulk operations.
    
    Features:
    - Single UPDATE query (10-50x faster)
    - Atomic operation
    - Flexible metadata updates
    
    Args:
        request: Document IDs and metadata to update
    
    Returns:
        Number of documents updated
    """
    if not request.document_ids:
        raise HTTPException(status_code=400, detail="No document IDs provided")
    
    if not request.metadata:
        raise HTTPException(status_code=400, detail="No metadata provided")
    
    if len(request.document_ids) > 1000:
        raise HTTPException(
            status_code=400,
            detail="Too many documents. Maximum 1000 per request."
        )
    
    db = get_database()
    
    async with db.session() as session:
        repo = DocumentRepository(session)
        
        try:
            # Use Phase 3.2 bulk_update_metadata method
            updated_count = await repo.bulk_update_metadata(
                request.document_ids,
                request.metadata
            )
            await session.commit()
            
            logger.info(
                f"Bulk updated {updated_count} documents with metadata: {request.metadata}"
            )
            
            return BulkUpdateResponse(
                updated=updated_count,
                success=True,
                message=f"Successfully updated {updated_count} documents"
            )
        
        except Exception as e:
            await session.rollback()
            logger.error(f"Bulk update failed: {e}", exc_info=True)
            raise HTTPException(
                status_code=500,
                detail=f"Bulk update failed: {str(e)}"
            )

