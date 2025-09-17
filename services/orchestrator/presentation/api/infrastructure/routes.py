"""API Routes for Infrastructure Management

Provides endpoints for:
- Distributed transaction management (Sagas)
- Distributed tracing
- Dead Letter Queue management
- Event streaming
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime

from .dtos import (
    DLQRetryRequest, EventReplayRequest, EventClearRequest,
    DLQStatsResponse, SagaStatsResponse, SagaDetailResponse,
    EventHistoryResponse, TracingStatsResponse, TraceDetailResponse,
    PeerInfoResponse
)
from ....main import container

router = APIRouter()


# Saga Management Routes
@router.post("/sagas", response_model=dict)
async def start_saga():
    """Start a new distributed transaction (saga)."""
    try:
        result = await container.start_saga_use_case.execute()
        return {"saga_id": result["saga_id"], "status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start saga: {str(e)}")


@router.get("/sagas/{saga_id}", response_model=SagaDetailResponse)
async def get_saga(saga_id: str):
    """Get details of a specific saga."""
    try:
        from ....application.infrastructure.queries import GetSagaQuery
        query = GetSagaQuery(saga_id=saga_id)
        result = await container.get_saga_use_case.execute(query)
        if not result:
            raise HTTPException(status_code=404, detail="Saga not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get saga: {str(e)}")


@router.get("/sagas", response_model=SagaStatsResponse)
async def list_sagas(limit: int = 50, offset: int = 0):
    """List sagas with pagination."""
    try:
        from ....application.infrastructure.queries import ListSagasQuery
        query = ListSagasQuery(limit=limit, offset=offset)
        result = await container.list_sagas_use_case.execute(query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list sagas: {str(e)}")


# Tracing Routes
@router.post("/traces", response_model=dict)
async def start_trace(service_name: str, operation_name: str):
    """Start a new distributed trace."""
    try:
        from ....application.infrastructure.commands import StartTraceCommand
        command = StartTraceCommand(
            service_name=service_name,
            operation_name=operation_name
        )
        result = await container.start_trace_use_case.execute(command)
        return {"trace_id": result["trace_id"], "status": "started"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to start trace: {str(e)}")


@router.get("/traces/{trace_id}", response_model=TraceDetailResponse)
async def get_trace(trace_id: str):
    """Get details of a specific trace."""
    try:
        from ....application.infrastructure.queries import GetTraceQuery
        query = GetTraceQuery(trace_id=trace_id)
        result = await container.get_trace_use_case.execute(query)
        if not result:
            raise HTTPException(status_code=404, detail="Trace not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get trace: {str(e)}")


@router.get("/traces", response_model=TracingStatsResponse)
async def list_traces(limit: int = 50, offset: int = 0):
    """List traces with pagination."""
    try:
        from ....application.infrastructure.queries import ListTracesQuery
        query = ListTracesQuery(limit=limit, offset=offset)
        result = await container.list_traces_use_case.execute(query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list traces: {str(e)}")


# DLQ Management Routes
@router.get("/dlq/stats", response_model=DLQStatsResponse)
async def get_dlq_stats():
    """Get Dead Letter Queue statistics."""
    try:
        result = await container.get_dlq_stats_use_case.execute()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get DLQ stats: {str(e)}")


@router.get("/dlq/events", response_model=EventHistoryResponse)
async def list_dlq_events(limit: int = 50, offset: int = 0):
    """List events in the Dead Letter Queue."""
    try:
        from ....application.infrastructure.queries import ListDLQEventsQuery
        query = ListDLQEventsQuery(limit=limit, offset=offset)
        result = await container.list_dlq_events_use_case.execute(query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list DLQ events: {str(e)}")


@router.post("/dlq/retry", response_model=dict)
async def retry_dlq_events(request: DLQRetryRequest):
    """Retry events from the Dead Letter Queue."""
    try:
        from ....application.infrastructure.commands import RetryEventCommand
        command = RetryEventCommand(
            event_ids=request.event_ids,
            max_retries=request.max_retries
        )
        result = await container.retry_event_use_case.execute(command)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to retry events: {str(e)}")


# Event Streaming Routes
@router.get("/events/stats", response_model=dict)
async def get_event_stream_stats():
    """Get event streaming statistics."""
    try:
        result = await container.get_event_stream_stats_use_case.execute()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get event stats: {str(e)}")


@router.post("/events/publish", response_model=dict)
async def publish_event(event_type: str, payload: dict):
    """Publish an event to the event stream."""
    try:
        from ....application.infrastructure.commands import PublishEventCommand
        command = PublishEventCommand(
            event_type=event_type,
            payload=payload
        )
        result = await container.publish_event_use_case.execute(command)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to publish event: {str(e)}")


@router.post("/events/replay", response_model=dict)
async def replay_events(request: EventReplayRequest):
    """Replay events from history."""
    # Placeholder - event replay functionality would be implemented here
    return {"message": "Event replay not yet implemented", "status": "pending"}


@router.post("/events/clear", response_model=dict)
async def clear_events(request: EventClearRequest):
    """Clear old events from storage."""
    # Placeholder - event clearing functionality would be implemented here
    return {"message": "Event clearing not yet implemented", "status": "pending"}
