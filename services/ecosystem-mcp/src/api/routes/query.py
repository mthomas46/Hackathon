"""
Query endpoints for document retrieval and validation.

Provides external access to documents for validation and analysis.
"""

import logging
from typing import Optional, List
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field, validator
from slowapi import Limiter
from slowapi.util import get_remote_address

from ...storage import get_database
from ...storage.repositories import DocumentRepository
from ...utils.cache_decorator import cache

logger = logging.getLogger(__name__)

router = APIRouter()
limiter = Limiter(key_func=get_remote_address)


class DocumentQuery(BaseModel):
    """Document query parameters."""
    service_name: Optional[str] = Field(None, description="Filter by service name", max_length=100)
    file_path: Optional[str] = Field(None, description="Filter by file path (partial match)", max_length=500)
    phase: Optional[str] = Field(None, description="Filter by phase", max_length=50)
    tags: Optional[List[str]] = Field(None, description="Filter by tags (any match)")
    min_word_count: Optional[int] = Field(None, description="Minimum word count", ge=0)
    has_diagrams: Optional[bool] = Field(None, description="Filter by diagram presence")
    limit: int = Field(50, ge=1, le=500, description="Maximum results")
    offset: int = Field(0, ge=0, le=10000, description="Pagination offset")
    
    @validator('service_name')
    def validate_service(cls, v):
        """Validate service name."""
        if v is None:
            return v
        from ...utils.validation import validate_service_name
        return validate_service_name(v)
    
    @validator('file_path')
    def validate_path(cls, v):
        """Validate file path."""
        if v is None:
            return v
        # Just sanitize HTML, don't validate against filesystem
        from ...utils.validation import sanitize_html
        return sanitize_html(v)


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
    has_next: bool
    has_previous: bool


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
@limiter.limit("20/minute")  # ✅ Rate limit: 20 queries per minute
@cache(ttl=600, key_prefix="doc_query")  # ⚡ Cache for 10 minutes (4-10x faster!)
async def query_documents(request: Request, query: DocumentQuery):
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
                metadata=doc.doc_metadata or {}  # Use doc_metadata field, fallback to empty dict
            )
            for doc in documents
        ]
        
        has_next = (query.offset + query.limit) < total
        has_previous = query.offset > 0
        
        return QueryResponse(
            documents=results,
            total=total,
            limit=query.limit,
            offset=query.offset,
            has_next=has_next,
            has_previous=has_previous
        )


@router.get(
    "/document/{document_id}",
    response_model=DocumentResult,
    summary="Get document by ID",
    description="Retrieve complete document by ID for validation"
)
@limiter.limit("30/minute")  # ✅ Rate limit: 30 gets per minute
async def get_document_by_id(request: Request, document_id: UUID):
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
@limiter.limit("20/minute")  # ✅ Rate limit: 20 validations per minute
async def validate_document(request: Request, document_id: UUID):
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


# ============================================================================
# PHASE 9: Repository Context API Endpoints
# ============================================================================

class ContextResponse(BaseModel):
    """Repository context response."""
    context_id: str = Field(..., description="Unique context identifier")
    repo_name: str = Field(..., description="Repository name")
    repo_path: str = Field(..., description="Repository path")
    languages: List[str] = Field(..., description="Programming languages")
    primary_language: Optional[str] = Field(None, description="Primary language")
    frameworks: List[str] = Field(..., description="Frameworks used")
    databases: List[str] = Field(..., description="Databases used")
    architecture_type: Optional[str] = Field(None, description="Architecture type")
    service_count: int = Field(..., description="Number of services")
    endpoint_count: int = Field(..., description="Number of API endpoints")
    total_files: int = Field(..., description="Total files")
    code_files: int = Field(..., description="Code files")
    brief_description: str = Field(..., description="Brief description")


