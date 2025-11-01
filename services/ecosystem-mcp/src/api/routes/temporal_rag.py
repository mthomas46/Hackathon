"""
Temporal RAG API (Phase 2.1)

API endpoints for temporal RAG queries:
- Time-travel queries (query as of a specific date)
- Evolution tracking (how information changed over time)
- Comparison queries (compare information between periods)
"""

import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query as QueryParam
from pydantic import BaseModel, Field, field_validator

from ...services.rag.temporal_rag_service import TemporalRAGService
from ...services.rag.context_aware_rag import get_context_aware_rag

logger = logging.getLogger(__name__)

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class TemporalQueryRequest(BaseModel):
    """
    Request for temporal RAG query.
    
    ✅ UTC STANDARDIZATION: Datetime fields are automatically converted to UTC.
    """
    question: str = Field(
        ...,
        description="Question to answer",
        min_length=3,
        max_length=1000
    )
    as_of_date: datetime = Field(
        ...,
        description="Point in time to query (ISO 8601 format)"
    )
    timeline_id: Optional[str] = Field(
        None,
        description="Specific timeline to use (optional)"
    )
    service_name: Optional[str] = Field(
        None,
        description="Service to query (if timeline_id not provided)"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum results to return"
    )
    use_enhancements: bool = Field(
        default=True,
        description="Enable Phase 4 enhancements (hybrid search, query rewriting, context optimization)"
    )
    
    @field_validator('as_of_date', mode='before')
    @classmethod
    def ensure_utc_date(cls, v):
        """
        Ensure datetime is UTC-aware.
        
        ✅ UTC STANDARDIZATION Phase 1
        """
        if isinstance(v, str):
            from ...utils.datetime_utils import parse_datetime_flexible
            return parse_datetime_flexible(v)
        from ...utils.datetime_utils import ensure_utc
        return ensure_utc(v)


class EvolutionQueryRequest(BaseModel):
    """Request for evolution tracking query."""
    topic: str = Field(
        ...,
        description="Topic to track evolution for",
        min_length=3,
        max_length=500
    )
    timeline_id: Optional[str] = Field(
        None,
        description="Timeline ID to analyze (optional if service_name provided)"
    )
    service_name: Optional[str] = Field(
        None,
        description="Service name to find timeline for (used if timeline_id not provided)"
    )
    limit_per_period: int = Field(
        default=3,
        ge=1,
        le=20,
        description="Maximum results per period"
    )


class ComparisonQueryRequest(BaseModel):
    """
    Request for comparison query.
    
    ✅ UTC STANDARDIZATION: Datetime fields are automatically converted to UTC.
    """
    question: str = Field(
        ...,
        description="Question to answer",
        min_length=3,
        max_length=1000
    )
    start_date: datetime = Field(
        ...,
        description="Start of comparison range (ISO 8601 format)"
    )
    end_date: datetime = Field(
        ...,
        description="End of comparison range (ISO 8601 format)"
    )
    timeline_id: Optional[str] = Field(
        None,
        description="Specific timeline to use (optional)"
    )
    
    @field_validator('start_date', 'end_date', mode='before')
    @classmethod
    def ensure_utc_dates(cls, v):
        """
        Ensure datetime fields are UTC-aware.
        
        ✅ UTC STANDARDIZATION Phase 1
        """
        if isinstance(v, str):
            from ...utils.datetime_utils import parse_datetime_flexible
            return parse_datetime_flexible(v)
        from ...utils.datetime_utils import ensure_utc
        return ensure_utc(v)
    service_name: Optional[str] = Field(
        None,
        description="Service to query (if timeline_id not provided)"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum results per period"
    )


class PeriodQueryRequest(BaseModel):
    """Request for period-specific query."""
    question: str = Field(
        ...,
        description="Question to answer",
        min_length=3,
        max_length=1000
    )
    timeline_id: str = Field(
        ...,
        description="Timeline ID"
    )
    period_id: str = Field(
        ...,
        description="Period ID to query"
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Maximum results"
    )


# ============================================================================
# API Endpoints
# ============================================================================

