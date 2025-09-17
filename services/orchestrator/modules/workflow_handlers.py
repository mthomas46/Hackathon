"""Workflow and job handlers for Orchestrator service.

Handles workflow execution, job management, and related operations.
Includes LangGraph workflow integration for advanced orchestration.
"""
from typing import Dict, Any, List, Optional

from services.shared.responses import create_success_response, create_error_response
from services.shared.constants_new import ErrorCodes
from .shared_utils import get_orchestrator_service_client

# Import LangGraph components
try:
    from .langgraph.engine import LangGraphWorkflowEngine
    from .langgraph.state import create_workflow_state
    from .workflows import create_document_analysis_workflow
    from .workflows.end_to_end_test import end_to_end_test_workflow
    LANGGRAPH_AVAILABLE = True
except ImportError:
    LANGGRAPH_AVAILABLE = False
    print("Warning: LangGraph not available, falling back to basic workflow handlers")


class WorkflowHandlers:
    """Handles workflow and job operations."""

    @staticmethod
    async def handle_workflow_run(request) -> Dict[str, Any]:
        """Execute a workflow using LangGraph when available."""
        try:
            workflow_type = getattr(request, 'workflow_type', 'generic')
            parameters = request.parameters or {}
            context = request.context or {}

            # Check if LangGraph is available and use it
            if LANGGRAPH_AVAILABLE:
                return await WorkflowHandlers._handle_langgraph_workflow(
                    workflow_type, parameters, context, getattr(request, 'user_id', None)
                )
            else:
                # Fallback to basic workflow execution
                return await WorkflowHandlers._handle_basic_workflow(request)

        except Exception as e:
            return create_error_response(
                "Workflow execution failed",
                error_code=ErrorCodes.INTERNAL_ERROR,
                details={
                    "workflow_type": getattr(request, 'workflow_type', 'unknown'),
                    "error": str(e)
                }
            )

    @staticmethod
    async def _handle_langgraph_workflow(
        workflow_type: str,
        parameters: Dict[str, Any],
        context: Dict[str, Any],
        user_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """Handle workflow execution using LangGraph."""
        try:
            # Initialize LangGraph engine
            engine = LangGraphWorkflowEngine()

            # Initialize tools for the required services
            required_services = WorkflowHandlers._get_services_for_workflow(workflow_type)
            tools = await engine.initialize_tools(required_services)

            # Register workflows if not already registered
            WorkflowHandlers._register_langgraph_workflows(engine)

            # Execute the workflow
            result = await engine.execute_workflow(
                workflow_type=workflow_type,
                input_data=parameters,
                tools=tools,
                user_id=user_id
            )

            return create_success_response(
                f"LangGraph workflow '{workflow_type}' completed successfully",
                result
            )

        except Exception as e:
            return create_error_response(
                f"LangGraph workflow execution failed: {str(e)}",
                error_code=ErrorCodes.INTERNAL_ERROR,
                details={
                    "workflow_type": workflow_type,
                    "error_type": type(e).__name__,
                    "langgraph_available": LANGGRAPH_AVAILABLE
                }
            )

    @staticmethod
    async def _handle_basic_workflow(request) -> Dict[str, Any]:
        """Fallback basic workflow execution."""
        workflow_id = getattr(request, 'workflow_id', 'unknown')
        parameters = request.parameters or {}
        context = request.context or {}

        # Placeholder basic workflow execution
        result = {
            "workflow_id": workflow_id,
            "execution_id": f"exec_{workflow_id}_12345",
            "status": "completed",
            "parameters": parameters,
            "context": context,
            "message": "Basic workflow execution (LangGraph not available)",
            "steps": [
                {"step_id": "step1", "status": "completed", "service": "orchestrator"},
                {"step_id": "step2", "status": "completed", "service": "logging"}
            ]
        }
        return create_success_response("Basic workflow execution completed", result)

    @staticmethod
    def _get_services_for_workflow(workflow_type: str) -> List[str]:
        """Determine which services are needed for a workflow type."""
        service_map = {
            "document_analysis": [
                "document_store", "summarizer_hub", "analysis_service",
                "notification_service", "logging_service"
            ],
            "code_documentation": [
                "code_analyzer", "document_store", "summarizer_hub",
                "prompt_store", "notification_service"
            ],
            "quality_assurance": [
                "analysis_service", "document_store", "code_analyzer",
                "notification_service", "logging_service"
            ],
            "generic": ["logging_service"]  # Basic services for generic workflows
        }

        return service_map.get(workflow_type, ["logging_service"])

    @staticmethod
    def _register_langgraph_workflows(engine: 'LangGraphWorkflowEngine'):
        """Register available LangGraph workflows with the engine."""
        try:
            # Register document analysis workflow
            doc_workflow = create_document_analysis_workflow()
            engine.workflows["document_analysis"] = doc_workflow

            # Register end-to-end test workflow
            e2e_workflow = end_to_end_test_workflow.get_workflow()
            engine.workflows["end_to_end_test"] = e2e_workflow

            # Register PR confidence orchestration workflow
            from .workflows.pr_confidence_orchestration import pr_confidence_orchestration_workflow
            engine.workflows["pr_confidence_analysis"] = pr_confidence_orchestration_workflow.workflow

            # Additional workflows can be registered here as they are implemented
            print(f"✓ Registered {len(engine.workflows)} LangGraph workflows")

        except Exception as e:
            print(f"Warning: Failed to register LangGraph workflows: {e}")

    @staticmethod
    async def handle_ingest(request) -> Dict[str, Any]:
        """Handle document ingestion requests."""
        try:
            source_url = request.source_url
            source_type = request.source_type
            parameters = request.parameters or {}

            # Placeholder - would integrate with actual ingestion logic
            result = {
                "ingestion_id": f"ingest_{source_type}_12345",
                "source_url": source_url,
                "source_type": source_type,
                "status": "queued",
                "parameters": parameters,
                "estimated_completion": "2024-01-01T01:00:00Z"
            }
            return create_success_response("Ingestion request queued", result)
        except Exception as e:
            return create_error_response("Ingestion request failed", error_code=ErrorCodes.VALIDATION_ERROR, details={"source_url": request.source_url, "error": str(e)})

    @staticmethod
    async def handle_registry_register(request) -> Dict[str, Any]:
        """Register a service in the registry."""
        try:
            # Placeholder - would integrate with actual service registry
            result = {
                "service_name": request.service_name,
                "service_url": request.service_url,
                "capabilities": request.capabilities,
                "status": "registered",
                "registered_at": "2024-01-01T00:00:00Z"
            }
            return create_success_response("Service registered successfully", result)
        except Exception as e:
            return create_error_response("Service registration failed", error_code=ErrorCodes.VALIDATION_ERROR, details={"service_name": request.service_name, "error": str(e)})

    @staticmethod
    async def handle_registry_list() -> Dict[str, Any]:
        """List registered services."""
        try:
            # Placeholder - would integrate with actual service registry
            services = [
                {
                    "service_name": "doc_store",
                    "service_url": "http://localhost:5087",
                    "capabilities": ["document_storage", "search"],
                    "status": "active",
                    "last_seen": "2024-01-01T00:00:00Z"
                },
                {
                    "service_name": "analysis-service",
                    "service_url": "http://localhost:5020",
                    "capabilities": ["analysis", "reporting"],
                    "status": "active",
                    "last_seen": "2024-01-01T00:00:00Z"
                }
            ]
            return create_success_response("Registry retrieved successfully", {"services": services})
        except Exception as e:
            return create_error_response("Failed to retrieve registry", error_code=ErrorCodes.DATABASE_ERROR, details={"error": str(e)})

    @staticmethod
    async def handle_peers() -> Dict[str, Any]:
        """List peer orchestrators."""
        try:
            # Placeholder - would integrate with actual peer discovery
            peers = []
            return create_success_response("Peers retrieved successfully", {"peers": peers})
        except Exception as e:
            return create_error_response("Failed to retrieve peers", error_code=ErrorCodes.DATABASE_ERROR, details={"error": str(e)})

    @staticmethod
    async def handle_registry_poll_openapi(request) -> Dict[str, Any]:
        """Poll OpenAPI specs from services."""
        try:
            service_urls = request.service_urls
            force_refresh = request.force_refresh

            # Placeholder - would integrate with actual OpenAPI polling
            result = {
                "services_polled": len(service_urls),
                "specs_updated": len(service_urls),
                "errors": [],
                "force_refresh": force_refresh
            }
            return create_success_response("OpenAPI polling completed", result)
        except Exception as e:
            return create_error_response("OpenAPI polling failed", error_code=ErrorCodes.INTERNAL_ERROR, details={"error": str(e)})

    @staticmethod
    async def handle_workflow_history(request) -> Dict[str, Any]:
        """Get workflow execution history."""
        try:
            workflow_id = request.workflow_id
            limit = request.limit
            status_filter = request.status_filter

            # Placeholder - would integrate with actual workflow history
            history = []
            return create_success_response("Workflow history retrieved successfully", {"history": history, "total": 0})
        except Exception as e:
            return create_error_response("Failed to retrieve workflow history", error_code=ErrorCodes.DATABASE_ERROR, details={"error": str(e)})

    @staticmethod
    async def handle_job_recalc_quality(request) -> Dict[str, Any]:
        """Handle quality recalculation jobs."""
        try:
            target_services = request.target_services
            force_recalc = request.force_recalc

            # Placeholder - would integrate with actual quality recalculation
            result = {
                "job_id": "quality_recalc_12345",
                "target_services": target_services,
                "force_recalc": force_recalc,
                "status": "queued"
            }
            return create_success_response("Quality recalculation job queued", result)
        except Exception as e:
            return create_error_response("Quality recalculation job failed", error_code=ErrorCodes.INTERNAL_ERROR, details={"error": str(e)})

    @staticmethod
    async def handle_job_notify_consolidation(request) -> Dict[str, Any]:
        """Handle consolidation notifications."""
        try:
            consolidation_id = request.consolidation_id
            notification_channels = request.notification_channels
            recipients = request.recipients

            # Placeholder - would integrate with actual notification system
            result = {
                "consolidation_id": consolidation_id,
                "notification_channels": notification_channels,
                "recipients": recipients or [],
                "status": "sent"
            }
            return create_success_response("Consolidation notification sent", result)
        except Exception as e:
            return create_error_response("Consolidation notification failed", error_code=ErrorCodes.INTERNAL_ERROR, details={"consolidation_id": request.consolidation_id, "error": str(e)})


# Create singleton instance
workflow_handlers = WorkflowHandlers()