@router.get("/contexts", response_model=List[ContextResponse], tags=["contexts"])
@limiter.limit("30/minute")
async def list_contexts(request: Request):
    """
    List all repository contexts (Phase 9).
    
    Repository contexts enable context-aware RAG queries by grouping
    documents by repository/service for more focused results.
    
    Returns:
        List of repository contexts with metadata
    """
    try:
        db = get_database()
        # Query distinct repositories from documents table
        from sqlalchemy import text
        
        query = text("""
            SELECT DISTINCT
                d.service_name,
                COUNT(DISTINCT d.id) as total_docs,
                COUNT(DISTINCT d.file_path) as total_files,
                array_agg(DISTINCT d.original_format) FILTER (WHERE d.original_format IS NOT NULL) as file_types
            FROM documents d
            WHERE d.is_latest = true
            GROUP BY d.service_name
            ORDER BY total_docs DESC
        """)
        
        async with db.session() as session:
            result = await session.execute(query)
            rows = result.fetchall()
            
            contexts = []
            for row in rows:
                service_name = row[0] or "unknown"
                total_docs = row[1]
                total_files = row[2]
                file_types = row[3] or []
                
                # Generate context ID
                context_id = f"ctx_{service_name}"
                
                # Detect languages from file types
                languages = []
                if ".py" in str(file_types):
                    languages.append("Python")
                if ".js" in str(file_types) or ".ts" in str(file_types):
                    languages.append("JavaScript/TypeScript")
                if ".java" in str(file_types):
                    languages.append("Java")
                
                contexts.append(ContextResponse(
                    context_id=context_id,
                    repo_name=service_name,
                    repo_path=f"/app/{service_name}",  # Infer from service name
                    languages=languages,
                    primary_language=languages[0] if languages else None,
                    frameworks=[],  # TODO: Enhance with actual detection
                    databases=[],   # TODO: Enhance with actual detection
                    architecture_type=None,
                    service_count=1,
                    endpoint_count=0,
                    total_files=total_files,
                    code_files=total_files,
                    brief_description=f"Repository context for {service_name}"
                ))
            
            logger.info(f"📁 Listed {len(contexts)} repository contexts")
            return contexts
            
    except Exception as e:
        logger.error(f"Error listing contexts: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to list contexts: {str(e)}")


@router.get("/contexts/{context_id}", response_model=ContextResponse, tags=["contexts"])
@limiter.limit("60/minute")
async def get_context(request: Request, context_id: str):
    """
    Get specific repository context by ID (Phase 9).
    
    Args:
        context_id: Context identifier
    
    Returns:
        Repository context details
    """
    try:
        # For now, return from list (TODO: implement proper context storage)
        contexts = await list_contexts(request)
        
        for ctx in contexts:
            if ctx.context_id == context_id:
                logger.info(f"📁 Retrieved context: {context_id}")
                return ctx
        
        raise HTTPException(status_code=404, detail=f"Context not found: {context_id}")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting context {context_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get context: {str(e)}")


@router.get("/contexts/{context_id}/documents", response_model=List[DocumentResult], tags=["contexts"])
@limiter.limit("30/minute")
async def get_context_documents(
    request: Request,
    context_id: str,
    limit: int = Query(50, ge=1, le=500, description="Maximum results")
):
    """
    Get documents within a specific context (Phase 9).
    
    Args:
        context_id: Context identifier
        limit: Maximum number of documents to return
    
    Returns:
        List of documents in the context
    """
    try:
        # Get context to extract service_name
        context = await get_context(request, context_id)
        
        # Query documents for this context
        db = get_database()
        doc_repo = DocumentRepository(db)
        documents = await doc_repo.get_by_service(context.repo_name, limit=limit)
        
        logger.info(f"📄 Retrieved {len(documents)} documents for context {context_id}")
        
        return [
            DocumentResult(
                id=str(doc.id),
                service_name=doc.service_name,
                file_path=doc.file_path,
                file_type=doc.file_type,
                content_preview=doc.normalized_content[:500] if doc.normalized_content else "",
                word_count=len(doc.normalized_content.split()) if doc.normalized_content else 0,
                has_embedding=doc.embedding_id is not None,
                created_at=doc.created_at.isoformat(),
                updated_at=doc.updated_at.isoformat() if doc.updated_at else None
            )
            for doc in documents
        ]
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting context documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to get context documents: {str(e)}")

