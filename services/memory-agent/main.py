from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional, Any, Dict
import asyncio
import os
from contextlib import asynccontextmanager
from datetime import timedelta

# ============================================================================
# SHARED MODULES - Leveraging centralized functionality for consistency
# ============================================================================
from services.shared.health import register_health_endpoints
from services.shared.responses import create_success_response
from services.shared.error_handling import ServiceException
from services.shared.constants_new import ServiceNames, ErrorCodes
from services.shared.utilities import utc_now, setup_common_middleware, attach_self_register
from services.shared.models import MemoryItem
from services.shared.logging import fire_and_forget

try:
    import redis.asyncio as aioredis  # type: ignore
except Exception:
    aioredis = None

# ============================================================================
# LOCAL MODULES - Service-specific functionality
# ============================================================================
from .modules.shared_utils import (
    get_memory_max_items,
    get_memory_ttl_seconds,
    get_redis_url,
    handle_memory_agent_error,
    create_memory_agent_success_response,
    build_memory_agent_context,
    create_memory_item,
    serialize_memory_value,
    deserialize_memory_value,
    cleanup_expired_memory_items,
    get_memory_stats_summary,
    validate_memory_item,
    extract_endpoint_from_text
)
from .modules.memory_ops import put_memory_item, list_memory_items, get_memory_stats, cleanup_expired_items

# ============================================================================
# GLOBAL STATE MANAGEMENT - Centralized memory state
# ============================================================================

# Import global memory state from dedicated module to avoid circular dependencies
from .modules.memory_state import _memory

"""Memory Agent

Stores short-lived operational context and summaries from events and services.
Provides simple put/list endpoints and subscribes to Redis pub/sub topics.
"""

# Global memory state imported from dedicated module
_endpoint_index: dict[str, int] = {}
_event_task = None


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Lifespan context manager for memory agent startup/shutdown."""
    global _event_task
    try:
        _event_task = asyncio.create_task(subscribe_events())
        yield
    finally:
        if _event_task:
            _event_task.cancel()


# ============================================================================
# APP INITIALIZATION - Using shared patterns for consistency
# ============================================================================

# Initialize FastAPI app with shared middleware
app = FastAPI(title="Memory Agent", version="1.0.0", lifespan=_lifespan)

# Use common middleware setup and error handlers to reduce duplication across services
setup_common_middleware(app, ServiceNames.MEMORY_AGENT)

# Auto-register with orchestrator
attach_self_register(app, ServiceNames.MEMORY_AGENT)

# Custom memory-specific health endpoint
@app.get("/health")
async def memory_health():
    """Memory agent health with memory statistics."""
    try:
        stats = get_memory_stats()
        return {
            "status": "healthy",
            "service": ServiceNames.MEMORY_AGENT,
            "version": "1.0.0",
            "environment": os.environ.get("ENVIRONMENT", "development"),
            "memory_count": stats.get("total_items", 0),
            "memory_capacity": stats.get("max_items", 0),
            "memory_usage_percent": stats.get("usage_percent", 0),
            "ttl_seconds": stats.get("ttl_seconds", 0)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": ServiceNames.MEMORY_AGENT,
            "version": "1.0.0",
            "error": str(e)
        }


class PutMemoryRequest(BaseModel):
    item: MemoryItem


@app.post("/memory/put")
async def put_memory(req: PutMemoryRequest):
    """Store a memory item with validation and error handling."""
    try:
        # Validate memory item
        validate_memory_item(req.item)

        result = put_memory_item(req.item)

        context = build_memory_agent_context("store", item_count=result.get("count", 1))
        context = {k: v for k, v in context.items() if k in ["request_id"]}
        return create_memory_agent_success_response("stored", result, **context)

    except Exception as e:
        context = {"item_type": getattr(req.item, 'type', None)}
        return handle_memory_agent_error("store memory item", e, **context)


@app.get("/memory/list")
async def list_memory(type: Optional[str] = None, key: Optional[str] = None, limit: int = 100):
    """List memory items with filtering and pagination."""
    try:
        items = list_memory_items(type, key, limit)
        result = {"items": [m.model_dump() for m in items]}

        context = build_memory_agent_context("list", memory_type=type, item_count=len(items), limit=limit)
        context = {k: v for k, v in context.items() if k in ["request_id"]}
        return create_memory_agent_success_response("retrieved", result, **context)

    except Exception as e:
        context = {"memory_type": type, "key": key}
        return handle_memory_agent_error("list memory items", e, **context)


async def subscribe_events():
    """Subscribe to Redis pub/sub channels for memory context collection."""
    if not aioredis:
        return

    redis_url = get_redis_url()
    client = aioredis.from_url(redis_url)
    pubsub = client.pubsub()

    # Subscribe to key ecosystem topics for memory context
    await pubsub.subscribe(
        "ingestion.requested",
        "docs.ingested.github",
        "docs.ingested.jira",
        "docs.ingested.confluence",
        "apis.ingested.swagger",
        "findings.created",
    )

    try:
        async for message in pubsub.listen():
            if message.get("type") != "message":
                continue

            channel = message.get("channel", b"").decode()
            data = message.get("data")

            try:
                payload = json.loads(data) if isinstance(data, (bytes, str)) else {"raw": str(data)}
            except Exception:
                payload = {"raw": str(data)}

            # Create memory item from event
            memory_item = await _create_memory_item_from_event(channel, payload)
            _memory.append(memory_item)

            # Maintain memory size limits
            max_items = get_memory_max_items()
            if len(_memory) > max_items:
                del _memory[: len(_memory) - max_items]

            # Update endpoint index from document events
            if channel.startswith("docs.ingested"):
                _update_endpoint_index_from_payload(payload)

    finally:
        await pubsub.close()
        await client.aclose()


async def _create_memory_item_from_event(channel: str, payload: Dict[str, Any]) -> MemoryItem:
    """Create a memory item from a Redis event."""
    # Determine memory item type and summary
    if channel == "ingestion.requested":
        kind = "operation"
        summary = f"{channel} event received"
    elif channel.startswith("docs.ingested"):
        kind = "doc_summary"
        summary = f"Document ingested from {channel.split('.')[-1]}"
    elif channel == "apis.ingested.swagger":
        kind = "api_summary"
        summary = "API specification ingested"
    elif channel == "findings.created":
        kind = "finding"
        cnt = payload.get("count", 0)
        sev = payload.get("severity_counts", {})
        summary = f"findings.created: {cnt} findings (severity: {sev})"
    else:
        kind = "event"
        summary = f"{channel} event received"

    # Create memory item
    return create_memory_item(
        key=payload.get("correlation_id") or f"{channel}:{len(_memory) + 1}",
        value={"channel": channel, "payload": payload},
        item_type=kind,
        ttl_seconds=get_memory_ttl_seconds(),
        metadata={
            "source": "redis_event",
            "channel": channel,
            "summary": summary
        }
    )


def _update_endpoint_index_from_payload(payload: Dict[str, Any]) -> None:
    """Update endpoint index from document payload."""
    if not isinstance(payload, dict):
        return

    doc_payload = payload.get("document") or {}
    text = doc_payload.get("content") or doc_payload.get("title") or ""

    endpoints = extract_endpoint_from_text(text)
    for endpoint in endpoints:
        _endpoint_index[endpoint] = _endpoint_index.get(endpoint, 0) + 1


## Lifespan handles startup


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5040)


