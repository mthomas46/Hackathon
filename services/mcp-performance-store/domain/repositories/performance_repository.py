"""
Performance Repository Interface.

Defines the contract for persisting and querying orchestration executions
and pattern performance metrics.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime

from services.mcp_performance_store.domain.entities import (
    OrchestrationExecution,
    PatternPerformance
)


class PerformanceRepository(ABC):
    """
    Abstract repository for performance data.
    
    Provides methods for storing and querying orchestration executions
    and pattern performance metrics.
    """
    
    # Orchestration Execution Methods
    
    @abstractmethod
    async def save_execution(self, execution: OrchestrationExecution) -> str:
        """
        Save an orchestration execution.
        
        Args:
            execution: The execution to save
        
        Returns:
            The execution_id of the saved execution
        """
        pass
    
    @abstractmethod
    async def get_execution(self, execution_id: str) -> Optional[OrchestrationExecution]:
        """
        Retrieve an execution by ID.
        
        Args:
            execution_id: ID of the execution
        
        Returns:
            The execution, or None if not found
        """
        pass
    
    @abstractmethod
    async def list_executions(
        self,
        mcp_id: Optional[str] = None,
        pattern_used: Optional[str] = None,
        success: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[OrchestrationExecution]:
        """
        List executions with optional filters.
        
        Args:
            mcp_id: Filter by MCP ID
            pattern_used: Filter by pattern
            success: Filter by success status
            start_time: Filter by start time
            end_time: Filter by end time
            limit: Maximum number of results
            offset: Offset for pagination
        
        Returns:
            List of matching executions
        """
        pass
    
    @abstractmethod
    async def count_executions(
        self,
        mcp_id: Optional[str] = None,
        pattern_used: Optional[str] = None,
        success: Optional[bool] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> int:
        """
        Count executions with optional filters.
        
        Args:
            mcp_id: Filter by MCP ID
            pattern_used: Filter by pattern
            success: Filter by success status
            start_time: Filter by start time
            end_time: Filter by end time
        
        Returns:
            Count of matching executions
        """
        pass
    
    @abstractmethod
    async def delete_execution(self, execution_id: str) -> bool:
        """
        Delete an execution.
        
        Args:
            execution_id: ID of the execution to delete
        
        Returns:
            True if deleted, False if not found
        """
        pass
    
    # Pattern Performance Methods
    
    @abstractmethod
    async def save_pattern_performance(self, performance: PatternPerformance) -> str:
        """
        Save or update pattern performance metrics.
        
        Args:
            performance: The pattern performance to save
        
        Returns:
            The pattern_id of the saved performance
        """
        pass
    
    @abstractmethod
    async def get_pattern_performance(self, pattern_id: str) -> Optional[PatternPerformance]:
        """
        Retrieve pattern performance by ID.
        
        Args:
            pattern_id: ID of the pattern
        
        Returns:
            The pattern performance, or None if not found
        """
        pass
    
    @abstractmethod
    async def get_pattern_performance_by_name(
        self,
        pattern_name: str,
        version: Optional[str] = None
    ) -> Optional[PatternPerformance]:
        """
        Retrieve pattern performance by name and version.
        
        Args:
            pattern_name: Name of the pattern
            version: Version of the pattern (optional)
        
        Returns:
            The pattern performance, or None if not found
        """
        pass
    
    @abstractmethod
    async def list_pattern_performances(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[PatternPerformance]:
        """
        List all pattern performances.
        
        Args:
            limit: Maximum number of results
            offset: Offset for pagination
        
        Returns:
            List of pattern performances
        """
        pass
    
    @abstractmethod
    async def delete_pattern_performance(self, pattern_id: str) -> bool:
        """
        Delete pattern performance.
        
        Args:
            pattern_id: ID of the pattern
        
        Returns:
            True if deleted, False if not found
        """
        pass
    
    # Analytics Methods
    
    @abstractmethod
    async def get_execution_stats_by_pattern(
        self,
        pattern_used: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated statistics for a pattern.
        
        Args:
            pattern_used: Pattern to analyze
            start_time: Start of time range
            end_time: End of time range
        
        Returns:
            Dictionary of statistics (avg_latency, success_rate, etc.)
        """
        pass
    
    @abstractmethod
    async def get_execution_stats_by_mcp(
        self,
        mcp_id: str,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get aggregated statistics for an MCP.
        
        Args:
            mcp_id: MCP to analyze
            start_time: Start of time range
            end_time: End of time range
        
        Returns:
            Dictionary of statistics
        """
        pass
    
    @abstractmethod
    async def get_latency_percentiles(
        self,
        pattern_used: Optional[str] = None,
        mcp_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, float]:
        """
        Calculate latency percentiles (p50, p95, p99).
        
        Args:
            pattern_used: Optional pattern filter
            mcp_id: Optional MCP filter
            start_time: Start of time range
            end_time: End of time range
        
        Returns:
            Dictionary with p50, p95, p99 latency values
        """
        pass
    
    @abstractmethod
    async def detect_anomalies(
        self,
        pattern_used: Optional[str] = None,
        threshold_factor: float = 2.0
    ) -> List[OrchestrationExecution]:
        """
        Detect anomalous executions based on latency.
        
        Args:
            pattern_used: Optional pattern filter
            threshold_factor: How many times the baseline to consider anomalous
        
        Returns:
            List of anomalous executions
        """
        pass
    
    @abstractmethod
    async def get_trend_data(
        self,
        pattern_used: str,
        time_window_minutes: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Get time-series data for trend analysis.
        
        Args:
            pattern_used: Pattern to analyze
            time_window_minutes: Size of time buckets
        
        Returns:
            List of time-bucketed metrics
        """
        pass
