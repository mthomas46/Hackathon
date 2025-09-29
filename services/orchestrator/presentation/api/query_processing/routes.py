"""API Routes for Query Processing

Provides endpoints for:
- Natural language query processing
- Structured query execution
- Query result retrieval
- Query history management
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional

from .dtos import (
    ProcessQueryRequest, QueryResultResponse, QueryHistoryResponse,
    QueryListResponse, StructuredQueryRequest
)
from ....main import container

router = APIRouter()


@router.post("/process", response_model=QueryResultResponse)
async def process_natural_language_query(request: ProcessQueryRequest):
    """Process a natural language query and return results."""
    try:
        from ....application.query_processing.commands import ProcessNaturalLanguageQueryCommand
        command = ProcessNaturalLanguageQueryCommand(
            query_text=request.query_text,
            context=request.context,
            max_results=request.max_results,
            include_explanation=request.include_explanation
        )
        result = await container.process_natural_language_query_use_case.execute(command)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")


@router.post("/structured", response_model=QueryResultResponse)
async def execute_structured_query(request: StructuredQueryRequest):
    """Execute a structured query with specific parameters."""
    try:
        from ....application.query_processing.commands import ExecuteStructuredQueryCommand
        command = ExecuteStructuredQueryCommand(
            query_type=request.query_type,
            parameters=request.parameters,
            filters=request.filters,
            sorting=request.sorting,
            pagination=request.pagination
        )
        result = await container.process_natural_language_query_use_case.execute(command)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute structured query: {str(e)}")


@router.get("/results/{query_id}", response_model=QueryResultResponse)
async def get_query_result(query_id: str):
    """Get the result of a previously executed query."""
    try:
        from ....application.query_processing.queries import GetQueryResultQuery
        query = GetQueryResultQuery(query_id=query_id)
        result = await container.get_query_result_use_case.execute(query)
        if not result:
            raise HTTPException(status_code=404, detail="Query result not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get query result: {str(e)}")


@router.get("/history", response_model=QueryListResponse)
async def list_query_history(
    intent: Optional[str] = None,
    status: Optional[str] = None,
    page: int = 1,
    page_size: int = 20
):
    """List query execution history with optional filters."""
    try:
        from ....application.query_processing.queries import ListQueriesQuery
        query = ListQueriesQuery(
            intent_filter=intent,
            status_filter=status,
            page=page,
            page_size=page_size
        )
        result = await container.list_queries_use_case.execute(query)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list query history: {str(e)}")


@router.get("/history/{query_id}", response_model=QueryHistoryResponse)
async def get_query_history(query_id: str):
    """Get detailed history for a specific query."""
    try:
        from ....application.query_processing.queries import GetQueryHistoryQuery
        query = GetQueryHistoryQuery(query_id=query_id)
        result = await container.list_queries_use_case.execute(query)
        if not result:
            raise HTTPException(status_code=404, detail="Query history not found")
        return result
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get query history: {str(e)}")


@router.get("/intents", response_model=dict)
async def list_query_intents():
    """List available query intents that can be processed."""
    try:
        return {
            "intents": [
                {
                    "name": "search",
                    "description": "Search for documents or content",
                    "example_queries": ["find documents about AI", "search for error logs"]
                },
                {
                    "name": "analytics",
                    "description": "Generate analytics and insights",
                    "example_queries": ["analyze code quality", "show usage statistics"]
                },
                {
                    "name": "summarize",
                    "description": "Create summaries of content",
                    "example_queries": ["summarize this document", "overview of recent changes"]
                },
                {
                    "name": "explain",
                    "description": "Explain code, concepts, or processes",
                    "example_queries": ["explain this function", "what does this code do"]
                },
                {
                    "name": "compare",
                    "description": "Compare different items or versions",
                    "example_queries": ["compare these two approaches", "differences between versions"]
                }
            ],
            "total_intents": 5
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list query intents: {str(e)}")


@router.delete("/results/{query_id}", response_model=dict)
async def delete_query_result(query_id: str):
    """Delete a query result from history."""
    try:
        # This would use a DeleteQueryResultUseCase in a full implementation
        raise HTTPException(status_code=501, detail="Query result deletion not yet implemented")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete query result: {str(e)}")


@router.get("/stats", response_model=dict)
async def get_query_stats():
    """Get query processing statistics."""
    try:
        return {
            "total_queries": 0,  # Would be populated from actual data
            "queries_today": 0,
            "avg_response_time_ms": 0.0,
            "success_rate": 0.0,
            "popular_intents": [],
            "system_load": "normal"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get query stats: {str(e)}")
