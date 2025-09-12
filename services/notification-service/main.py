"""Service: Notification Service

Endpoints:
- POST /owners/update, POST /owners/resolve, POST /notify, GET /dlq, GET /health

Responsibilities: Resolve owners to targets, send notifications with dedup/backoff,
and expose a dead-letter queue. Caches owner resolutions with TTL.
Dependencies: shared middlewares; webhook posting via httpx.
"""
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional, Dict, Any, List

from services.shared.middleware import RequestIdMiddleware, RequestMetricsMiddleware  # type: ignore
from services.shared.utilities import attach_self_register  # type: ignore

from .modules.owner_resolver import owner_resolver
from .modules.notification_sender import notification_sender
from .modules.dlq_manager import dlq_manager

app = FastAPI(title="Notification Service", version="0.1.0")
app.add_middleware(RequestIdMiddleware)
app.add_middleware(RequestMetricsMiddleware, service_name="notification-service")
attach_self_register(app, "notification-service")


class OwnerUpdate(BaseModel):
    id: str
    owner: Optional[str] = None
    team: Optional[str] = None


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "notification-service"}


@app.post("/owners/update")
async def owners_update(req: OwnerUpdate):
    """Update owner information (stub implementation)."""
    # Stub: in a real system, update ownership registry (DB or config repo)
    return {"status": "ok", "id": req.id, "owner": req.owner, "team": req.team}


class NotifyPayload(BaseModel):
    """Notification payload data model."""
    channel: str  # slack|email|webhook
    target: str   # webhook URL or email address
    title: str
    message: str
    metadata: Dict[str, Any] = {}
    labels: List[str] = []


@app.post("/notify")
async def notify(req: NotifyPayload):
    """Send a notification with deduplication."""
    try:
        return await notification_sender.send_notification(
            channel=req.channel,
            target=req.target,
            title=req.title,
            message=req.message,
            metadata=req.metadata,
            labels=req.labels
        )
    except Exception as e:
        # Add failed notification to DLQ
        dlq_manager.add_failed_notification(req.model_dump(), str(e))
        raise


class ResolveOwnersRequest(BaseModel):
    """Owner resolution request data model."""
    owners: List[str]


@app.post("/owners/resolve")
async def owners_resolve(req: ResolveOwnersRequest):
    """Resolve owners to their target information."""
    resolved = owner_resolver.resolve_owners(req.owners)
    return {"resolved": resolved}


@app.get("/dlq")
async def get_dlq(limit: int = 50):
    """Get dead letter queue entries."""
    items = dlq_manager.get_dlq_entries(limit)
    return {"items": items}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5095)


