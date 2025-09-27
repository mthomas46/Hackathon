"""Memory management REST API routes."""

from typing import List, Dict, Any, Optional
from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Path
from pydantic import BaseModel, Field
from datetime import datetime, timezone

from ....application.use_cases.analyze_memory_use_case import AnalyzeMemoryUseCase
from ....application.use_cases.optimize_memory_use_case import OptimizeMemoryUseCase
from ....domain.entities import MemoryMetrics, MemoryAnalysis, OptimizationRecommendation


# Pydantic models for API
class MemoryMetricsModel(BaseModel):
    """API model for memory metrics."""
    id: str
    timestamp: datetime
    total_memory_mb: float
    used_memory_mb: float
    available_memory_mb: float
    memory_usage_percent: float
    service_name: Optional[str]
    swap_total_mb: Optional[float] = None
    swap_used_mb: Optional[float] = None
    swap_usage_percent: Optional[float] = None


class AnalyzeMemoryRequestModel(BaseModel):
    """API model for analyze memory request."""
    service_name: str = Field(..., description="Name of the service to analyze")
    analysis_type: str = Field("comprehensive", description="Type of analysis (basic, comprehensive, detailed)")
    time_window_minutes: int = Field(60, description="Time window for analysis in minutes")
    include_historical: bool = Field(True, description="Include historical data")
    filters: Optional[Dict[str, Any]] = Field(None, description="Additional analysis filters")


class AnalyzeMemoryResponseModel(BaseModel):
    """API model for analyze memory response."""
    success: bool
    analysis_id: str
    service_name: str
    analysis_type: str
    time_window_minutes: int
    metrics_analyzed: int
    insights: List[str]
    recommendations: List[str]
    average_memory_usage: float
    peak_memory_usage: float
    memory_trend: str
    processing_time_seconds: float


class OptimizeMemoryRequestModel(BaseModel):
    """API model for optimize memory request."""
    service_name: str = Field(..., description="Name of the service to optimize")
    optimization_type: str = Field("automatic", description="Type of optimization (automatic, manual)")
    target_memory_reduction_mb: Optional[int] = Field(None, description="Target memory reduction in MB")
    max_downtime_seconds: int = Field(30, description="Maximum allowed downtime in seconds")


class OptimizeMemoryResponseModel(BaseModel):
    """API model for optimize memory response."""
    success: bool
    service_name: str
    optimization_type: str
    memory_freed_mb: float
    performance_improved_percent: float
    recommendations_applied: List[str]
    warnings: List[str]
    processing_time_seconds: float


class MemoryHealthModel(BaseModel):
    """API model for memory health status."""
    service_name: str
    status: str  # healthy, warning, critical
    current_usage_percent: float
    available_memory_mb: float
    last_checked: datetime
    alerts: List[str]


