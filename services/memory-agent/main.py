"""Service: Memory Agent

Endpoints:
- POST /memory/put: Store operational context and summaries from events
- GET /memory/list: Retrieve stored memory items with filtering and pagination
- GET /health: Service health check with memory statistics

Responsibilities:
- Store short-lived operational context and event summaries for service coordination
- Subscribe to Redis pub/sub topics for real-time event processing
- Provide memory management with TTL-based expiration and capacity limits
- Support filtering and pagination for memory retrieval operations
- Maintain event-driven context for distributed system coordination

Dependencies: shared middlewares, Redis for event pub/sub, shared models and utilities.
"""
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
from services.shared.monitoring.health import register_health_endpoints
from services.shared.core.responses.responses import create_success_response
from services.shared.utilities.error_handling import ServiceException
from services.shared.core.constants_new import ServiceNames, ErrorCodes
from services.shared.utilities import utc_now, setup_common_middleware, attach_self_register
from services.shared.core.models.models import MemoryItem
from services.shared.monitoring.logging import fire_and_forget

try:
    import redis.asyncio as aioredis  # type: ignore
except Exception:
    aioredis = None

# ============================================================================
# LOCAL MODULES - Service-specific functionality
# ============================================================================
try:
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
except ImportError:
    # Fallback for when running as script
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from modules.shared_utils import (
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
    from modules.memory_ops import put_memory_item, list_memory_items, get_memory_stats, cleanup_expired_items
from .modules.event_processor import event_processor

# ============================================================================
# GLOBAL STATE MANAGEMENT - Centralized memory state
# ============================================================================

# Import global memory state from dedicated module to avoid circular dependencies
from .modules.memory_state import _memory

# Service configuration constants
SERVICE_NAME = "memory-agent"
SERVICE_TITLE = "Memory Agent"
SERVICE_VERSION = "1.0.0"
DEFAULT_PORT = 5040

# Global event task
_event_task = None


@asynccontextmanager
async def _lifespan(app: FastAPI):
    """Lifespan context manager for memory agent startup/shutdown."""
    global _event_task
    try:
        # Initialize Redis and start event processing
        if await event_processor.initialize_redis():
            await event_processor.subscribe_to_channels()
            _event_task = asyncio.create_task(event_processor.process_events())
        yield
    finally:
        if _event_task:
            _event_task.cancel()


# ============================================================================
# APP INITIALIZATION - Using shared patterns for consistency
# ============================================================================

# Initialize FastAPI app with shared middleware
app = FastAPI(
    title=SERVICE_TITLE,
    version=SERVICE_VERSION,
    description="Memory agent service for storing operational context and event summaries",
    lifespan=_lifespan
)

# Use common middleware setup and error handlers to reduce duplication across services
setup_common_middleware(app, ServiceNames.MEMORY_AGENT)

# Auto-register with orchestrator
attach_self_register(app, ServiceNames.MEMORY_AGENT)

# Custom memory-specific health endpoint
@app.get("/health")
async def memory_health():
    """Memory agent health check with comprehensive memory statistics."""
    try:
        stats = get_memory_stats()
        return {
            "status": "healthy",
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "environment": os.environ.get("ENVIRONMENT", "development"),
            "memory_count": stats.get("total_items", 0),
            "memory_capacity": stats.get("max_items", 0),
            "memory_usage_percent": stats.get("usage_percent", 0),
            "ttl_seconds": stats.get("ttl_seconds", 0),
            "description": "Memory agent operational with active memory management"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "error": str(e),
            "description": "Memory agent experiencing issues"
        }


class PutMemoryRequest(BaseModel):
    """Request model for storing memory items.

    Contains a single memory item to be stored in the memory agent's
    operational context storage with TTL-based expiration.
    """

    item: MemoryItem
    """The memory item to store, containing type, key, value, and metadata."""


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




## Lifespan handles startup


if __name__ == "__main__":
    """Run the Memory Agent service directly."""
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=DEFAULT_PORT,
        log_level="info"
    )


