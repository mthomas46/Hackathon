"""
Use case for retrieving pattern performance metrics.
"""
import logging
from typing import Optional

from services.mcp_performance_store.domain.repositories import PerformanceRepository
from services.mcp_performance_store.application.dto import PatternPerformanceResponse, TimeWindowMetricsResponse


class GetPatternPerformanceUseCase:
    """
    Use case for retrieving pattern performance metrics.
    
    Handles fetching and converting pattern performance data.
    """
    
    def __init__(self, repository: PerformanceRepository):
        """
        Initialize use case.
        
        Args:
            repository: Performance repository
        """
        self.repository = repository
        self.logger = logging.getLogger(__name__)
    
    async def execute_by_id(self, pattern_id: str) -> Optional[PatternPerformanceResponse]:
        """
        Get pattern performance by ID.
        
        Args:
            pattern_id: Pattern ID
        
        Returns:
            Pattern performance response or None
        """
        self.logger.info(f"Retrieving pattern performance for ID: {pattern_id}")
        
        performance = await self.repository.get_pattern_performance(pattern_id)
        
        if performance is None:
            self.logger.warning(f"Pattern performance not found: {pattern_id}")
            return None
        
        return self._to_response(performance)
    
    async def execute_by_name(
        self,
        pattern_name: str,
        version: Optional[str] = None
    ) -> Optional[PatternPerformanceResponse]:
        """
        Get pattern performance by name and version.
        
        Args:
            pattern_name: Pattern name
            version: Pattern version (optional)
        
        Returns:
            Pattern performance response or None
        """
        self.logger.info(
            f"Retrieving pattern performance for: {pattern_name} "
            f"version={version or 'latest'}"
        )
        
        performance = await self.repository.get_pattern_performance_by_name(
            pattern_name,
            version
        )
        
        if performance is None:
            self.logger.warning(
                f"Pattern performance not found: {pattern_name} v{version}"
            )
            return None
        
        return self._to_response(performance)
    
    def _to_response(self, performance) -> PatternPerformanceResponse:
        """Convert pattern performance entity to response DTO."""
        overall_score = performance.calculate_overall_score()
        health_status = performance.get_health_status()
        
        return PatternPerformanceResponse(
            pattern_id=performance.pattern_id,
            pattern_name=performance.pattern_name,
            version=performance.version,
            total_executions=performance.total_executions,
            success_rate=performance.success_rate,
            avg_latency_ms=performance.avg_latency_ms,
            p50_latency_ms=performance.p50_latency_ms,
            p95_latency_ms=performance.p95_latency_ms,
            p99_latency_ms=performance.p99_latency_ms,
            avg_cost_cents=performance.avg_cost_cents,
            avg_accuracy=performance.avg_accuracy,
            avg_confidence=performance.avg_confidence,
            last_hour=TimeWindowMetricsResponse(**performance.last_hour.dict()),
            last_day=TimeWindowMetricsResponse(**performance.last_day.dict()),
            last_week=TimeWindowMetricsResponse(**performance.last_week.dict()),
            last_month=TimeWindowMetricsResponse(**performance.last_month.dict()),
            trend_direction=performance.trend_direction.value,
            anomalies_detected=performance.anomalies_detected,
            health_status=health_status,
            overall_score=overall_score,
            last_updated=performance.last_updated,
            created_at=performance.created_at
        )
