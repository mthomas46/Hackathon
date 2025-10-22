"""
Dynamic Timeline Constructor (Phase 6.2)

Builds temporary timelines from document sets for on-demand temporal analysis.
"""

import logging
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum

from .document_finder import RelevantDocument

logger = logging.getLogger(__name__)


class DynamicPeriodStrategy(Enum):
    """Strategies for automatic period generation."""
    AUTO = "auto"  # Automatically determine best strategy
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    ADAPTIVE = "adaptive"  # Adaptive based on document density


@dataclass
class DynamicPeriod:
    """A period in a dynamic timeline."""
    name: str
    start_date: datetime
    end_date: datetime
    documents: List[str]  # Document IDs
    document_count: int
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'documents': self.documents,
            'document_count': self.document_count
        }


@dataclass
class DynamicTimeline:
    """A temporary timeline constructed from documents."""
    timeline_id: str
    name: str
    start_date: datetime
    end_date: datetime
    periods: List[DynamicPeriod]
    documents: List[RelevantDocument]
    confidence: str  # HIGH/MEDIUM/LOW/NONE
    period_strategy: str
    created_at: datetime
    expires_at: datetime
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            'timeline_id': self.timeline_id,
            'name': self.name,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'period_count': len(self.periods),
            'document_count': len(self.documents),
            'confidence': self.confidence,
            'period_strategy': self.period_strategy,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'periods': [p.to_dict() for p in self.periods]
        }