@router.post(
    "/temporal/query",
    summary="Time-travel query",
    description="""
    Query documents as they existed at a specific point in time.
    
    Example:
    ```json
    {
        "question": "What did the API documentation say about authentication?",
        "as_of_date": "2025-01-15T00:00:00Z",
        "service_name": "ecosystem-mcp"
    }
    ```
    
    This endpoint:
    - Finds the timeline covering the specified date
    - Identifies the relevant time period
    - Queries only documents that existed at that time
    - Falls back to standard RAG if temporal data unavailable
    """,
    response_model=Dict[str, Any]
)
async def temporal_query(request: TemporalQueryRequest):
    """
    Execute a time-travel query.
    
    Returns information as it existed at a specific point in time.
    """
    try:
        logger.info(f"⏰ Temporal query: {request.question[:100]} @ {request.as_of_date}")
        
        temporal_rag = TemporalRAGService()
        
        result = await temporal_rag.query_as_of(
            query=request.question,
            as_of_date=request.as_of_date,
            timeline_id=UUID(request.timeline_id) if request.timeline_id else None,
            service_name=request.service_name,
            limit=request.limit
        )
        
        return result
        
    except ValueError as e:
        logger.error(f"Validation error in temporal query: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to execute temporal query: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.post(
    "/temporal/evolution",
    summary="Track information evolution",
    description="""
    Track how information about a topic evolved over time.
    
    Example:
    ```json
    {
        "topic": "API authentication approach",
        "timeline_id": "123e4567-e89b-12d3-a456-426614174000",
        "limit_per_period": 3
    }
    ```
    
    This endpoint:
    - Queries each period in the timeline
    - Shows how information changed across periods
    - Identifies major changes
    - Provides evolution timeline
    """,
    response_model=Dict[str, Any]
)
async def track_evolution(request: EvolutionQueryRequest):
    """
    Track how information evolved over time.
    
    Returns evolution timeline with changes across all periods.
    """
    try:
        logger.info(f"📈 Evolution tracking: {request.topic[:100]}")
        
        context_rag = get_context_aware_rag()
        
        # Convert timeline_id to UUID if provided
        timeline_uuid = None
        if request.timeline_id:
            try:
                timeline_uuid = UUID(request.timeline_id)
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid timeline_id format: {request.timeline_id}"
                )
        
        # Require at least one identifier
        if not timeline_uuid and not request.service_name:
            raise HTTPException(
                status_code=400,
                detail="Either timeline_id or service_name must be provided"
            )
        
        result = await context_rag.query_evolution(
            topic=request.topic,
            timeline_id=timeline_uuid,
            service_name=request.service_name,
            limit_per_period=request.limit_per_period
        )
        
        return result
        
    except ValueError as e:
        logger.error(f"Validation error in evolution tracking: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to track evolution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Evolution tracking failed: {str(e)}")


@router.post(
    "/temporal/comparison",
    summary="Compare information between periods",
    description="""
    Compare information about a topic between two time periods.
    
    Example:
    ```json
    {
        "question": "authentication approach",
        "start_date": "2025-01-01T00:00:00Z",
        "end_date": "2025-03-31T23:59:59Z",
        "service_name": "ecosystem-mcp"
    }
    ```
    
    This endpoint:
    - Queries information at start and end of range
    - Detects changes between periods
    - Shows what was added, removed, or modified
    - Provides change summary
    """,
    response_model=Dict[str, Any]
)
async def compare_periods(request: ComparisonQueryRequest):
    """
    Compare information between two time periods.
    
    Returns comparison showing changes and differences.
    """
    try:
        logger.info(
            f"⚖️ Comparison query: {request.question[:100]} "
            f"({request.start_date.date()} to {request.end_date.date()})"
        )
        
        if request.start_date >= request.end_date:
            raise ValueError("start_date must be before end_date")
        
        context_rag = get_context_aware_rag()
        
        result = await context_rag.query_comparison(
            query=request.question,
            start_date=request.start_date,
            end_date=request.end_date,
            timeline_id=request.timeline_id,
            service_name=request.service_name,
            limit=request.limit
        )
        
        return result
        
    except ValueError as e:
        logger.error(f"Validation error in comparison: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to compare periods: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Comparison failed: {str(e)}")


