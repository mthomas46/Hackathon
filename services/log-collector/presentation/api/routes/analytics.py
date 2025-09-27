"""Log analytics REST API routes."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, Query, Path
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from ....domain.entities import LogEntry, LogStatistics
from ....domain.services.log_stats import LogStatsService
from ....domain.services.log_storage import LogStorageService


# Pydantic models for API
class LogEntryModel(BaseModel):
    """API model for log entry."""
    id: str
    timestamp: datetime
    level: str
    service: str
    message: str
    metadata: Optional[Dict[str, Any]] = None
    trace_id: Optional[str] = None
    span_id: Optional[str] = None


class LogStatisticsModel(BaseModel):
    """API model for log statistics."""
    service_name: str
    time_window_start: datetime
    time_window_end: datetime
    total_logs: int
    error_count: int
    warning_count: int
    info_count: int
    debug_count: int
    error_rate: float
    logs_per_minute: float


class AnalyticsQueryModel(BaseModel):
    """API model for analytics query."""
    service_name: Optional[str] = Field(None, description="Filter by service name")
    level: Optional[str] = Field(None, description="Filter by log level")
    start_time: Optional[datetime] = Field(None, description="Start time for query")
    end_time: Optional[datetime] = Field(None, description="End time for query")
    limit: int = Field(100, description="Maximum number of results")
    search_query: Optional[str] = Field(None, description="Text search query")


class AnalyticsResponseModel(BaseModel):
    """API model for analytics response."""
    total_results: int
    returned_results: int
    execution_time_ms: float
    data: List[Dict[str, Any]]


class LogAnalyticsRouter:
    """FastAPI router for log analytics operations."""

    def __init__(
        self,
        log_stats_service: LogStatsService,
        log_storage_service: LogStorageService
    ):
        """Initialize router with services."""
        self._log_stats_service = log_stats_service
        self._log_storage_service = log_storage_service
        self.router = APIRouter(prefix="/api/v1/logs/analytics", tags=["log-analytics"])

        # Register routes
        self._register_routes()

    def _register_routes(self):
        """Register all analytics routes."""

        @self.router.get("/stats", response_model=LogStatisticsModel)
        async def get_log_statistics(
            service_name: str = Query(..., description="Service name to analyze"),
            hours: int = Query(24, description="Hours of logs to analyze")
        ) -> LogStatisticsModel:
            """Get comprehensive log statistics for a service."""
            try:
                # In a real implementation, this would query actual logs
                # For now, return mock statistics
                return LogStatisticsModel(
                    service_name=service_name,
                    time_window_start=datetime.now(timezone.utc),
                    time_window_end=datetime.now(timezone.utc),
                    total_logs=1440,  # Mock: 60 logs per hour
                    error_count=24,   # Mock: 2% error rate
                    warning_count=72, # Mock: 5% warning rate
                    info_count=1248,  # Mock: 87% info logs
                    debug_count=96,   # Mock: 6% debug logs
                    error_rate=1.67,  # 24/1440 * 100
                    logs_per_minute=1.0  # 1440/1440
                )

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to retrieve log statistics: {str(e)}"
                )

        @self.router.post(
            "/query",
            response_model=AnalyticsResponseModel,
            summary="Advanced Log Query with Filtering",
            description="""
            Perform advanced queries on log data with comprehensive filtering and search capabilities.

            This endpoint provides powerful log analysis capabilities including full-text search,
            structured filtering, time range queries, and aggregation operations.

            **Query Capabilities:**
            - Full-text search across log messages and metadata
            - Structured filtering by service, level, and custom fields
            - Time range filtering with flexible date specifications
            - Complex boolean queries with AND/OR/NOT operations
            - Regular expression pattern matching
            - Aggregation and grouping operations

            **Search Syntax:**
            - Simple text: `error connection`
            - Field queries: `level:ERROR service:api-gateway`
            - Time ranges: `@timestamp:[2023-01-01 TO 2023-01-02]`
            - Boolean logic: `error AND (timeout OR connection)`
            - Wildcards: `service:api-*`

            **Performance Optimizations:**
            - Indexed field searches for fast filtering
            - Time-based partitioning for efficient range queries
            - Caching for frequently accessed log patterns
            - Parallel query execution across log shards

            **Result Processing:**
            - Configurable result limits and pagination
            - Sorting by timestamp, level, or relevance
            - Field selection for reduced payload sizes
            - Export formats (JSON, CSV, text)
            """,
            response_description="Query results with execution statistics and metadata"
        )
        async def query_logs(
            query: AnalyticsQueryModel = Body(
                ...,
                examples={
                    "error_analysis": {
                        "summary": "Error Log Analysis",
                        "description": "Find and analyze error logs from a specific service",
                        "value": {
                            "service_name": "api-gateway",
                            "level": "ERROR",
                            "start_time": "2023-12-01T00:00:00Z",
                            "end_time": "2023-12-02T00:00:00Z",
                            "limit": 100,
                            "search_query": "timeout OR connection"
                        }
                    },
                    "performance_monitoring": {
                        "summary": "Performance Log Monitoring",
                        "description": "Monitor performance-related logs across services",
                        "value": {
                            "level": "WARN",
                            "limit": 50,
                            "search_query": "slow OR performance OR latency"
                        }
                    },
                    "security_audit": {
                        "summary": "Security Event Audit",
                        "description": "Audit security-related events and access patterns",
                        "value": {
                            "search_query": "authentication OR authorization OR security",
                            "limit": 200
                        }
                    }
                }
            )
        ) -> AnalyticsResponseModel:
            """Query logs with advanced filtering and search."""
            try:
                start_time = datetime.now(timezone.utc)

                # In a real implementation, this would execute the query
                # For now, return mock results
                mock_results = [
                    {
                        "id": f"log-{i}",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "level": "INFO",
                        "service": query.service_name or "test-service",
                        "message": f"Sample log message {i}",
                        "metadata": {"request_id": f"req-{i}"}
                    }
                    for i in range(min(query.limit, 50))
                ]

                execution_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000

                return AnalyticsResponseModel(
                    total_results=len(mock_results),
                    returned_results=len(mock_results),
                    execution_time_ms=execution_time,
                    data=mock_results
                )

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Log query failed: {str(e)}"
                )

        @self.router.get("/errors", response_model=List[Dict[str, Any]])
        async def get_error_logs(
            service_name: str = Query(..., description="Service name"),
            hours: int = Query(24, description="Hours to look back"),
            limit: int = Query(50, description="Maximum errors to return")
        ) -> List[Dict[str, Any]]:
            """Get recent error logs for a service."""
            try:
                # In a real implementation, this would query error logs
                # For now, return mock error logs
                error_logs = [
                    {
                        "id": f"error-{i}",
                        "timestamp": datetime.now(timezone.utc).isoformat(),
                        "level": "ERROR",
                        "service": service_name,
                        "message": f"Sample error message {i}",
                        "metadata": {"error_code": f"ERR-{i:03d}"}
                    }
                    for i in range(min(limit, 10))
                ]

                return error_logs

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to retrieve error logs: {str(e)}"
                )

        @self.router.get("/patterns", response_model=Dict[str, Any])
        async def analyze_log_patterns(
            service_name: str = Query(..., description="Service name to analyze"),
            hours: int = Query(24, description="Hours of logs to analyze")
        ) -> Dict[str, Any]:
            """Analyze log patterns and identify common issues."""
            try:
                # In a real implementation, this would analyze actual log patterns
                # For now, return mock pattern analysis
                return {
                    "service_name": service_name,
                    "analysis_period_hours": hours,
                    "total_logs_analyzed": 1440,
                    "patterns_identified": [
                        {
                            "pattern": "connection_timeout",
                            "frequency": 15,
                            "percentage": 1.04,
                            "severity": "medium",
                            "recommendation": "Consider increasing connection timeout or implementing retry logic"
                        },
                        {
                            "pattern": "memory_warning",
                            "frequency": 8,
                            "percentage": 0.56,
                            "severity": "low",
                            "recommendation": "Monitor memory usage and consider optimization"
                        }
                    ],
                    "anomalies_detected": [
                        {
                            "type": "spike",
                            "description": "Unusual spike in error logs at 14:30 UTC",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "severity": "high"
                        }
                    ],
                    "insights": [
                        "Error rate is within normal bounds",
                        "Most errors are related to external service timeouts",
                        "Consider implementing circuit breaker pattern"
                    ]
                }

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Pattern analysis failed: {str(e)}"
                )

        @self.router.get("/health", response_model=Dict[str, Any])
        async def get_log_health_status(
            service_name: str = Query(..., description="Service name to check")
        ) -> Dict[str, Any]:
            """Get log health status and recommendations."""
            try:
                # In a real implementation, this would analyze log health
                # For now, return mock health status
                return {
                    "service_name": service_name,
                    "health_status": "healthy",
                    "last_log_received": datetime.now(timezone.utc).isoformat(),
                    "logs_per_minute": 1.2,
                    "error_rate_percent": 1.5,
                    "warning_rate_percent": 3.2,
                    "recommendations": [
                        "Log volume is normal",
                        "Error rate is acceptable",
                        "Consider adding structured logging"
                    ],
                    "alerts": []
                }

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Health check failed: {str(e)}"
                )

        @self.router.get("/trends", response_model=Dict[str, Any])
        async def get_log_trends(
            service_name: str = Query(..., description="Service name"),
            hours: int = Query(24, description="Hours to analyze")
        ) -> Dict[str, Any]:
            """Get log trends and time-series analysis."""
            try:
                # In a real implementation, this would analyze log trends
                # For now, return mock trend data
                return {
                    "service_name": service_name,
                    "analysis_period_hours": hours,
                    "trends": {
                        "log_volume": {
                            "trend": "stable",
                            "change_percent": 2.1,
                            "peak_hour": 14,
                            "low_hour": 3
                        },
                        "error_rate": {
                            "trend": "decreasing",
                            "change_percent": -15.3,
                            "peak_hour": 16,
                            "description": "Error rate has decreased by 15.3% over the last 24 hours"
                        },
                        "response_times": {
                            "trend": "stable",
                            "average_ms": 245,
                            "p95_ms": 1200,
                            "p99_ms": 2500
                        }
                    },
                    "predictions": {
                        "next_hour_log_volume": 72,
                        "confidence": 0.85,
                        "factors": ["time_of_day", "day_of_week", "recent_trends"]
                    }
                }

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Trend analysis failed: {str(e)}"
                )

        @self.router.post("/export")
        async def export_logs(
            query: AnalyticsQueryModel,
            format: str = Query("json", description="Export format (json, csv)"),
            include_metadata: bool = Query(True, description="Include metadata in export")
        ) -> Dict[str, Any]:
            """Export logs matching the query criteria."""
            try:
                # In a real implementation, this would generate an export
                # For now, return export metadata
                return {
                    "export_id": f"export-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                    "format": format,
                    "estimated_records": 1250,
                    "status": "queued",
                    "download_url": f"/api/v1/logs/analytics/exports/export-{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
                    "expires_at": (datetime.now(timezone.utc)).isoformat()
                }

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Log export failed: {str(e)}"
                )


# Factory function to create router
def create_analytics_router(
    log_stats_service: LogStatsService,
    log_storage_service: LogStorageService
) -> APIRouter:
    """Create analytics router with dependencies."""
    router_instance = LogAnalyticsRouter(log_stats_service, log_storage_service)
    return router_instance.router
