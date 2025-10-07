"""Client for MCP Performance Store API."""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from clients.base_client import BaseClient


logger = logging.getLogger(__name__)


class PerformanceStoreClient(BaseClient):
    """Client for interacting with MCP Performance Store."""
    
    def __init__(self, base_url: str = "http://localhost:5649"):
        """Initialize the Performance Store client."""
        super().__init__(base_url)
    
    # ==================== Execution Recording ====================
    
    async def record_execution(
        self,
        orchestration_id: str,
        pattern_name: str,
        mcp_id: str,
        status: str,
        duration_ms: float,
        **kwargs
    ) -> Dict[str, Any]:
        """Record an execution."""
        payload = {
            "orchestration_id": orchestration_id,
            "pattern_name": pattern_name,
            "mcp_id": mcp_id,
            "status": status,
            "duration_ms": duration_ms,
            **kwargs
        }
        return await self.post("/api/v1/executions", json=payload)
    
    # ==================== Execution Queries ====================
    
    async def get_execution(self, execution_id: str) -> Dict[str, Any]:
        """Get a specific execution by ID."""
        return await self.get(f"/api/v1/executions/{execution_id}")
    
    async def get_recent_executions(
        self,
        limit: int = 10,
        status: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Get recent executions."""
        params = {"limit": limit}
        if status:
            params["status"] = status
        return await self.get("/api/v1/executions/recent", params=params)
    
    async def get_executions_by_mcp(
        self,
        mcp_id: str,
        limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get executions for a specific MCP."""
        return await self.get(
            f"/api/v1/executions/mcp/{mcp_id}",
            params={"limit": limit}
        )
    
    # ==================== Performance Metrics ====================
    
    async def get_performance_summary(
        self,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """Get performance summary."""
        return await self.get(
            "/api/v1/performance/summary",
            params={"time_window_hours": time_window_hours}
        )
    
    async def get_pattern_metrics(
        self,
        pattern_name: str,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """Get metrics for a specific pattern."""
        return await self.get(
            f"/api/v1/performance/patterns/{pattern_name}",
            params={"time_window_hours": time_window_hours}
        )
    
    async def get_mcp_metrics(
        self,
        mcp_id: str,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """Get metrics for a specific MCP."""
        return await self.get(
            f"/api/v1/performance/mcps/{mcp_id}",
            params={"time_window_hours": time_window_hours}
        )
    
    # ==================== Analytics ====================
    
    async def get_orchestration_trends(
        self,
        time_window_days: int = 7
    ) -> Dict[str, Any]:
        """Analyze orchestration performance trends."""
        return await self.get(
            "/api/v1/analytics/trends/orchestration",
            params={"time_window_days": time_window_days}
        )
    
    async def get_pattern_trends(
        self,
        pattern_name: str
    ) -> Dict[str, Any]:
        """Analyze trends for a specific pattern."""
        return await self.get(f"/api/v1/analytics/trends/pattern/{pattern_name}")
    
    async def compare_patterns(self) -> Dict[str, Any]:
        """Compare performance across all patterns."""
        return await self.get("/api/v1/analytics/compare/patterns")
    
    async def detect_degradation(
        self,
        threshold_percent: float = 20.0
    ) -> Dict[str, Any]:
        """Detect performance degradation."""
        return await self.get(
            "/api/v1/analytics/degradation",
            params={"threshold_percent": threshold_percent}
        )
    
    # ==================== Anomaly Detection ====================
    
    async def detect_orchestration_anomalies(
        self,
        days: int = 7
    ) -> Dict[str, Any]:
        """Detect anomalies in orchestration executions."""
        return await self.get(
            "/api/v1/anomalies/detect/orchestration",
            params={"days": days}
        )
    
    async def detect_pattern_anomalies(
        self,
        pattern_name: str,
        days: int = 7
    ) -> Dict[str, Any]:
        """Detect anomalies for a specific pattern."""
        return await self.get(
            f"/api/v1/anomalies/detect/pattern/{pattern_name}",
            params={"days": days}
        )
