"""
API Routes for Reporting.

Provides endpoints for:
- Report generation and management
- Report template management
- Report retrieval and download
"""

import time
from typing import Optional

from fastapi import APIRouter, HTTPException

from services.shared.core.constants_new import ServiceNames
from services.shared.utilities.logging_client import get_log_collector_client

from ....main import container
from .dtos import (
    GenerateReportRequest,
    ReportListResponse,
    ReportResponse,
    ReportTemplateResponse,
    ReportTemplatesListResponse,
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


@router.post("/generate", response_model=ReportResponse)
async def generate_report(request: GenerateReportRequest):
    """Generate a new report."""
    start_time = time.time()
    request_id = f"report_generation_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log report generation start
        if logger:
            await logger.log_business_event(
                "report_generation_started",
                {
                    "request_id": request_id,
                    "operation": "report_generation_workflow",
                    "report_type": request.report_type,
                    "parameters_count": len(request.parameters) if request.parameters else 0,
                    "filters_applied": bool(request.filters),
                    "date_range_specified": bool(request.date_range),
                    "output_format": request.format,
                    "charts_included": request.include_charts,
                    "data_aggregation_required": True,
                },
            )

            await logger.log_info(
                "Initiating report generation workflow",
                {
                    "request_id": request_id,
                    "report_type": request.report_type,
                    "output_format": request.format,
                    "visualization_enabled": request.include_charts,
                    "date_range_filter": bool(request.date_range),
                    "parameters_provided": bool(request.parameters),
                    "analytics_engine_activated": True,
                },
            )

        from ....application.reporting.commands import GenerateReportCommand

        command = GenerateReportCommand(
            report_type=request.report_type,
            parameters=request.parameters,
            filters=request.filters,
            date_range=request.date_range,
            format=request.format,
            include_charts=request.include_charts,
        )
        result = await container.generate_report_use_case.execute(command)

        response_time = time.time() - start_time
        report_id = result.get("report_id") or result.get("id")
        report_size = len(str(result)) if result else 0

        # Log successful report generation
        if logger:
            await logger.log_business_event(
                "report_generation_completed",
                {
                    "request_id": request_id,
                    "report_id": report_id,
                    "operation": "report_generation_workflow",
                    "response_time_seconds": response_time,
                    "success": True,
                    "report_type": request.report_type,
                    "output_format": request.format,
                    "charts_generated": request.include_charts,
                    "data_aggregation_completed": True,
                    "report_size_bytes": report_size,
                },
            )

            await logger.log_performance_metric(
                "report_generation",
                response_time,
                {
                    "request_id": request_id,
                    "report_id": report_id,
                    "report_type": request.report_type,
                    "generation_success": True,
                    "output_format": request.format,
                    "analytics_processing_time": response_time,
                },
            )

        return result

    except Exception as e:
        error_time = time.time() - start_time

        # Log report generation failure
        if logger:
            await logger.log_error(
                f"Report generation failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "report_generation_workflow",
                    "report_type": request.report_type,
                    "parameters_count": len(request.parameters) if request.parameters else 0,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "output_format": request.format,
                    "report_generation_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "report_generation_failed",
                {
                    "request_id": request_id,
                    "operation": "report_generation_workflow",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "report_type": request.report_type,
                    "output_format": request.format,
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to generate report: {str(e)}")


@router.get("/reports/{report_id}", response_model=ReportResponse)
async def get_report(report_id: str):
    """Get a specific report by ID."""
    start_time = time.time()
    request_id = f"report_retrieval_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log report retrieval start
        if logger:
            await logger.log_business_event(
                "report_retrieval_started",
                {
                    "request_id": request_id,
                    "report_id": report_id,
                    "operation": "report_access_management",
                    "data_scope": "stored_report",
                    "report_cache_access": True,
                },
            )

            await logger.log_info(
                "Retrieving stored report",
                {
                    "request_id": request_id,
                    "report_id": report_id,
                    "access_mode": "cached_report_retrieval",
                    "report_persistence": True,
                },
            )

        from ....application.reporting.queries import GetReportQuery

        query = GetReportQuery(report_id=report_id)
        result = await container.get_report_use_case.execute(query)

        if not result:
            response_time = time.time() - start_time

            # Log report not found
            if logger:
                await logger.log_business_event(
                    "report_not_found",
                    {
                        "request_id": request_id,
                        "report_id": report_id,
                        "operation": "report_access_management",
                        "response_time_seconds": response_time,
                        "result_status": "not_found",
                        "cache_miss": True,
                    },
                )

            raise HTTPException(status_code=404, detail="Report not found")

        response_time = time.time() - start_time
        report_size = len(str(result)) if result else 0

        # Log successful report retrieval
        if logger:
            await logger.log_business_event(
                "report_retrieved",
                {
                    "request_id": request_id,
                    "report_id": report_id,
                    "operation": "report_access_management",
                    "response_time_seconds": response_time,
                    "success": True,
                    "report_size_bytes": report_size,
                    "cache_hit": True,
                    "report_format": result.get("format", "unknown"),
                },
            )

            await logger.log_performance_metric(
                "report_retrieval",
                response_time,
                {
                    "request_id": request_id,
                    "report_id": report_id,
                    "retrieval_success": True,
                    "cache_access_time": response_time,
                },
            )

        return result

    except HTTPException:
        raise
    except Exception as e:
        error_time = time.time() - start_time

        # Log report retrieval failure
        if logger:
            await logger.log_error(
                f"Report retrieval failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "report_access_management",
                    "report_id": report_id,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "report_retrieval_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "report_retrieval_failed",
                {
                    "request_id": request_id,
                    "operation": "report_access_management",
                    "report_id": report_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to get report: {str(e)}")


@router.get("/reports", response_model=ReportListResponse)
async def list_reports(
    report_type: Optional[str] = None, status: Optional[str] = None, page: int = 1, page_size: int = 20
):
    """List reports with optional filters."""
    start_time = time.time()
    request_id = f"reports_listing_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log reports listing start
        if logger:
            filters_applied = bool(report_type or status)
            await logger.log_business_event(
                "reports_listing_started",
                {
                    "request_id": request_id,
                    "operation": "report_inventory_management",
                    "query_type": "report_list",
                    "pagination_enabled": True,
                    "filters_applied": filters_applied,
                    "report_type_filter": report_type,
                    "status_filter": status,
                    "page": page,
                    "page_size": page_size,
                },
            )

            await logger.log_info(
                "Listing reports with filtering",
                {
                    "request_id": request_id,
                    "pagination_page": page,
                    "pagination_size": page_size,
                    "filters_active": filters_applied,
                    "inventory_scope": "filtered_reports" if filters_applied else "all_reports",
                },
            )

        from ....application.reporting.queries import ListReportsQuery

        query = ListReportsQuery(report_type_filter=report_type, status_filter=status, page=page, page_size=page_size)
        result = await container.list_reports_use_case.execute(query)

        response_time = time.time() - start_time
        reports_returned = len(result.get("reports", [])) if result and hasattr(result, "get") else 0

        # Log successful reports listing
        if logger:
            await logger.log_business_event(
                "reports_listed",
                {
                    "request_id": request_id,
                    "operation": "report_inventory_management",
                    "response_time_seconds": response_time,
                    "success": True,
                    "reports_returned": reports_returned,
                    "filters_applied": filters_applied,
                    "page": page,
                    "page_size": page_size,
                    "total_available": result.total if result and hasattr(result, "total") else 0,
                },
            )

            await logger.log_performance_metric(
                "reports_listing",
                response_time,
                {
                    "request_id": request_id,
                    "reports_returned": reports_returned,
                    "filters_used": filters_applied,
                    "listing_success": True,
                },
            )

        return result

    except Exception as e:
        error_time = time.time() - start_time

        # Log reports listing failure
        if logger:
            await logger.log_error(
                f"Reports listing failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "report_inventory_management",
                    "report_type_filter": report_type,
                    "status_filter": status,
                    "page": page,
                    "page_size": page_size,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "reports_listing_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "reports_listing_failed",
                {
                    "request_id": request_id,
                    "operation": "report_inventory_management",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to list reports: {str(e)}")


@router.get("/templates", response_model=ReportTemplatesListResponse)
async def list_report_templates():
    """List available report templates."""
    start_time = time.time()
    request_id = f"templates_listing_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log report templates listing start
        if logger:
            await logger.log_business_event(
                "report_templates_listing_started",
                {
                    "request_id": request_id,
                    "operation": "report_template_management",
                    "query_type": "available_templates",
                    "data_scope": "template_inventory",
                    "template_repository_access": True,
                },
            )

            await logger.log_info(
                "Listing available report templates",
                {
                    "request_id": request_id,
                    "query_operation": "template_inventory_access",
                    "includes_parameter_schemas": True,
                    "system_template_repository": True,
                },
            )

        # Return available report templates
        templates = [
            {
                "template_id": "pr-confidence-template",
                "name": "PR Confidence Analysis",
                "description": "Analyze confidence scores for pull requests",
                "report_type": "pr_confidence",
                "parameters_schema": {
                    "repository": {"type": "string", "required": True},
                    "date_range": {"type": "object", "required": False},
                },
                "default_parameters": {"include_charts": True, "format": "pdf"},
                "created_at": "2024-01-01T00:00:00Z",
            },
            {
                "template_id": "summarization-template",
                "name": "Document Summarization Report",
                "description": "Generate summaries of ingested documents",
                "report_type": "summarization",
                "parameters_schema": {
                    "document_ids": {"type": "array", "required": True},
                    "summary_length": {"type": "string", "enum": ["short", "medium", "long"], "required": False},
                },
                "default_parameters": {"include_charts": False, "format": "json"},
                "created_at": "2024-01-01T00:00:00Z",
            },
        ]

        response_time = time.time() - start_time

        # Log successful report templates listing
        if logger:
            await logger.log_business_event(
                "report_templates_listed",
                {
                    "request_id": request_id,
                    "operation": "report_template_management",
                    "response_time_seconds": response_time,
                    "success": True,
                    "templates_returned": len(templates),
                    "template_categories": len(set(t["report_type"] for t in templates)),
                    "total_parameter_schemas": sum(len(t.get("parameters_schema", {})) for t in templates),
                    "template_inventory_complete": True,
                },
            )

            await logger.log_performance_metric(
                "report_templates_listing",
                response_time,
                {
                    "request_id": request_id,
                    "templates_returned": len(templates),
                    "listing_success": True,
                    "system_template_access": True,
                },
            )

        return {"templates": templates, "total": len(templates)}

    except Exception as e:
        error_time = time.time() - start_time

        # Log report templates listing failure
        if logger:
            await logger.log_error(
                f"Report templates listing failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "report_template_management",
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "report_templates_listing_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "report_templates_listing_failed",
                {
                    "request_id": request_id,
                    "operation": "report_template_management",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to list report templates: {str(e)}")


@router.get("/templates/{template_id}", response_model=ReportTemplateResponse)
async def get_report_template(template_id: str):
    """Get details of a specific report template."""
    start_time = time.time()
    request_id = f"template_detail_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log report template detail retrieval start
        if logger:
            await logger.log_business_event(
                "report_template_detail_started",
                {
                    "request_id": request_id,
                    "template_id": template_id,
                    "operation": "report_template_access",
                    "query_type": "template_detail",
                    "data_scope": "individual_template",
                },
            )

            await logger.log_info(
                "Retrieving report template details",
                {
                    "request_id": request_id,
                    "template_id": template_id,
                    "detail_level": "comprehensive_template_info",
                    "includes_parameter_schema": True,
                    "includes_default_config": True,
                },
            )

        # Return template details
        templates = {
            "pr-confidence-template": {
                "template_id": "pr-confidence-template",
                "name": "PR Confidence Analysis",
                "description": "Analyze confidence scores for pull requests",
                "report_type": "pr_confidence",
                "parameters_schema": {
                    "repository": {"type": "string", "required": True},
                    "date_range": {"type": "object", "required": False},
                },
                "default_parameters": {"include_charts": True, "format": "pdf"},
                "created_at": "2024-01-01T00:00:00Z",
            },
            "summarization-template": {
                "template_id": "summarization-template",
                "name": "Document Summarization Report",
                "description": "Generate summaries of ingested documents",
                "report_type": "summarization",
                "parameters_schema": {
                    "document_ids": {"type": "array", "required": True},
                    "summary_length": {"type": "string", "enum": ["short", "medium", "long"], "required": False},
                },
                "default_parameters": {"include_charts": False, "format": "json"},
                "created_at": "2024-01-01T00:00:00Z",
            },
        }

        if template_id not in templates:
            response_time = time.time() - start_time

            # Log template not found
            if logger:
                await logger.log_business_event(
                    "report_template_not_found",
                    {
                        "request_id": request_id,
                        "template_id": template_id,
                        "operation": "report_template_access",
                        "response_time_seconds": response_time,
                        "template_status": "not_found",
                        "template_lookup_failed": True,
                    },
                )

            raise HTTPException(status_code=404, detail="Report template not found")

        template = templates[template_id]
        response_time = time.time() - start_time

        # Log successful template detail retrieval
        if logger:
            await logger.log_business_event(
                "report_template_detail_retrieved",
                {
                    "request_id": request_id,
                    "template_id": template_id,
                    "operation": "report_template_access",
                    "response_time_seconds": response_time,
                    "success": True,
                    "template_type": template.get("report_type"),
                    "parameter_count": len(template.get("parameters_schema", {})),
                    "has_default_config": bool(template.get("default_parameters")),
                },
            )

            await logger.log_performance_metric(
                "report_template_detail_retrieval",
                response_time,
                {
                    "request_id": request_id,
                    "template_id": template_id,
                    "retrieval_success": True,
                    "template_access_time": response_time,
                },
            )

        return template

    except HTTPException:
        raise
    except Exception as e:
        error_time = time.time() - start_time

        # Log template detail retrieval failure
        if logger:
            await logger.log_error(
                f"Report template detail retrieval failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "report_template_access",
                    "template_id": template_id,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "template_detail_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "report_template_detail_failed",
                {
                    "request_id": request_id,
                    "operation": "report_template_access",
                    "template_id": template_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to get report template: {str(e)}")


@router.delete("/reports/{report_id}", response_model=dict)
async def delete_report(report_id: str):
    """Delete a report."""
    start_time = time.time()
    request_id = f"report_deletion_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log report deletion start
        if logger:
            await logger.log_business_event(
                "report_deletion_started",
                {
                    "request_id": request_id,
                    "report_id": report_id,
                    "operation": "report_lifecycle_management",
                    "control_type": "report_cleanup",
                    "data_management": True,
                    "storage_optimization": True,
                },
            )

            await logger.log_info(
                "Initiating report deletion",
                {
                    "request_id": request_id,
                    "report_id": report_id,
                    "control_operation": "report_deletion",
                    "implementation_status": "placeholder",
                    "storage_cleanup_required": True,
                },
            )

        # This would use a DeleteReportUseCase in a full implementation
        response_time = time.time() - start_time

        # Log report deletion (placeholder implementation)
        if logger:
            await logger.log_business_event(
                "report_deletion_not_implemented",
                {
                    "request_id": request_id,
                    "report_id": report_id,
                    "operation": "report_lifecycle_management",
                    "response_time_seconds": response_time,
                    "implementation_status": "placeholder",
                    "feature_planned": True,
                },
            )

        raise HTTPException(status_code=501, detail="Report deletion not yet implemented")

    except HTTPException:
        raise
    except Exception as e:
        error_time = time.time() - start_time

        # Log report deletion failure
        if logger:
            await logger.log_error(
                f"Report deletion failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "report_lifecycle_management",
                    "report_id": report_id,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "report_deletion_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "report_deletion_failed",
                {
                    "request_id": request_id,
                    "operation": "report_lifecycle_management",
                    "report_id": report_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to delete report: {str(e)}")


@router.get("/types", response_model=dict)
async def list_report_types():
    """List available report types."""
    start_time = time.time()
    request_id = f"report_types_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log report types listing start
        if logger:
            await logger.log_business_event(
                "report_types_listing_started",
                {
                    "request_id": request_id,
                    "operation": "report_capability_discovery",
                    "query_type": "available_report_types",
                    "data_scope": "system_capabilities",
                    "report_type_inventory": True,
                },
            )

            await logger.log_info(
                "Listing available report types and capabilities",
                {
                    "request_id": request_id,
                    "query_operation": "report_type_capability_inventory",
                    "includes_parameter_specs": True,
                    "includes_format_options": True,
                },
            )

        # Return available report types
        report_types = [
            {
                "type": "pr_confidence",
                "name": "PR Confidence Analysis",
                "description": "Analyze AI confidence scores for code review decisions",
                "parameters": ["repository", "date_range", "confidence_threshold"],
                "formats": ["json", "pdf", "html"],
            },
            {
                "type": "summarization",
                "name": "Document Summarization",
                "description": "Generate summaries of ingested documents",
                "parameters": ["document_ids", "summary_length", "focus_areas"],
                "formats": ["json", "pdf", "html"],
            },
            {
                "type": "analytics",
                "name": "Usage Analytics",
                "description": "Analyze system usage patterns and metrics",
                "parameters": ["time_range", "metrics", "group_by"],
                "formats": ["json", "pdf", "csv"],
            },
            {
                "type": "performance",
                "name": "Performance Report",
                "description": "System performance and bottleneck analysis",
                "parameters": ["time_range", "components", "thresholds"],
                "formats": ["json", "pdf", "html"],
            },
            {
                "type": "health",
                "name": "System Health Report",
                "description": "Comprehensive system health assessment",
                "parameters": ["include_history", "detail_level"],
                "formats": ["json", "pdf", "html"],
            },
        ]

        response_time = time.time() - start_time

        # Log successful report types listing
        if logger:
            await logger.log_business_event(
                "report_types_listed",
                {
                    "request_id": request_id,
                    "operation": "report_capability_discovery",
                    "response_time_seconds": response_time,
                    "success": True,
                    "report_types_returned": len(report_types),
                    "total_parameters": sum(len(rt["parameters"]) for rt in report_types),
                    "total_formats": sum(len(rt["formats"]) for rt in report_types),
                    "capability_inventory_complete": True,
                },
            )

            await logger.log_performance_metric(
                "report_types_listing",
                response_time,
                {
                    "request_id": request_id,
                    "report_types_returned": len(report_types),
                    "listing_success": True,
                    "system_capability_query": True,
                },
            )

        return {"report_types": report_types, "total_types": len(report_types)}

    except Exception as e:
        error_time = time.time() - start_time

        # Log report types listing failure
        if logger:
            await logger.log_error(
                f"Report types listing failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "report_capability_discovery",
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "report_types_listing_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "report_types_listing_failed",
                {
                    "request_id": request_id,
                    "operation": "report_capability_discovery",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to list report types: {str(e)}")


@router.get("/stats", response_model=dict)
async def get_reporting_stats():
    """Get reporting system statistics."""
    start_time = time.time()
    request_id = f"reporting_stats_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log reporting stats retrieval start
        if logger:
            await logger.log_business_event(
                "reporting_stats_retrieval_started",
                {
                    "request_id": request_id,
                    "operation": "reporting_system_monitoring",
                    "query_type": "reporting_statistics",
                    "data_scope": "system_metrics",
                    "reporting_analytics": True,
                },
            )

            await logger.log_info(
                "Retrieving reporting system statistics",
                {
                    "request_id": request_id,
                    "stats_type": "comprehensive_reporting_metrics",
                    "includes_performance_data": True,
                    "includes_usage_analytics": True,
                },
            )

        # Return reporting statistics (placeholder data)
        stats = {
            "total_reports": 0,  # Would be populated from actual data
            "reports_generated_today": 0,
            "active_templates": 2,
            "popular_report_types": ["pr_confidence", "summarization"],
            "avg_generation_time_ms": 0.0,
            "storage_used_mb": 0.0,
        }

        response_time = time.time() - start_time

        # Log successful reporting stats retrieval
        if logger:
            await logger.log_business_event(
                "reporting_stats_retrieved",
                {
                    "request_id": request_id,
                    "operation": "reporting_system_monitoring",
                    "response_time_seconds": response_time,
                    "success": True,
                    "stats_completeness": "placeholder_data",
                    "metrics_available": len(stats),
                    "performance_data_included": True,
                    "usage_analytics_included": True,
                },
            )

            await logger.log_performance_metric(
                "reporting_stats_retrieval",
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

        # Log reporting stats retrieval failure
        if logger:
            await logger.log_error(
                f"Reporting stats retrieval failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "reporting_system_monitoring",
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "reporting_stats_retrieval_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "reporting_stats_retrieval_failed",
                {
                    "request_id": request_id,
                    "operation": "reporting_system_monitoring",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to get reporting stats: {str(e)}")
