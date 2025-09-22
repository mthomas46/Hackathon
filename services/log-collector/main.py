"""Service: Log Collector (Enhanced)

Endpoints:
- POST /logs: Store a single log entry
- POST /logs/batch: Store multiple log entries at once
- GET /logs: Retrieve logs with optional filtering by service/level
- GET /logs/time-range: Get logs within specific time range
- GET /search: Full-text search across log content
- GET /stats: Get aggregated statistics and analytics (with time window support)
- GET /metrics/{service}: Detailed metrics and health analysis for specific service
- POST /export: Export logs to file with filtering
- GET /health: Health check with current log count and storage info

Responsibilities:
- Receive structured log entries from various services
- Maintain bounded in-memory history with optional disk persistence
- Provide advanced search, filtering, and analytics capabilities
- Enable comprehensive diagnostics through detailed statistics
- Support time-based analysis and service health monitoring
- Integrated with standardized logging and monitoring system
- Automatic cleanup of old log files with configurable retention

Features:
- Persistent storage: Logs saved to disk for durability and recovery
- Full-text search: Search across messages, services, and log levels
- Time-range queries: Analyze logs from specific time periods
- Service metrics: Detailed health scoring and performance analysis
- Export functionality: Export filtered logs in JSON/JSONL formats
- Advanced statistics: Error rates, throughput, response times, patterns

Dependencies: shared middlewares for request tracking and metrics.
"""

import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request, Response
from pydantic import BaseModel

from services.shared.standardized_logger import StandardizedLogger
from services.shared.utilities.middleware import RequestIdMiddleware, RequestMetricsMiddleware  # type: ignore

try:
    # Try to use persistent storage first
    try:
        from .modules.log_storage import persistent_log_storage as log_storage

        print("✅ Using persistent log storage with disk persistence")
    except ImportError:
        from .modules.log_storage import log_storage

        print("⚠️  Using in-memory log storage only")

    from .modules.log_stats import calculate_log_statistics
except ImportError:
    # Fallback for when running as script
    import os
    import sys

    sys.path.insert(0, os.path.dirname(__file__))

    # Try to use persistent storage first
    try:
        from modules.log_storage import persistent_log_storage as log_storage

        print("✅ Using persistent log storage with disk persistence")
    except ImportError:
        from modules.log_storage import log_storage

        print("⚠️  Using in-memory log storage only")

    from modules.log_stats import calculate_log_statistics

# Service configuration constants
SERVICE_NAME = "log-collector"
SERVICE_VERSION = "0.1.0"
DEFAULT_PORT = 5080

# Default limits and constraints
DEFAULT_MAX_LOGS = 5000
DEFAULT_QUERY_LIMIT = 100

# Initialize standardized logger and monitoring
logger = StandardizedLogger(
    SERVICE_NAME,
    {
        "log_level": "INFO",
        "structured_logging": True,
        "monitoring_enabled": True,
        "metrics_interval": 30,
        "console_logging": True,
        "log_file": f"/tmp/{SERVICE_NAME}.log",
        "max_log_size": 10485760,  # 10MB
        "backup_count": 5,
    },
)
logger.start_monitoring()

app = FastAPI(
    title="Log Collector",
    version=SERVICE_VERSION,
    description="Centralized log collection service for distributed systems with standardized logging",
)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RequestMetricsMiddleware, service_name=SERVICE_NAME)

# Store logger instance for access in endpoints
app.state.logger = logger


class LogItem(BaseModel):
    """Structured log entry data model for consistent logging across services.

    All log entries follow this standard format to enable consistent
    storage, filtering, and analysis across the system.
    """

    service: str
    """Service name that generated the log entry (e.g., 'api-gateway', 'user-service')."""

    level: str
    """Log level: 'debug', 'info', 'warning', 'error', 'fatal', etc."""

    message: str
    """Human-readable log message describing the event."""

    timestamp: Optional[str] = None
    """ISO 8601 timestamp. Auto-generated if not provided."""

    context: Optional[Dict[str, Any]] = None
    """Additional structured context data (request_id, user_id, etc.)."""


