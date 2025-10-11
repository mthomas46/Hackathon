"""
Query endpoints for document retrieval and validation.

Provides external access to documents for validation and analysis.
"""

import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ...storage import get_database
from ...storage.repositories import DocumentRepository

logger = logging.getLogger(__name__)

router = APIRouter()


class DocumentQuery(BaseModel):
    """Document query parameters."""
    service_name: Optional[str] = Field(None, description="Filter by service name")
    file_path: Optional[str] = Field(None, description="Filter by file path (partial match)")
    phase: Optional[str] = Field(None, description="Filter by phase")
    tags: Optional[List[str]] = Field(None, description="Filter by tags (any match)")
    min_word_count: Optional[int] = Field(None, description="Minimum word count")
    has_diagrams: Optional[bool] = Field(None, description="Filter by diagram presence")
    limit: int = Field(50, ge=1, le=500, description="Maximum results")
    offset: int = Field(0, ge=0, description="Pagination offset")


class DocumentResult(BaseModel):
    """Single document result."""
    id: str
    service_name: str
    file_path: str
    original_format: str
    normalized_content: str
    content_hash: str
    created_at: str
    updated_at: str
    is_latest: bool
    metadata: dict


class QueryResponse(BaseModel):
    """Query response with results."""
    documents: List[DocumentResult]
    total: int
    limit: int
    offset: int


class DocumentValidation(BaseModel):
    """Document validation result."""
    document_id: str
    is_valid: bool
    issues: List[str]
    content_length: int
    has_metadata: bool
    has_embedding: bool


@router.post(
    "/query",
    response_model=QueryResponse,
    summary="Query documents",
    description="Query documents with filters for external validation"
)
async def query_documents(query: DocumentQuery):
    """
    Query documents from database.
    
    Supports filtering by:
    - Service name
    - File path (partial match)
    - Phase
    - Tags
    - Word count
    - Diagram presence
    
    Returns:
        Matching documents with full content and metadata
    """
    db = get_database()
    
    async with db.session() as session:
        repo = DocumentRepository(session)
        
        # Build query based on filters
        # For now, simple service filter
        # TODO: Implement advanced filtering in repository
        
        if query.service_name:
            documents = await repo.get_by_service(
                query.service_name,
                limit=query.limit,
                offset=query.offset
            )
            total = await repo.count_by_service(query.service_name)
        else:
            documents = await repo.get_all(
                limit=query.limit,
                offset=query.offset
            )
            total = await repo.count()
        
        results = [
            DocumentResult(
                id=str(doc.id),
                service_name=doc.service_name,
                file_path=doc.file_path,
                original_format=doc.original_format,
                normalized_content=doc.normalized_content,
                content_hash=doc.content_hash,
                created_at=doc.created_at.isoformat(),
                updated_at=doc.updated_at.isoformat(),
                is_latest=doc.is_latest,
                metadata=doc.metadata
            )
            for doc in documents
        ]
        
        return QueryResponse(
            documents=results,
            total=total,
            limit=query.limit,
            offset=query.offset
        )


@router.get(
    "/document/{document_id}",
    response_model=DocumentResult,
    summary="Get document by ID",
    description="Retrieve complete document by ID for validation"
)
async def get_document_by_id(document_id: UUID):
    """
    Get complete document by ID.
    
    Args:
        document_id: Document UUID
    
    Returns:
        Complete document with content and metadata
    """
    db = get_database()
    
    async with db.session() as session:
        repo = DocumentRepository(session)
        doc = await repo.get_by_id(document_id)
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return DocumentResult(
            id=str(doc.id),
            service_name=doc.service_name,
            file_path=doc.file_path,
            original_format=doc.original_format,
            normalized_content=doc.normalized_content,
            content_hash=doc.content_hash,
            created_at=doc.created_at.isoformat(),
            updated_at=doc.updated_at.isoformat(),
            is_latest=doc.is_latest,
            metadata=doc.metadata
        )


@router.post(
    "/validate/{document_id}",
    response_model=DocumentValidation,
    summary="Validate document",
    description="Validate document completeness and integrity"
)
async def validate_document(document_id: UUID):
    """
    Validate document completeness.
    
    Checks:
    - Document exists
    - Has content
    - Has metadata
    - Has embedding (if expected)
    - Content hash matches
    
    Args:
        document_id: Document UUID
    
    Returns:
        Validation result with issues
    """
    db = get_database()
    
    async with db.session() as session:
        repo = DocumentRepository(session)
        doc = await repo.get_by_id(document_id)
        
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        issues = []
        
        # Check content
        if not doc.normalized_content:
            issues.append("Missing normalized content")
        
        # Check metadata
        has_metadata = bool(doc.metadata)
        if not has_metadata:
            issues.append("Missing metadata")
        
        # Check embedding
        has_embedding = doc.embedding_id is not None
        if not has_embedding:
            issues.append("Missing embedding")
        
        # Verify content hash
        import hashlib
        actual_hash = hashlib.sha256(
            doc.original_content.encode()
        ).hexdigest()
        if actual_hash != doc.content_hash:
            issues.append(f"Content hash mismatch: expected {doc.content_hash}, got {actual_hash}")
        
        is_valid = len(issues) == 0
        
        return DocumentValidation(
            document_id=str(document_id),
            is_valid=is_valid,
            issues=issues,
            content_length=len(doc.normalized_content),
            has_metadata=has_metadata,
            has_embedding=has_embedding
        )


@router.get(
    "/export",
    summary="Export documents",
    description="Export documents in various formats for external analysis"
)
async def export_documents(
    service_name: Optional[str] = Query(None),
    format: str = Query("json", regex="^(json|csv|jsonl)$"),
    limit: int = Query(100, ge=1, le=1000)
):
    """
    Export documents for external analysis.
    
    Formats:
    - json: JSON array
    - csv: CSV format
    - jsonl: JSON lines (one per line)
    
    Args:
        service_name: Optional service filter
        format: Export format
        limit: Maximum documents
    
    Returns:
        Documents in requested format
    """
    db = get_database()
    
    async with db.session() as session:
        repo = DocumentRepository(session)
        
        if service_name:
            documents = await repo.get_by_service(service_name, limit=limit)
        else:
            documents = await repo.get_all(limit=limit)
        
        if format == "json":
            return {
                "documents": [
                    {
                        "id": str(doc.id),
                        "service_name": doc.service_name,
                        "file_path": doc.file_path,
                        "original_format": doc.original_format,
                        "content_hash": doc.content_hash,
                        "created_at": doc.created_at.isoformat(),
                        "metadata": doc.metadata
                    }
                    for doc in documents
                ]
            }
        elif format == "jsonl":
            import json
            lines = []
            for doc in documents:
                lines.append(json.dumps({
                    "id": str(doc.id),
                    "service_name": doc.service_name,
                    "file_path": doc.file_path,
                    "content_hash": doc.content_hash
                }))
            return {"content": "\n".join(lines)}
        elif format == "csv":
            # Simple CSV implementation
            import io
            import csv
            
            output = io.StringIO()
            writer = csv.writer(output)
            writer.writerow(["id", "service_name", "file_path", "created_at"])
            
            for doc in documents:
                writer.writerow([
                    str(doc.id),
                    doc.service_name,
                    doc.file_path,
                    doc.created_at.isoformat()
                ])
            
            return {"content": output.getvalue()}

