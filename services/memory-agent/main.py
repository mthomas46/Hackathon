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
from contextlib import asynccontextmanager
from typing import Optional
from datetime import datetime, timezone

import sys
from pathlib import Path

from fastapi import FastAPI
from typing import Dict, Any
from pydantic import BaseModel

# Import domain entities with fallbacks
try:
    from .domain.entities.memory_item import MemoryItem
except ImportError:
    # Fallback MemoryItem class
    from dataclasses import dataclass
    from typing import Optional
    from datetime import datetime

    @dataclass
    class MemoryItem:
        id: str
        user_id: str
        memory_type: str
        content: str
        metadata: Optional[dict] = None

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

try:
    from services.shared.presentation.api.responses import APIResponse
    from services.shared.infrastructure.config import load_service_config
except ImportError:
    # Fallback implementations
    from datetime import datetime, timezone
    
    class APIResponse(BaseModel):
        success: bool
        message: Optional[str] = None
        data: Optional[Any] = None
        timestamp: str = ""
        request_id: Optional[str] = None

    def load_service_config(**kwargs):
        """Load fallback service configuration for memory-agent.

        Returns a mock configuration object when the shared config module is unavailable.
        Used for local development and testing scenarios.
        """
        return type('Config', (), {
            'service_name': 'memory-agent',
            'service_description': 'Memory Agent Service',
            'service_version': '1.0.0',
            'server': type('Server', (), {'host': '0.0.0.0', 'port': 5006})(),
            'port': 5006,
        })()

# ============================================================================
# SHARED MODULES - Leveraging centralized functionality for consistency
# ============================================================================
try:
    from services.shared.utilities import attach_self_register, setup_common_middleware