@app.get("/health")
async def health(request: Request):
    """Health check endpoint returning service status and current log count.

    Provides basic service health information including the current
    number of stored log entries for monitoring purposes.
    """
    start_time = time.time()
    logger_instance = request.app.state.logger

    try:
        # Get health data
        health_data = {
            "status": "healthy",
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "count": log_storage.get_count(),
            "description": "Log collection service is operational",
        }

        # Add monitoring data from standardized logger
        monitoring_health = logger_instance.get_health_status()
        health_data["monitoring"] = monitoring_health

        # Log successful health check
        response_time = time.time() - start_time
        logger_instance.log_request("GET", "/health", 200, response_time, extra={"log_count": health_data["count"]})

        return health_data

    except Exception as e:
        # Log error
        response_time = time.time() - start_time
        logger_instance.log_error(e, {"endpoint": "/health"})

        # Return error health status
        return {
            "status": "unhealthy",
            "service": SERVICE_NAME,
            "error": str(e),
            "description": "Log collection service encountered an error",
        }


@app.post("/logs")
async def put_log(item: LogItem, request: Request, response: Response):
    """Store a single log entry in the collection.

    Accepts a structured log entry and stores it with automatic timestamp
    generation if not provided. Returns the current total log count.
    """
    start_time = time.time()
    logger_instance = request.app.state.logger

    try:
        # Add log entry
        count = log_storage.add_log(item.model_dump())

        # Log successful log storage
        response_time = time.time() - start_time
        logger_instance.log_request(
            "POST",
            "/logs",
            200,
            response_time,
            extra={"log_service": item.service, "log_level": item.level, "total_logs": count},
        )

        # Log business event for log collection
        logger_instance.log_business_event(
            "log_collected",
            {
                "service": item.service,
                "level": item.level,
                "message_length": len(item.message),
                "has_context": item.context is not None,
            },
        )

        return {"status": "ok", "count": count}

    except Exception as e:
        # Log error
        response_time = time.time() - start_time
        logger_instance.log_error(
            e,
            {
                "endpoint": "/logs",
                "log_service": item.service if item else "unknown",
                "log_level": item.level if item else "unknown",
            },
        )

        response.status_code = 500
        return {"status": "error", "message": "Failed to store log entry"}


class LogBatch(BaseModel):
    """Batch of multiple log entries for efficient bulk submission.

    Used when multiple log entries need to be submitted together,
    reducing the number of individual API calls.
    """

    items: List[LogItem]
    """List of log entries to store."""


@app.post("/logs/batch")
async def put_logs(batch: LogBatch, request: Request, response: Response):
    """Store multiple log entries in a single batch operation.

    This endpoint allows efficient bulk submission of multiple log entries,
    reducing network overhead compared to individual log submissions.
    """
    start_time = time.time()
    logger_instance = request.app.state.logger

    try:
        # Add batch log entries
        entries = [item.model_dump() for item in batch.items]
        count = log_storage.add_logs_batch(entries)

        # Log successful batch storage
        response_time = time.time() - start_time
        logger_instance.log_request(
            "POST", "/logs/batch", 200, response_time, extra={"batch_size": len(batch.items), "total_logs": count}
        )

        # Log business event for batch collection
        logger_instance.log_business_event(
            "log_batch_collected",
            {
                "batch_size": len(batch.items),
                "total_logs": count,
                "services": list(set(item.service for item in batch.items)),
                "levels": list(set(item.level for item in batch.items)),
            },
        )

        return {"status": "ok", "count": count, "added": len(batch.items)}

    except Exception as e:
        # Log error
        response_time = time.time() - start_time
        logger_instance.log_error(e, {"endpoint": "/logs/batch", "batch_size": len(batch.items) if batch else 0})

        response.status_code = 500
        return {"status": "error", "message": "Failed to store log batch"}


@app.get("/logs")
async def list_logs(request: Request, service: Optional[str] = None, level: Optional[str] = None, limit: int = 100):
    """Retrieve logs with optional filtering by service and/or log level.

    Supports filtering logs by service name, log level, and limiting the number
    of results. Returns the most recent logs matching the criteria.
    """
    start_time = time.time()
    logger_instance = request.app.state.logger

    try:
        # Get logs with filtering
        logs = log_storage.get_logs(service=service, level=level, limit=limit)

        # Log successful query
        response_time = time.time() - start_time
        logger_instance.log_request(
            "GET",
            "/logs",
            200,
            response_time,
            extra={"service_filter": service, "level_filter": level, "limit": limit, "results_count": len(logs)},
        )

        return {"items": logs}

    except Exception as e:
        # Log error
        response_time = time.time() - start_time
        logger_instance.log_error(e, {"endpoint": "/logs", "service_filter": service, "level_filter": level})

        return {"error": "Failed to retrieve logs", "message": str(e)}