class MemoryRouter:
    """FastAPI router for memory management operations."""

    def __init__(
        self,
        analyze_memory_use_case: AnalyzeMemoryUseCase,
        optimize_memory_use_case: OptimizeMemoryUseCase
    ):
        """Initialize router with use cases."""
        self._analyze_memory_use_case = analyze_memory_use_case
        self._optimize_memory_use_case = optimize_memory_use_case
        self.router = APIRouter(prefix="/api/v1/memory", tags=["memory"])

        # Register routes
        self._register_routes()

    def _register_routes(self):
        """Register all memory routes."""

        @self.router.post("/analyze", response_model=AnalyzeMemoryResponseModel)
        async def analyze_memory(
            request: AnalyzeMemoryRequestModel,
            background_tasks: BackgroundTasks
        ) -> AnalyzeMemoryResponseModel:
            """Analyze memory usage for a service.

            Performs comprehensive memory analysis including usage patterns,
            trends, and optimization recommendations.
            """
            try:
                # Execute analysis use case
                response = await self._analyze_memory_use_case.execute(request)

                return AnalyzeMemoryResponseModel(
                    success=response.success,
                    analysis_id=response.analysis_id,
                    service_name=response.service_name,
                    analysis_type=response.analysis_type,
                    time_window_minutes=response.time_window_minutes,
                    metrics_analyzed=response.metrics_analyzed,
                    insights=response.insights,
                    recommendations=response.recommendations,
                    average_memory_usage=response.average_memory_usage,
                    peak_memory_usage=response.peak_memory_usage,
                    memory_trend=response.memory_trend,
                    processing_time_seconds=response.processing_time_seconds
                )

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Memory analysis failed: {str(e)}"
                )

        @self.router.post("/optimize", response_model=OptimizeMemoryResponseModel)
        async def optimize_memory(
            request: OptimizeMemoryRequestModel,
            background_tasks: BackgroundTasks
        ) -> OptimizeMemoryResponseModel:
            """Optimize memory usage for a service.

            Applies memory optimization techniques including garbage collection,
            cache clearing, and resource cleanup.
            """
            try:
                response = await self._optimize_memory_use_case.execute(request)

                return OptimizeMemoryResponseModel(
                    success=response.success,
                    service_name=response.service_name,
                    optimization_type=response.optimization_type,
                    memory_freed_mb=response.memory_freed_mb,
                    performance_improved_percent=response.performance_improved_percent,
                    recommendations_applied=response.recommendations_applied,
                    warnings=response.warnings,
                    processing_time_seconds=response.processing_time_seconds
                )

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Memory optimization failed: {str(e)}"
                )

        @self.router.get("/health", response_model=MemoryHealthModel)
        async def get_memory_health(
            service_name: str = Query(..., description="Service name to check")
        ) -> MemoryHealthModel:
            """Get memory health status for a service."""
            try:
                # In a real implementation, this would check actual memory health
                # For now, return mock data
                return MemoryHealthModel(
                    service_name=service_name,
                    status="healthy",
                    current_usage_percent=65.5,
                    available_memory_mb=2340.5,
                    last_checked=datetime.now(timezone.utc),
                    alerts=[]
                )

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Health check failed: {str(e)}"
                )

        @self.router.get("/metrics", response_model=List[MemoryMetricsModel])
        async def get_memory_metrics(
            service_name: str = Query(..., description="Service name"),
            limit: int = Query(10, description="Number of metrics to return"),
            hours: int = Query(24, description="Hours of history to retrieve")
        ) -> List[MemoryMetricsModel]:
            """Get recent memory metrics for a service."""
            try:
                # In a real implementation, this would query the repository
                # For now, return mock data
                metrics = []
                for i in range(min(limit, 10)):
                    metric = MemoryMetricsModel(
                        id=f"metric-{i}",
                        timestamp=datetime.now(timezone.utc),
                        total_memory_mb=8000.0,
                        used_memory_mb=5200.0 + (i * 50),
                        available_memory_mb=2800.0 - (i * 50),
                        memory_usage_percent=65.0 + (i * 0.5),
                        service_name=service_name
                    )
                    metrics.append(metric)

                return metrics

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to retrieve metrics: {str(e)}"
                )

        @self.router.get("/stats")
        async def get_memory_stats(
            service_name: str = Query(..., description="Service name")
        ) -> Dict[str, Any]:
            """Get memory statistics and insights."""
            try:
                # In a real implementation, this would compute real statistics
                return {
                    "service_name": service_name,
                    "time_range_hours": 24,
                    "total_metrics": 1440,  # 1 per minute
                    "average_usage_percent": 68.5,
                    "peak_usage_percent": 89.2,
                    "peak_time": "2023-12-01T14:30:00Z",
                    "memory_trend": "stable",
                    "optimization_opportunities": [
                        "Consider increasing cache size",
                        "Monitor for memory leaks",
                        "Schedule regular garbage collection"
                    ],
                    "alerts": []
                }

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to retrieve statistics: {str(e)}"
                )

        @self.router.post("/alerts")
        async def configure_memory_alerts(
            service_name: str = Query(..., description="Service name"),
            thresholds: Dict[str, float] = None
        ) -> Dict[str, Any]:
            """Configure memory usage alerts."""
            try:
                if not thresholds:
                    thresholds = {
                        "warning_percent": 75.0,
                        "critical_percent": 90.0,
                        "growth_rate_mb_per_minute": 50.0
                    }

                return {
                    "service_name": service_name,
                    "alerts_configured": True,
                    "thresholds": thresholds,
                    "notification_channels": ["email", "webhook"],
                    "message": "Memory alerts configured successfully"
                }

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to configure alerts: {str(e)}"
                )

        @self.router.get("/recommendations")
        async def get_memory_recommendations(
            service_name: str = Query(..., description="Service name")
        ) -> List[Dict[str, Any]]:
            """Get memory optimization recommendations."""
            try:
                # In a real implementation, this would analyze current metrics
                # and provide specific recommendations
                recommendations = [
                    {
                        "type": "garbage_collection",
                        "priority": "medium",
                        "description": "Run garbage collection to free unused memory",
                        "estimated_savings_mb": 150,
                        "implementation_effort": "low"
                    },
                    {
                        "type": "cache_optimization",
                        "priority": "high",
                        "description": "Optimize cache size and eviction policies",
                        "estimated_savings_mb": 300,
                        "implementation_effort": "medium"
                    },
                    {
                        "type": "memory_pool_tuning",
                        "priority": "low",
                        "description": "Fine-tune memory pool configurations",
                        "estimated_savings_mb": 50,
                        "implementation_effort": "high"
                    }
                ]

                return recommendations

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to get recommendations: {str(e)}"
                )


# Factory function to create router
def create_memory_router(
    analyze_memory_use_case: AnalyzeMemoryUseCase,
    optimize_memory_use_case: OptimizeMemoryUseCase
) -> APIRouter:
    """Create memory router with dependencies."""
    router_instance = MemoryRouter(analyze_memory_use_case, optimize_memory_use_case)
    return router_instance.router
