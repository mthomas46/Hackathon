"""
Temporal Versioning API Routes

Provides endpoints for:
- Timeline queries ("as of" date)
- Document version history
- Content deduplication stats
- Change tracking
"""

import logging
from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ...storage import get_database
from ...services.versioning.timeline_query_engine import (
    TimelineQueryEngine,
    DocumentSnapshot,
    TimelineEvent,
    DocumentChange
)
from ...services.versioning.content_deduplicator import ContentDeduplicator

logger = logging.getLogger(__name__)
router = APIRouter()


# ==========================================
# Request/Response Models
# ==========================================

class DocumentSnapshotResponse(BaseModel):
    """Document at a specific point in time."""
    document_id: str
    version_id: str
    version_number: int
    content_hash: str
    modified_at: datetime
    created_by: str
    title: str
    source_path: str
    content_size: int


class TimelineEventResponse(BaseModel):
    """Event in a document's timeline."""
    version_id: str
    version_number: int
    event_timestamp: datetime
    event_type: str
    actor: str
    content_hash: str
    title: str
    is_latest: bool


class DocumentChangeResponse(BaseModel):
    """Changes to a document over time."""
    document_id: str
    title: str
    version_count: int
    first_change: datetime
    last_change: datetime
    contributors: List[str]
    source_path: str


class AsOfQueryRequest(BaseModel):
    """Request for 'as of' date query."""
    as_of_date: datetime = Field(..., description="Point in time to query")
    filters: Optional[dict] = Field(None, description="Optional filters")
    limit: int = Field(100, ge=1, le=1000)
    offset: int = Field(0, ge=0)


class AsOfQueryResponse(BaseModel):
    """Response for 'as of' date query."""
    as_of_date: datetime
    total_documents: int
    documents: List[DocumentSnapshotResponse]


class TimelineQueryRequest(BaseModel):
    """Request for document timeline."""
    document_id: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class TimelineQueryResponse(BaseModel):
    """Response for document timeline."""
    document_id: str
    total_events: int
    events: List[TimelineEventResponse]


class ChangesQueryRequest(BaseModel):
    """Request for changes between dates."""
    start_date: datetime
    end_date: datetime
    limit: int = Field(100, ge=1, le=1000)


class ChangesQueryResponse(BaseModel):
    """Response for changes between dates."""
    start_date: datetime
    end_date: datetime
    total_changes: int
    changes: List[DocumentChangeResponse]


class ActivitySummaryResponse(BaseModel):
    """Activity summary statistics."""
    total_versions: int
    unique_documents: int
    unique_contributors: int
    activity_by_day: dict
    top_contributors: dict
    period_start: str
    period_end: str


class DeduplicationStatsResponse(BaseModel):
    """Content deduplication statistics."""
    unique_content_items: int
    total_versions: int
    deduplicated_items: int
    total_content_size: int
    size_without_dedup: int
    space_saved: int
    deduplication_ratio: float


class ContentInfoResponse(BaseModel):
    """Information about stored content."""
    content_hash: str
    mime_type: Optional[str]
    compression_type: Optional[str]
    content_size: int
    first_seen_at: Optional[str]
    reference_count: int
    storage_location: Optional[str]


class CleanupStatsResponse(BaseModel):
    """Cleanup statistics."""
    total_items: int
    total_size_bytes: int
    total_size_mb: float
    dry_run: bool
    deleted: int


# ==========================================
# Endpoints
# ==========================================

@router.post("/as-of", response_model=AsOfQueryResponse)
async def query_documents_as_of(
    request: AsOfQueryRequest
):
    """
    Query documents as they existed at a specific point in time.
    
    Example:
        "Show me all documents as of October 1, 2025"
    
    Returns the version of each document that was current at that timestamp.
    """
    try:
        db = get_database()
        async with db.get_session() as session:
            engine = TimelineQueryEngine(session)
        
        snapshots = await engine.get_documents_as_of(
            as_of_date=request.as_of_date,
            filters=request.filters,
            limit=request.limit,
            offset=request.offset
        )
        
        return AsOfQueryResponse(
            as_of_date=request.as_of_date,
            total_documents=len(snapshots),
            documents=[
                DocumentSnapshotResponse(
                    document_id=str(s.document_id),
                    version_id=str(s.version_id),
                    version_number=s.version_number,
                    content_hash=s.content_hash,
                    modified_at=s.modified_at,
                    created_by=s.created_by,
                    title=s.title,
                    source_path=s.source_path,
                    content_size=s.content_size
                )
                for s in snapshots
            ]
        )
    
    except Exception as e:
        logger.error(f"Failed to query documents as of: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/timeline", response_model=TimelineQueryResponse)