@app.get("/stats")
async def stats(request: Request, hours: Optional[int] = None):
    """Get comprehensive log statistics and aggregations.

    Returns aggregated statistics including counts by level, service,
    error rates, and top services by log volume for system monitoring.
    Supports time-window filtering with the 'hours' parameter.
    """
    start_time = time.time()
    logger_instance = request.app.state.logger

    try:
        # Get all logs and calculate statistics
        all_logs = log_storage.get_all_logs()
        stats_data = calculate_log_statistics(all_logs, time_window_hours=hours)

        # Log successful stats query
        response_time = time.time() - start_time
        logger_instance.log_request(
            "GET",
            "/stats",
            200,
            response_time,
            extra={
                "total_logs": stats_data.get("total_logs", 0),
                "services_count": len(stats_data.get("by_service", {})),
                "error_rate": stats_data.get("error_rate", 0),
                "time_window_hours": hours,
            },
        )

        # Log business event for stats access
        logger_instance.log_business_event(
            "log_stats_accessed",
            {
                "total_logs": stats_data.get("total_logs", 0),
                "unique_services": len(stats_data.get("by_service", {})),
                "time_window_hours": hours,
                "time_range": stats_data.get("time_range", "unknown"),
            },
        )

        return stats_data

    except Exception as e:
        # Log error
        response_time = time.time() - start_time
        logger_instance.log_error(e, {"endpoint": "/stats", "hours": hours})

        return {"error": "Failed to calculate statistics", "message": str(e)}


@app.get("/search")
async def search_logs(
    request: Request, q: str, fields: Optional[str] = None, case_sensitive: bool = False, limit: int = 100
):
    """Search logs using full-text search across specified fields.

    Performs full-text search across log messages, services, and levels.
    Supports field-specific search and case sensitivity options.
    """
    start_time = time.time()
    logger_instance = request.app.state.logger

    try:
        # Parse fields parameter
        search_fields = None
        if fields:
            search_fields = [f.strip() for f in fields.split(",") if f.strip()]

        # Perform search
        results = log_storage.search_logs(query=q, fields=search_fields, case_sensitive=case_sensitive, limit=limit)

        # Log successful search
        response_time = time.time() - start_time
        logger_instance.log_request(
            "GET",
            "/search",
            200,
            response_time,
            extra={
                "query": q,
                "fields": fields,
                "case_sensitive": case_sensitive,
                "limit": limit,
                "results_count": len(results),
            },
        )

        # Log business event for search usage
        logger_instance.log_business_event(
            "log_search_performed",
            {
                "query": q,
                "fields": search_fields,
                "case_sensitive": case_sensitive,
                "results_count": len(results),
                "limit": limit,
            },
        )

        return {"query": q, "results": results, "total": len(results)}

    except Exception as e:
        # Log error
        response_time = time.time() - start_time
        logger_instance.log_error(e, {"endpoint": "/search", "query": q, "fields": fields})

        return {"error": "Search failed", "message": str(e)}


@app.get("/logs/time-range")
async def get_logs_by_time_range(
    request: Request, start_time: Optional[str] = None, end_time: Optional[str] = None, limit: int = 100
):
    """Get logs within a specific time range.

    Retrieves logs between start_time and end_time (ISO 8601 format).
    Useful for analyzing logs from specific time periods.
    """
    start_time_request = time.time()
    logger_instance = request.app.state.logger

    try:
        # Get logs in time range
        logs = log_storage.get_logs_by_time_range(start_time=start_time, end_time=end_time, limit=limit)

        # Log successful time range query
        response_time = time.time() - start_time_request
        logger_instance.log_request(
            "GET",
            "/logs/time-range",
            200,
            response_time,
            extra={"start_time": start_time, "end_time": end_time, "limit": limit, "results_count": len(logs)},
        )

        # Log business event for time range analysis
        logger_instance.log_business_event(
            "log_time_range_queried",
            {"start_time": start_time, "end_time": end_time, "results_count": len(logs), "limit": limit},
        )

        return {"start_time": start_time, "end_time": end_time, "logs": logs}

    except Exception as e:
        # Log error
        response_time = time.time() - start_time_request
        logger_instance.log_error(e, {"endpoint": "/logs/time-range", "start_time": start_time, "end_time": end_time})

        return {"error": "Time range query failed", "message": str(e)}


