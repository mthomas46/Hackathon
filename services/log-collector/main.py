"""Service: Log Collector

Endpoints:
- POST /logs: Store a single log entry
- POST /logs/batch: Store multiple log entries at once
- GET /logs: Retrieve logs with optional filtering by service/level
- GET /stats: Get aggregated statistics and analytics
- GET /health: Health check with current log count

Responsibilities:
- Receive structured log entries from various services
- Maintain bounded in-memory history for recent logs
- Provide basic aggregation and filtering capabilities
- Enable quick diagnostics through statistics endpoint
- Integrated with standardized logging and monitoring system

Dependencies: shared middlewares for request tracking and metrics.
"""

import time
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request, Response
from pydantic import BaseModel

from services.shared.standardized_logger import StandardizedLogger
from services.shared.utilities.middleware import RequestIdMiddleware, RequestMetricsMiddleware  # type: ignore

try:
    from .modules.log_stats import calculate_log_statistics
    from .modules.log_storage import log_storage
except ImportError:
    # Fallback for when running as script
    import os
    import sys

    sys.path.insert(0, os.path.dirname(__file__))
    from modules.log_stats import calculate_log_statistics
    from modules.log_storage import log_storage

# ============================================================================
# STANDARDIZED CONFIGURATION
# ============================================================================
from services.shared.infrastructure.config import load_service_config
from services.shared.utilities import setup_common_middleware
from services.shared.presentation.responses import create_error_response, create_success_response
from services.shared.monitoring.health import register_health_endpoints

# Load standardized configuration
config = load_service_config(
    service_type="log-collector",
    config_file="./config.yaml"  # Optional config file override
)

# Service configuration from standardized config
SERVICE_NAME = config.service_name
SERVICE_TITLE = config.service_description or "Log Collector"
SERVICE_VERSION = config.service_version
DEFAULT_PORT = config.port

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
    title=SERVICE_TITLE,
    version=SERVICE_VERSION,
    description="Centralized log collection service for distributed systems with standardized logging",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup standardized middleware and utilities
setup_common_middleware(app, service_name=SERVICE_NAME)

# Register standardized health endpoints
register_health_endpoints(app, SERVICE_NAME, SERVICE_VERSION)

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
        from datetime import datetime

        health_data = {
            "status": "healthy",
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "timestamp": datetime.utcnow().isoformat(),
            "count": log_storage.get_count(),
            "description": "Log collection service is operational",
        }

        # Add monitoring data from standardized logger
        monitoring_health = logger_instance.get_health_status()
        health_data["monitoring"] = monitoring_health

        # Log successful health check
        response_time = time.time() - start_time
        logger_instance.log_request(
            "GET",
            "/health",
            200,
            response_time,
            extra={"log_count": health_data["count"]},
        )

        return create_success_response(
            data={
                "status": "healthy",
                "service": SERVICE_NAME,
                "version": SERVICE_VERSION,
                "log_count": health_data["count"],
                "monitoring": health_data.get("monitoring"),
                "features": {
                    "log_collection": True,
                    "batch_processing": True,
                    "statistics": True,
                    "standardized_logging": True,
                }
            },
            message="Service is healthy"
        )

    except Exception as e:
        # Log error
        response_time = time.time() - start_time
        logger_instance.log_error(e, {"endpoint": "/health"})

        # Return error health status
        return create_error_response(
            message=f"Health check failed: {str(e)}",
            error_code="HEALTH_CHECK_FAILED",
            details={"error": str(e)}
        )


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
            extra={
                "log_service": item.service,
                "log_level": item.level,
                "total_logs": count,
            },
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
            "POST",
            "/logs/batch",
            200,
            response_time,
            extra={"batch_size": len(batch.items), "total_logs": count},
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
        logger_instance.log_error(
            e,
            {"endpoint": "/logs/batch", "batch_size": len(batch.items) if batch else 0},
        )

        response.status_code = 500
        return {"status": "error", "message": "Failed to store log batch"}


@app.get("/logs")
async def list_logs(
    request: Request,
    service: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 100,
):
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
            extra={
                "service_filter": service,
                "level_filter": level,
                "limit": limit,
                "results_count": len(logs),
            },
        )

        return {"items": logs}

    except Exception as e:
        # Log error
        response_time = time.time() - start_time
        logger_instance.log_error(
            e, {"endpoint": "/logs", "service_filter": service, "level_filter": level}
        )

        return {"error": "Failed to retrieve logs", "message": str(e)}


@app.get("/stats")
async def stats(request: Request):
    """Get comprehensive log statistics and aggregations.

    Returns aggregated statistics including counts by level, service,
    error rates, and top services by log volume for system monitoring.
    """
    start_time = time.time()
    logger_instance = request.app.state.logger

    try:
        # Get all logs and calculate statistics
        all_logs = log_storage.get_all_logs()
        stats_data = calculate_log_statistics(all_logs)

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
            },
        )

        # Log business event for stats access
        logger_instance.log_business_event(
            "log_stats_accessed",
            {
                "total_logs": stats_data.get("total_logs", 0),
                "unique_services": len(stats_data.get("by_service", {})),
                "time_range": stats_data.get("time_range", "unknown"),
            },
        )

        return stats_data

    except Exception as e:
        # Log error
        response_time = time.time() - start_time
        logger_instance.log_error(e, {"endpoint": "/stats"})

        return {"error": "Failed to calculate statistics", "message": str(e)}


if __name__ == "__main__":
    """Run the Log Collector service directly."""
    import atexit

    import uvicorn

    # Log service startup
    logger.info(
        "Starting Log Collector service", port=DEFAULT_PORT, version=SERVICE_VERSION
    )

    # Register cleanup function
    @atexit.register
    def cleanup():
        logger.info("Shutting down Log Collector service")
        logger.stop_monitoring()

    try:
        uvicorn.run(app, host="127.0.0.1", port=DEFAULT_PORT, log_level="info")
    except KeyboardInterrupt:
        logger.info("Service interrupted by user")
    except Exception as e:
        logger.error(f"Service failed to start: {e}")
        raise
