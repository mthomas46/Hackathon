"""
Timeline API Routes

Provides RESTful endpoints for timeline-based document analysis:
- Timeline management (CRUD)
- Period listing
- Document placement queries
- Confidence checks
"""

import logging
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from ...storage import get_database
from ...services.timeline import (
    TimelineManager,
    PeriodGenerator,
    DocumentPlacer,
    TemporalConfidenceCalculator
)
from ...models.timeline import (
    Timeline,
    TimelineCreate,
    TimelineUpdate,
    TimePeriod,
    DocumentPlacement,
    TemporalConfidence,
    PeriodStrategy,
    TimelineListResponse,
    TimePeriodListResponse,
    DocumentPlacementListResponse,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/timelines", tags=["timeline"])


# ==========================================
# Request/Response Models
# ==========================================

class TimelineCreateRequest(BaseModel):
    """Request for creating a timeline."""
    timeline: TimelineCreate
    skip_confidence_check: bool = Field(
        default=False,
        description="Skip pre-flight confidence validation"
    )
    minimum_confidence: TemporalConfidence = Field(
        default=TemporalConfidence.MEDIUM,
        description="Minimum required confidence level"
    )
    generate_periods: bool = Field(
        default=True,
        description="Automatically generate periods after creation"
    )
    place_documents: bool = Field(
        default=True,
        description="Automatically place documents after period generation"
    )


class TimelineCreateResponse(BaseModel):
    """Response for timeline creation."""
    timeline: Timeline
    periods_generated: int = 0
    documents_placed: int = 0


class ConfidenceCheckRequest(BaseModel):
    """Request for pre-flight confidence check."""
    service_name: str
    minimum_confidence: TemporalConfidence = TemporalConfidence.MEDIUM


class ConfidenceCheckResponse(BaseModel):
    """Response for confidence check."""
    can_proceed: bool
    actual_confidence: str
    required_confidence: str
    recommendation: str
    confidence_details: dict


class PeriodGenerationRequest(BaseModel):
    """Request for generating periods."""
    timeline_id: str
    strategy: Optional[PeriodStrategy] = None  # Use timeline's strategy if None


class DocumentPlacementRequest(BaseModel):
    """Request for placing documents."""
    timeline_id: str


# ==========================================
# Timeline Endpoints
# ==========================================

@router.post("/", response_model=TimelineCreateResponse)
async def create_timeline(
    request: TimelineCreateRequest
):
    """
    Create a new timeline with optional period generation and document placement.
    
    Workflow:
    1. Pre-flight confidence check (unless skipped)
    2. Create timeline
    3. Generate periods (if requested)
    4. Place documents (if requested)
    
    Returns:
        Timeline with creation statistics
    """
    try:
        db = get_database()
        async with db.session() as session:
            manager = TimelineManager(session)
            
            # Create timeline
            timeline = await manager.create_timeline(
                timeline_create=request.timeline,
                skip_confidence_check=request.skip_confidence_check,
                minimum_confidence=request.minimum_confidence
            )
            
            logger.info(f"✅ Timeline created: {timeline.id}")
            
            periods_generated = 0
            documents_placed = 0
            
            # Generate periods if requested
            if request.generate_periods:
                generator = PeriodGenerator(session)
                period_creates = await generator.generate_periods(
                    timeline_id=str(timeline.id),
                    service_name=timeline.service_name,
                    start_date=timeline.start_date,
                    end_date=timeline.end_date,
                    strategy=timeline.period_strategy,
                    repo_path=timeline.repo_path
                )
                
                # Save periods
                from ...storage.repositories.timeline_repository import TimePeriodRepository
                from ...storage.db_models import TimePeriodModel
                
                period_repo = TimePeriodRepository(session)
                for period_create in period_creates:
                    period_model = TimePeriodModel(
                        timeline_id=timeline.id,
                        name=period_create.name,
                        description=period_create.description,
                        start_date=period_create.start_date,
                        end_date=period_create.end_date,
                        sequence_number=period_create.sequence_number,
                        period_metadata=period_create.metadata.model_dump()
                    )
                    await period_repo.create(period_model)
                    periods_generated += 1
                
                await session.commit()
                logger.info(f"✅ Generated {periods_generated} periods")
                
                # Place documents if requested
                if request.place_documents:
                    placer = DocumentPlacer(session)
                    placement_stats = await placer.place_documents(
                        timeline_id=timeline.id,
                        service_name=timeline.service_name,
                        repo_path=timeline.repo_path
                    )
                    documents_placed = placement_stats["placed_documents"]
                    logger.info(f"✅ Placed {documents_placed} documents")
            
            return TimelineCreateResponse(
                timeline=timeline,
                periods_generated=periods_generated,
                documents_placed=documents_placed
            )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Failed to create timeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{timeline_id}", response_model=Timeline)
async def get_timeline(
    timeline_id: str,
    include_periods: bool = Query(False, description="Include periods in response")
):
    """
    Get a timeline by ID.
    
    Args:
        timeline_id: Timeline UUID
        include_periods: Whether to include periods
    
    Returns:
        Timeline
    """
    try:
        db = get_database()
        async with db.session() as session:
            manager = TimelineManager(session)
            timeline = await manager.get_timeline(
                UUID(timeline_id),
                include_periods=include_periods
            )
            
            if not timeline:
                raise HTTPException(status_code=404, detail="Timeline not found")
            
            return timeline
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timeline ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get timeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{timeline_id}", response_model=Timeline)
async def update_timeline(
    timeline_id: str,
    timeline_update: TimelineUpdate
):
    """
    Update a timeline.
    
    Args:
        timeline_id: Timeline UUID
        timeline_update: Update data
    
    Returns:
        Updated timeline
    """
    try:
        db = get_database()
        async with db.session() as session:
            manager = TimelineManager(session)
            timeline = await manager.update_timeline(
                UUID(timeline_id),
                timeline_update
            )
            
            if not timeline:
                raise HTTPException(status_code=404, detail="Timeline not found")
            
            return timeline
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timeline ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update timeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{timeline_id}")
async def delete_timeline(timeline_id: str):
    """
    Delete a timeline and all its periods/placements.
    
    Args:
        timeline_id: Timeline UUID
    
    Returns:
        Success message
    """
    try:
        db = get_database()
        async with db.session() as session:
            manager = TimelineManager(session)
            deleted = await manager.delete_timeline(UUID(timeline_id))
            
            if not deleted:
                raise HTTPException(status_code=404, detail="Timeline not found")
            
            return {"message": "Timeline deleted successfully"}
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timeline ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to delete timeline: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/", response_model=TimelineListResponse)
async def list_timelines(
    service_name: Optional[str] = Query(None, description="Filter by service"),
    confidence_level: Optional[str] = Query(None, description="Filter by confidence"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    List timelines with optional filters.
    
    Args:
        service_name: Optional service filter
        confidence_level: Optional confidence filter (HIGH, MEDIUM, LOW, NONE)
        page: Page number
        page_size: Items per page
    
    Returns:
        List of timelines with pagination
    """
    try:
        db = get_database()
        async with db.session() as session:
            manager = TimelineManager(session)
            
            offset = (page - 1) * page_size
            timelines = await manager.list_timelines(
                service_name=service_name,
                confidence_level=confidence_level,
                limit=page_size,
                offset=offset
            )
            
            return TimelineListResponse(
                timelines=timelines,
                total=len(timelines),  # Could be enhanced with actual count
                page=page,
                page_size=page_size
            )
    
    except Exception as e:
        logger.error(f"Failed to list timelines: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{timeline_id}/statistics")
async def get_timeline_statistics(timeline_id: str):
    """
    Get statistics for a timeline.
    
    Args:
        timeline_id: Timeline UUID
    
    Returns:
        Statistics dictionary
    """
    try:
        db = get_database()
        async with db.session() as session:
            manager = TimelineManager(session)
            stats = await manager.get_timeline_statistics(UUID(timeline_id))
            return stats
    
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail="Invalid timeline ID")
    except Exception as e:
        logger.error(f"Failed to get statistics: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Period Endpoints
# ==========================================

@router.get("/{timeline_id}/periods", response_model=TimePeriodListResponse)
async def get_timeline_periods(
    timeline_id: str,
    order_by_sequence: bool = Query(True, description="Order by sequence number")
):
    """
    Get all periods for a timeline.
    
    Args:
        timeline_id: Timeline UUID
        order_by_sequence: Whether to order by sequence
    
    Returns:
        List of periods
    """
    try:
        db = get_database()
        async with db.session() as session:
            from ...storage.repositories.timeline_repository import TimePeriodRepository
            from ...models.timeline import PeriodMetadata
            
            period_repo = TimePeriodRepository(session)
            period_models = await period_repo.get_by_timeline(
                UUID(timeline_id),
                order_by_sequence=order_by_sequence
            )
            
            periods = [
                TimePeriod(
                    id=p.id,
                    timeline_id=p.timeline_id,
                    name=p.name,
                    description=p.description,
                    start_date=p.start_date,
                    end_date=p.end_date,
                    sequence_number=p.sequence_number,
                    document_count=p.document_count,
                    commit_count=p.commit_count,
                    metadata=PeriodMetadata(**p.period_metadata),
                    created_at=p.created_at,
                    updated_at=p.updated_at
                )
                for p in period_models
            ]
            
            return TimePeriodListResponse(
                periods=periods,
                total=len(periods),
                timeline_id=UUID(timeline_id)
            )
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timeline ID")
    except Exception as e:
        logger.error(f"Failed to get periods: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{timeline_id}/periods/generate")
async def generate_periods(
    timeline_id: str
):
    """
    Generate periods for a timeline.
    
    Args:
        timeline_id: Timeline ID from path
    
    Returns:
        Number of periods generated
    """
    logger.info(f"🔧 [PERIOD_GEN] Starting period generation for timeline: {timeline_id}")
    
    try:
        # Validate UUID format
        logger.debug(f"🔧 [PERIOD_GEN] Step 1: Validating UUID format")
        logger.debug(f"   Raw timeline_id: {timeline_id!r} (type: {type(timeline_id)})")
        
        try:
            timeline_uuid = UUID(timeline_id)
            logger.debug(f"   ✅ UUID parsed successfully: {timeline_uuid}")
        except ValueError as e:
            logger.error(f"   ❌ UUID parsing failed: {e}")
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid timeline ID format: {timeline_id}. Must be valid UUID."
            )
        
        db = get_database()
        async with db.session() as session:
            # Get timeline
            logger.debug(f"🔧 [PERIOD_GEN] Step 2: Fetching timeline from database")
            manager = TimelineManager(session)
            timeline = await manager.get_timeline(timeline_uuid)
            
            if not timeline:
                logger.error(f"   ❌ Timeline not found: {timeline_uuid}")
                raise HTTPException(status_code=404, detail=f"Timeline not found: {timeline_id}")
            
            logger.info(f"   ✅ Timeline found: {timeline.name}")
            logger.debug(f"   Service: {timeline.service_name}")
            logger.debug(f"   Date range: {timeline.start_date} to {timeline.end_date}")
            
            # Use timeline's strategy
            strategy = timeline.period_strategy
            logger.info(f"🔧 [PERIOD_GEN] Step 3: Using strategy: {strategy} (type: {type(strategy).__name__})")
            logger.info(f"   Is PeriodStrategy enum? {isinstance(strategy, PeriodStrategy)}")
            logger.info(f"   Has .value attribute? {hasattr(strategy, 'value')}")
            
            # Generate periods
            logger.debug(f"🔧 [PERIOD_GEN] Step 4: Generating periods")
            generator = PeriodGenerator(session)
            
            try:
                period_creates = await generator.generate_periods(
                    timeline_id=timeline_id,
                    service_name=timeline.service_name,
                    start_date=timeline.start_date,
                    end_date=timeline.end_date,
                    strategy=strategy,
                    repo_path=timeline.repo_path
                )
                logger.info(f"   ✅ Generated {len(period_creates)} period definitions")
            except Exception as e:
                logger.error(f"   ❌ Period generation failed: {e}", exc_info=True)
                raise
            
            # Save periods
            logger.debug(f"🔧 [PERIOD_GEN] Step 5: Saving periods to database")
            from ...storage.repositories.timeline_repository import TimePeriodRepository
            from ...storage.db_models import TimePeriodModel
            
            period_repo = TimePeriodRepository(session)
            
            # Delete existing periods first
            logger.debug(f"   Deleting existing periods for timeline {timeline_uuid}")
            await period_repo.delete_by_timeline(timeline_uuid)
            
            # Create new periods
            logger.debug(f"   Creating {len(period_creates)} new periods")
            for i, period_create in enumerate(period_creates, 1):
                logger.debug(f"   Period {i}: {period_create.name} ({period_create.start_date} to {period_create.end_date})")
                period_model = TimePeriodModel(
                    timeline_id=timeline_uuid,
                    name=period_create.name,
                    description=period_create.description,
                    start_date=period_create.start_date,
                    end_date=period_create.end_date,
                    sequence_number=period_create.sequence_number,
                    period_metadata=period_create.metadata.model_dump()
                )
                await period_repo.create(period_model)
            
            logger.debug(f"🔧 [PERIOD_GEN] Step 6: Committing transaction")
            await session.commit()
            
            logger.info(f"✅ [PERIOD_GEN] SUCCESS: Generated {len(period_creates)} periods for timeline {timeline_id}")
            
            # ✅ FIX: Handle both string and enum for strategy value
            strategy_value = strategy.value if hasattr(strategy, 'value') else str(strategy)
            
            return {
                "success": True,
                "message": f"Generated {len(period_creates)} periods",
                "count": len(period_creates),
                "strategy": strategy_value,
                "timeline_id": timeline_id
            }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [PERIOD_GEN] FAILED: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Period generation failed: {str(e)}")


# ==========================================
# Document Placement Endpoints
# ==========================================

@router.get("/{timeline_id}/periods/{period_id}/documents", response_model=DocumentPlacementListResponse)
async def get_period_documents(
    timeline_id: str,
    period_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(100, ge=1, le=1000)
):
    """
    Get documents placed in a specific period.
    
    Args:
        timeline_id: Timeline UUID
        period_id: Period UUID
        page: Page number
        page_size: Items per page
    
    Returns:
        List of document placements
    """
    try:
        db = get_database()
        async with db.session() as session:
            from ...storage.repositories.timeline_repository import DocumentPlacementRepository
            from ...models.timeline import PlacementMetadata, PlacementSource
            
            placement_repo = DocumentPlacementRepository(session)
            
            offset = (page - 1) * page_size
            placement_models = await placement_repo.get_by_period(
                UUID(period_id),
                limit=page_size,
                offset=offset
            )
            
            placements = [
                DocumentPlacement(
                    id=p.id,
                    period_id=p.period_id,
                    document_id=p.document_id,
                    placement_date=p.placement_date,
                    placement_source=PlacementSource(p.placement_source),
                    git_commit_sha=p.git_commit_sha,
                    relevance_score=p.relevance_score,
                    metadata=PlacementMetadata(**p.placement_metadata),
                    created_at=p.created_at
                )
                for p in placement_models
            ]
            
            return DocumentPlacementListResponse(
                placements=placements,
                total=len(placements),
                period_id=UUID(period_id)
            )
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid UUID")
    except Exception as e:
        logger.error(f"Failed to get period documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{timeline_id}/documents/place")
async def place_documents(request: DocumentPlacementRequest):
    """
    Place documents into timeline periods.
    
    Args:
        request: Document placement request
    
    Returns:
        Placement statistics
    """
    try:
        db = get_database()
        async with db.session() as session:
            # Get timeline
            manager = TimelineManager(session)
            timeline = await manager.get_timeline(UUID(request.timeline_id))
            
            if not timeline:
                raise HTTPException(status_code=404, detail="Timeline not found")
            
            # Place documents
            placer = DocumentPlacer(session)
            stats = await placer.place_documents(
                timeline_id=UUID(request.timeline_id),
                service_name=timeline.service_name,
                repo_path=timeline.repo_path
            )
            
            return stats
    
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid timeline ID")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to place documents: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# ==========================================
# Confidence Check Endpoints
# ==========================================

@router.post("/confidence/check", response_model=ConfidenceCheckResponse)
async def check_confidence(request: ConfidenceCheckRequest):
    """
    Check temporal confidence for a service before creating timeline.
    
    Args:
        request: Confidence check request
    
    Returns:
        Confidence check result with recommendations
    """
    try:
        db = get_database()
        async with db.session() as session:
            calculator = TemporalConfidenceCalculator(session)
            result = await calculator.check_pre_flight(
                service_name=request.service_name,
                minimum_confidence=request.minimum_confidence
            )
            
            return ConfidenceCheckResponse(
                can_proceed=result["can_proceed"],
                actual_confidence=result["actual_confidence"],
                required_confidence=result["required_confidence"],
                recommendation=result["recommendation"],
                confidence_details=result["confidence_metadata"].model_dump()
            )
    
    except Exception as e:
        logger.error(f"Failed to check confidence: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/confidence/upgrade-path/{service_name}")
async def get_upgrade_path(service_name: str):
    """
    Get upgrade suggestions to improve temporal confidence.
    
    Args:
        service_name: Service name
    
    Returns:
        Upgrade suggestions
    """
    try:
        db = get_database()
        async with db.session() as session:
            calculator = TemporalConfidenceCalculator(session)
            suggestions = await calculator.suggest_upgrade_path(service_name)
            return suggestions
    
    except Exception as e:
        logger.error(f"Failed to get upgrade path: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