@app.get("/metrics/{service_name}")
async def get_service_metrics(request: Request, service_name: str, time_window_minutes: int = 60):
    """Get detailed metrics and health analysis for a specific service.

    Provides comprehensive analysis of a service's logging behavior,
    including error rates, performance metrics, and health scoring.
    """
    start_time_request = time.time()
    logger_instance = request.app.state.logger

    try:
        # Get detailed service metrics
        metrics = log_storage.get_service_metrics(service_name=service_name, time_window_minutes=time_window_minutes)

        # Log successful metrics query
        response_time = time.time() - start_time_request
        logger_instance.log_request(
            "GET",
            f"/metrics/{service_name}",
            200,
            response_time,
            extra={
                "service_name": service_name,
                "time_window_minutes": time_window_minutes,
                "total_logs": metrics.get("total_logs", 0),
                "error_rate": metrics.get("performance", {}).get("error_rate", 0),
            },
        )

        # Log business event for service metrics access
        logger_instance.log_business_event(
            "service_metrics_analyzed",
            {
                "service_name": service_name,
                "time_window_minutes": time_window_minutes,
                "total_logs": metrics.get("total_logs", 0),
                "error_rate": metrics.get("performance", {}).get("error_rate", 0),
                "health_score": metrics.get("performance", {}).get("health_score", 0),
            },
        )

        return metrics

    except Exception as e:
        # Log error
        response_time = time.time() - start_time_request
        logger_instance.log_error(
            e,
            {
                "endpoint": f"/metrics/{service_name}",
                "service_name": service_name,
                "time_window_minutes": time_window_minutes,
            },
        )

        return {"error": f"Failed to get metrics for service {service_name}", "message": str(e)}


@app.post("/export")
async def export_logs(
    request: Request, filepath: str, service: Optional[str] = None, level: Optional[str] = None, format: str = "json"
):
    """Export logs to a file with optional filtering.

    Exports filtered logs to a specified file path on the server.
    Supports JSON and JSONL formats for different use cases.
    """
    start_time_request = time.time()
    logger_instance = request.app.state.logger

    try:
        # Validate format
        if format not in ["json", "jsonl"]:
            return {"error": "Invalid format. Supported: json, jsonl"}

        # Perform export
        exported_count = log_storage.export_logs(filepath=filepath, service=service, level=level, format=format)

        # Log successful export
        response_time = time.time() - start_time_request
        logger_instance.log_request(
            "POST",
            "/export",
            200,
            response_time,
            extra={
                "filepath": filepath,
                "service_filter": service,
                "level_filter": level,
                "format": format,
                "exported_count": exported_count,
            },
        )

        # Log business event for log export
        logger_instance.log_business_event(
            "logs_exported",
            {
                "filepath": filepath,
                "service_filter": service,
                "level_filter": level,
                "format": format,
                "exported_count": exported_count,
            },
        )

        return {
            "status": "success",
            "filepath": filepath,
            "exported_count": exported_count,
            "format": format,
            "filters": {"service": service, "level": level},
        }

    except Exception as e:
        # Log error
        response_time = time.time() - start_time_request
        logger_instance.log_error(
            e, {"endpoint": "/export", "filepath": filepath, "service": service, "level": level, "format": format}
        )

        return {"error": "Export failed", "message": str(e)}


if __name__ == "__main__":
    """Run the Log Collector service directly."""
    import asyncio
    import atexit

    import uvicorn

    # Initialize async components
    async def init_async_components():
        try:
            await log_storage.initialize_async()
        except Exception as e:
            logger.warning(f"Failed to initialize async components: {e}")

    # Run async initialization
    asyncio.run(init_async_components())

    # Log service startup
    logger.info("Starting Log Collector service", port=DEFAULT_PORT, version=SERVICE_VERSION)

    # Register cleanup function
    @atexit.register
    def cleanup():
        logger.info("Shutting down Log Collector service", service=SERVICE_NAME)
        logger.stop_monitoring()

    try:
        uvicorn.run(app, host="0.0.0.0", port=DEFAULT_PORT, log_level="info")
    except KeyboardInterrupt:
        logger.info("Service interrupted by user", service=SERVICE_NAME)
    except Exception as e:
        logger.error(f"Service failed to start: {e}", service=SERVICE_NAME, error=str(e))
        raise
