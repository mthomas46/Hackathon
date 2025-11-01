"""
Dynamic Temporal RAG API Routes (Phase 6)

Endpoints for dynamic timeline construction and temporal Q&A.
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from typing import Optional
import json

from ...services.dynamic_rag import get_orchestrator

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/dynamic-rag", tags=["dynamic-rag"])


@router.post("/query")
async def dynamic_temporal_query(
    query: str = Query(..., description="Natural language query"),
    service_name: Optional[str] = Query(None, description="Optional service filter"),
    citation_format: str = Query("markdown", description="Citation format (markdown/html/plain)"),
    use_cache: bool = Query(True, description="Use cached timelines if available"),
    use_enhancements: bool = Query(True, description="Enable Phase 7 enhancements (hybrid search, query rewriting)")  # ✨ PHASE 8
):
    """
    Execute a dynamic temporal RAG query.
    
    Automatically:
    1. Extracts topics from your query
    2. Finds relevant documents
    3. Constructs a temporary timeline
    4. Synthesizes an answer with temporal context
    5. Formats citations
    
    Returns:
        Complete response with answer, timeline, and citations
    """
    try:
        logger.info(f"Dynamic RAG query: {query[:100]}...")
        
        orchestrator = get_orchestrator()
        
        result = await orchestrator.execute(
            query=query,
            service_name=service_name,
            citation_format=citation_format,
            use_cache=use_cache,
            use_enhancements=use_enhancements  # ✨ PHASE 8
        )
        
        if not result.get('success'):
            raise HTTPException(
                status_code=404 if 'No relevant documents found' in result.get('error', '') else 500,
                detail=result.get('error', 'Query execution failed')
            )
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in dynamic RAG query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/query/stream")
async def dynamic_temporal_query_stream(
    query: str = Query(..., description="Natural language query"),
    service_name: Optional[str] = Query(None, description="Optional service filter"),
    citation_format: str = Query("markdown", description="Citation format")
):
    """
    Execute a dynamic temporal RAG query with streaming updates.
    
    Returns real-time progress updates as Server-Sent Events (SSE).
    
    Useful for showing progress in UI.
    """
    try:
        logger.info(f"Streaming dynamic RAG query: {query[:100]}...")
        
        orchestrator = get_orchestrator()
        
        async def event_generator():
            """Generate SSE events."""
            async for update in orchestrator.execute_streaming(
                query=query,
                service_name=service_name,
                citation_format=citation_format
            ):
                # Format as SSE
                yield f"data: {json.dumps(update)}\n\n"
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream"
        )
        
    except Exception as e:
        logger.error(f"Error in streaming dynamic RAG query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/capabilities")
async def get_capabilities():
    """
    Get capabilities of the dynamic temporal RAG system.
    
    Returns information about supported features.
    """
    return {
        'success': True,
        'capabilities': {
            'topic_extraction': {
                'supported_types': [
                    'endpoints',
                    'parameters',
                    'services',
                    'technologies',
                    'concepts',
                    'file_paths'
                ],
                'confidence_scoring': True
            },
            'document_search': {
                'strategies': ['semantic', 'keyword', 'path'],
                'max_documents': 50,
                'deduplication': True,
                'git_history_ranking': True
            },
            'timeline_construction': {
                'strategies': ['auto', 'monthly', 'quarterly', 'yearly', 'adaptive'],
                'cache_ttl_hours': 1,
                'confidence_levels': ['HIGH', 'MEDIUM', 'LOW', 'NONE']
            },
            'answer_synthesis': {
                'llm_based': True,
                'temporal_context': True,
                'source_attribution': True
            },
            'citation_formats': ['markdown', 'html', 'plain'],
            'streaming': True
        }
    }


@router.delete("/cache")
async def clear_cache():
    """
    Clear all cached dynamic timelines.
    
    Useful for forcing fresh timeline construction.
    """
    try:
        orchestrator = get_orchestrator()
        orchestrator.cleanup_expired_caches()
        
        return {
            'success': True,
            'message': 'Dynamic timeline cache cleared'
        }
        
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health_check():
    """
    Health check for dynamic RAG system.
    
    Returns status of all components.
    """
    try:
        orchestrator = get_orchestrator()
        
        return {
            'success': True,
            'status': 'healthy',
            'components': {
                'topic_extractor': 'operational',
                'document_finder': 'operational',
                'timeline_constructor': 'operational',
                'answer_synthesizer': 'operational',
                'citation_formatter': 'operational',
                'orchestrator': 'operational'
            }
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }

