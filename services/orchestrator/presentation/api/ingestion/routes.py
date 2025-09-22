"""
API Routes for Document Ingestion.

Provides endpoints for:
- Starting document ingestion workflows
- Monitoring ingestion status
- Listing ingestion history
"""

import time
from typing import Optional

from fastapi import APIRouter, HTTPException

from services.shared.core.constants_new import ServiceNames
from services.shared.utilities.logging_client import get_log_collector_client

from ....main import container
from .dtos import DocumentMetadataResponse, IngestionListResponse, IngestionStatusResponse, IngestRequest

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


@router.post("/ingest", response_model=dict)
async def start_ingestion(request: IngestRequest):
    """Start a document ingestion workflow."""
    start_time = time.time()
    request_id = f"ingestion_start_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log ingestion workflow start
        if logger:
            await logger.log_business_event(
                "ingestion_workflow_started",
                {
                    "request_id": request_id,
                    "operation": "document_ingestion_workflow",
                    "source_url": request.source_url,
                    "source_type": request.source_type,
                    "parameters_count": len(request.parameters) if request.parameters else 0,
                    "ingestion_type": "document_processing_workflow",
                    "workflow_initiation": True,
                },
            )

            await logger.log_info(
                "Starting document ingestion workflow",
                {
                    "request_id": request_id,
                    "source_url": request.source_url,
                    "source_type": request.source_type,
                    "parameters_provided": bool(request.parameters),
                    "workflow_type": "document_ingestion",
                    "processing_pipeline": True,
                },
            )

        from ....application.ingestion.commands import StartIngestionCommand

        command = StartIngestionCommand(
            source_url=request.source_url, source_type=request.source_type, parameters=request.parameters or {}
        )
        result = await container.start_ingestion_use_case.execute(command)

        ingestion_id = result.get("ingestion_id") or result.get("id")
        response_time = time.time() - start_time

        # Log successful ingestion workflow start
        if logger:
            await logger.log_business_event(
                "ingestion_workflow_created",
                {
                    "request_id": request_id,
                    "ingestion_id": ingestion_id,
                    "operation": "document_ingestion_workflow",
                    "response_time_seconds": response_time,
                    "success": True,
                    "source_url": request.source_url,
                    "source_type": request.source_type,
                    "workflow_status": "initialized",
                    "processing_queue": True,
                },
            )

            await logger.log_performance_metric(
                "ingestion_workflow_creation",
                response_time,
                {
                    "request_id": request_id,
                    "ingestion_id": ingestion_id,
                    "creation_success": True,
                    "source_type": request.source_type,
                },
            )

        return result

    except Exception as e:
        error_time = time.time() - start_time

        # Log ingestion workflow creation failure
        if logger:
            await logger.log_error(
                f"Ingestion workflow creation failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "document_ingestion_workflow",
                    "source_url": request.source_url,
                    "source_type": request.source_type,
                    "parameters_count": len(request.parameters) if request.parameters else 0,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "ingestion_workflow_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "ingestion_workflow_creation_failed",
                {
                    "request_id": request_id,
                    "operation": "document_ingestion_workflow",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "source_url": request.source_url,
                    "source_type": request.source_type,
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to start ingestion: {str(e)}")


@router.get("/ingest/{ingestion_id}", response_model=IngestionStatusResponse)
async def get_ingestion_status(ingestion_id: str):
    """Get the status of a specific ingestion."""
    start_time = time.time()
    request_id = f"ingestion_status_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log ingestion status retrieval start
        if logger:
            await logger.log_business_event(
                "ingestion_status_retrieval_started",
                {
                    "request_id": request_id,
                    "ingestion_id": ingestion_id,
                    "operation": "ingestion_workflow_monitoring",
                    "query_type": "workflow_status",
                    "data_scope": "single_ingestion",
                    "monitoring_type": "workflow_progress",
                },
            )

            await logger.log_info(
                "Retrieving ingestion workflow status",
                {
                    "request_id": request_id,
                    "ingestion_id": ingestion_id,
                    "query_operation": "ingestion_status_lookup",
                    "includes_processing_details": True,
                    "progress_tracking": True,
                },
            )

        from ....application.ingestion.queries import GetIngestionStatusQuery

        query = GetIngestionStatusQuery(ingestion_id=ingestion_id)
        result = await container.get_ingestion_status_use_case.execute(query)

        if not result:
            response_time = time.time() - start_time

            # Log ingestion not found
            if logger:
                await logger.log_business_event(
                    "ingestion_not_found",
                    {
                        "request_id": request_id,
                        "ingestion_id": ingestion_id,
                        "operation": "ingestion_workflow_monitoring",
                        "response_time_seconds": response_time,
                        "query_result": "not_found",
                        "workflow_lookup_failed": True,
                    },
                )

            raise HTTPException(status_code=404, detail="Ingestion not found")

        response_time = time.time() - start_time

        # Log successful ingestion status retrieval
        if logger:
            await logger.log_business_event(
                "ingestion_status_retrieved",
                {
                    "request_id": request_id,
                    "ingestion_id": ingestion_id,
                    "operation": "ingestion_workflow_monitoring",
                    "response_time_seconds": response_time,
                    "success": True,
                    "workflow_status": result.get("status", "unknown"),
                    "progress_percentage": result.get("progress", 0),
                    "documents_processed": result.get("processed_count", 0),
                    "total_documents": result.get("total_count", 0),
                },
            )

            await logger.log_performance_metric(
                "ingestion_status_retrieval",
                response_time,
                {
                    "request_id": request_id,
                    "ingestion_id": ingestion_id,
                    "retrieval_success": True,
                    "data_returned": bool(result),
                },
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        error_time = time.time() - start_time

        # Log ingestion status retrieval failure
        if logger:
            await logger.log_error(
                f"Ingestion status retrieval failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "ingestion_workflow_monitoring",
                    "ingestion_id": ingestion_id,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "ingestion_status_retrieval_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "ingestion_status_retrieval_failed",
                {
                    "request_id": request_id,
                    "operation": "ingestion_workflow_monitoring",
                    "ingestion_id": ingestion_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to get ingestion status: {str(e)}")


@router.get("/ingest", response_model=IngestionListResponse)
async def list_ingestions(
    status: Optional[str] = None, source_type: Optional[str] = None, limit: int = 50, offset: int = 0
):
    """List ingestion workflows with optional filters."""
    start_time = time.time()
    request_id = f"ingestions_list_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log ingestion listing start
        if logger:
            filters_applied = bool(status or source_type)
            await logger.log_business_event(
                "ingestion_listing_started",
                {
                    "request_id": request_id,
                    "operation": "ingestion_workflow_inventory",
                    "query_type": "workflow_list",
                    "pagination_enabled": True,
                    "filters_applied": filters_applied,
                    "status_filter": status,
                    "source_type_filter": source_type,
                    "limit": limit,
                    "offset": offset,
                },
            )

            await logger.log_info(
                "Listing ingestion workflows",
                {
                    "request_id": request_id,
                    "pagination_limit": limit,
                    "pagination_offset": offset,
                    "filters_active": filters_applied,
                    "query_scope": "filtered_ingestions" if filters_applied else "all_ingestions",
                },
            )

        from ....application.ingestion.queries import ListIngestionsQuery

        query = ListIngestionsQuery(status_filter=status, source_type_filter=source_type, limit=limit, offset=offset)
        result = await container.list_ingestions_use_case.execute(query)

        response_time = time.time() - start_time
        ingestions_returned = len(result.get("ingestions", [])) if result and hasattr(result, "get") else 0

        # Log successful ingestion listing
        if logger:
            await logger.log_business_event(
                "ingestion_listing_completed",
                {
                    "request_id": request_id,
                    "operation": "ingestion_workflow_inventory",
                    "response_time_seconds": response_time,
                    "success": True,
                    "ingestions_returned": ingestions_returned,
                    "filters_applied": filters_applied,
                    "limit": limit,
                    "offset": offset,
                    "total_available": result.total if result and hasattr(result, "total") else 0,
                },
            )

            await logger.log_performance_metric(
                "ingestion_listing",
                response_time,
                {
                    "request_id": request_id,
                    "ingestions_returned": ingestions_returned,
                    "filters_used": filters_applied,
                    "listing_success": True,
                },
            )

        return result

    except Exception as e:
        error_time = time.time() - start_time

        # Log ingestion listing failure
        if logger:
            await logger.log_error(
                f"Ingestion listing failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "ingestion_workflow_inventory",
                    "status_filter": status,
                    "source_type_filter": source_type,
                    "limit": limit,
                    "offset": offset,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "ingestion_listing_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "ingestion_listing_failed",
                {
                    "request_id": request_id,
                    "operation": "ingestion_workflow_inventory",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to list ingestions: {str(e)}")


@router.get("/documents/{document_id}", response_model=DocumentMetadataResponse)
async def get_document_metadata(document_id: str):
    """Get metadata for a specific ingested document."""
    start_time = time.time()
    request_id = f"document_metadata_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log document metadata retrieval start
        if logger:
            await logger.log_business_event(
                "document_metadata_retrieval_started",
                {
                    "request_id": request_id,
                    "document_id": document_id,
                    "operation": "ingested_document_metadata",
                    "query_type": "document_metadata",
                    "data_scope": "single_document",
                    "ingestion_result_query": True,
                },
            )

            await logger.log_info(
                "Retrieving document metadata from ingestion results",
                {
                    "request_id": request_id,
                    "document_id": document_id,
                    "query_operation": "document_metadata_lookup",
                    "includes_ingestion_context": True,
                    "metadata_comprehensive": True,
                },
            )

        # This would typically use a dedicated query, but for now we'll use placeholder
        # In a full implementation, this would query the document store
        response_time = time.time() - start_time

        # Log document metadata retrieval (placeholder implementation)
        if logger:
            await logger.log_business_event(
                "document_metadata_not_implemented",
                {
                    "request_id": request_id,
                    "document_id": document_id,
                    "operation": "ingested_document_metadata",
                    "response_time_seconds": response_time,
                    "implementation_status": "placeholder",
                    "feature_planned": True,
                },
            )

        raise HTTPException(status_code=501, detail="Document metadata retrieval not yet implemented")

    except HTTPException:
        raise
    except Exception as e:
        error_time = time.time() - start_time

        # Log document metadata retrieval failure
        if logger:
            await logger.log_error(
                f"Document metadata retrieval failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "ingested_document_metadata",
                    "document_id": document_id,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "document_metadata_retrieval_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "document_metadata_retrieval_failed",
                {
                    "request_id": request_id,
                    "operation": "ingested_document_metadata",
                    "document_id": document_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to get document metadata: {str(e)}")


@router.get("/sources", response_model=dict)
async def list_ingestion_sources():
    """List available ingestion sources and their capabilities."""
    start_time = time.time()
    request_id = f"ingestion_sources_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log ingestion sources listing start
        if logger:
            await logger.log_business_event(
                "ingestion_sources_listing_started",
                {
                    "request_id": request_id,
                    "operation": "ingestion_capability_discovery",
                    "query_type": "available_sources",
                    "data_scope": "system_capabilities",
                    "source_inventory": True,
                },
            )

            await logger.log_info(
                "Listing available ingestion sources and capabilities",
                {
                    "request_id": request_id,
                    "query_operation": "source_capability_inventory",
                    "includes_format_support": True,
                    "system_integration_query": True,
                },
            )

        # This would typically query available ingestion adapters/capabilities
        sources = [
            {
                "type": "github",
                "name": "GitHub Repository",
                "description": "Ingest code, issues, and pull requests from GitHub",
                "supported_formats": ["markdown", "code", "issues", "pull_requests"],
            },
            {
                "type": "gitlab",
                "name": "GitLab Repository",
                "description": "Ingest code, issues, and merge requests from GitLab",
                "supported_formats": ["markdown", "code", "issues", "merge_requests"],
            },
            {
                "type": "jira",
                "name": "Jira Issues",
                "description": "Ingest issues and project data from Jira",
                "supported_formats": ["issues", "projects", "epics"],
            },
            {
                "type": "confluence",
                "name": "Confluence Pages",
                "description": "Ingest documentation and knowledge base from Confluence",
                "supported_formats": ["pages", "blogs", "spaces"],
            },
        ]

        response_time = time.time() - start_time

        # Log successful ingestion sources listing
        if logger:
            await logger.log_business_event(
                "ingestion_sources_listed",
                {
                    "request_id": request_id,
                    "operation": "ingestion_capability_discovery",
                    "response_time_seconds": response_time,
                    "success": True,
                    "sources_returned": len(sources),
                    "source_types": len(set(s.get("type") for s in sources)),
                    "total_supported_formats": sum(len(s.get("supported_formats", [])) for s in sources),
                    "capability_inventory_complete": True,
                },
            )

            await logger.log_performance_metric(
                "ingestion_sources_listing",
                response_time,
                {
                    "request_id": request_id,
                    "sources_returned": len(sources),
                    "listing_success": True,
                    "system_capability_query": True,
                },
            )

        return {"sources": sources}

    except Exception as e:
        error_time = time.time() - start_time

        # Log ingestion sources listing failure
        if logger:
            await logger.log_error(
                f"Ingestion sources listing failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "ingestion_capability_discovery",
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "ingestion_sources_listing_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "ingestion_sources_listing_failed",
                {
                    "request_id": request_id,
                    "operation": "ingestion_capability_discovery",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to list ingestion sources: {str(e)}")


@router.delete("/ingest/{ingestion_id}", response_model=dict)
async def cancel_ingestion(ingestion_id: str):
    """Cancel a running ingestion workflow."""
    start_time = time.time()
    request_id = f"ingestion_cancel_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log ingestion cancellation start
        if logger:
            await logger.log_business_event(
                "ingestion_cancellation_started",
                {
                    "request_id": request_id,
                    "ingestion_id": ingestion_id,
                    "operation": "ingestion_workflow_control",
                    "control_type": "workflow_cancellation",
                    "workflow_management": True,
                    "graceful_shutdown": True,
                },
            )

            await logger.log_info(
                "Initiating ingestion workflow cancellation",
                {
                    "request_id": request_id,
                    "ingestion_id": ingestion_id,
                    "control_operation": "workflow_cancellation",
                    "implementation_status": "placeholder",
                    "graceful_termination": True,
                },
            )

        # This would use a CancelIngestionUseCase in a full implementation
        response_time = time.time() - start_time

        # Log ingestion cancellation (placeholder implementation)
        if logger:
            await logger.log_business_event(
                "ingestion_cancellation_not_implemented",
                {
                    "request_id": request_id,
                    "ingestion_id": ingestion_id,
                    "operation": "ingestion_workflow_control",
                    "response_time_seconds": response_time,
                    "implementation_status": "placeholder",
                    "feature_planned": True,
                },
            )

        raise HTTPException(status_code=501, detail="Ingestion cancellation not yet implemented")

    except HTTPException:
        raise
    except Exception as e:
        error_time = time.time() - start_time

        # Log ingestion cancellation failure
        if logger:
            await logger.log_error(
                f"Ingestion cancellation failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "ingestion_workflow_control",
                    "ingestion_id": ingestion_id,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "ingestion_cancellation_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "ingestion_cancellation_failed",
                {
                    "request_id": request_id,
                    "operation": "ingestion_workflow_control",
                    "ingestion_id": ingestion_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to cancel ingestion: {str(e)}")
