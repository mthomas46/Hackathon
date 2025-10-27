"""
Period Generator

Generates time periods for timelines using various strategies:
- Monthly: One period per month
- Quarterly: One period per quarter
- Adaptive: Based on major commits/releases
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any
from dateutil.relativedelta import relativedelta

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ...storage.db_models import GitCommitModel, DocumentModel
from ...models.timeline import PeriodStrategy, TimePeriodCreate, PeriodMetadata

logger = logging.getLogger(__name__)


class PeriodGenerator:
    """
    Generates time periods for timelines using various strategies.
    
    Supports:
    - Monthly periods
    - Quarterly periods  
    - Adaptive periods (based on commit activity)
    """
    
    def __init__(self, db_session: AsyncSession):
        """
        Initialize period generator.
        
        Args:
            db_session: Async SQLAlchemy session
        """
        self.db = db_session
        self.logger = logging.getLogger(__name__)
    
    async def generate_periods(
        self,
        timeline_id: str,
        service_name: str,
        start_date: datetime,
        end_date: datetime,
        strategy: PeriodStrategy,
        repo_path: str = None
    ) -> List[TimePeriodCreate]:
        """
        Generate time periods for a timeline.
        
        Args:
            timeline_id: Timeline ID
            service_name: Service name
            start_date: Timeline start date
            end_date: Timeline end date
            strategy: Period generation strategy
            repo_path: Optional repository path filter
        
        Returns:
            List of TimePeriodCreate objects
        """
        try:
            # ✅ FIX: Handle both string and enum for period_strategy
            strategy_value = strategy.value if hasattr(strategy, 'value') else str(strategy)
            self.logger.info(
                f"Generating periods using {strategy_value} strategy "
                f"from {start_date.date()} to {end_date.date()}"
            )
            
            # ✅ FIX: Handle both string and enum values for comparison
            strategy_str = str(strategy).lower() if isinstance(strategy, str) else strategy.value
            
            if strategy_str == "monthly":
                periods = await self._generate_monthly_periods(
                    timeline_id, start_date, end_date
                )
            elif strategy_str == "quarterly":
                periods = await self._generate_quarterly_periods(
                    timeline_id, start_date, end_date
                )
            elif strategy_str == "adaptive":
                periods = await self._generate_adaptive_periods(
                    timeline_id, service_name, start_date, end_date, repo_path
                )
            else:
                raise ValueError(f"Unknown strategy: {strategy} (type: {type(strategy)})")
            
            self.logger.info(f"Generated {len(periods)} periods")
            return periods
            
        except Exception as e:
            self.logger.error(f"Failed to generate periods: {e}", exc_info=True)
            raise
    
    async def _generate_monthly_periods(
        self,
        timeline_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[TimePeriodCreate]:
        """
        Generate monthly periods.
        
        Args:
            timeline_id: Timeline ID
            start_date: Start date
            end_date: End date
        
        Returns:
            List of monthly periods
        """
        periods = []
        sequence = 1
        current = start_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        while current <= end_date:
            # Calculate period end (last day of month)
            next_month = current + relativedelta(months=1)
            period_end = next_month - timedelta(seconds=1)
            
            # Don't go past timeline end
            if period_end > end_date:
                period_end = end_date
            
            # Format period name
            month_name = current.strftime("%B %Y")
            
            period = TimePeriodCreate(
                timeline_id=timeline_id,
                name=month_name,
                description=f"Monthly period for {month_name}",
                start_date=current,
                end_date=period_end,
                sequence_number=sequence,
                metadata=PeriodMetadata(
                    tags=["monthly"],
                    extra={"month": current.month, "year": current.year}
                )
            )
            
            periods.append(period)
            sequence += 1
            current = next_month
        
        return periods
    
    async def _generate_quarterly_periods(
        self,
        timeline_id: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[TimePeriodCreate]:
        """
        Generate quarterly periods.
        
        Args:
            timeline_id: Timeline ID
            start_date: Start date
            end_date: End date
        
        Returns:
            List of quarterly periods
        """
        periods = []
        sequence = 1
        
        # Align to quarter start
        quarter_start_month = ((start_date.month - 1) // 3) * 3 + 1
        current = start_date.replace(
            month=quarter_start_month,
            day=1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0
        )
        
        while current <= end_date:
            # Calculate quarter end
            quarter_end = current + relativedelta(months=3) - timedelta(seconds=1)
            
            # Don't go past timeline end
            if quarter_end > end_date:
                quarter_end = end_date
            
            # Format period name (Q1 2025, Q2 2025, etc.)
            quarter = ((current.month - 1) // 3) + 1
            quarter_name = f"Q{quarter} {current.year}"
            
            period = TimePeriodCreate(
                timeline_id=timeline_id,
                name=quarter_name,
                description=f"Quarterly period for {quarter_name}",
                start_date=current,
                end_date=quarter_end,
                sequence_number=sequence,
                metadata=PeriodMetadata(
                    tags=["quarterly"],
                    extra={"quarter": quarter, "year": current.year}
                )
            )
            
            periods.append(period)
            sequence += 1
            current = current + relativedelta(months=3)
        
        return periods
    
    async def _generate_adaptive_periods(
        self,
        timeline_id: str,
        service_name: str,
        start_date: datetime,
        end_date: datetime,
        repo_path: str = None
    ) -> List[TimePeriodCreate]:
        """
        Generate adaptive periods based on commit activity.
        
        Identifies major development periods based on:
        - Commit frequency spikes
        - Major commits (large changes)
        - Natural lulls in activity
        
        Args:
            timeline_id: Timeline ID
            service_name: Service name
            start_date: Start date
            end_date: End date
            repo_path: Optional repository path filter
        
        Returns:
            List of adaptive periods
        """
        try:
            # Get commit activity data
            commit_stats = await self._analyze_commit_activity(
                service_name, start_date, end_date, repo_path
            )
            
            if not commit_stats or len(commit_stats) == 0:
                self.logger.warning(
                    "No commit activity found, falling back to monthly periods"
                )
                return await self._generate_monthly_periods(
                    timeline_id, start_date, end_date
                )
            
            # Identify period boundaries based on activity
            boundaries = self._identify_period_boundaries(
                commit_stats, start_date, end_date
            )
            
            # Create periods from boundaries
            periods = []
            for i, (period_start, period_end, metadata) in enumerate(boundaries, 1):
                # Ensure we don't exceed timeline bounds
                if period_start < start_date:
                    period_start = start_date
                if period_end > end_date:
                    period_end = end_date
                
                period = TimePeriodCreate(
                    timeline_id=timeline_id,
                    name=metadata.get("name", f"Period {i}"),
                    description=metadata.get("description", ""),
                    start_date=period_start,
                    end_date=period_end,
                    sequence_number=i,
                    metadata=PeriodMetadata(
                        tags=["adaptive"],
                        major_commits=metadata.get("major_commits", []),
                        highlights=metadata.get("highlights", []),
                        extra=metadata.get("extra", {})
                    )
                )
                
                periods.append(period)
            
            self.logger.info(f"Generated {len(periods)} adaptive periods")
            return periods
            
        except Exception as e:
            self.logger.error(
                f"Adaptive period generation failed, falling back to monthly: {e}",
                exc_info=True
            )
            return await self._generate_monthly_periods(
                timeline_id, start_date, end_date
            )
    
    async def _analyze_commit_activity(
        self,
        service_name: str,
        start_date: datetime,
        end_date: datetime,
        repo_path: str = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze commit activity to identify major development periods.
        
        Args:
            service_name: Service name
            start_date: Start date
            end_date: End date
            repo_path: Optional repository path filter
        
        Returns:
            List of commit statistics by time bucket
        """
        try:
            # Get commits in date range that are linked to documents from this service
            query = select(
                func.date_trunc('week', GitCommitModel.date).label('week'),
                func.count(GitCommitModel.sha).label('commit_count'),
                func.array_agg(GitCommitModel.sha).label('commit_shas'),
                func.array_agg(GitCommitModel.message).label('commit_messages')
            ).select_from(GitCommitModel).join(
                DocumentModel,
                DocumentModel.git_commit_sha == GitCommitModel.sha
            ).where(
                DocumentModel.service_name == service_name,
                GitCommitModel.date >= start_date,
                GitCommitModel.date <= end_date
            ).group_by('week').order_by('week')
            
            result = await self.db.execute(query)
            
            commit_stats = []
            for row in result:
                commit_stats.append({
                    'week': row.week,
                    'commit_count': row.commit_count,
                    'commit_shas': row.commit_shas,
                    'commit_messages': row.commit_messages
                })
            
            return commit_stats
            
        except Exception as e:
            self.logger.error(f"Failed to analyze commit activity: {e}", exc_info=True)
            return []
    
    def _identify_period_boundaries(
        self,
        commit_stats: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime
    ) -> List[tuple]:
        """
        Identify period boundaries from commit statistics.
        
        Uses heuristics to find natural breaks in development:
        - Low activity periods (< 25% of average)
        - Major activity spikes (> 200% of average)
        
        Args:
            commit_stats: Commit statistics by time bucket
            start_date: Timeline start
            end_date: Timeline end
        
        Returns:
            List of (start_date, end_date, metadata) tuples
        """
        if not commit_stats:
            return [(start_date, end_date, {"name": "Full Period"})]
        
        # Calculate average commit rate
        total_commits = sum(s['commit_count'] for s in commit_stats)
        avg_commits_per_week = total_commits / len(commit_stats)
        
        self.logger.debug(
            f"Average commits per week: {avg_commits_per_week:.1f}"
        )
        
        boundaries = []
        current_period_start = start_date
        current_period_commits = []
        current_period_highlights = []
        
        for i, stat in enumerate(commit_stats):
            week_date = stat['week']
            commit_count = stat['commit_count']
            
            # Check for major activity spike (potential release/milestone)
            is_major_spike = commit_count > (avg_commits_per_week * 2)
            
            # Check for lull (potential period boundary)
            is_lull = commit_count < (avg_commits_per_week * 0.25)
            
            current_period_commits.extend(stat['commit_shas'])
            
            if is_major_spike:
                current_period_highlights.append(
                    f"High activity: {commit_count} commits"
                )
            
            # Create boundary at lulls or major spikes (but not too frequently)
            should_create_boundary = (
                (is_lull or is_major_spike) and
                len(current_period_commits) > 10 and  # At least 10 commits per period
                (week_date - current_period_start).days > 14  # At least 2 weeks
            )
            
            if should_create_boundary or i == len(commit_stats) - 1:
                # Create period
                period_end = week_date
                if i == len(commit_stats) - 1:
                    period_end = end_date
                
                # Generate period name based on characteristics
                period_name = self._generate_period_name(
                    current_period_start,
                    period_end,
                    len(current_period_commits),
                    current_period_highlights
                )
                
                boundaries.append((
                    current_period_start,
                    period_end,
                    {
                        "name": period_name,
                        "description": f"Period from {current_period_start.date()} to {period_end.date()}",
                        "major_commits": current_period_commits[:10],  # Top 10
                        "highlights": current_period_highlights,
                        "extra": {
                            "total_commits": len(current_period_commits),
                            "avg_commits_per_week": len(current_period_commits) / max(1, (period_end - current_period_start).days / 7)
                        }
                    }
                ))
                
                # Reset for next period
                current_period_start = week_date
                current_period_commits = []
                current_period_highlights = []
        
        # Ensure we have at least one period
        if not boundaries:
            boundaries = [(
                start_date,
                end_date,
                {
                    "name": "Full Period",
                    "description": "Complete timeline period",
                    "major_commits": [s['commit_shas'][0] for s in commit_stats[:10] if s['commit_shas']],
                    "highlights": ["Low activity throughout"],
                    "extra": {"total_commits": total_commits}
                }
            )]
        
        return boundaries
    
    def _generate_period_name(
        self,
        start_date: datetime,
        end_date: datetime,
        commit_count: int,
        highlights: List[str]
    ) -> str:
        """
        Generate a descriptive name for an adaptive period.
        
        Args:
            start_date: Period start
            end_date: Period end
            commit_count: Number of commits
            highlights: Period highlights
        
        Returns:
            Period name
        """
        # If high activity, call it "Development Phase"
        if commit_count > 50:
            return f"Major Development ({start_date.strftime('%b %Y')})"
        elif commit_count > 20:
            return f"Active Development ({start_date.strftime('%b %Y')})"
        else:
            return f"Maintenance ({start_date.strftime('%b %Y')})"