async def get_document_timeline(
    request: TimelineQueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get complete timeline for a document.
    
    Returns all versions and events in chronological order.
    """
    try:
        engine = TimelineQueryEngine(db)
        document_id = UUID(request.document_id)
        
        events = await engine.get_document_timeline(
            document_id=document_id,
            start_date=request.start_date,
            end_date=request.end_date
        )
        
        return TimelineQueryResponse(
            document_id=request.document_id,
            total_events=len(events),
            events=[
                TimelineEventResponse(
                    version_id=str(e.version_id),
                    version_number=e.version_number,
                    event_timestamp=e.event_timestamp,
                    event_type=e.event_type,
                    actor=e.actor,
                    content_hash=e.content_hash,
                    title=e.title,
                    is_latest=e.is_latest
                )
                for e in events
            ]
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid document ID: {e}")
    except Exception as e:
        logger.error(f"Failed to get document timeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/changes", response_model=ChangesQueryResponse)
async def get_changes_between_dates(
    request: ChangesQueryRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Get all document changes in a time range.
    
    Example:
        "What changed between Oct 1 and Oct 15?"
    """
    try:
        engine = TimelineQueryEngine(db)
        
        changes = await engine.get_changes_between(
            start_date=request.start_date,
            end_date=request.end_date,
            limit=request.limit
        )
        
        return ChangesQueryResponse(
            start_date=request.start_date,
            end_date=request.end_date,
            total_changes=len(changes),
            changes=[
                DocumentChangeResponse(
                    document_id=str(c.document_id),
                    title=c.title,
                    version_count=c.version_count,
                    first_change=c.first_change,
                    last_change=c.last_change,
                    contributors=c.contributors,
                    source_path=c.source_path
                )
                for c in changes
            ]
        )
    
    except Exception as e:
        logger.error(f"Failed to get changes: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/activity-summary", response_model=ActivitySummaryResponse)
async def get_activity_summary(
    start_date: Optional[datetime] = Query(None),
    end_date: Optional[datetime] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """
    Get activity summary statistics for a time period.
    
    Includes:
    - Total versions created
    - Unique documents modified
    - Unique contributors
    - Activity by day
    - Top contributors
    """
    try:
        engine = TimelineQueryEngine(db)
        summary = await engine.get_activity_summary(start_date, end_date)
        
        return ActivitySummaryResponse(**summary)
    
    except Exception as e:
        logger.error(f"Failed to get activity summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/deduplication-stats", response_model=DeduplicationStatsResponse)
async def get_deduplication_stats(
    db: AsyncSession = Depends(get_db)
):
    """
    Get content deduplication statistics.
    
    Shows:
    - How many unique content items exist
    - How many versions reference them
    - Space saved by deduplication
    - Deduplication ratio
    """
    try:
        engine = TimelineQueryEngine(db)
        stats = await engine.get_deduplication_stats()
        
        return DeduplicationStatsResponse(**stats)
    
    except Exception as e:
        logger.error(f"Failed to get deduplication stats: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/content/{content_hash}", response_model=ContentInfoResponse)
async def get_content_info(
    content_hash: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get information about stored content.
    
    Returns metadata about a specific content hash, including:
    - MIME type
    - Size
    - Reference count
    - First seen date
    """
    try:
        deduplicator = ContentDeduplicator(db)
        info = await deduplicator.get_content_info(content_hash)
        
        if not info:
            raise HTTPException(status_code=404, detail="Content not found")
        
        return ContentInfoResponse(**info)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get content info: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/content/{content_hash}/verify")
async def verify_content_integrity(
    content_hash: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Verify that stored content matches its hash.
    
    Performs integrity check to ensure content hasn't been corrupted.
    """
    try:
        deduplicator = ContentDeduplicator(db)
        is_valid = await deduplicator.verify_integrity(content_hash)
        
        return {
            "content_hash": content_hash,
            "integrity_verified": is_valid,
            "message": "Content integrity verified" if is_valid else "INTEGRITY CHECK FAILED"
        }
    
    except Exception as e:
        logger.error(f"Failed to verify integrity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/content/cleanup", response_model=CleanupStatsResponse)
async def cleanup_unreferenced_content(
    dry_run: bool = Query(True, description="If true, only report what would be deleted"),
    db: AsyncSession = Depends(get_db)
):
    """
    Clean up content with zero references.
    
    By default, runs in dry-run mode to show what would be deleted.
    Set dry_run=false to actually delete unreferenced content.
    """
    try:
        deduplicator = ContentDeduplicator(db)
        stats = await deduplicator.cleanup_unreferenced(dry_run=dry_run)
        
        return CleanupStatsResponse(**stats)
    
    except Exception as e:
        logger.error(f"Failed to cleanup content: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/version/{version_id}", response_model=DocumentSnapshotResponse)
async def get_version_by_id(
    version_id: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific version by its ID.
    
    Returns complete information about a document version.
    """
    try:
        engine = TimelineQueryEngine(db)
        version_uuid = UUID(version_id)
        
        snapshot = await engine.get_version_by_id(version_uuid)
        
        if not snapshot:
            raise HTTPException(status_code=404, detail="Version not found")
        
        return DocumentSnapshotResponse(
            document_id=str(snapshot.document_id),
            version_id=str(snapshot.version_id),
            version_number=snapshot.version_number,
            content_hash=snapshot.content_hash,
            modified_at=snapshot.modified_at,
            created_by=snapshot.created_by,
            title=snapshot.title,
            source_path=snapshot.source_path,
            content_size=snapshot.content_size
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid version ID: {e}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get version: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

