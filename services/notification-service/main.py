"""Service: Notification Service

Endpoints:
- POST /owners/update, POST /owners/resolve, POST /notify, GET /dlq, GET /health

Responsibilities: Resolve owners to targets, send notifications with dedup/backoff,
and expose a dead-letter queue. Caches owner resolutions with TTL.
Dependencies: shared middlewares; webhook posting via httpx.
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import os
import httpx
import time

from services.shared.middleware import RequestIdMiddleware, RequestMetricsMiddleware  # type: ignore
from services.shared.utilities import attach_self_register  # type: ignore


app = FastAPI(title="Notification Service", version="0.1.0")
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RequestMetricsMiddleware, service_name="notification-service")
attach_self_register(app, "notification-service")

_dedup_cache: Dict[str, float] = {}
_dlq: List[Dict[str, Any]] = []
_resolve_cache: Dict[str, Dict[str, Any]] = {}
_resolve_cache_ttl = 300.0


class OwnerUpdate(BaseModel):
    id: str
    owner: Optional[str] = None
    team: Optional[str] = None


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "notification-service"}


@app.post("/owners/update")
async def owners_update(req: OwnerUpdate):
    # Stub: in a real system, update ownership registry (DB or config repo)
    return {"status": "ok", "id": req.id, "owner": req.owner, "team": req.team}


class NotifyPayload(BaseModel):
    channel: str  # slack|email|webhook
    target: str   # webhook URL or email address
    title: str
    message: str
    metadata: Dict[str, Any] = {}
    labels: List[str] = []


@app.post("/notify")
async def notify(req: NotifyPayload):
    channel = req.channel.lower().strip()
    # Deduplicate by (target,title,message) within 10 minutes
    dedup_key = f"{req.target}|{req.title}|{hash(req.message)}"
    now = time.time()
    if _dedup_cache.get(dedup_key, 0) > now - 600:
        return {"status": "duplicate_suppressed"}
    _dedup_cache[dedup_key] = now
    if channel == "webhook":
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.post(req.target, json={"title": req.title, "message": req.message, "metadata": req.metadata, "labels": req.labels})
                r.raise_for_status()
        except Exception as e:
            _dlq.append({"payload": req.model_dump(), "error": str(e), "ts": now})
            raise HTTPException(status_code=502, detail=f"Webhook failed: {e}")
        return {"status": "sent"}
    # Stubs for slack/email; would integrate with provider SDKs
    return {"status": "queued", "channel": channel}


def _load_owner_map() -> Dict[str, Dict[str, str]]:
    """Load owner-to-target mapping from env JSON or file.

    NOTIFY_OWNER_MAP_JSON: JSON string {"alice": {"email": "a@b"}, "devops": {"webhook": "https://..."}}
    NOTIFY_OWNER_MAP_FILE: path to JSON file with same structure
    """
    import json
    data: Dict[str, Dict[str, str]] = {}
    s = os.environ.get("NOTIFY_OWNER_MAP_JSON")
    f = os.environ.get("NOTIFY_OWNER_MAP_FILE")
    if s:
        try:
            data = json.loads(s)
        except Exception:
            data = {}
    elif f and os.path.exists(f):
        try:
            with open(f, "r") as fh:
                data = json.load(fh)
        except Exception:
            data = {}
    return data or {}


class ResolveOwnersRequest(BaseModel):
    owners: List[str]


@app.post("/owners/resolve")
async def owners_resolve(req: ResolveOwnersRequest):
    m = _load_owner_map()
    out: Dict[str, Dict[str, str]] = {}
    for o in req.owners or []:
        # Cache
        cached = _resolve_cache.get(o)
        if cached and (time.time() - cached.get("_ts", 0) <= _resolve_cache_ttl):
            out[o] = {k: v for k, v in cached.items() if k != "_ts"}
            continue
        info = m.get(o) or {}
        # Heuristics if no mapping provided
        if not info:
            if o.startswith("http://") or o.startswith("https://"):
                info = {"webhook": o}
            elif "@" in o:
                info = {"email": o}
            else:
                info = {"handle": o}
        out[o] = info
        _resolve_cache[o] = {**info, "_ts": time.time()}
    return {"resolved": out}


@app.get("/dlq")
async def get_dlq(limit: int = 50):
    return {"items": _dlq[-max(1, min(limit, 500)):]}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5095)


