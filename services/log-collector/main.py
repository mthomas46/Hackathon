"""Service: Log Collector

Endpoints:
- POST /logs, POST /logs/batch, GET /logs, GET /stats, GET /health

Responsibilities: Receive structured logs, retain bounded history, and expose
basic aggregate stats for quick diagnostics.
Dependencies: shared middlewares.
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from services.shared.middleware import RequestIdMiddleware, RequestMetricsMiddleware  # type: ignore

from .modules.log_storage import log_storage
from .modules.log_stats import calculate_log_statistics

app = FastAPI(title="Log Collector", version="0.1.0")
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RequestMetricsMiddleware, service_name="log-collector")


class LogItem(BaseModel):
    """Log entry data model."""
    service: str
    level: str
    message: str
    timestamp: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy", "service": "log-collector", "count": log_storage.get_count()}


@app.post("/logs")
async def put_log(item: LogItem):
    """Store a single log entry."""
    count = log_storage.add_log(item.model_dump())
    return {"status": "ok", "count": count}


class LogBatch(BaseModel):
    """Batch of log entries."""
    items: List[LogItem]


@app.post("/logs/batch")
async def put_logs(batch: LogBatch):
    """Store multiple log entries."""
    entries = [item.model_dump() for item in batch.items]
    count = log_storage.add_logs_batch(entries)
    return {"status": "ok", "count": count, "added": len(batch.items)}


@app.get("/logs")
async def list_logs(service: Optional[str] = None, level: Optional[str] = None, limit: int = 100):
    """Retrieve logs with optional filtering."""
    logs = log_storage.get_logs(service=service, level=level, limit=limit)
    return {"items": logs}


@app.get("/stats")
async def stats():
    """Get log statistics and aggregations."""
    all_logs = log_storage.get_all_logs()
    return calculate_log_statistics(all_logs)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5080)


