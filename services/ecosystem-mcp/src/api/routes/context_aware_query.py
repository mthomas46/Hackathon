"""
Context-Aware Query API (Week 3, Day 2)

API endpoints for context-aware RAG queries:
- Query with repository context
- Query with hierarchical filtering
- Query with technology stack filtering
- Get available contexts
- Get context summaries
"""

import logging
from typing import Optional, List
from datetime import timedelta

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from ...services.rag.context_aware_rag import get_context_aware_rag
from ...services.analysis.hierarchical_context_manager import ContextLevel

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class ContextAwareQueryRequest(BaseModel):
    """Request for context-aware RAG query."""
    question: str = Field(
        ...,
        description="Question to answer",
        min_length=3,
        max_length=1000
    )
    repo_id: Optional[str] = Field(
        None,
        description="Repository ID to filter by"
    )
    context_id: Optional[str] = Field(
        None,
        description="Hierarchical context ID for filtering"
    )
    context_level: Optional[str] = Field(
        None,
        description="Context level: ROOT, SERVICE, MODULE, or COMPONENT"
    )
    service_filter: Optional[str] = Field(
        None,
        description="Service name to filter by"
    )
    tech_filter: Optional[List[str]] = Field(
        None,
        description="Technology stack to filter by (e.g., ['python', 'fastapi'])"
    )
    language_filter: Optional[str] = Field(
        None,
        description="Programming language to filter by"
    )
    time_range_hours: Optional[int] = Field(
        None,
        ge=1,
        le=8760,  # Max 1 year
        description="Only include documents from last N hours"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum results to return"
    )


class ContextInfo(BaseModel):
    """Context information."""
    name: Optional[str]
    level: Optional[str]
    full_path: Optional[str]
    file_count: Optional[int]


class ResultMetadata(BaseModel):
    """Result metadata."""
    filters_applied: bool
    context_used: bool


class QueryResult(BaseModel):
    """Single query result."""
    content: str
    metadata: dict
    distance: Optional[float]
    relevance_score: float
    vector_score: float
    keyword_score: float
    context: Optional[dict] = None


class ContextAwareQueryResponse(BaseModel):
    """Response for context-aware query."""
    query: str
    answer: Optional[str] = None  # ✨ PHASE 5: NEW - LLM generated answer
    filters: dict
    context_info: Optional[ContextInfo]
    results: List[QueryResult]
    total: int
    metadata: dict  # Changed from ResultMetadata to dict for flexibility


class ContextSummary(BaseModel):
    """Context summary."""
    id: str
    name: str
    level: str
    full_path: str
    parent_id: Optional[str]
    children_count: int
    file_count: int
    lines_of_code: int
    technologies: List[str]
    primary_language: Optional[str]
    services: List[str]
    description: str


# ============================================================================
# Context-Aware Query Endpoints
# ============================================================================

@router.post(
    "/query/context-aware",
    response_model=ContextAwareQueryResponse,
    summary="Context-aware RAG query",
    description="Query documents with hierarchical context filtering"
)
async def context_aware_query(request: ContextAwareQueryRequest):
    """
    Execute context-aware RAG query.
    
    Filters documents by:
    - Repository ID
    - Hierarchical context (ROOT/SERVICE/MODULE/COMPONENT)
    - Service name
    - Technology stack
    - Programming language
    - Time range
    
    Example:
    ```json
    {
        "question": "How does authentication work?",
        "repo_id": "my-api",
        "context_id": "service-auth",
        "tech_filter": ["python", "fastapi"],
        "limit": 10
    }
    ```
    """
    try:
        logger.info(f"🔍 Context-aware query: {request.question[:50]}...")
        
        # Get RAG service
        rag = get_context_aware_rag()
        
        # Parse context level if provided
        context_level = None
        if request.context_level:
            try:
                context_level = ContextLevel[request.context_level.upper()]
            except KeyError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid context_level: {request.context_level}. "
                           f"Must be one of: ROOT, SERVICE, MODULE, COMPONENT"
                )
        
        # Parse time range
        time_range = None
        if request.time_range_hours:
            time_range = timedelta(hours=request.time_range_hours)
        
        # Execute query
        result = await rag.query_with_context(
            query=request.question,
            repo_id=request.repo_id,
            context_id=request.context_id,
            context_level=context_level,
            service_filter=request.service_filter,
            tech_filter=request.tech_filter,
            language_filter=request.language_filter,
            time_range=time_range,
            limit=request.limit
        )
        
        logger.info(f"✅ Found {result['total']} results")
        
        return ContextAwareQueryResponse(**result)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Context-aware query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Query failed: {str(e)}"
        )


