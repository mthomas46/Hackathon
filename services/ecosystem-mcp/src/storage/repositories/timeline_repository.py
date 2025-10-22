"""
Timeline repository for Ecosystem MCP Service.

Provides database operations for timelines, time periods, and document placements.
"""

from typing import Optional, List
from uuid import UUID
from datetime import datetime

from sqlalchemy import select, and_, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..db_models import TimelineModel, TimePeriodModel, DocumentPlacementModel
from .base import BaseRepository
from ...utils.cache_decorator import cache


class TimelineRepository(BaseRepository[TimelineModel]):
    """
    Timeline repository with domain-specific methods.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize timeline repository."""
        super().__init__(session, TimelineModel)
    
    async def get_by_service(
        self,
        service_name: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[TimelineModel]:
        """
        Get timelines for a service.
        
        Args:
            service_name: Service name
            limit: Maximum timelines
            offset: Offset for pagination
        
        Returns:
            List of timelines
        """
        result = await self.session.execute(
            select(self.model_class)
            .where(self.model_class.service_name == service_name)
            .order_by(desc(self.model_class.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    async def get_with_periods(
        self,
        timeline_id: UUID
    ) -> Optional[TimelineModel]:
        """
        Get timeline with all its periods loaded (eager loading).
        
        Args:
            timeline_id: Timeline ID
        
        Returns:
            Timeline with periods or None
        """
        result = await self.session.execute(
            select(self.model_class)
            .where(self.model_class.id == timeline_id)
            .options(selectinload(self.model_class.periods))
        )
        return result.scalar_one_or_none()
    
    async def get_by_confidence(
        self,
        confidence_level: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[TimelineModel]:
        """
        Get timelines by confidence level.
        
        Args:
            confidence_level: Confidence level (HIGH, MEDIUM, LOW, NONE)
            limit: Maximum timelines
            offset: Offset for pagination
        
        Returns:
            List of timelines
        """
        result = await self.session.execute(
            select(self.model_class)
            .where(self.model_class.confidence_level == confidence_level)
            .order_by(desc(self.model_class.created_at))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    async def count_by_service(self, service_name: str) -> int:
        """
        Count timelines for a service.
        
        Args:
            service_name: Service name
        
        Returns:
            Count of timelines
        """
        result = await self.session.execute(
            select(func.count()).select_from(self.model_class).where(
                self.model_class.service_name == service_name
            )
        )
        return result.scalar() or 0


class TimePeriodRepository(BaseRepository[TimePeriodModel]):
    """
    Time period repository with domain-specific methods.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize time period repository."""
        super().__init__(session, TimePeriodModel)
    
    async def get_by_timeline(
        self,
        timeline_id: UUID,
        order_by_sequence: bool = True
    ) -> List[TimePeriodModel]:
        """
        Get all periods for a timeline.
        
        Args:
            timeline_id: Timeline ID
            order_by_sequence: Whether to order by sequence number
        
        Returns:
            List of time periods
        """
        query = select(self.model_class).where(
            self.model_class.timeline_id == timeline_id
        )
        
        if order_by_sequence:
            query = query.order_by(self.model_class.sequence_number)
        
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    async def get_by_date_range(
        self,
        timeline_id: UUID,
        start_date: datetime,
        end_date: datetime
    ) -> List[TimePeriodModel]:
        """
        Get periods that overlap with a date range.
        
        Args:
            timeline_id: Timeline ID
            start_date: Range start
            end_date: Range end
        
        Returns:
            List of overlapping periods
        """
        result = await self.session.execute(
            select(self.model_class)
            .where(
                and_(
                    self.model_class.timeline_id == timeline_id,
                    self.model_class.start_date <= end_date,
                    self.model_class.end_date >= start_date
                )
            )
            .order_by(self.model_class.sequence_number)
        )
        return list(result.scalars().all())
    
    async def get_with_placements(
        self,
        period_id: UUID
    ) -> Optional[TimePeriodModel]:
        """
        Get period with all document placements loaded.
        
        Args:
            period_id: Period ID
        
        Returns:
            Period with placements or None
        """
        result = await self.session.execute(
            select(self.model_class)
            .where(self.model_class.id == period_id)
            .options(selectinload(self.model_class.document_placements))
        )
        return result.scalar_one_or_none()
    
    async def delete_by_timeline(self, timeline_id: UUID) -> int:
        """
        Delete all periods for a timeline.
        
        Args:
            timeline_id: Timeline ID
        
        Returns:
            Number of periods deleted
        """
        periods = await self.get_by_timeline(timeline_id)
        count = len(periods)
        
        for period in periods:
            await self.session.delete(period)
        
        return count


class DocumentPlacementRepository(BaseRepository[DocumentPlacementModel]):
    """
    Document placement repository with domain-specific methods.
    """
    
    def __init__(self, session: AsyncSession):
        """Initialize document placement repository."""
        super().__init__(session, DocumentPlacementModel)
    
    async def get_by_period(
        self,
        period_id: UUID,
        limit: int = 1000,
        offset: int = 0
    ) -> List[DocumentPlacementModel]:
        """
        Get document placements for a period.
        
        Args:
            period_id: Period ID
            limit: Maximum placements
            offset: Offset for pagination
        
        Returns:
            List of document placements
        """
        result = await self.session.execute(
            select(self.model_class)
            .where(self.model_class.period_id == period_id)
            .order_by(self.model_class.placement_date)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())
    
    async def get_by_document(
        self,
        document_id: UUID
    ) -> List[DocumentPlacementModel]:
        """
        Get all placements for a document across periods.
        
        Args:
            document_id: Document ID
        
        Returns:
            List of placements
        """
        result = await self.session.execute(
            select(self.model_class)
            .where(self.model_class.document_id == document_id)
            .order_by(self.model_class.placement_date)
        )
        return list(result.scalars().all())
    
    async def exists(
        self,
        period_id: UUID,
        document_id: UUID
    ) -> bool:
        """
        Check if a placement exists.
        
        Args:
            period_id: Period ID
            document_id: Document ID
        
        Returns:
            True if placement exists
        """
        result = await self.session.execute(
            select(func.count())
            .select_from(self.model_class)
            .where(
                and_(
                    self.model_class.period_id == period_id,
                    self.model_class.document_id == document_id
                )
            )
        )
        count = result.scalar() or 0
        return count > 0
    
    async def bulk_create(
        self,
        placements: List[DocumentPlacementModel]
    ) -> List[DocumentPlacementModel]:
        """
        Bulk create placements (optimized).
        
        Args:
            placements: List of placement models
        
        Returns:
            Created placements
        """
        self.session.add_all(placements)
        await self.session.flush()
        return placements
    
    async def delete_by_period(self, period_id: UUID) -> int:
        """
        Delete all placements for a period.
        
        Args:
            period_id: Period ID
        
        Returns:
            Number of placements deleted
        """
        placements = await self.get_by_period(period_id, limit=10000)
        count = len(placements)
        
        for placement in placements:
            await self.session.delete(placement)
        
        return count