except ImportError:
    # Fallback implementations
    def attach_self_register(app, service_name=None, **kwargs):
        """Attach service self-registration functionality to FastAPI app.

        This is a fallback implementation when the shared utilities are unavailable.
        In a real implementation, this would register the service with an orchestrator.
        """
        pass

    def setup_common_middleware(app, **kwargs):
        """Setup common middleware for the FastAPI application.

        This is a fallback implementation when shared utilities are unavailable.
        In a real implementation, this would add logging, CORS, and other middleware.
        """
        pass

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

    # Add current directory to path for relative imports
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)

    try:
        from modules.memory_ops import get_memory_stats, list_memory_items, put_memory_item
        from modules.shared_utils import (
            build_memory_agent_context,
            create_memory_agent_success_response,
            handle_memory_agent_error,
            validate_memory_item,
        )
    except ImportError:
        # Mock implementations for local testing
        def get_memory_stats():
            """Get mock memory statistics for testing.

            Returns basic mock statistics when memory operations are unavailable.
            """
            return {"total_items": 0, "total_sessions": 0}

        def list_memory_items(**kwargs):
            """List mock memory items for testing.

            Returns empty list when memory operations are unavailable.
            """
            return []

        def put_memory_item(item):
            """Store mock memory item for testing.

            Returns mock success response when memory operations are unavailable.
            """
            return {
                "count": 1,
                "max_items": 100,
                "utilization_percent": 1.0
            }

        def build_memory_agent_context(**kwargs):
            """Build mock memory agent context for testing.

            Returns empty context when shared utilities are unavailable.
            """
            return {}

        def create_memory_agent_success_response(action, data, **kwargs):
            """Create mock success response for testing.

            Returns standardized success response when shared utilities are unavailable.
            """
            return {
                "success": True,
                "data": data,
                "message": f"Memory {action}",
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        def handle_memory_agent_error(operation, error, **kwargs):
            """Handle mock memory agent error for testing.

            Returns standardized error response when shared utilities are unavailable.
            """
            return {
                "success": False,
                "message": f"{operation}: {str(error)}",
                "data": None,
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

        def validate_memory_item(item):
            """Validate mock memory item for testing.

            Always returns True when validation utilities are unavailable.
            """
            return True

try:
    from .modules.event_processor import event_processor
except ImportError:
    # Fallback for event processor
    class MockEventProcessor:
        async def initialize_redis(self):
            return True

        async def subscribe_to_channels(self):
            pass

        async def process_events(self):
            pass
    event_processor = MockEventProcessor()

# Import global memory state from dedicated module to avoid circular dependencies

# ============================================================================
# GLOBAL STATE MANAGEMENT - Centralized memory state
# ============================================================================


# Load standardized configuration
config = load_service_config("memory-agent")

# Service configuration from standardized config
SERVICE_NAME = config.service_name
SERVICE_TITLE = "Memory Agent"
SERVICE_VERSION = config.service_version
DEFAULT_API_PORT = int(os.environ.get("SERVICE_API_PORT", "5090"))

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

# Initialize FastAPI app with standardized configuration
app = FastAPI(
    title=SERVICE_TITLE,
    version=SERVICE_VERSION,
    description="Memory agent service for storing operational context and event summaries",
    lifespan=_lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Setup standardized middleware and utilities
setup_common_middleware(app, service_name=config.service_name)

# Auto-register with orchestrator using standardized service name
attach_self_register(app, config.service_name)

# ============================================================================
# DATASTORE OPERATION LOGGING - Track all operations to log-collector
# ============================================================================
try:
    from services.shared.infrastructure.logging.datastore_operation_logger import add_datastore_logging
    
    add_datastore_logging(
        app,
        service_name="memory-agent",
        log_collector_url="http://localhost:8104",
        timeout_seconds=1.0
    )
    print("✅ DataStore operation logging enabled for memory-agent → log-collector")
except Exception as e:
    print(f"⚠️  Could not enable datastore logging: {e}")

# Custom memory-specific health endpoint
@app.get("/health", summary="Memory Agent Health Check", description="Returns service health status including memory statistics and operational metrics.", tags=["health"], responses={200: {"description": "Service is healthy with memory statistics"}, 500: {"description": "Service health check failed"}})
async def memory_health():
    """Memory agent health check with comprehensive memory statistics."""
    try:
        stats = get_memory_stats()
        from datetime import datetime

        return {
            "success": True,
            "message": "Memory agent operational with active memory management",
            "data": {
                "status": "healthy",
                "service": SERVICE_NAME,
                "version": SERVICE_VERSION,
                "timestamp": datetime.utcnow().isoformat(),
                "environment": os.environ.get("ENVIRONMENT", "development"),
                "memory_count": stats.get("total_items", 0),
                "memory_capacity": stats.get("max_items", 0),
                "memory_usage_percent": stats.get("usage_percent", 0),
                "ttl_seconds": stats.get("ttl_seconds", 0),
            }
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Memory agent experiencing issues: {str(e)}",
            "data": {
                "status": "unhealthy",
                "service": SERVICE_NAME,
                "version": SERVICE_VERSION,
                "error": str(e),
            }
        }


class MemoryItemRequest(BaseModel):
    """Pydantic model for memory item API requests."""
    id: str
    user_id: str
    memory_type: str
    content: str
    metadata: Optional[Dict[str, Any]] = None

class PutMemoryRequest(BaseModel):
    """Request model for storing memory items.

    Contains a single memory item to be stored in the memory agent's
    operational context storage with TTL-based expiration.
    """

    item: MemoryItemRequest
    """The memory item to store, containing type, key, value, and metadata."""


@app.post("/memory/put", summary="Store Memory Item", description="Stores a memory item with optional TTL for operational context and event summaries.", response_model=APIResponse, tags=["memory", "storage"], responses={201: {"description": "Memory item stored successfully"}, 400: {"description": "Invalid memory data"}, 500: {"description": "Memory storage failed"}})
async def put_memory(req: PutMemoryRequest):
    """Store a memory item with validation and error handling."""
    try:
        # Convert Pydantic request model to MemoryItem dataclass entity
        memory_item = MemoryItem(
            id=req.item.id,
            user_id=req.item.user_id,
            memory_type=req.item.memory_type,
            content=req.item.content,
            metadata=req.item.metadata or {}
        )
        
        # Validate memory item
        validate_memory_item(memory_item)

        result = put_memory_item(memory_item)

        context = build_memory_agent_context("store", item_count=result.get("count", 1))
        context = {k: v for k, v in context.items() if k in ["request_id"]}
        return create_memory_agent_success_response("stored", result, **context)

    except Exception as e:
        context = {"item_type": getattr(req.item, "memory_type", None)}
        return handle_memory_agent_error("store memory item", e, **context)


@app.get("/memory/list", summary="List Memory Items", description="Retrieves stored memory items with optional filtering by type, key, and pagination.", response_model=APIResponse, tags=["memory", "query"], responses={200: {"description": "Memory items retrieved successfully"}, 400: {"description": "Invalid query parameters"}})
async def list_memory(
    type: Optional[str] = None, key: Optional[str] = None, limit: int = 100
):
    """List memory items with filtering and pagination."""
    try:
        items = list_memory_items(type, key, limit)
        result = {"items": [m.model_dump() for m in items]}

        context = build_memory_agent_context(
            "list", memory_type=type, item_count=len(items), limit=limit
        )
        context = {k: v for k, v in context.items() if k in ["request_id"]}
        return create_memory_agent_success_response("retrieved", result, **context)

    except Exception as e:
        context = {"memory_type": type, "key": key}
        return handle_memory_agent_error("list memory items", e, **context)


## Lifespan handles startup


if __name__ == "__main__":
    """Run the Memory Agent service directly."""
    import uvicorn

    host = os.getenv("MEMORY_AGENT_API_HOST", "0.0.0.0")
    uvicorn.run(app, host=host, port=DEFAULT_API_PORT, log_level="info")
