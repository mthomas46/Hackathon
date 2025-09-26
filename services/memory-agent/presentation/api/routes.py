"""API routes for memory agent service."""

from fastapi import APIRouter, HTTPException, Query, status
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from ...application.commands import StoreMemoryCommand
from ...application.queries import ListMemoryQuery
from ...domain.services import MemoryService
from ...infrastructure.persistence import MemoryRepository

# Create router
router = APIRouter(prefix="/api/v1", tags=["Memory Agent API"])

# Request/Response models
class MemoryItemRequest(BaseModel):
    """Request model for memory item."""
    type: str
    key: str
    value: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None
    ttl_seconds: Optional[int] = None

class MemoryQueryRequest(BaseModel):
    """Request model for memory queries."""
    type: Optional[str] = None
    key: Optional[str] = None
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results")

class MemoryResponse(BaseModel):
    """Response model for memory operations."""
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    count: Optional[int] = None

# Routes
@router.post("/memory/put", status_code=status.HTTP_201_CREATED, summary="Store Memory Item", description="Stores a memory item with optional TTL for operational context and event summaries.")
async def store_memory_item(request: MemoryItemRequest):
    """Store a memory item."""
    try:
        # Create command
        command = StoreMemoryCommand(
            user_id=request.key,  # Using key as user_id for now
            memory_type=request.type,
            content=str(request.value),  # Convert dict to string for now
            metadata=request.metadata
        )

        # Execute command
        memory_service = MemoryService(repository=None)  # Will use default repository
        result = await memory_service.store_memory(
            user_id=command.user_id,
            memory_type=command.memory_type,
            content=command.content,
            metadata=command.metadata
        )

        return MemoryResponse(
            success=True,
            message="Memory item stored successfully",
            data=result,
            count=1
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to store memory item: {str(e)}"
        )

@router.get("/memory/list", summary="List Memory Items", description="Retrieves stored memory items with optional filtering by type, key, and pagination.")
async def list_memory_items(
    type: Optional[str] = Query(None, description="Filter by memory type"),
    key: Optional[str] = Query(None, description="Filter by memory key"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results")
):
    """List memory items with filtering."""
    try:
        # Create query
        query = ListMemoriesQuery(
            user_id=key or "default",  # Using key as user_id for now
            memory_type=type,
            limit=limit
        )

        # Execute query
        repository = MemoryRepository()
        items = await repository.find_memories(query)

        return MemoryResponse(
            success=True,
            message="Memory items retrieved successfully",
            data={"items": items},
            count=len(items)
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list memory items: {str(e)}"
        )

@router.get("/memory/stats", summary="Get Memory Statistics", description="Returns comprehensive memory statistics and usage metrics.")
async def get_memory_stats():
    """Get memory statistics."""
    try:
        memory_service = MemoryService(repository=None)  # Will use default repository
        stats = await memory_service.get_memory_statistics(user_id="system")

        return MemoryResponse(
            success=True,
            message="Memory statistics retrieved successfully",
            data=stats
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get memory statistics: {str(e)}"
        )
