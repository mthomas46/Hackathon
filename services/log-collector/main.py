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
from datetime import datetime, timezone

from services.shared.middleware import RequestIdMiddleware, RequestMetricsMiddleware  # type: ignore

app = FastAPI(title="Log Collector", version="0.1.0")
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RequestMetricsMiddleware, service_name="log-collector")


class LogItem(BaseModel):
    service: str
    level: str
    message: str
    timestamp: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


_logs: List[Dict[str, Any]] = []
_max_logs = 5000


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "log-collector", "count": len(_logs)}


@app.post("/logs")
async def put_log(item: LogItem):
    entry = item.model_dump()
    entry["timestamp"] = entry.get("timestamp") or _now_iso()
    _logs.append(entry)
    if len(_logs) > _max_logs:
        del _logs[: len(_logs) - _max_logs]
    return {"status": "ok", "count": len(_logs)}


class LogBatch(BaseModel):
    items: List[LogItem]


@app.post("/logs/batch")
async def put_logs(batch: LogBatch):
    for it in batch.items:
        await put_log(it)
    return {"status": "ok", "count": len(_logs), "added": len(batch.items)}


@app.get("/logs")
async def list_logs(service: Optional[str] = None, level: Optional[str] = None, limit: int = 100):
    out = [l for l in _logs if (service is None or l.get("service") == service) and (level is None or l.get("level") == level)]
    return {"items": out[-limit:]}


@app.get("/stats")
async def stats():
    by_level: Dict[str, int] = {}
    by_service: Dict[str, int] = {}
    errors_by_service: Dict[str, int] = {}
    for l in _logs:
        lvl = str(l.get("level", "")).lower()
        svc = l.get("service", "")
        by_level[lvl] = by_level.get(lvl, 0) + 1
        by_service[svc] = by_service.get(svc, 0) + 1
        if lvl in ("error", "fatal"): errors_by_service[svc] = errors_by_service.get(svc, 0) + 1
    top_services = sorted(by_service.items(), key=lambda x: x[1], reverse=True)[:5]
    return {
        "count": len(_logs),
        "by_level": by_level,
        "by_service": by_service,
        "errors_by_service": errors_by_service,
        "top_services": top_services,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5080)


