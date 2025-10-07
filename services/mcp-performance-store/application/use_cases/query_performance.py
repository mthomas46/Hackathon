"""Query Performance Use Case - Application Layer.

Handles querying executions and retrieving performance metrics.
"""

import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from services.mcp_performance_store.domain.entities.orchestration_execution import OrchestrationExecution
from services.mcp_performance_store.domain.entities.pattern_performance import PatternPerformance
from services.mcp_performance_store.domain.value_objects.execution_status import ExecutionStatus
from services.mcp_performance_store.domain.repositories.execution_repository import (
    ExecutionRepository,
    EntityNotFoundError,
)
from services.mcp_performance_store.domain.repositories.pattern_performance_repository import (
    PatternPerformanceRepository,
)

logger = logging.getLogger(__name__)


class QueryPerformanceError(Exception):
    """Raised when querying performance fails."""
    pass


class QueryPerformanceUseCase:
    """
    Use case for querying performance metrics and executions.
    
    Provides methods to query executions by various criteria and
    retrieve aggregated performance metrics for patterns.
    """
    
    def __init__(
        self,
        execution_repo: ExecutionRepository,
        pattern_repo: PatternPerformanceRepository
    ):
        """
        Initialize use case.
        
        Args:
            execution_repo: Repository for execution queries
            pattern_repo: Repository for pattern performance queries
        """
        self.execution_repo = execution_repo
        self.pattern_repo = pattern_repo
        logger.info("QueryPerformanceUseCase initialized")
    
    # ==================== Execution Queries ====================
    
    async def get_execution(self, execution_id: str) -> OrchestrationExecution:
        """
        Get an execution by ID.
        
        Args:
            execution_id: The execution ID
            
        Returns:
            The execution
            
        Raises:
            QueryPerformanceError: If execution not found or query fails
        """
        try:
            execution = await self.execution_repo.get_by_id(execution_id)
            if execution is None:
                raise QueryPerformanceError(f"Execution {execution_id} not found")
            return execution
        except QueryPerformanceError:
            raise
        except Exception as e:
            logger.error(f"Failed to get execution {execution_id}: {e}")
            raise QueryPerformanceError(f"Failed to get execution: {e}")
    
    async def get_recent_executions(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[OrchestrationExecution]:
        """
        Get recent executions.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of recent executions
        """
        try:
            return await self.execution_repo.get_recent(limit=limit, offset=offset)
        except Exception as e:
            logger.error(f"Failed to get recent executions: {e}")
            raise QueryPerformanceError(f"Failed to get recent executions: {e}")
    
    async def get_executions_by_pattern(
        self,
        pattern_name: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[OrchestrationExecution]:
        """
        Get executions for a specific pattern.
        
        Args:
            pattern_name: The pattern name
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of executions for the pattern
        """
        try:
            return await self.execution_repo.get_by_pattern(
                pattern_name=pattern_name,
                limit=limit,
                offset=offset
            )
        except Exception as e:
            logger.error(f"Failed to get executions for pattern {pattern_name}: {e}")
            raise QueryPerformanceError(f"Failed to get executions by pattern: {e}")
    
    async def get_executions_by_status(
        self,
        status: ExecutionStatus,
        limit: int = 100,
        offset: int = 0
    ) -> List[OrchestrationExecution]:
        """
        Get executions by status.
        
        Args:
            status: The execution status
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List of executions with that status
        """
        try:
            return await self.execution_repo.get_by_status(
                status=status,
                limit=limit,
                offset=offset
            )
        except Exception as e:
            logger.error(f"Failed to get executions by status {status}: {e}")
            raise QueryPerformanceError(f"Failed to get executions by status: {e}")
    
    async def get_executions_by_date_range(
        self,
        start: datetime,
        end: datetime,
        limit: int = 1000
    ) -> List[OrchestrationExecution]:
        """
        Get executions within a date range.
        
        Args:
            start: Start datetime
            end: End datetime
            limit: Maximum number of results
            
        Returns:
            List of executions in date range
        """
        try:
            return await self.execution_repo.get_by_date_range(
                start=start,
                end=end,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get executions by date range: {e}")
            raise QueryPerformanceError(f"Failed to get executions by date range: {e}")
    
    async def get_executions_by_composition(
        self,
        composition_id: str,
        limit: int = 100
    ) -> List[OrchestrationExecution]:
        """
        Get executions for a specific composition.
        
        Args:
            composition_id: The composition ID
            limit: Maximum number of results
            
        Returns:
            List of executions for the composition
        """
        try:
            return await self.execution_repo.get_by_composition(
                composition_id=composition_id,
                limit=limit
            )
        except Exception as e:
            logger.error(f"Failed to get executions for composition {composition_id}: {e}")
            raise QueryPerformanceError(f"Failed to get executions by composition: {e}")
    
    # ==================== Pattern Performance Queries ====================
    
    async def get_pattern_performance(self, pattern_name: str) -> PatternPerformance:
        """
        Get performance metrics for a pattern.
        
        Args:
            pattern_name: The pattern name
            
        Returns:
            Pattern performance metrics
            
        Raises:
            QueryPerformanceError: If pattern not found or query fails
        """
        try:
            performance = await self.pattern_repo.get_by_pattern(pattern_name)
            if performance is None:
                raise QueryPerformanceError(f"Pattern {pattern_name} not found")
            return performance
        except QueryPerformanceError:
            raise
        except Exception as e:
            logger.error(f"Failed to get pattern performance for {pattern_name}: {e}")
            raise QueryPerformanceError(f"Failed to get pattern performance: {e}")
    
    async def get_all_patterns(self) -> List[PatternPerformance]:
        """
        Get performance metrics for all patterns.
        
        Returns:
            List of all pattern performances
        """
        try:
            return await self.pattern_repo.get_all()
        except Exception as e:
            logger.error(f"Failed to get all patterns: {e}")
            raise QueryPerformanceError(f"Failed to get all patterns: {e}")
    
    async def get_top_performers(self, limit: int = 10) -> List[PatternPerformance]:
        """
        Get top performing patterns.
        
        Args:
            limit: Maximum number of results
            
        Returns:
            List of top performing patterns
        """
        try:
            return await self.pattern_repo.get_top_performers(limit=limit)
        except Exception as e:
            logger.error(f"Failed to get top performers: {e}")
            raise QueryPerformanceError(f"Failed to get top performers: {e}")
    
    async def get_degrading_patterns(self) -> List[PatternPerformance]:
        """
        Get patterns with degrading performance.
        
        Returns:
            List of degrading patterns
        """
        try:
            return await self.pattern_repo.get_degrading_patterns()
        except Exception as e:
            logger.error(f"Failed to get degrading patterns: {e}")
            raise QueryPerformanceError(f"Failed to get degrading patterns: {e}")
    
    # ==================== Summary & Metrics ====================
    
    async def get_summary(self) -> Dict[str, Any]:
        """
        Get overall performance summary.
        
        Returns:
            Dictionary with summary metrics
        """
        try:
            # Get counts
            total_executions = await self.execution_repo.count()
            success_count = await self.execution_repo.count_by_status(ExecutionStatus.SUCCESS)
            failed_count = await self.execution_repo.count_by_status(ExecutionStatus.FAILED)
            timeout_count = await self.execution_repo.count_by_status(ExecutionStatus.TIMEOUT)
            
            # Calculate rates
            success_rate = success_count / total_executions if total_executions > 0 else 0.0
            failure_rate = failed_count / total_executions if total_executions > 0 else 0.0
            timeout_rate = timeout_count / total_executions if total_executions > 0 else 0.0
            
            # Get pattern count
            patterns_count = await self.pattern_repo.count()
            
            # Get recent executions for avg duration
            recent = await self.execution_repo.get_recent(limit=100)
            avg_duration_ms = 0.0
            if recent:
                durations = [e.total_duration_ms for e in recent if e.total_duration_ms > 0]
                avg_duration_ms = sum(durations) / len(durations) if durations else 0.0
            
            # Get degrading patterns count
            degrading = await self.pattern_repo.get_degrading_patterns()
            
            return {
                "total_executions": total_executions,
                "successful_executions": success_count,
                "failed_executions": failed_count,
                "timeout_executions": timeout_count,
                "success_rate": success_rate,
                "failure_rate": failure_rate,
                "timeout_rate": timeout_rate,
                "patterns_tracked": patterns_count,
                "degrading_patterns_count": len(degrading),
                "avg_duration_ms": avg_duration_ms,
            }
        except Exception as e:
            logger.error(f"Failed to get summary: {e}")
            raise QueryPerformanceError(f"Failed to get summary: {e}")
    
    async def get_trends(self, hours: int = 24) -> Dict[str, Any]:
        """
        Get performance trends over time.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            Dictionary with trend data
        """
        try:
            # Get executions in time range
            end = datetime.now()
            start = end - timedelta(hours=hours)
            executions = await self.execution_repo.get_by_date_range(start, end)
            
            # Calculate metrics
            total = len(executions)
            if total == 0:
                return {
                    "hours": hours,
                    "total_executions": 0,
                    "success_rate": 0.0,
                    "avg_duration_ms": 0.0,
                    "patterns_used": 0,
                }
            
            success = sum(1 for e in executions if e.status == ExecutionStatus.SUCCESS)
            durations = [e.total_duration_ms for e in executions if e.total_duration_ms > 0]
            patterns = set(e.pattern_name for e in executions if e.pattern_name)
            
            return {
                "hours": hours,
                "total_executions": total,
                "successful_executions": success,
                "failed_executions": sum(1 for e in executions if e.status == ExecutionStatus.FAILED),
                "timeout_executions": sum(1 for e in executions if e.status == ExecutionStatus.TIMEOUT),
                "success_rate": success / total,
                "avg_duration_ms": sum(durations) / len(durations) if durations else 0.0,
                "min_duration_ms": min(durations) if durations else 0.0,
                "max_duration_ms": max(durations) if durations else 0.0,
                "patterns_used": len(patterns),
            }
        except Exception as e:
            logger.error(f"Failed to get trends: {e}")
            raise QueryPerformanceError(f"Failed to get trends: {e}")