class DynamicTimelineConstructor:
    """
    Constructs temporary timelines from document sets.
    
    Features:
    - Automatic period generation
    - Confidence calculation
    - Document placement in periods
    - Caching (1 hour TTL)
    - Multiple period strategies
    """
    
    # Cache for dynamic timelines (timeline_id -> DynamicTimeline)
    _cache: Dict[str, DynamicTimeline] = {}
    
    def __init__(self):
        logger.info("DynamicTimelineConstructor initialized")
    
    async def construct_timeline(
        self,
        documents: List[RelevantDocument],
        timeline_name: str,
        period_strategy: DynamicPeriodStrategy = DynamicPeriodStrategy.AUTO
    ) -> DynamicTimeline:
        """
        Construct a temporary timeline from documents.
        
        Args:
            documents: List of relevant documents
            timeline_name: Name for the timeline
            period_strategy: Strategy for period generation
        
        Returns:
            DynamicTimeline with periods and confidence
        """
        logger.info(f"Constructing dynamic timeline with {len(documents)} documents")
        
        try:
            # Generate timeline ID
            import uuid
            timeline_id = f"dynamic-{uuid.uuid4()}"
            
            # Determine date range
            start_date, end_date = self._determine_date_range(documents)
            
            # Select period strategy if AUTO
            if period_strategy == DynamicPeriodStrategy.AUTO:
                period_strategy = self._select_period_strategy(
                    start_date, end_date, len(documents)
                )
            
            # Generate periods
            periods = await self._generate_periods(
                start_date, end_date, period_strategy
            )
            
            # Place documents in periods
            periods_with_docs = await self._place_documents(
                periods, documents
            )
            
            # Calculate confidence
            confidence = self._calculate_confidence(documents)
            
            # Create timeline
            now = datetime.utcnow()
            timeline = DynamicTimeline(
                timeline_id=timeline_id,
                name=timeline_name,
                start_date=start_date,
                end_date=end_date,
                periods=periods_with_docs,
                documents=documents,
                confidence=confidence,
                period_strategy=period_strategy.value,
                created_at=now,
                expires_at=now + timedelta(hours=1)  # 1 hour TTL
            )
            
            # Cache timeline
            self._cache[timeline_id] = timeline
            
            logger.info(f"✅ Constructed timeline with {len(periods_with_docs)} periods, "
                       f"confidence: {confidence}")
            
            return timeline
            
        except Exception as e:
            logger.error(f"Error constructing timeline: {e}")
            raise
    
    def get_cached_timeline(self, timeline_id: str) -> Optional[DynamicTimeline]:
        """Get cached timeline if it exists and hasn't expired."""
        if timeline_id in self._cache:
            timeline = self._cache[timeline_id]
            
            # Check if expired
            if datetime.utcnow() < timeline.expires_at:
                logger.debug(f"Cache hit for timeline {timeline_id}")
                return timeline
            else:
                # Remove expired timeline
                del self._cache[timeline_id]
                logger.debug(f"Timeline {timeline_id} expired and removed")
        
        return None
    
    def _determine_date_range(
        self,
        documents: List[RelevantDocument]
    ) -> tuple[datetime, datetime]:
        """Determine date range from documents."""
        if not documents:
            # Default to last year
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=365)
            return start_date, end_date
        
        # Find min and max dates
        dates = [doc.last_modified for doc in documents if doc.last_modified]
        
        if not dates:
            # Fallback to default
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=365)
        else:
            start_date = min(dates)
            end_date = max(dates)
            
            # Add buffer (5% of range or 30 days minimum)
            date_range = (end_date - start_date).days
            buffer_days = max(int(date_range * 0.05), 30)
            
            start_date = start_date - timedelta(days=buffer_days)
            end_date = end_date + timedelta(days=buffer_days)
        
        return start_date, end_date
    
    def _select_period_strategy(
        self,
        start_date: datetime,
        end_date: datetime,
        document_count: int
    ) -> DynamicPeriodStrategy:
        """Auto-select best period strategy."""
        # Calculate timeline duration in months
        duration_days = (end_date - start_date).days
        duration_months = duration_days / 30
        
        # Rules for strategy selection
        if duration_months < 3:
            # Short timeline: monthly periods
            return DynamicPeriodStrategy.MONTHLY
        elif duration_months < 12:
            # Medium timeline: monthly or quarterly
            if document_count < 20:
                return DynamicPeriodStrategy.MONTHLY
            else:
                return DynamicPeriodStrategy.QUARTERLY
        else:
            # Long timeline: quarterly or adaptive
            if document_count < 30:
                return DynamicPeriodStrategy.QUARTERLY
            else:
                return DynamicPeriodStrategy.ADAPTIVE
    
    async def _generate_periods(
        self,
        start_date: datetime,
        end_date: datetime,
        strategy: DynamicPeriodStrategy
    ) -> List[DynamicPeriod]:
        """Generate periods based on strategy."""
        periods = []
        
        if strategy == DynamicPeriodStrategy.MONTHLY:
            periods = self._generate_monthly_periods(start_date, end_date)
        elif strategy == DynamicPeriodStrategy.QUARTERLY:
            periods = self._generate_quarterly_periods(start_date, end_date)
        elif strategy == DynamicPeriodStrategy.YEARLY:
            periods = self._generate_yearly_periods(start_date, end_date)
        elif strategy == DynamicPeriodStrategy.ADAPTIVE:
            periods = self._generate_adaptive_periods(start_date, end_date)
        
        return periods
    
    def _generate_monthly_periods(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[DynamicPeriod]:
        """Generate monthly periods."""
        periods = []
        current = start_date.replace(day=1)
        
        while current <= end_date:
            # Calculate next month
            if current.month == 12:
                next_month = current.replace(year=current.year + 1, month=1)
            else:
                next_month = current.replace(month=current.month + 1)
            
            period_end = next_month - timedelta(days=1)
            
            periods.append(DynamicPeriod(
                name=current.strftime("%Y-%m"),
                start_date=current,
                end_date=min(period_end, end_date),
                documents=[],
                document_count=0
            ))
            
            current = next_month
        
        return periods
    
    def _generate_quarterly_periods(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[DynamicPeriod]:
        """Generate quarterly periods."""
        periods = []
        current = start_date.replace(day=1, month=((start_date.month - 1) // 3) * 3 + 1)
        
        while current <= end_date:
            # Calculate next quarter
            if current.month + 3 > 12:
                next_quarter = current.replace(year=current.year + 1, month=(current.month + 3) % 12)
            else:
                next_quarter = current.replace(month=current.month + 3)
            
            period_end = next_quarter - timedelta(days=1)
            
            quarter_num = ((current.month - 1) // 3) + 1
            
            periods.append(DynamicPeriod(
                name=f"{current.year}-Q{quarter_num}",
                start_date=current,
                end_date=min(period_end, end_date),
                documents=[],
                document_count=0
            ))
            
            current = next_quarter
        
        return periods
    
    def _generate_yearly_periods(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[DynamicPeriod]:
        """Generate yearly periods."""
        periods = []
        current = start_date.replace(day=1, month=1)
        
        while current <= end_date:
            next_year = current.replace(year=current.year + 1)
            period_end = next_year - timedelta(days=1)
            
            periods.append(DynamicPeriod(
                name=str(current.year),
                start_date=current,
                end_date=min(period_end, end_date),
                documents=[],
                document_count=0
            ))
            
            current = next_year
        
        return periods
    
    def _generate_adaptive_periods(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> List[DynamicPeriod]:
        """Generate adaptive periods based on document density."""
        # For now, use quarterly as default adaptive strategy
        # TODO: Implement true adaptive based on document distribution
        return self._generate_quarterly_periods(start_date, end_date)
    
    async def _place_documents(
        self,
        periods: List[DynamicPeriod],
        documents: List[RelevantDocument]
    ) -> List[DynamicPeriod]:
        """Place documents in appropriate periods."""
        for doc in documents:
            if not doc.last_modified:
                continue
            
            # Find matching period
            for period in periods:
                if period.start_date <= doc.last_modified <= period.end_date:
                    period.documents.append(doc.document_id)
                    period.document_count += 1
                    break
        
        return periods
    
    def _calculate_confidence(self, documents: List[RelevantDocument]) -> str:
        """Calculate timeline confidence based on documents."""
        if not documents:
            return "NONE"
        
        # Check ingestion modes
        git_history_count = sum(
            1 for doc in documents
            if doc.ingestion_mode == "git_history"
        )
        
        # Calculate percentage
        git_percentage = git_history_count / len(documents) if documents else 0
        
        # Determine confidence level
        if git_percentage >= 0.8:
            return "HIGH"
        elif git_percentage >= 0.5:
            return "MEDIUM"
        elif git_percentage >= 0.2:
            return "LOW"
        else:
            return "NONE"
    
    def clear_cache(self):
        """Clear all cached timelines."""
        self._cache.clear()
        logger.info("Cleared dynamic timeline cache")
    
    def cleanup_expired(self):
        """Remove expired timelines from cache."""
        now = datetime.utcnow()
        expired = [
            tid for tid, timeline in self._cache.items()
            if timeline.expires_at <= now
        ]
        
        for tid in expired:
            del self._cache[tid]
        
        logger.info(f"Removed {len(expired)} expired timelines from cache")

