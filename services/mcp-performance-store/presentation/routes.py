"""
FastAPI routes for MCP Performance Store.
"""
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import List, Optional
from datetime import datetime

from services.mcp_performance_store.application.dto import (
    RecordExecutionRequest,
    ExecutionQueryRequest,
    ExecutionResponse,
    PatternPerformanceResponse
)
from services.mcp_performance_store.application.use_cases import (
    RecordExecutionUseCase,
    QueryExecutionsUseCase,
    GetPatternPerformanceUseCase
)
from services.mcp_performance_store.presentation.dependencies import (
    get_record_use_case,
    get_query_use_case,
    get_pattern_performance_use_case
)


router = APIRouter(prefix="/api/v1", tags=["performance"])


@router.post(
    "/performance/record",
    response_model=ExecutionResponse,
    status_code=201,
    summary="Record orchestration execution",
    description="Record performance metrics for an MCP orchestration execution"
)
async def record_execution(
    request: RecordExecutionRequest,
    use_case: RecordExecutionUseCase = Depends(get_record_use_case)
) -> ExecutionResponse:
    """Record a new orchestration execution."""
    try:
        response = await use_case.execute(request)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record execution: {str(e)}")


@router.get(
    "/performance/executions",
    response_model=List[ExecutionResponse],
    summary="Query orchestration executions",
    description="Query executions with optional filters"
)
async def query_executions(
    mcp_id: Optional[str] = Query(None, description="Filter by MCP ID"),
    pattern_used: Optional[str] = Query(None, description="Filter by pattern"),
    success: Optional[bool] = Query(None, description="Filter by success status"),
    start_time: Optional[datetime] = Query(None, description="Filter by start time"),
    end_time: Optional[datetime] = Query(None, description="Filter by end time"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum results"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    use_case: QueryExecutionsUseCase = Depends(get_query_use_case)
) -> List[ExecutionResponse]:
    """Query orchestration executions."""
    try:
        query_request = ExecutionQueryRequest(
            mcp_id=mcp_id,
            pattern_used=pattern_used,
            success=success,
            start_time=start_time,
            end_time=end_time,
            limit=limit,
            offset=offset
        )
        executions = await use_case.execute(query_request)
        return executions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to query executions: {str(e)}")


@router.get(
    "/performance/executions/count",
    response_model=dict,
    summary="Count matching executions",
    description="Get count of executions matching filters"
)
async def count_executions(
    mcp_id: Optional[str] = Query(None),
    pattern_used: Optional[str] = Query(None),
    success: Optional[bool] = Query(None),
    start_time: Optional[datetime] = Query(None),
    end_time: Optional[datetime] = Query(None),
    use_case: QueryExecutionsUseCase = Depends(get_query_use_case)
) -> dict:
    """Count matching executions."""
    try:
        query_request = ExecutionQueryRequest(
            mcp_id=mcp_id,
            pattern_used=pattern_used,
            success=success,
            start_time=start_time,
            end_time=end_time
        )
        count = await use_case.get_execution_count(query_request)
        return {"count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to count executions: {str(e)}")


@router.get(
    "/performance/patterns/{pattern_id}",
    response_model=PatternPerformanceResponse,
    summary="Get pattern performance by ID",
    description="Retrieve aggregated performance metrics for a pattern"
)
async def get_pattern_performance_by_id(
    pattern_id: str,
    use_case: GetPatternPerformanceUseCase = Depends(get_pattern_performance_use_case)
) -> PatternPerformanceResponse:
    """Get pattern performance by ID."""
    try:
        performance = await use_case.execute_by_id(pattern_id)
        if performance is None:
            raise HTTPException(status_code=404, detail=f"Pattern not found: {pattern_id}")
        return performance
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pattern performance: {str(e)}")


@router.get(
    "/performance/patterns",
    response_model=PatternPerformanceResponse,
    summary="Get pattern performance by name",
    description="Retrieve pattern performance by name and version"
)
async def get_pattern_performance_by_name(
    name: str = Query(..., description="Pattern name"),
    version: Optional[str] = Query(None, description="Pattern version"),
    use_case: GetPatternPerformanceUseCase = Depends(get_pattern_performance_use_case)
) -> PatternPerformanceResponse:
    """Get pattern performance by name."""
    try:
        performance = await use_case.execute_by_name(name, version)
        if performance is None:
            raise HTTPException(
                status_code=404,
                detail=f"Pattern not found: {name} v{version or 'latest'}"
            )
        return performance
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get pattern performance: {str(e)}")