@router.get(
    "/query/contexts/{repo_id}",
    response_model=List[dict],
    summary="Get repository contexts",
    description="Get all available contexts for a repository"
)
async def get_repository_contexts(repo_id: str):
    """
    Get all available contexts for a repository.
    
    Returns hierarchical contexts at all levels:
    - ROOT: Repository root
    - SERVICE: Service/microservice level
    - MODULE: Package/directory level
    - COMPONENT: File/class level
    """
    try:
        logger.info(f"📚 Fetching contexts for repo: {repo_id}")
        
        rag = get_context_aware_rag()
        contexts = await rag.get_repository_contexts(repo_id)
        
        # Convert to dict
        context_dicts = [ctx.to_dict() for ctx in contexts]
        
        logger.info(f"✅ Found {len(context_dicts)} contexts")
        
        return context_dicts
    
    except Exception as e:
        logger.error(f"❌ Failed to get contexts: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get contexts: {str(e)}"
        )


@router.get(
    "/query/context/{context_id}/summary",
    response_model=ContextSummary,
    summary="Get context summary",
    description="Get detailed summary of a specific context"
)
async def get_context_summary(context_id: str):
    """
    Get detailed summary of a specific context.
    
    Includes:
    - Context metadata
    - File counts and LOC
    - Technology stack
    - Child contexts
    - Parent context
    """
    try:
        logger.info(f"📊 Fetching summary for context: {context_id}")
        
        rag = get_context_aware_rag()
        summary = await rag.get_context_summary(context_id)
        
        if not summary:
            raise HTTPException(
                status_code=404,
                detail=f"Context not found: {context_id}"
            )
        
        logger.info(f"✅ Context summary retrieved")
        
        return ContextSummary(**summary)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to get context summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get context summary: {str(e)}"
        )


@router.get(
    "/query/context-levels",
    summary="Get available context levels",
    description="Get list of available context hierarchy levels"
)
async def get_context_levels():
    """Get available context levels."""
    return {
        "levels": [
            {
                "name": "ROOT",
                "value": 0,
                "description": "Repository root level"
            },
            {
                "name": "SERVICE",
                "value": 1,
                "description": "Service/microservice level"
            },
            {
                "name": "MODULE",
                "value": 2,
                "description": "Package/directory level"
            },
            {
                "name": "COMPONENT",
                "value": 3,
                "description": "File/class level"
            }
        ]
    }


@router.post(
    "/query/context-aware/batch",
    summary="Batch context-aware queries",
    description="Execute multiple context-aware queries in batch"
)
async def batch_context_aware_queries(
    queries: List[ContextAwareQueryRequest]
):
    """
    Execute multiple context-aware queries in batch.
    
    Useful for:
    - Comparing results across different contexts
    - Multi-context analysis
    - Batch processing
    """
    try:
        logger.info(f"📦 Batch query: {len(queries)} queries")
        
        rag = get_context_aware_rag()
        results = []
        
        for idx, request in enumerate(queries):
            try:
                # Parse context level
                context_level = None
                if request.context_level:
                    context_level = ContextLevel[request.context_level.upper()]
                
                # Parse time range
                time_range = None
                if request.time_range_hours:
                    time_range = timedelta(hours=request.time_range_hours)
                
                # Execute query
                result = await rag.query_with_context(
                    query=request.question,
                    repo_id=request.repo_id,
                    context_id=request.context_id,
                    context_level=context_level,
                    service_filter=request.service_filter,
                    tech_filter=request.tech_filter,
                    language_filter=request.language_filter,
                    time_range=time_range,
                    limit=request.limit
                )
                
                results.append({
                    "index": idx,
                    "success": True,
                    "result": result
                })
                
            except Exception as e:
                logger.error(f"❌ Query {idx} failed: {e}")
                results.append({
                    "index": idx,
                    "success": False,
                    "error": str(e)
                })
        
        successful = sum(1 for r in results if r["success"])
        logger.info(f"✅ Batch complete: {successful}/{len(queries)} successful")
        
        return {
            "total": len(queries),
            "successful": successful,
            "failed": len(queries) - successful,
            "results": results
        }
    
    except Exception as e:
        logger.error(f"❌ Batch query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Batch query failed: {str(e)}"
        )

