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

import asyncio
import os
import time
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI
from pydantic import BaseModel

from services.shared.core.constants_new import ServiceNames
from services.shared.core.models.models import MemoryItem

# ============================================================================
# SHARED MODULES - Leveraging centralized functionality for consistency
# ============================================================================
from services.shared.utilities.logging_client import get_log_collector_client
from services.shared.utilities.utilities import attach_self_register, setup_common_middleware

try:
    import redis.asyncio as aioredis  # type: ignore
except Exception:
    aioredis = None

# ============================================================================
# LOCAL MODULES - Service-specific functionality
# ============================================================================
try:
    from .modules.memory_ops import get_memory_stats, list_memory_items, put_memory_item
    from .modules.shared_utils import (
        build_memory_agent_context,
        create_memory_agent_success_response,
        handle_memory_agent_error,
        validate_memory_item,
    )
except ImportError:
    # Fallback for when running as script
    import os
    import sys

    sys.path.insert(0, os.path.dirname(__file__))
    from modules.shared_utils import (
        handle_memory_agent_error,
        create_memory_agent_success_response,
        build_memory_agent_context,
        validate_memory_item,
    )
    from modules.memory_ops import put_memory_item, list_memory_items, get_memory_stats

from .modules.event_processor import event_processor

# Import global memory state from dedicated module to avoid circular dependencies

# ============================================================================
# GLOBAL STATE MANAGEMENT - Centralized memory state
# ============================================================================


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
    global _event_task, logger_client

    try:
        # Initialize logger client
        try:
            logger_client = await get_log_collector_client(ServiceNames.MEMORY_AGENT)
            if logger_client:
                await logger_client.log_business_event(
                    "memory_agent_startup",
                    {
                        "version": SERVICE_VERSION,
                        "redis_enabled": aioredis is not None,
                        "memory_persistence": True,
                        "ttl_enabled": True,
                        "event_streaming": True,
                    },
                )
                await logger_client.log_info(
                    "Memory Agent service started",
                    {"redis_available": aioredis is not None, "memory_management": True, "event_streaming": True},
                )
        except Exception as e:
            print(f"Failed to initialize log collector client: {e}")

        # Initialize Redis and start event processing
        if await event_processor.initialize_redis():
            await event_processor.subscribe_to_channels()
            _event_task = asyncio.create_task(event_processor.process_events())
        yield
    finally:
        # Log shutdown
        if logger_client:
            try:
                await logger_client.log_info("Memory Agent service shutting down")
            except Exception:
                pass

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
    lifespan=_lifespan,
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
            "description": "Memory agent operational with active memory management",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": SERVICE_NAME,
            "version": SERVICE_VERSION,
            "error": str(e),
            "description": "Memory agent experiencing issues",
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
    start_time = time.time()
    request_id = f"mem_put_{int(time.time() * 1000)}"

    try:
        # Log memory storage start
        if logger_client:
            await logger_client.log_business_event(
                "memory_item_storage_started",
                {
                    "request_id": request_id,
                    "item_type": getattr(req.item, "type", None),
                    "item_key": getattr(req.item, "key", None),
                    "has_summary": bool(getattr(req.item, "summary", None)),
                    "data_size": len(str(getattr(req.item, "data", {}))),
                },
            )

            await logger_client.log_info(
                "Storing memory item",
                {
                    "request_id": request_id,
                    "item_type": getattr(req.item, "type", None),
                    "has_key": bool(getattr(req.item, "key", None)),
                },
            )

        # Validate memory item
        validate_memory_item(req.item)

        result = put_memory_item(req.item)
        response_time = time.time() - start_time

        # Log successful storage
        if logger_client:
            await logger_client.log_business_event(
                "memory_item_stored",
                {
                    "request_id": request_id,
                    "item_type": getattr(req.item, "type", None),
                    "item_key": getattr(req.item, "key", None),
                    "total_memory_items": result.get("count", 1),
                    "response_time_seconds": response_time,
                    "success": True,
                },
            )

            await logger_client.log_performance_metric(
                "memory_storage",
                response_time,
                {"request_id": request_id, "item_type": getattr(req.item, "type", None), "storage_success": True},
            )

        context = build_memory_agent_context("store", item_count=result.get("count", 1))
        context = {k: v for k, v in context.items() if k in ["request_id"]}
        return create_memory_agent_success_response("stored", result, **context)

    except Exception as e:
        error_time = time.time() - start_time

        # Log storage failure
        if logger_client:
            await logger_client.log_error(
                f"Memory item storage failed: {str(e)}",
                {
                    "request_id": request_id,
                    "item_type": getattr(req.item, "type", None),
                    "item_key": getattr(req.item, "key", None),
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                },
                error=e,
            )

            await logger_client.log_business_event(
                "memory_item_storage_failed",
                {
                    "request_id": request_id,
                    "item_type": getattr(req.item, "type", None),
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        context = {"item_type": getattr(req.item, "type", None)}
        return handle_memory_agent_error("store memory item", e, **context)


@app.get("/memory/list")
async def list_memory(type: Optional[str] = None, key: Optional[str] = None, limit: int = 100):
    """List memory items with filtering and pagination."""
    start_time = time.time()
    request_id = f"mem_list_{int(time.time() * 1000)}"

    try:
        # Log memory retrieval start
        if logger_client:
            await logger_client.log_business_event(
                "memory_items_retrieval_started",
                {
                    "request_id": request_id,
                    "filter_type": type,
                    "filter_key": key,
                    "limit": limit,
                    "has_filters": bool(type or key),
                },
            )

            await logger_client.log_info(
                "Retrieving memory items",
                {"request_id": request_id, "filter_type": type, "has_key_filter": bool(key), "limit": limit},
            )

        items = list_memory_items(type, key, limit)
        result = {"items": [m.model_dump() for m in items]}
        response_time = time.time() - start_time

        # Log successful retrieval
        if logger_client:
            await logger_client.log_business_event(
                "memory_items_retrieved",
                {
                    "request_id": request_id,
                    "filter_type": type,
                    "filter_key": key,
                    "limit": limit,
                    "items_returned": len(items),
                    "response_time_seconds": response_time,
                    "success": True,
                },
            )

            await logger_client.log_performance_metric(
                "memory_retrieval",
                response_time,
                {
                    "request_id": request_id,
                    "filter_type": type,
                    "items_returned": len(items),
                    "retrieval_success": True,
                },
            )

        context = build_memory_agent_context("list", memory_type=type, item_count=len(items), limit=limit)
        context = {k: v for k, v in context.items() if k in ["request_id"]}
        return create_memory_agent_success_response("retrieved", result, **context)

    except Exception as e:
        error_time = time.time() - start_time

        # Log retrieval failure
        if logger_client:
            await logger_client.log_error(
                f"Memory items retrieval failed: {str(e)}",
                {
                    "request_id": request_id,
                    "filter_type": type,
                    "filter_key": key,
                    "limit": limit,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                },
                error=e,
            )

            await logger_client.log_business_event(
                "memory_items_retrieval_failed",
                {
                    "request_id": request_id,
                    "filter_type": type,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        context = {"memory_type": type, "key": key}
        return handle_memory_agent_error("list memory items", e, **context)


## Lifespan handles startup


if __name__ == "__main__":
    """Run the Memory Agent service directly."""
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=DEFAULT_PORT, log_level="info")
