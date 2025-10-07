"""MCP Performance Store Service - Main Application.

FastAPI service for tracking and querying MCP performance metrics.
"""

import logging
from contextlib import asynccontextmanager
from typing import Optional

import redis.asyncio as redis
from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

from services.mcp_performance_store.domain.entities.orchestration_execution import OrchestrationExecution
from services.mcp_performance_store.domain.value_objects.execution_status import ExecutionStatus
from services.mcp_performance_store.infrastructure.config import get_settings
from services.mcp_performance_store.infrastructure.repositories import (
    RedisExecutionRepository,
    RedisPatternPerformanceRepository,
)
from services.mcp_performance_store.application.use_cases import (
    RecordExecutionUseCase,
    RecordExecutionError,
    QueryPerformanceUseCase,
    QueryPerformanceError,
)
from services.mcp_performance_store.application.dto import (
    RecordExecutionRequest,
    ExecutionResponse,
    ExecutionListResponse,
    PatternPerformanceResponse,
    MetricsSummaryResponse,
    TrendsResponse,
)
from services.mcp_performance_store.domain.services import (
    AnalyticsService,
    AnomalyDetectionService,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Global state
redis_client: Optional[redis.Redis] = None
execution_repository: Optional[RedisExecutionRepository] = None
pattern_repository: Optional[RedisPatternPerformanceRepository] = None
analytics_service: Optional[AnalyticsService] = None
anomaly_service: Optional[AnomalyDetectionService] = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for the application."""
    global redis_client, execution_repository, pattern_repository, analytics_service, anomaly_service
    
    # Startup
    settings = get_settings()
    logger.info(f"Starting {settings.service_name} v{settings.service_version}")
    
    # Initialize Redis
    logger.info(f"Connecting to Redis at {settings.redis_host}:{settings.redis_port}")
    redis_client = redis.Redis(
        host=settings.redis_host,
        port=settings.redis_port,
        db=settings.redis_db,
        password=settings.redis_password,
        socket_timeout=settings.redis_socket_timeout,
        socket_connect_timeout=settings.redis_socket_connect_timeout,
        decode_responses=False,
    )
    
    try:
        await redis_client.ping()
        logger.info("Redis connection successful")
    except Exception as e:
        logger.error(f"Failed to connect to Redis: {e}")
        raise
    
    # Initialize repositories
    execution_repository = RedisExecutionRepository(redis_client, settings.redis_key_prefix)
    pattern_repository = RedisPatternPerformanceRepository(redis_client, settings.redis_key_prefix)
    logger.info("Repositories initialized")
    
    # Initialize services
    analytics_service = AnalyticsService(min_samples_for_trend=5)
    anomaly_service = AnomalyDetectionService(z_score_threshold=3.0, min_samples=10)
    logger.info("Analytics and anomaly detection services initialized")
    
    logger.info("Service ready")
    yield
    
    # Shutdown
    logger.info("Shutting down...")
    if redis_client:
        await redis_client.aclose()
        logger.info("Redis connection closed")


# Create FastAPI app
settings = get_settings()
app = FastAPI(
    title=settings.service_name,
    version=settings.service_version,
    lifespan=lifespan
)


# ==================== Dependency Injection ====================

def get_record_use_case() -> RecordExecutionUseCase:
    """Get RecordExecutionUseCase instance."""
    return RecordExecutionUseCase(execution_repository, pattern_repository)


def get_query_use_case() -> QueryPerformanceUseCase:
    """Get QueryPerformanceUseCase instance."""
    return QueryPerformanceUseCase(execution_repository, pattern_repository)


# ==================== Health Check ====================

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    try:
        if redis_client:
            await redis_client.ping()
        return {"status": "healthy", "service": settings.service_name}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={"status": "unhealthy", "error": str(e)}
        )


# ==================== Execution Endpoints ====================

@app.post("/api/v1/executions", status_code=201)
async def record_execution(
    request: RecordExecutionRequest,
    use_case: RecordExecutionUseCase = Depends(get_record_use_case)
):
    """
    Record a new execution.
    
    Records execution details and automatically updates pattern performance metrics.
    """
    try:
        # Convert DTO to domain entity
        execution = OrchestrationExecution(
            execution_id=request.execution_id,
            query=request.query,
            context=request.context,
            composition_id=request.composition_id,
            mcp_ids=request.mcp_ids,
            pattern_name=request.pattern_name,
            pattern_config=request.pattern_config,
            start_time=request.start_time,
            end_time=request.end_time,
            total_duration_ms=request.total_duration_ms,
            interpretation_ms=request.interpretation_ms,
            retrieval_ms=request.retrieval_ms,
            pattern_execution_ms=request.pattern_execution_ms,
            composition_ms=request.composition_ms,
            status=request.status,
            error_message=request.error_message,
            error_type=request.error_type,
            confidence=request.confidence,
            num_sources=request.num_sources,
            response_length=request.response_length,
            service=request.service,
            user_id=request.user_id,
            session_id=request.session_id,
            tags=request.tags,
            metadata=request.metadata,
        )
        
        await use_case.execute(execution)
        
        return {"message": "Execution recorded successfully", "execution_id": request.execution_id}
        
    except RecordExecutionError as e:
        logger.warning(f"Failed to record execution: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error recording execution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/executions/{execution_id}", response_model=ExecutionResponse)
async def get_execution(
    execution_id: str,
    use_case: QueryPerformanceUseCase = Depends(get_query_use_case)
):
    """Get an execution by ID."""
    try:
        execution = await use_case.get_execution(execution_id)
        return ExecutionResponse(
            execution_id=execution.execution_id,
            query=execution.query,
            pattern_name=execution.pattern_name,
            status=execution.status.value,
            total_duration_ms=execution.total_duration_ms,
            confidence=execution.confidence,
            num_sources=execution.num_sources,
            start_time=execution.start_time,
            end_time=execution.end_time,
            error_message=execution.error_message,
            composition_id=execution.composition_id,
        )
    except QueryPerformanceError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting execution: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/executions", response_model=ExecutionListResponse)
async def list_executions(
    pattern: Optional[str] = Query(None, description="Filter by pattern name"),
    status: Optional[str] = Query(None, description="Filter by status"),
    composition_id: Optional[str] = Query(None, description="Filter by composition ID"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Results to skip"),
    use_case: QueryPerformanceUseCase = Depends(get_query_use_case)
):
    """
    List executions with optional filters.
    
    Filters: pattern, status, composition_id
    Pagination: limit, offset
    """
    try:
        # Query based on filters
        if pattern:
            executions = await use_case.get_executions_by_pattern(pattern, limit, offset)
        elif status:
            exec_status = ExecutionStatus(status)
            executions = await use_case.get_executions_by_status(exec_status, limit, offset)
        elif composition_id:
            executions = await use_case.get_executions_by_composition(composition_id, limit)
        else:
            executions = await use_case.get_recent_executions(limit, offset)
        
        # Convert to response
        exec_responses = [
            ExecutionResponse(
                execution_id=e.execution_id,
                query=e.query,
                pattern_name=e.pattern_name,
                status=e.status.value,
                total_duration_ms=e.total_duration_ms,
                confidence=e.confidence,
                num_sources=e.num_sources,
                start_time=e.start_time,
                end_time=e.end_time,
                error_message=e.error_message,
                composition_id=e.composition_id,
            )
            for e in executions
        ]
        
        return ExecutionListResponse(
            executions=exec_responses,
            total=len(exec_responses),
            limit=limit,
            offset=offset
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid status value: {e}")
    except Exception as e:
        logger.error(f"Error listing executions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/executions/recent", response_model=ExecutionListResponse)
async def get_recent_executions(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    use_case: QueryPerformanceUseCase = Depends(get_query_use_case)
):
    """Get most recent executions."""
    try:
        executions = await use_case.get_recent_executions(limit, offset)
        
        exec_responses = [
            ExecutionResponse(
                execution_id=e.execution_id,
                query=e.query,
                pattern_name=e.pattern_name,
                status=e.status.value,
                total_duration_ms=e.total_duration_ms,
                confidence=e.confidence,
                num_sources=e.num_sources,
                start_time=e.start_time,
                end_time=e.end_time,
                error_message=e.error_message,
                composition_id=e.composition_id,
            )
            for e in executions
        ]
        
        return ExecutionListResponse(
            executions=exec_responses,
            total=len(exec_responses),
            limit=limit,
            offset=offset
        )
    except Exception as e:
        logger.error(f"Error getting recent executions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== Pattern Performance Endpoints ====================

@app.get("/api/v1/patterns", response_model=list[PatternPerformanceResponse])
async def list_patterns(
    use_case: QueryPerformanceUseCase = Depends(get_query_use_case)
):
    """Get all pattern performance metrics."""
    try:
        patterns = await use_case.get_all_patterns()
        return [
            PatternPerformanceResponse(**p.to_dict())
            for p in patterns
        ]
    except Exception as e:
        logger.error(f"Error listing patterns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/patterns/{pattern_name}/performance", response_model=PatternPerformanceResponse)
async def get_pattern_performance(
    pattern_name: str,
    use_case: QueryPerformanceUseCase = Depends(get_query_use_case)
):
    """Get performance metrics for a specific pattern."""
    try:
        performance = await use_case.get_pattern_performance(pattern_name)
        return PatternPerformanceResponse(**performance.to_dict())
    except QueryPerformanceError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"Error getting pattern performance: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== Metrics & Analytics Endpoints ====================

@app.get("/api/v1/metrics/summary", response_model=MetricsSummaryResponse)
async def get_metrics_summary(
    use_case: QueryPerformanceUseCase = Depends(get_query_use_case)
):
    """Get overall metrics summary."""
    try:
        summary = await use_case.get_summary()
        return MetricsSummaryResponse(**summary)
    except Exception as e:
        logger.error(f"Error getting metrics summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/metrics/trends", response_model=TrendsResponse)
async def get_trends(
    hours: int = Query(24, ge=1, le=720, description="Hours to look back"),
    use_case: QueryPerformanceUseCase = Depends(get_query_use_case)
):
    """Get performance trends over time."""
    try:
        trends = await use_case.get_trends(hours)
        return TrendsResponse(**trends)
    except Exception as e:
        logger.error(f"Error getting trends: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/metrics/anomalies", response_model=list[PatternPerformanceResponse])
async def get_anomalies(
    use_case: QueryPerformanceUseCase = Depends(get_query_use_case)
):
    """
    Get patterns with performance anomalies (degrading performance).
    
    Returns patterns where recent performance (24h) is significantly
    worse than longer-term performance (7d).
    """
    try:
        degrading = await use_case.get_degrading_patterns()
        return [
            PatternPerformanceResponse(**p.to_dict())
            for p in degrading
        ]
    except Exception as e:
        logger.error(f"Error getting anomalies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== Analytics & Anomaly Detection ====================

@app.get("/api/v1/analytics/trends/orchestration")
async def get_orchestration_trends(
    time_window_days: int = Query(7, ge=1, le=30)
):
    """
    Analyze performance trends for orchestration executions.
    
    Returns trend analysis including:
    - Duration trends
    - Success rate trends
    - Token usage trends
    - Statistical analysis (mean, stdev, percentiles)
    """
    try:
        from datetime import datetime, timedelta
        
        # Get recent executions
        cutoff_date = datetime.now() - timedelta(days=time_window_days)
        all_executions = await execution_repository.get_by_date_range(cutoff_date, datetime.now())
        
        if not all_executions:
            return {"status": "no_data", "message": "No execution data available"}
        
        # Analyze trends
        analysis = analytics_service.analyze_orchestration_trends(all_executions, time_window_days)
        return analysis
    except Exception as e:
        logger.error(f"Error analyzing orchestration trends: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/analytics/trends/pattern/{pattern_name}")
async def get_pattern_trends(pattern_name: str):
    """
    Analyze performance trends for a specific pattern.
    
    Returns pattern-specific trend analysis including:
    - Duration trends
    - Success rate trends
    - Token usage trends
    - Confidence score trends
    """
    try:
        # Get all pattern performances
        all_patterns = await pattern_repository.get_by_pattern(pattern_name)
        
        if not all_patterns:
            return {
                "status": "no_data",
                "message": f"No data found for pattern '{pattern_name}'"
            }
        
        # Analyze trends
        analysis = analytics_service.analyze_pattern_trends(all_patterns, pattern_name)
        return analysis
    except Exception as e:
        logger.error(f"Error analyzing pattern trends: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/analytics/compare/patterns")
async def compare_patterns():
    """
    Compare performance across all patterns.
    
    Returns comparative statistics including:
    - Fastest/slowest patterns
    - Most/least reliable patterns
    - Token usage by pattern
    - Cost by pattern
    """
    try:
        from datetime import datetime, timedelta
        
        # Get recent pattern performances (last 7 days)
        cutoff_date = datetime.now() - timedelta(days=7)
        all_patterns = await pattern_repository.get_by_date_range(cutoff_date, datetime.now())
        
        if not all_patterns:
            return {"status": "no_data", "message": "No pattern data available"}
        
        # Compare patterns
        comparison = analytics_service.compare_patterns(all_patterns)
        return comparison
    except Exception as e:
        logger.error(f"Error comparing patterns: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/analytics/degradation")
async def detect_degradation(
    threshold_percent: float = Query(20.0, ge=5.0, le=100.0)
):
    """
    Detect performance degradation by comparing recent vs historical performance.
    
    Args:
        threshold_percent: Percentage threshold for degradation alert (default: 20%)
    
    Returns degradation analysis comparing:
    - Recent performance (last 24 hours)
    - Historical baseline (7-30 days ago)
    """
    try:
        from datetime import datetime, timedelta
        
        # Get recent executions (last 24 hours)
        now = datetime.now()
        recent_cutoff = now - timedelta(hours=24)
        recent_executions = await execution_repository.get_by_date_range(recent_cutoff, now)
        
        # Get historical baseline (7-30 days ago)
        hist_start = now - timedelta(days=30)
        hist_end = now - timedelta(days=7)
        hist_executions = await execution_repository.get_by_date_range(hist_start, hist_end)
        
        if not recent_executions or not hist_executions:
            return {
                "status": "insufficient_data",
                "message": "Need both recent and historical data for degradation detection"
            }
        
        # Detect degradation
        analysis = analytics_service.detect_performance_degradation(
            recent_executions,
            hist_executions,
            threshold_percent
        )
        return analysis
    except Exception as e:
        logger.error(f"Error detecting degradation: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/anomalies/detect/orchestration")
async def detect_orchestration_anomalies(
    days: int = Query(7, ge=1, le=30)
):
    """
    Detect anomalies in orchestration executions.
    
    Uses statistical methods (Z-score) to identify:
    - Duration spikes/drops
    - Failure spikes
    - Token usage spikes
    - Cost spikes
    """
    try:
        from datetime import datetime, timedelta
        
        # Get recent executions
        cutoff_date = datetime.now() - timedelta(days=days)
        executions = await execution_repository.get_by_date_range(cutoff_date, datetime.now())
        
        if not executions:
            return {"anomalies": [], "message": "No execution data available"}
        
        # Detect anomalies
        anomalies = anomaly_service.detect_orchestration_anomalies(executions)
        
        return {
            "total_executions": len(executions),
            "anomalies_detected": len(anomalies),
            "anomalies": [anomaly.to_dict() for anomaly in anomalies]
        }
    except Exception as e:
        logger.error(f"Error detecting orchestration anomalies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


@app.get("/api/v1/anomalies/detect/pattern/{pattern_name}")
async def detect_pattern_anomalies(
    pattern_name: str,
    days: int = Query(7, ge=1, le=30)
):
    """
    Detect anomalies for a specific pattern.
    
    Uses statistical methods to identify:
    - Duration anomalies
    - Confidence score drops
    - Token usage spikes
    """
    try:
        from datetime import datetime, timedelta
        
        # Get pattern performances
        cutoff_date = datetime.now() - timedelta(days=days)
        performances = await pattern_repository.get_by_date_range(cutoff_date, datetime.now())
        
        # Filter by pattern
        pattern_perfs = [p for p in performances if p.pattern_name == pattern_name]
        
        if not pattern_perfs:
            return {
                "anomalies": [],
                "message": f"No data found for pattern '{pattern_name}'"
            }
        
        # Detect anomalies
        anomalies = anomaly_service.detect_pattern_anomalies(pattern_perfs, pattern_name)
        
        return {
            "pattern_name": pattern_name,
            "total_executions": len(pattern_perfs),
            "anomalies_detected": len(anomalies),
            "anomalies": [anomaly.to_dict() for anomaly in anomalies]
        }
    except Exception as e:
        logger.error(f"Error detecting pattern anomalies: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal server error")


# ==================== Main ====================

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.service_port,
        log_level=settings.log_level.lower(),
        reload=False
    )