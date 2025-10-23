"""
Timeline Manager

Manages timeline CRUD operations with confidence validation.
Integrates with TemporalConfidenceCalculator for pre-flight checks.
"""

import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from ...storage.db_models import TimelineModel, TimePeriodModel
from ...storage.repositories.timeline_repository import (
    TimelineRepository,
    TimePeriodRepository,
    DocumentPlacementRepository
)
from ...models.timeline import (
    Timeline,
    TimelineCreate,
    TimelineUpdate,
    TimePeriod,
    TemporalConfidence,
    PeriodStrategy,
)
from .confidence_calculator import TemporalConfidenceCalculator

logger = logging.getLogger(__name__)


class TimelineManager:
    """
    Manages timeline operations with confidence-based validation.
    
    Provides:
    - Timeline CRUD operations
    - Pre-flight confidence checks
    - Confidence-aware warnings
    - Integration with period and placement management
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize timeline manager.
        
        Args:
            db_session: Async SQLAlchemy session
        """
        self.db = db_session
        self.timeline_repo = TimelineRepository(db_session)
        self.period_repo = TimePeriodRepository(db_session)
        self.placement_repo = DocumentPlacementRepository(db_session)
        self.confidence_calculator = TemporalConfidenceCalculator(db_session)
        self.logger = logging.getLogger(__name__)
    
    async def create_timeline(
        self,
        timeline_create: TimelineCreate,
        skip_confidence_check: bool = False,
        minimum_confidence: TemporalConfidence = TemporalConfidence.MEDIUM
    ) -> Timeline:
        """
        Create a new timeline with confidence validation.
        
        Args:
            timeline_create: Timeline creation data
            skip_confidence_check: Skip pre-flight confidence check
            minimum_confidence: Minimum required confidence level
        
        Returns:
            Created timeline
        
        Raises:
            ValueError: If confidence check fails
        """
        try:
            self.logger.info(
                f"Creating timeline '{timeline_create.name}' "
                f"for service '{timeline_create.service_name}'"
            )
            
            # Pre-flight confidence check (unless skipped)
            if not skip_confidence_check:
                pre_flight = await self.confidence_calculator.check_pre_flight(
                    service_name=timeline_create.service_name,
                    minimum_confidence=minimum_confidence,
                    auto_adjust=True  # Gracefully handle snapshot-only services
                )
                
                if not pre_flight["can_proceed"]:
                    self.logger.warning(
                        f"Timeline creation blocked: {pre_flight['recommendation']}"
                    )
                    raise ValueError(
                        f"Insufficient temporal confidence. {pre_flight['recommendation']}"
                    )
                
                confidence_metadata = pre_flight["confidence_metadata"]
                actual_confidence = pre_flight["actual_confidence"]
                
                self.logger.info(
                    f"Pre-flight check passed: {actual_confidence} confidence "
                    f"({confidence_metadata.git_percentage:.1f}% git_history)"
                )
            else:
                # Calculate confidence without checking
                self.logger.info("Skipping confidence check (skip_confidence_check=True)")
                confidence_metadata = await self.confidence_calculator.calculate_confidence(
                    service_name=timeline_create.service_name
                )
                
                # Determine actual confidence
                git_pct = confidence_metadata.git_percentage
                if git_pct >= 90.0:
                    actual_confidence = "HIGH"
                elif git_pct >= 50.0:
                    actual_confidence = "MEDIUM"
                elif git_pct > 0.0:
                    actual_confidence = "LOW"
                else:
                    actual_confidence = "NONE"
            
            # Create timeline model
            timeline_model = TimelineModel(
                name=timeline_create.name,
                description=timeline_create.description,
                service_name=timeline_create.service_name,
                repo_path=timeline_create.repo_path,
                start_date=timeline_create.start_date,
                end_date=timeline_create.end_date,
                confidence_level=actual_confidence,
                confidence_metadata=confidence_metadata.model_dump(mode='json'),
                period_strategy=timeline_create.period_strategy.value,
                created_by=timeline_create.created_by,
                timeline_metadata=timeline_create.metadata.model_dump(mode='json')
            )
            
            # Save to database
            created = await self.timeline_repo.create(timeline_model)
            await self.db.commit()
            
            self.logger.info(
                f"✅ Timeline created: {created.id} "
                f"(confidence={actual_confidence})"
            )
            
            # Convert to Pydantic model
            return self._model_to_pydantic(created)
            
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to create timeline: {e}", exc_info=True)
            await self.db.session.rollback()
            raise
    
    async def get_timeline(
        self,
        timeline_id: UUID,
        include_periods: bool = False
    ) -> Optional[Timeline]:
        """
        Get a timeline by ID.
        
        Args:
            timeline_id: Timeline ID
            include_periods: Whether to eager-load periods
        
        Returns:
            Timeline or None
        """
        try:
            if include_periods:
                timeline_model = await self.timeline_repo.get_with_periods(timeline_id)
            else:
                timeline_model = await self.timeline_repo.get_by_id(timeline_id)
            
            if not timeline_model:
                return None
            
            return self._model_to_pydantic(timeline_model)
            
        except Exception as e:
            self.logger.error(f"Failed to get timeline: {e}", exc_info=True)
            raise
    
    async def update_timeline(
        self,
        timeline_id: UUID,
        timeline_update: TimelineUpdate
    ) -> Optional[Timeline]:
        """
        Update a timeline.
        
        Args:
            timeline_id: Timeline ID
            timeline_update: Update data
        
        Returns:
            Updated timeline or None if not found
        """
        try:
            timeline_model = await self.timeline_repo.get_by_id(timeline_id)
            
            if not timeline_model:
                self.logger.warning(f"Timeline not found: {timeline_id}")
                return None
            
            # Update fields
            update_data = timeline_update.model_dump(exclude_unset=True)
            
            for field, value in update_data.items():
                if field == "period_strategy" and value is not None:
                    setattr(timeline_model, field, value.value)
                elif field == "metadata" and value is not None:
                    setattr(timeline_model, "timeline_metadata", value.model_dump())
                else:
                    setattr(timeline_model, field, value)
            
            timeline_model.updated_at = datetime.utcnow()
            
            await self.db.commit()
            
            self.logger.info(f"✅ Timeline updated: {timeline_id}")
            
            return self._model_to_pydantic(timeline_model)
            
        except Exception as e:
            self.logger.error(f"Failed to update timeline: {e}", exc_info=True)
            await self.db.rollback()
            raise
    
    async def delete_timeline(
        self,
        timeline_id: UUID
    ) -> bool:
        """
        Delete a timeline and all its periods/placements.
        
        Args:
            timeline_id: Timeline ID
        
        Returns:
            True if deleted, False if not found
        """
        try:
            timeline_model = await self.timeline_repo.get_by_id(timeline_id)
            
            if not timeline_model:
                self.logger.warning(f"Timeline not found: {timeline_id}")
                return False
            
            # Delete periods (cascade will delete placements)
            deleted_periods = await self.period_repo.delete_by_timeline(timeline_id)
            
            # Delete timeline
            await self.timeline_repo.delete(timeline_id)
            await self.db.commit()
            
            self.logger.info(
                f"✅ Timeline deleted: {timeline_id} "
                f"(deleted {deleted_periods} periods)"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to delete timeline: {e}", exc_info=True)
            await self.db.rollback()
            raise
    
    async def list_timelines(
        self,
        service_name: Optional[str] = None,
        confidence_level: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[Timeline]:
        """
        List timelines with optional filters.
        
        Args:
            service_name: Optional service filter
            confidence_level: Optional confidence filter
            limit: Maximum results
            offset: Pagination offset
        
        Returns:
            List of timelines
        """
        try:
            if service_name:
                timeline_models = await self.timeline_repo.get_by_service(
                    service_name, limit, offset
                )
            elif confidence_level:
                timeline_models = await self.timeline_repo.get_by_confidence(
                    confidence_level, limit, offset
                )
            else:
                timeline_models = await self.timeline_repo.list(limit, offset)
            
            return [self._model_to_pydantic(t) for t in timeline_models]
            
        except Exception as e:
            self.logger.error(f"Failed to list timelines: {e}", exc_info=True)
            raise
    
    async def get_timeline_statistics(
        self,
        timeline_id: UUID
    ) -> Dict[str, Any]:
        """
        Get statistics for a timeline.
        
        Args:
            timeline_id: Timeline ID
        
        Returns:
            Dict with statistics
        """
        try:
            timeline_model = await self.timeline_repo.get_with_periods(timeline_id)
            
            if not timeline_model:
                raise ValueError(f"Timeline not found: {timeline_id}")
            
            periods = timeline_model.periods
            
            total_periods = len(periods)
            total_documents = sum(p.document_count for p in periods)
            total_commits = sum(p.commit_count for p in periods)
            
            # Period with most documents
            most_active_period = max(periods, key=lambda p: p.document_count) if periods else None
            
            return {
                "timeline_id": str(timeline_id),
                "timeline_name": timeline_model.name,
                "service_name": timeline_model.service_name,
                "confidence_level": timeline_model.confidence_level,
                "total_periods": total_periods,
                "total_documents": total_documents,
                "total_commits": total_commits,
                "period_strategy": timeline_model.period_strategy,
                "date_range": {
                    "start": timeline_model.start_date.isoformat(),
                    "end": timeline_model.end_date.isoformat()
                },
                "most_active_period": {
                    "name": most_active_period.name,
                    "document_count": most_active_period.document_count,
                    "commit_count": most_active_period.commit_count
                } if most_active_period else None,
                "created_at": timeline_model.created_at.isoformat(),
                "updated_at": timeline_model.updated_at.isoformat()
            }
            
        except ValueError:
            raise
        except Exception as e:
            self.logger.error(f"Failed to get timeline statistics: {e}", exc_info=True)
            raise
    
    def _model_to_pydantic(self, model: TimelineModel) -> Timeline:
        """
        Convert SQLAlchemy model to Pydantic model.
        
        Args:
            model: Timeline model
        
        Returns:
            Timeline Pydantic model
        """
        from ...models.timeline import TimelineMetadata, ConfidenceMetadata
        
        return Timeline(
            id=model.id,
            name=model.name,
            description=model.description,
            service_name=model.service_name,
            repo_path=model.repo_path,
            start_date=model.start_date,
            end_date=model.end_date,
            confidence_level=TemporalConfidence(model.confidence_level),
            confidence_metadata=ConfidenceMetadata(**model.confidence_metadata),
            period_strategy=PeriodStrategy(model.period_strategy),
            created_at=model.created_at,
            updated_at=model.updated_at,
            created_by=model.created_by,
            metadata=TimelineMetadata(**model.timeline_metadata)
        )

