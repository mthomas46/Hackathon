"""
HTTP client for MCP Performance Store service.

Provides methods for recording execution metrics and querying performance data.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from common.http_client import ServiceHTTPClient

logger = logging.getLogger(__name__)


class PerformanceStoreClient:
    """
    Client for interacting with MCP Performance Store service.
    
    Enables other services to:
    - Record orchestration executions
    - Query performance metrics
    - Get analytics and trends
    - Detect anomalies
    """
    
    def __init__(self, base_url: str = "http://localhost:5649"):
        """
        Initialize Performance Store client.
        
        Args:
            base_url: Base URL of Performance Store service
        """
        self.client = ServiceHTTPClient(
            base_url=base_url,
            service_name="mcp-performance-store",
            timeout=30,
            max_retries=3,
        )
        logger.info(f"PerformanceStoreClient initialized for {base_url}")
    
    async def close(self):
        """Close HTTP client."""
        await self.client.close()
    
    async def health_check(self) -> bool:
        """
        Check if Performance Store is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        return await self.client.health_check()
    
    # ========================================================================
    # Execution Recording
    # ========================================================================
    
    async def record_execution(
        self,
        orchestration_id: str,
        mcp_id: str,
        pattern_name: str,
        status: str,
        duration_ms: float,
        query: Optional[str] = None,
        confidence: Optional[float] = None,
        num_sources: Optional[int] = None,
        response_length: Optional[int] = None,
        error_message: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Record an orchestration execution.
        
        Args:
            orchestration_id: Unique execution ID
            mcp_id: MCP that was used
            pattern_name: LLM pattern that was executed
            status: Execution status (success/failed/timeout/cancelled)
            duration_ms: Total duration in milliseconds
            query: Original query (optional)
            confidence: Result confidence (0-1)
            num_sources: Number of sources used
            response_length: Length of response
            error_message: Error message if failed
            metadata: Additional metadata
        
        Returns:
            Recorded execution data
        """
        try:
            payload = {
                "execution_id": orchestration_id,
                "mcp_id": mcp_id,
                "pattern_name": pattern_name,
                "status": status,
                "total_duration_ms": duration_ms,
            }
            
            if query:
                payload["query"] = query
            if confidence is not None:
                payload["confidence"] = confidence
            if num_sources is not None:
                payload["num_sources"] = num_sources
            if response_length is not None:
                payload["response_length"] = response_length
            if error_message:
                payload["error_message"] = error_message
            if metadata:
                payload["metadata"] = metadata
            
            result = await self.client.post("/api/v1/executions", json=payload)
            
            logger.info(
                f"Recorded execution {orchestration_id} "
                f"(pattern={pattern_name}, status={status}, duration={duration_ms}ms)"
            )
            
            return result
        except Exception as e:
            logger.error(f"Failed to record execution {orchestration_id}: {e}")
            # Don't raise - performance recording should not block main workflow
            return {}
    
    async def get_execution(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """
        Get execution by ID.
        
        Args:
            execution_id: Execution ID
        
        Returns:
            Execution data or None if not found
        """
        try:
            return await self.client.get(f"/api/v1/executions/{execution_id}")
        except Exception as e:
            logger.warning(f"Failed to get execution {execution_id}: {e}")
            return None
    
    async def get_recent_executions(
        self,
        limit: int = 10,
        pattern_name: Optional[str] = None,
        mcp_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Get recent executions.
        
        Args:
            limit: Maximum number of executions
            pattern_name: Filter by pattern
            mcp_id: Filter by MCP
        
        Returns:
            List of recent executions
        """
        try:
            params = {"limit": limit}
            if pattern_name:
                params["pattern"] = pattern_name
            if mcp_id:
                params["mcp_id"] = mcp_id
            
            result = await self.client.get("/api/v1/executions/recent", params=params)
            return result.get("executions", [])
        except Exception as e:
            logger.warning(f"Failed to get recent executions: {e}")
            return []
    
    # ========================================================================
    # Performance Metrics
    # ========================================================================
    
    async def get_performance_summary(
        self,
        time_window_hours: int = 24,
        pattern_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get performance summary.
        
        Args:
            time_window_hours: Time window in hours
            pattern_name: Filter by pattern
        
        Returns:
            Performance summary
        """
        try:
            params = {"time_window_hours": time_window_hours}
            if pattern_name:
                params["pattern"] = pattern_name
            
            return await self.client.get("/api/v1/performance/summary", params=params)
        except Exception as e:
            logger.warning(f"Failed to get performance summary: {e}")
            return {}
    
    async def get_pattern_performance(self, pattern_name: str) -> Optional[Dict[str, Any]]:
        """
        Get performance metrics for a specific pattern.
        
        Args:
            pattern_name: Pattern name
        
        Returns:
            Pattern performance data
        """
        try:
            return await self.client.get(f"/api/v1/performance/patterns/{pattern_name}")
        except Exception as e:
            logger.warning(f"Failed to get pattern performance for {pattern_name}: {e}")
            return None
    
    async def list_patterns(self) -> List[str]:
        """
        List all patterns with recorded performance.
        
        Returns:
            List of pattern names
        """
        try:
            result = await self.client.get("/api/v1/performance/patterns")
            return result.get("patterns", [])
        except Exception as e:
            logger.warning(f"Failed to list patterns: {e}")
            return []
    
    # ========================================================================
    # Analytics & Trends
    # ========================================================================
    
    async def get_orchestration_trends(
        self,
        time_window_days: int = 7,
    ) -> Dict[str, Any]:
        """
        Get orchestration performance trends.
        
        Args:
            time_window_days: Time window in days
        
        Returns:
            Trend analysis
        """
        try:
            params = {"days": time_window_days}
            return await self.client.get("/api/v1/analytics/trends/orchestration", params=params)
        except Exception as e:
            logger.warning(f"Failed to get orchestration trends: {e}")
            return {}
    
    async def get_pattern_trends(
        self,
        pattern_name: str,
        time_window_days: int = 7,
    ) -> Dict[str, Any]:
        """
        Get pattern performance trends.
        
        Args:
            pattern_name: Pattern name
            time_window_days: Time window in days
        
        Returns:
            Trend analysis
        """
        try:
            params = {"days": time_window_days}
            return await self.client.get(
                f"/api/v1/analytics/trends/pattern/{pattern_name}",
                params=params
            )
        except Exception as e:
            logger.warning(f"Failed to get pattern trends for {pattern_name}: {e}")
            return {}
    
    async def compare_patterns(
        self,
        pattern1: str,
        pattern2: str,
        time_window_days: int = 7,
    ) -> Dict[str, Any]:
        """
        Compare performance of two patterns.
        
        Args:
            pattern1: First pattern name
            pattern2: Second pattern name
            time_window_days: Time window in days
        
        Returns:
            Comparison analysis
        """
        try:
            params = {
                "pattern1": pattern1,
                "pattern2": pattern2,
                "days": time_window_days,
            }
            return await self.client.get("/api/v1/analytics/comparison", params=params)
        except Exception as e:
            logger.warning(f"Failed to compare patterns {pattern1} vs {pattern2}: {e}")
            return {}
    
    async def get_degrading_patterns(self) -> List[str]:
        """
        Get list of patterns with degrading performance.
        
        Returns:
            List of degrading pattern names
        """
        try:
            result = await self.client.get("/api/v1/analytics/degrading")
            return result.get("degrading_patterns", [])
        except Exception as e:
            logger.warning(f"Failed to get degrading patterns: {e}")
            return []
    
    # ========================================================================
    # Anomaly Detection
    # ========================================================================
    
    async def detect_orchestration_anomalies(
        self,
        time_window_days: int = 7,
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies in orchestration executions.
        
        Args:
            time_window_days: Time window in days
        
        Returns:
            List of detected anomalies
        """
        try:
            params = {"days": time_window_days}
            result = await self.client.get(
                "/api/v1/anomalies/detect/orchestration",
                params=params
            )
            return result.get("anomalies", [])
        except Exception as e:
            logger.warning(f"Failed to detect orchestration anomalies: {e}")
            return []
    
    async def detect_pattern_anomalies(
        self,
        pattern_name: str,
        time_window_days: int = 7,
    ) -> List[Dict[str, Any]]:
        """
        Detect anomalies for a specific pattern.
        
        Args:
            pattern_name: Pattern name
            time_window_days: Time window in days
        
        Returns:
            List of detected anomalies
        """
        try:
            params = {"days": time_window_days}
            result = await self.client.get(
                f"/api/v1/anomalies/detect/pattern/{pattern_name}",
                params=params
            )
            return result.get("anomalies", [])
        except Exception as e:
            logger.warning(f"Failed to detect pattern anomalies for {pattern_name}: {e}")
            return []