@router.post(
    "/temporal/query-period",
    summary="Query specific period",
    description="""
    Query documents within a specific timeline period.
    
    Example:
    ```json
    {
        "question": "What are the API endpoints?",
        "timeline_id": "123e4567-e89b-12d3-a456-426614174000",
        "period_id": "234e5678-e89b-12d3-a456-426614174111"
    }
    ```
    
    This is a convenience endpoint for querying a known period.
    """,
    response_model=Dict[str, Any]
)
async def query_period(request: PeriodQueryRequest):
    """
    Query documents within a specific period.
    
    Returns results filtered to the specified period.
    """
    try:
        logger.info(
            f"🕐 Period query: {request.question[:100]} "
            f"(period={request.period_id})"
        )
        
        context_rag = get_context_aware_rag()
        
        result = await context_rag.query_period(
            query=request.question,
            timeline_id=request.timeline_id,
            period_id=request.period_id,
            limit=request.limit
        )
        
        return result
        
    except ValueError as e:
        logger.error(f"Validation error in period query: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to query period: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Period query failed: {str(e)}")


@router.get(
    "/temporal/capabilities/{timeline_id}",
    summary="Get temporal query capabilities",
    description="""
    Check what temporal query features are available for a timeline.
    
    Returns confidence level and available features based on timeline quality.
    """,
    response_model=Dict[str, Any]
)
async def get_temporal_capabilities(timeline_id: str):
    """
    Get temporal query capabilities for a timeline.
    
    Returns confidence level and available features.
    """
    try:
        logger.info(f"🔍 Getting temporal capabilities for timeline {timeline_id}")
        
        from ...storage import get_database
        from ...storage.repositories.timeline_repository import TimelineRepository
        
        async with get_database().session() as session:
            timeline_repo = TimelineRepository(session)
            timeline = await timeline_repo.get_by_id(UUID(timeline_id))
            
            if not timeline:
                raise HTTPException(status_code=404, detail="Timeline not found")
            
            confidence = timeline.confidence_level
            metadata = timeline.confidence_metadata
            
            # Determine available features based on confidence
            features = {
                "time_travel_queries": confidence in ["HIGH", "MEDIUM"],
                "evolution_tracking": confidence in ["HIGH", "MEDIUM"],
                "period_comparison": confidence in ["HIGH", "MEDIUM"],
                "change_detection": confidence in ["HIGH", "MEDIUM"],
                "fallback_to_standard_rag": True
            }
            
            return {
                "timeline_id": str(timeline_id),
                "timeline_name": timeline.name,
                "confidence_level": confidence,
                "confidence_metadata": metadata,
                "available_features": features,
                "recommendations": _get_recommendations(confidence)
            }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get capabilities: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get capabilities: {str(e)}"
        )


def _get_recommendations(confidence_level: str) -> List[str]:
    """Get recommendations based on confidence level."""
    if confidence_level == "HIGH":
        return [
            "All temporal features available",
            "Timeline has git history with accurate dates",
            "Time-travel queries will be precise"
        ]
    elif confidence_level == "MEDIUM":
        return [
            "Most temporal features available",
            "Timeline uses created_at timestamps",
            "Time-travel queries may be approximate"
        ]
    elif confidence_level == "LOW":
        return [
            "Limited temporal features",
            "Timeline has mixed data sources",
            "Consider using standard RAG instead"
        ]
    else:
        return [
            "Temporal features not recommended",
            "Timeline lacks temporal metadata",
            "Use standard RAG queries instead"
        ]


# ============================================================================
# Timeline Query Endpoint (Final 20% for 100% completion)
# ============================================================================

class TimelineQueryRequest(BaseModel):
    """Request for timeline query."""
    service_name: str = Field(
        ...,
        description="Service name to get timeline for",
        min_length=1,
        max_length=255
    )
    limit: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Maximum number of periods to return"
    )


@router.post(
    "/temporal/timeline",
    summary="Query Timeline",
    description="""
    Get timeline information and periods for a service.
    
    Returns:
    - Timeline metadata
    - Time periods within the timeline
    - Period statistics
    
    Use this to:
    - Discover available time periods
    - Understand timeline structure
    - Plan temporal queries
    """
)
async def query_timeline(request: TimelineQueryRequest):
    """
    Query timeline information for a service.
    
    This endpoint retrieves timeline metadata and periods,
    allowing clients to discover what temporal data is available.
    """
    try:
        logger.info(f"📊 Timeline query: {request.service_name}")
        
        context_rag = get_context_aware_rag()
        result = await context_rag.query_timeline(
            service_name=request.service_name,
            limit=request.limit
        )
        
        return {
            "success": True,
            "service_name": request.service_name,
            "timeline": result,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except ValueError as e:
        logger.error(f"Timeline query error: {e}")
        raise HTTPException(
            status_code=404,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Timeline query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Timeline query failed: {str(e)}"
        )

