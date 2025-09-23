"""
API Routes for Query Processing.

Provides endpoints for:
- Natural language query processing
- Structured query execution
- Query result retrieval
- Query history management
"""

import time
from typing import Optional

from fastapi import APIRouter, HTTPException

from services.shared.core.constants_new import ServiceNames
from services.shared.utilities.logging_client import get_log_collector_client

from ....main import container
from .dtos import (
    ProcessQueryRequest,
    QueryHistoryResponse,
    QueryListResponse,
    QueryResultResponse,
    StructuredQueryRequest,
)

# Global logger client instance
logger_client = None


async def get_logger_client():
    """Get or initialize the logger client."""
    global logger_client
    if logger_client is None:
        try:
            logger_client = await get_log_collector_client(ServiceNames.ORCHESTRATOR)
        except Exception:
            pass  # Fallback to no logging if client unavailable
    return logger_client


router = APIRouter()


@router.post("/process", response_model=QueryResultResponse)
async def process_natural_language_query(request: ProcessQueryRequest):
    """Process a natural language query and return results."""
    start_time = time.time()
    request_id = f"nl_query_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log natural language query processing start
        if logger:
            await logger.log_business_event(
                "natural_language_query_started",
                {
                    "request_id": request_id,
                    "operation": "natural_language_query_processing",
                    "query_type": "natural_language",
                    "query_length": len(request.query_text) if request.query_text else 0,
                    "max_results_requested": request.max_results,
                    "explanation_requested": request.include_explanation,
                    "context_provided": bool(request.context),
                    "processing_mode": "ai_powered_query_processing",
                },
            )

            await logger.log_info(
                "Processing natural language query",
                {
                    "request_id": request_id,
                    "query_preview": (
                        request.query_text[:100] + "..." if len(request.query_text or "") > 100 else request.query_text
                    ),
                    "max_results": request.max_results,
                    "include_explanation": request.include_explanation,
                    "context_available": bool(request.context),
                    "query_processing_engine": "ai_driven",
                },
            )

        from ....application.query_processing.commands import ProcessNaturalLanguageQueryCommand

        command = ProcessNaturalLanguageQueryCommand(
            query_text=request.query_text,
            context=request.context,
            max_results=request.max_results,
            include_explanation=request.include_explanation,
        )
        result = await container.process_natural_language_query_use_case.execute(command)

        response_time = time.time() - start_time
        results_count = len(result.get("results", [])) if result and hasattr(result, "get") else 0

        # Log successful natural language query processing
        if logger:
            await logger.log_business_event(
                "natural_language_query_completed",
                {
                    "request_id": request_id,
                    "operation": "natural_language_query_processing",
                    "response_time_seconds": response_time,
                    "success": True,
                    "results_returned": results_count,
                    "max_results_requested": request.max_results,
                    "explanation_included": request.include_explanation,
                    "query_complexity": "natural_language_ai_processed",
                },
            )

            await logger.log_performance_metric(
                "natural_language_query_processing",
                response_time,
                {
                    "request_id": request_id,
                    "query_length": len(request.query_text) if request.query_text else 0,
                    "results_returned": results_count,
                    "processing_success": True,
                    "ai_query_processing_time": response_time,
                },
            )

        return result

    except Exception as e:
        error_time = time.time() - start_time

        # Log natural language query processing failure
        if logger:
            await logger.log_error(
                f"Natural language query processing failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "natural_language_query_processing",
                    "query_length": len(request.query_text) if request.query_text else 0,
                    "max_results_requested": request.max_results,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "natural_language_query_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "natural_language_query_failed",
                {
                    "request_id": request_id,
                    "operation": "natural_language_query_processing",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "query_length": len(request.query_text) if request.query_text else 0,
                    "max_results_requested": request.max_results,
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to process query: {str(e)}")


@router.post("/structured", response_model=QueryResultResponse)
async def execute_structured_query(request: StructuredQueryRequest):
    """Execute a structured query with specific parameters."""
    start_time = time.time()
    request_id = f"structured_query_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log structured query execution start
        if logger:
            await logger.log_business_event(
                "structured_query_started",
                {
                    "request_id": request_id,
                    "operation": "structured_query_execution",
                    "query_type": request.query_type,
                    "parameters_count": len(request.parameters) if request.parameters else 0,
                    "filters_applied": bool(request.filters),
                    "sorting_enabled": bool(request.sorting),
                    "pagination_used": bool(request.pagination),
                    "processing_mode": "parameterized_query_execution",
                },
            )

            await logger.log_info(
                "Executing structured query",
                {
                    "request_id": request_id,
                    "query_type": request.query_type,
                    "parameters_provided": bool(request.parameters),
                    "filters_active": bool(request.filters),
                    "sorting_configured": bool(request.sorting),
                    "pagination_enabled": bool(request.pagination),
                },
            )

        from ....application.query_processing.commands import ExecuteStructuredQueryCommand

        command = ExecuteStructuredQueryCommand(
            query_type=request.query_type,
            parameters=request.parameters,
            filters=request.filters,
            sorting=request.sorting,
            pagination=request.pagination,
        )
        result = await container.process_natural_language_query_use_case.execute(command)

        response_time = time.time() - start_time
        results_count = len(result.get("results", [])) if result and hasattr(result, "get") else 0

        # Log successful structured query execution
        if logger:
            await logger.log_business_event(
                "structured_query_completed",
                {
                    "request_id": request_id,
                    "operation": "structured_query_execution",
                    "response_time_seconds": response_time,
                    "success": True,
                    "query_type": request.query_type,
                    "results_returned": results_count,
                    "filters_applied": bool(request.filters),
                    "sorting_used": bool(request.sorting),
                    "pagination_applied": bool(request.pagination),
                },
            )

            await logger.log_performance_metric(
                "structured_query_execution",
                response_time,
                {
                    "request_id": request_id,
                    "query_type": request.query_type,
                    "results_returned": results_count,
                    "execution_success": True,
                    "structured_query_processing_time": response_time,
                },
            )

        return result

    except Exception as e:
        error_time = time.time() - start_time

        # Log structured query execution failure
        if logger:
            await logger.log_error(
                f"Structured query execution failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "structured_query_execution",
                    "query_type": request.query_type,
                    "parameters_count": len(request.parameters) if request.parameters else 0,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "structured_query_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "structured_query_failed",
                {
                    "request_id": request_id,
                    "operation": "structured_query_execution",
                    "query_type": request.query_type,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "parameters_count": len(request.parameters) if request.parameters else 0,
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to execute structured query: {str(e)}")


@router.get("/results/{query_id}", response_model=QueryResultResponse)
async def get_query_result(query_id: str):
    """Get the result of a previously executed query."""
    start_time = time.time()
    request_id = f"query_result_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log query result retrieval start
        if logger:
            await logger.log_business_event(
                "query_result_retrieval_started",
                {
                    "request_id": request_id,
                    "query_id": query_id,
                    "operation": "query_result_access",
                    "data_scope": "stored_query_result",
                    "result_cache_access": True,
                },
            )

            await logger.log_info(
                "Retrieving stored query result",
                {
                    "request_id": request_id,
                    "query_id": query_id,
                    "result_access_mode": "cached_result_retrieval",
                    "query_result_persistence": True,
                },
            )

        from ....application.query_processing.queries import GetQueryResultQuery

        query = GetQueryResultQuery(query_id=query_id)
        result = await container.get_query_result_use_case.execute(query)

        if not result:
            response_time = time.time() - start_time

            # Log query result not found
            if logger:
                await logger.log_business_event(
                    "query_result_not_found",
                    {
                        "request_id": request_id,
                        "query_id": query_id,
                        "operation": "query_result_access",
                        "response_time_seconds": response_time,
                        "result_status": "not_found",
                        "cache_miss": True,
                    },
                )

            raise HTTPException(status_code=404, detail="Query result not found")

        response_time = time.time() - start_time

        # Log successful query result retrieval
        if logger:
            await logger.log_business_event(
                "query_result_retrieved",
                {
                    "request_id": request_id,
                    "query_id": query_id,
                    "operation": "query_result_access",
                    "response_time_seconds": response_time,
                    "success": True,
                    "result_size": len(str(result)) if result else 0,
                    "cache_hit": True,
                    "result_format": "structured_response",
                },
            )

            await logger.log_performance_metric(
                "query_result_retrieval",
                response_time,
                {
                    "request_id": request_id,
                    "query_id": query_id,
                    "retrieval_success": True,
                    "cache_access_time": response_time,
                },
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        error_time = time.time() - start_time

        # Log query result retrieval failure
        if logger:
            await logger.log_error(
                f"Query result retrieval failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "query_result_access",
                    "query_id": query_id,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "query_result_retrieval_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "query_result_retrieval_failed",
                {
                    "request_id": request_id,
                    "operation": "query_result_access",
                    "query_id": query_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to get query result: {str(e)}")


@router.get("/history", response_model=QueryListResponse)
async def list_query_history(
    intent: Optional[str] = None, status: Optional[str] = None, page: int = 1, page_size: int = 20
):
    """List query execution history with optional filters."""
    start_time = time.time()
    request_id = f"query_history_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log query history listing start
        if logger:
            filters_applied = bool(intent or status)
            await logger.log_business_event(
                "query_history_listing_started",
                {
                    "request_id": request_id,
                    "operation": "query_execution_history",
                    "query_type": "historical_queries",
                    "pagination_enabled": True,
                    "filters_applied": filters_applied,
                    "intent_filter": intent,
                    "status_filter": status,
                    "page": page,
                    "page_size": page_size,
                },
            )

            await logger.log_info(
                "Listing query execution history",
                {
                    "request_id": request_id,
                    "pagination_page": page,
                    "pagination_size": page_size,
                    "filters_active": filters_applied,
                    "history_scope": "filtered_queries" if filters_applied else "all_queries",
                },
            )

        from ....application.query_processing.queries import ListQueriesQuery

        query = ListQueriesQuery(intent_filter=intent, status_filter=status, page=page, page_size=page_size)
        result = await container.list_queries_use_case.execute(query)

        response_time = time.time() - start_time
        queries_returned = len(result.get("queries", [])) if result and hasattr(result, "get") else 0

        # Log successful query history listing
        if logger:
            await logger.log_business_event(
                "query_history_listed",
                {
                    "request_id": request_id,
                    "operation": "query_execution_history",
                    "response_time_seconds": response_time,
                    "success": True,
                    "queries_returned": queries_returned,
                    "filters_applied": filters_applied,
                    "page": page,
                    "page_size": page_size,
                    "total_available": result.total if result and hasattr(result, "total") else 0,
                },
            )

            await logger.log_performance_metric(
                "query_history_listing",
                response_time,
                {
                    "request_id": request_id,
                    "queries_returned": queries_returned,
                    "filters_used": filters_applied,
                    "history_listing_success": True,
                },
            )

        return result

    except Exception as e:
        error_time = time.time() - start_time

        # Log query history listing failure
        if logger:
            await logger.log_error(
                f"Query history listing failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "query_execution_history",
                    "intent_filter": intent,
                    "status_filter": status,
                    "page": page,
                    "page_size": page_size,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "query_history_listing_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "query_history_listing_failed",
                {
                    "request_id": request_id,
                    "operation": "query_execution_history",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to list query history: {str(e)}")


@router.get("/history/{query_id}", response_model=QueryHistoryResponse)
async def get_query_history(query_id: str):
    """Get detailed history for a specific query."""
    start_time = time.time()
    request_id = f"query_history_detail_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log query history detail retrieval start
        if logger:
            await logger.log_business_event(
                "query_history_detail_started",
                {
                    "request_id": request_id,
                    "query_id": query_id,
                    "operation": "detailed_query_history",
                    "history_type": "individual_query_timeline",
                    "data_scope": "comprehensive_query_lifecycle",
                },
            )

            await logger.log_info(
                "Retrieving detailed query history",
                {
                    "request_id": request_id,
                    "query_id": query_id,
                    "history_depth": "full_lifecycle",
                    "includes_execution_details": True,
                    "includes_performance_metrics": True,
                },
            )

        from ....application.query_processing.queries import GetQueryHistoryQuery

        query = GetQueryHistoryQuery(query_id=query_id)
        result = await container.list_queries_use_case.execute(query)

        if not result:
            response_time = time.time() - start_time

            # Log query history not found
            if logger:
                await logger.log_business_event(
                    "query_history_not_found",
                    {
                        "request_id": request_id,
                        "query_id": query_id,
                        "operation": "detailed_query_history",
                        "response_time_seconds": response_time,
                        "history_status": "not_found",
                        "query_lifecycle_missing": True,
                    },
                )

            raise HTTPException(status_code=404, detail="Query history not found")

        response_time = time.time() - start_time

        # Log successful query history detail retrieval
        if logger:
            await logger.log_business_event(
                "query_history_detail_retrieved",
                {
                    "request_id": request_id,
                    "query_id": query_id,
                    "operation": "detailed_query_history",
                    "response_time_seconds": response_time,
                    "success": True,
                    "history_completeness": "full_lifecycle",
                    "execution_events_count": len(result.get("execution_events", [])) if result else 0,
                    "performance_data_included": True,
                },
            )

            await logger.log_performance_metric(
                "query_history_detail_retrieval",
                response_time,
                {
                    "request_id": request_id,
                    "query_id": query_id,
                    "retrieval_success": True,
                    "history_detail_access_time": response_time,
                },
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        error_time = time.time() - start_time

        # Log query history detail retrieval failure
        if logger:
            await logger.log_error(
                f"Query history detail retrieval failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "detailed_query_history",
                    "query_id": query_id,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "query_history_detail_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "query_history_detail_failed",
                {
                    "request_id": request_id,
                    "operation": "detailed_query_history",
                    "query_id": query_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to get query history: {str(e)}")


@router.get("/intents", response_model=dict)
async def list_query_intents():
    """List available query intents that can be processed."""
    start_time = time.time()
    request_id = f"query_intents_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log query intents listing start
        if logger:
            await logger.log_business_event(
                "query_intents_listing_started",
                {
                    "request_id": request_id,
                    "operation": "query_capability_discovery",
                    "query_type": "available_intents",
                    "data_scope": "system_capabilities",
                    "intent_inventory": True,
                },
            )

            await logger.log_info(
                "Listing available query intents and capabilities",
                {
                    "request_id": request_id,
                    "query_operation": "intent_capability_inventory",
                    "includes_examples": True,
                    "system_integration_query": True,
                },
            )

        # Return available query intents
        intents = [
            {
                "name": "search",
                "description": "Search for documents or content",
                "example_queries": ["find documents about AI", "search for error logs"],
            },
            {
                "name": "analytics",
                "description": "Generate analytics and insights",
                "example_queries": ["analyze code quality", "show usage statistics"],
            },
            {
                "name": "summarize",
                "description": "Create summaries of content",
                "example_queries": ["summarize this document", "overview of recent changes"],
            },
            {
                "name": "explain",
                "description": "Explain code, concepts, or processes",
                "example_queries": ["explain this function", "what does this code do"],
            },
            {
                "name": "compare",
                "description": "Compare different items or versions",
                "example_queries": ["compare these two approaches", "differences between versions"],
            },
        ]

        response_time = time.time() - start_time

        # Log successful query intents listing
        if logger:
            await logger.log_business_event(
                "query_intents_listed",
                {
                    "request_id": request_id,
                    "operation": "query_capability_discovery",
                    "response_time_seconds": response_time,
                    "success": True,
                    "intents_returned": len(intents),
                    "intent_categories": len(set(intent["name"] for intent in intents)),
                    "total_examples": sum(len(intent.get("example_queries", [])) for intent in intents),
                    "capability_inventory_complete": True,
                },
            )

            await logger.log_performance_metric(
                "query_intents_listing",
                response_time,
                {
                    "request_id": request_id,
                    "intents_returned": len(intents),
                    "listing_success": True,
                    "system_capability_query": True,
                },
            )

        return {"intents": intents, "total_intents": len(intents)}

    except Exception as e:
        error_time = time.time() - start_time

        # Log query intents listing failure
        if logger:
            await logger.log_error(
                f"Query intents listing failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "query_capability_discovery",
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "query_intents_listing_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "query_intents_listing_failed",
                {
                    "request_id": request_id,
                    "operation": "query_capability_discovery",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to list query intents: {str(e)}")


@router.delete("/results/{query_id}", response_model=dict)
async def delete_query_result(query_id: str):
    """Delete a query result from history."""
    start_time = time.time()
    request_id = f"query_result_delete_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log query result deletion start
        if logger:
            await logger.log_business_event(
                "query_result_deletion_started",
                {
                    "request_id": request_id,
                    "query_id": query_id,
                    "operation": "query_result_management",
                    "control_type": "result_cleanup",
                    "data_management": True,
                    "privacy_compliance": True,
                },
            )

            await logger.log_info(
                "Initiating query result deletion",
                {
                    "request_id": request_id,
                    "query_id": query_id,
                    "control_operation": "result_deletion",
                    "implementation_status": "placeholder",
                    "data_cleanup_required": True,
                },
            )

        # This would use a DeleteQueryResultUseCase in a full implementation
        response_time = time.time() - start_time

        # Log query result deletion (placeholder implementation)
        if logger:
            await logger.log_business_event(
                "query_result_deletion_not_implemented",
                {
                    "request_id": request_id,
                    "query_id": query_id,
                    "operation": "query_result_management",
                    "response_time_seconds": response_time,
                    "implementation_status": "placeholder",
                    "feature_planned": True,
                },
            )

        raise HTTPException(status_code=501, detail="Query result deletion not yet implemented")

    except HTTPException:
        raise
    except Exception as e:
        error_time = time.time() - start_time

        # Log query result deletion failure
        if logger:
            await logger.log_error(
                f"Query result deletion failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "query_result_management",
                    "query_id": query_id,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "query_result_deletion_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "query_result_deletion_failed",
                {
                    "request_id": request_id,
                    "operation": "query_result_management",
                    "query_id": query_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to delete query result: {str(e)}")


@router.get("/stats", response_model=dict)
async def get_query_stats():
    """Get query processing statistics."""
    start_time = time.time()
    request_id = f"query_stats_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log query stats retrieval start
        if logger:
            await logger.log_business_event(
                "query_stats_retrieval_started",
                {
                    "request_id": request_id,
                    "operation": "query_system_monitoring",
                    "query_type": "processing_statistics",
                    "data_scope": "system_metrics",
                    "performance_analytics": True,
                },
            )

            await logger.log_info(
                "Retrieving query processing statistics",
                {
                    "request_id": request_id,
                    "stats_type": "comprehensive_query_metrics",
                    "includes_performance_data": True,
                    "includes_usage_analytics": True,
                },
            )

        # Return query processing statistics (placeholder data)
        stats = {
            "total_queries": 0,  # Would be populated from actual data
            "queries_today": 0,
            "avg_response_time_ms": 0.0,
            "success_rate": 0.0,
            "popular_intents": [],
            "system_load": "normal",
        }

        response_time = time.time() - start_time

        # Log successful query stats retrieval
        if logger:
            await logger.log_business_event(
                "query_stats_retrieved",
                {
                    "request_id": request_id,
                    "operation": "query_system_monitoring",
                    "response_time_seconds": response_time,
                    "success": True,
                    "stats_completeness": "placeholder_data",
                    "metrics_available": len(stats),
                    "performance_data_included": True,
                    "system_health_indicators": True,
                },
            )

            await logger.log_performance_metric(
                "query_stats_retrieval",
                response_time,
                {
                    "request_id": request_id,
                    "stats_retrieval_success": True,
                    "metrics_returned": len(stats),
                    "system_monitoring_query": True,
                },
            )

        return stats

    except Exception as e:
        error_time = time.time() - start_time

        # Log query stats retrieval failure
        if logger:
            await logger.log_error(
                f"Query stats retrieval failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "query_system_monitoring",
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "query_stats_retrieval_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "query_stats_retrieval_failed",
                {
                    "request_id": request_id,
                    "operation": "query_system_monitoring",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to get query stats: {str(e)}")
