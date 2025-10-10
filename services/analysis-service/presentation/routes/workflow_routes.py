"""Workflow Routes.

Workflow event processing, status tracking, and webhook configuration.
"""
from fastapi import APIRouter

# Import shared utilities
from services.shared.presentation.api.responses import create_success_response, create_error_response
from services.shared.core.constants_new import ErrorCodes
from services.shared.infrastructure.monitoring.logging import fire_and_forget

# Import models
from ...modules.models import WorkflowEventRequest, WorkflowStatusRequest, WebhookConfigRequest

# Service metadata
SERVICE_NAME = "analysis-service"

# Create router
router = APIRouter(tags=["Workflows"])


@router.post("/workflows/events")
async def process_workflow_event_endpoint(req: WorkflowEventRequest):
    """Process workflow events and trigger appropriate analyses.

    Receives workflow events (PRs, commits, releases, etc.) and automatically
    triggers relevant documentation analysis based on the event type and content.
    Supports GitHub, GitLab, and other webhook integrations.

    Args:
        req: Workflow event request with event details

    Returns:
        Workflow processing result with analysis types triggered
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_workflow_event(req)

        # Log successful workflow processing
        workflow_id = result.workflow_id
        priority = result.priority
        analysis_count = len(result.analysis_types)
        fire_and_forget(
            "info",
            "Workflow event processed",
            SERVICE_NAME,
            {
                "workflow_id": workflow_id,
                "event_type": result.event_type,
                "event_action": result.event_action,
                "priority": priority,
                "analysis_types_count": analysis_count,
                "estimated_processing_time": result.estimated_processing_time,
                "processing_time": result.processing_time
            }
        )

        return create_success_response(
            f"Workflow event processed - {analysis_count} analysis types triggered",
            {
                "workflow_id": workflow_id,
                "status": result.status,
                "priority": priority,
                "analysis_types": result.analysis_types,
                "estimated_processing_time": result.estimated_processing_time,
                "processing_time": result.processing_time,
                "event_type": result.event_type,
                "event_action": result.event_action
            },
            workflow_id=workflow_id,
            priority=priority,
            analysis_types_count=analysis_count,
            processing_time=result.processing_time
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Workflow event processing failed",
            SERVICE_NAME,
            {"event_type": req.event_type, "event_action": req.action, "error": str(e)}
        )

        return create_error_response(
            f"Workflow event processing failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )


@router.get("/workflows/{workflow_id}")
async def get_workflow_status_endpoint(workflow_id: str):
    """Get the status of a workflow analysis.

    Retrieves the current status, progress, and results of a workflow-triggered
    analysis. Useful for monitoring long-running analyses and checking completion.

    Args:
        workflow_id: Unique identifier for the workflow

    Returns:
        Workflow status including progress, results, and errors
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        # Create status request
        req = WorkflowStatusRequest(workflow_id=workflow_id)

        result = await analysis_handlers.handle_workflow_status(req)

        if result.status == 'not_found':
            return create_error_response(
                "Workflow not found",
                error_code=ErrorCodes.RESOURCE_NOT_FOUND
            )

        # Log status check
        fire_and_forget(
            "info",
            "Workflow status retrieved",
            SERVICE_NAME,
            {
                "workflow_id": workflow_id,
                "status": result.status,
                "priority": result.priority
            }
        )

        return create_success_response(
            f"Workflow status: {result.status}",
            {
                "workflow_id": result.workflow_id,
                "status": result.status,
                "priority": result.priority,
                "created_at": result.created_at,
                "processed_at": result.processed_at,
                "completed_at": result.completed_at,
                "analysis_plan": result.analysis_plan,
                "results": result.results,
                "error": result.error
            },
            status=result.status,
            priority=result.priority
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Workflow status retrieval failed",
            SERVICE_NAME,
            {"workflow_id": workflow_id, "error": str(e)}
        )

        return create_error_response(
            f"Workflow status retrieval failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )


@router.get("/workflows/queue/status")
async def get_workflow_queue_status_endpoint():
    """Get the status of workflow analysis queues.

    Provides an overview of the current workflow processing queues, including
    queue lengths, active workflows, and recent events. Useful for monitoring
    system load and processing capacity.

    Returns:
        Queue status with pending, active, and recent workflow events
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_workflow_queue_status()

        # Log queue status check
        total_queued = result.total_queued
        active_workflows = result.active_workflows
        fire_and_forget(
            "info",
            "Workflow queue status retrieved",
            SERVICE_NAME,
            {
                "total_queued": total_queued,
                "active_workflows": active_workflows,
                "queues": result.queues
            }
        )

        return create_success_response(
            f"Queue status: {total_queued} queued, {active_workflows} active workflows",
            {
                "queues": result.queues,
                "total_queued": total_queued,
                "active_workflows": active_workflows,
                "recent_events": result.recent_events
            },
            total_queued=total_queued,
            active_workflows=active_workflows
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Workflow queue status retrieval failed",
            SERVICE_NAME,
            {"error": str(e)}
        )

        return create_error_response(
            f"Workflow queue status retrieval failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )


@router.post("/workflows/webhook/config")
async def configure_webhook_endpoint(req: WebhookConfigRequest):
    """Configure webhook settings for workflow integration.

    Sets up webhook configuration for receiving workflow events from external
    systems like GitHub, GitLab, or CI/CD pipelines. Enables secure event processing
    with signature validation.

    Args:
        req: Webhook configuration request with settings

    Returns:
        Configuration result with enabled events and webhook URL
    """
    # Import here to avoid circular dependencies
    from ...modules.analysis_handlers import AnalysisHandlers
    
    analysis_handlers = AnalysisHandlers()
    
    try:
        result = await analysis_handlers.handle_webhook_config(req)

        # Log webhook configuration
        configured = result.configured
        events_count = len(result.enabled_events)
        fire_and_forget(
            "info",
            "Webhook configuration updated",
            SERVICE_NAME,
            {
                "configured": configured,
                "enabled_events_count": events_count,
                "enabled_events": result.enabled_events
            }
        )

        return create_success_response(
            f"Webhook configuration {'updated' if configured else 'failed'}",
            {
                "configured": configured,
                "enabled_events": result.enabled_events,
                "webhook_url": result.webhook_url
            },
            configured=configured,
            enabled_events_count=events_count
        )

    except Exception as e:
        # Log the error
        fire_and_forget(
            "error",
            "Webhook configuration failed",
            SERVICE_NAME,
            {"error": str(e)}
        )

        return create_error_response(
            f"Webhook configuration failed: {str(e)}",
            error_code=ErrorCodes.ANALYSIS_FAILED
        )

