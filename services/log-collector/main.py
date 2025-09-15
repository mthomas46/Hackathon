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

Dependencies: shared middlewares for request tracking and metrics.
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from services.shared.middleware import RequestIdMiddleware, RequestMetricsMiddleware  # type: ignore

from .modules.log_storage import log_storage
from .modules.log_stats import calculate_log_statistics

# Service configuration constants
SERVICE_NAME = "log-collector"
SERVICE_VERSION = "0.1.0"
DEFAULT_PORT = 5080

# Default limits and constraints
DEFAULT_MAX_LOGS = 5000
DEFAULT_QUERY_LIMIT = 100

app = FastAPI(
    title="Log Collector",
    version=SERVICE_VERSION,
    description="Centralized log collection service for distributed systems"
)
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RequestMetricsMiddleware, service_name=SERVICE_NAME)


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
async def health():
    """Health check endpoint returning service status and current log count.

    Provides basic service health information including the current
    number of stored log entries for monitoring purposes.
    """
    return {
        "status": "healthy",
        "service": SERVICE_NAME,
        "version": SERVICE_VERSION,
        "count": log_storage.get_count(),
        "description": "Log collection service is operational"
    }


@app.post("/logs")
async def put_log(item: LogItem):
    """Store a single log entry in the collection.

    Accepts a structured log entry and stores it with automatic timestamp
    generation if not provided. Returns the current total log count.
    """
    count = log_storage.add_log(item.model_dump())
    return {"status": "ok", "count": count}


class LogBatch(BaseModel):
    """Batch of multiple log entries for efficient bulk submission.

    Used when multiple log entries need to be submitted together,
    reducing the number of individual API calls.
    """
    items: List[LogItem]
    """List of log entries to store."""


@app.post("/logs/batch")
async def put_logs(batch: LogBatch):
    """Store multiple log entries in a single batch operation.

    This endpoint allows efficient bulk submission of multiple log entries,
    reducing network overhead compared to individual log submissions.
    """
    entries = [item.model_dump() for item in batch.items]
    count = log_storage.add_logs_batch(entries)
    return {"status": "ok", "count": count, "added": len(batch.items)}


@app.get("/logs")
async def list_logs(service: Optional[str] = None, level: Optional[str] = None, limit: int = 100):
    """Retrieve logs with optional filtering by service and/or log level.

    Supports filtering logs by service name, log level, and limiting the number
    of results. Returns the most recent logs matching the criteria.
    """
    logs = log_storage.get_logs(service=service, level=level, limit=limit)
    return {"items": logs}


@app.get("/stats")
async def stats():
    """Get comprehensive log statistics and aggregations.

    Returns aggregated statistics including counts by level, service,
    error rates, and top services by log volume for system monitoring.
    """
    all_logs = log_storage.get_all_logs()
    return calculate_log_statistics(all_logs)


if __name__ == "__main__":
    """Run the Log Collector service directly."""
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=DEFAULT_PORT,
        log_level="info"
    )


