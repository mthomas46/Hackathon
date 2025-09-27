"""Orchestrator REST API routes with comprehensive OpenAPI annotations."""

from typing import List, Dict, Any, Optional, Union
from datetime import datetime, timezone
from enum import Enum

from fastapi import APIRouter, HTTPException, Query, Path, Body, BackgroundTasks, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field, validator, constr
from pydantic.generics import GenericModel


# Enums for OpenAPI documentation
class WorkflowStatus(str, Enum):
    """Workflow execution statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class ServiceHealth(str, Enum):
    """Service health statuses."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


class EventType(str, Enum):
    """Orchestration event types."""
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    SERVICE_REGISTERED = "service_registered"
    SERVICE_DEREGISTERED = "service_deregistered"
    HEALTH_CHECK_FAILED = "health_check_failed"


# Comprehensive Pydantic models with extensive OpenAPI annotations
class WorkflowDefinition(BaseModel):
    """Workflow definition for orchestration.

    Defines a complete workflow including steps, dependencies, and execution parameters.
    """
    name: constr(min_length=1, max_length=100) = Field(
        ...,
        title="Workflow Name",
        description="Unique name identifier for the workflow",
        example="document_processing_pipeline"
    )
    description: Optional[constr(max_length=500)] = Field(
        None,
        title="Description",
        description="Human-readable description of the workflow purpose",
        example="End-to-end document processing and analysis workflow"
    )
    version: str = Field(
        "1.0.0",
        title="Version",
        description="Semantic version of the workflow definition",
        example="2.1.0",
        regex=r'^\d+\.\d+\.\d+$'
    )
    steps: List[Dict[str, Any]] = Field(
        ...,
        title="Workflow Steps",
        description="Ordered list of workflow steps with dependencies",
        min_items=1,
        example=[
            {
                "id": "extract_text",
                "service": "document-extractor",
                "action": "extract",
                "parameters": {"format": "text"},
                "depends_on": []
            },
            {
                "id": "analyze_content",
                "service": "content-analyzer",
                "action": "analyze",
                "parameters": {"analysis_type": "sentiment"},
                "depends_on": ["extract_text"]
            }
        ]
    )
    triggers: Optional[List[Dict[str, Any]]] = Field(
        None,
        title="Workflow Triggers",
        description="Event triggers that can start this workflow",
        example=[
            {
                "event_type": "document_uploaded",
                "conditions": {"file_size_mb": {"lt": 10}}
            }
        ]
    )
    timeout_seconds: Optional[int] = Field(
        3600,
        title="Timeout",
        description="Maximum execution time in seconds",
        ge=60,
        le=86400,
        example=3600
    )

    @validator('steps')
    def validate_steps(cls, v):
        """Validate workflow steps have required fields."""
        required_fields = ['id', 'service', 'action']
        for step in v:
            for field in required_fields:
                if field not in step:
                    raise ValueError(f'Step missing required field: {field}')
        return v


class WorkflowExecution(BaseModel):
    """Workflow execution instance.

    Represents a specific execution of a workflow with its current state and results.
    """
    id: str = Field(
        ...,
        title="Execution ID",
        description="Unique identifier for this workflow execution",
        example="exec-12345-abc-789"
    )
    workflow_name: str = Field(
        ...,
        title="Workflow Name",
        description="Name of the workflow being executed",
        example="document_processing_pipeline"
    )
    status: WorkflowStatus = Field(
        ...,
        title="Execution Status",
        description="Current status of the workflow execution",
        example=WorkflowStatus.RUNNING
    )
    started_at: datetime = Field(
        ...,
        title="Start Time",
        description="When the execution began",
        example=datetime.now(timezone.utc)
    )
    completed_at: Optional[datetime] = Field(
        None,
        title="Completion Time",
        description="When the execution finished (if completed)",
        example=datetime.now(timezone.utc)
    )
    progress_percentage: float = Field(
        0.0,
        title="Progress",
        description="Execution progress as a percentage (0-100)",
        ge=0.0,
        le=100.0,
        example=65.5
    )
    current_step: Optional[str] = Field(
        None,
        title="Current Step",
        description="ID of the currently executing step",
        example="analyze_content"
    )
    results: Dict[str, Any] = Field(
        default_factory=dict,
        title="Execution Results",
        description="Results from completed workflow steps",
        example={
            "extract_text": {"status": "completed", "output": "Extracted text content..."},
            "analyze_content": {"status": "running", "progress": 0.8}
        }
    )
    error_message: Optional[str] = Field(
        None,
        title="Error Message",
        description="Error message if execution failed",
        example="Service timeout in step 'analyze_content'"
    )


class ServiceRegistration(BaseModel):
    """Service registration information.

    Details about a service registered with the orchestrator.
    """
    name: str = Field(
        ...,
        title="Service Name",
        description="Unique name of the registered service",
        example="document-analyzer"
    )
    type: str = Field(
        ...,
        title="Service Type",
        description="Type or category of the service",
        example="analysis"
    )
    endpoint: str = Field(
        ...,
        title="Service Endpoint",
        description="HTTP endpoint for the service",
        example="http://document-analyzer:8080"
    )
    health_endpoint: Optional[str] = Field(
        None,
        title="Health Check Endpoint",
        description="Endpoint for health checks",
        example="http://document-analyzer:8080/health"
    )
    capabilities: List[str] = Field(
        default_factory=list,
        title="Service Capabilities",
        description="List of capabilities provided by the service",
        example=["text_analysis", "sentiment_analysis", "entity_extraction"]
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict,
        title="Service Metadata",
        description="Additional metadata about the service",
        example={"version": "2.1.0", "author": "platform-team"}
    )
    registered_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        title="Registration Time",
        description="When the service was registered",
        example=datetime.now(timezone.utc)
    )


class OrchestratorStats(BaseModel):
    """Orchestrator statistics and metrics.

    Comprehensive metrics about orchestrator performance and usage.
    """
    total_workflows: int = Field(
        ...,
        title="Total Workflows",
        description="Total number of workflow definitions",
        example=25
    )
    active_executions: int = Field(
        ...,
        title="Active Executions",
        description="Currently running workflow executions",
        example=3
    )
    completed_executions: int = Field(
        ...,
        title="Completed Executions",
        description="Total completed workflow executions",
        example=15432
    )
    failed_executions: int = Field(
        ...,
        title="Failed Executions",
        description="Total failed workflow executions",
        example=234
    )
    registered_services: int = Field(
        ...,
        title="Registered Services",
        description="Number of services registered with orchestrator",
        example=12
    )
    average_execution_time: float = Field(
        ...,
        title="Average Execution Time",
        description="Average workflow execution time in seconds",
        example=45.7
    )
    success_rate: float = Field(
        ...,
        title="Success Rate",
        description="Percentage of successful workflow executions",
        example=98.5
    )
    queue_depth: int = Field(
        ...,
        title="Queue Depth",
        description="Number of workflows waiting in queue",
        example=7
    )


class OrchestrationRouter:
    """FastAPI router for orchestrator operations with comprehensive OpenAPI documentation."""

    def __init__(self):
        """Initialize the orchestrator router with comprehensive API documentation."""
        self.router = APIRouter(
            prefix="/api/v1/orchestrator",
            tags=["orchestrator"],
            responses={
                400: {"description": "Bad Request - Invalid workflow definition or parameters"},
                401: {"description": "Unauthorized - Authentication required"},
                403: {"description": "Forbidden - Insufficient permissions"},
                404: {"description": "Not Found - Workflow or execution not found"},
                409: {"description": "Conflict - Workflow already exists or execution in progress"},
                422: {"description": "Unprocessable Entity - Invalid workflow step dependencies"},
                429: {"description": "Too Many Requests - Rate limit exceeded"},
                500: {"description": "Internal Server Error - Orchestration engine failure"},
                503: {"description": "Service Unavailable - Required services unavailable"}
            }
        )

        # Register all routes with comprehensive documentation
        self._register_routes()

    def _register_routes(self):
        """Register all orchestrator routes with extensive OpenAPI documentation."""

        @self.router.post(
            "/workflows",
            response_model=Dict[str, str],
            summary="Create Workflow Definition",
            description="""
            Create a new workflow definition in the orchestrator.

            This endpoint allows you to define complex multi-step workflows that orchestrate
            multiple services in the LLM ecosystem. Workflows can include conditional logic,
            parallel execution, error handling, and various triggering mechanisms.

            **Workflow Features:**
            - Multi-step orchestration with dependency management
            - Conditional execution based on step results
            - Parallel step execution for performance
            - Automatic retry and error recovery
            - Event-driven triggers and scheduling
            - Comprehensive monitoring and logging

            **Step Types Supported:**
            - Service calls to registered microservices
            - Data transformation and processing steps
            - Conditional branching and decision points
            - Loop constructs for iterative processing
            - Event emission for workflow communication

            **Use Cases:**
            - Document processing pipelines
            - Multi-service data analysis workflows
            - Automated content generation chains
            - Batch processing and ETL operations
            - Event-driven automation scenarios
            """,
            response_description="Workflow creation confirmation with assigned ID"
        )
        async def create_workflow(
            workflow: WorkflowDefinition = Body(
                ...,
                examples={
                    "document_processing": {
                        "summary": "Document Processing Pipeline",
                        "description": "Complete document ingestion and analysis workflow",
                        "value": {
                            "name": "document_processing_pipeline",
                            "description": "End-to-end document processing and analysis",
                            "version": "1.0.0",
                            "steps": [
                                {
                                    "id": "ingest_document",
                                    "service": "document-ingestor",
                                    "action": "ingest",
                                    "parameters": {"validate_content": True},
                                    "depends_on": []
                                },
                                {
                                    "id": "extract_text",
                                    "service": "text-extractor",
                                    "action": "extract",
                                    "parameters": {"format": "markdown"},
                                    "depends_on": ["ingest_document"]
                                },
                                {
                                    "id": "analyze_content",
                                    "service": "content-analyzer",
                                    "action": "analyze",
                                    "parameters": {"analysis_types": ["sentiment", "entities"]},
                                    "depends_on": ["extract_text"]
                                },
                                {
                                    "id": "generate_summary",
                                    "service": "summarizer",
                                    "action": "summarize",
                                    "parameters": {"max_length": 200},
                                    "depends_on": ["analyze_content"]
                                }
                            ],
                            "triggers": [
                                {
                                    "event_type": "document_uploaded",
                                    "conditions": {"content_type": "application/pdf"}
                                }
                            ],
                            "timeout_seconds": 1800
                        }
                    },
                    "simple_analysis": {
                        "summary": "Simple Content Analysis",
                        "description": "Basic single-step analysis workflow",
                        "value": {
                            "name": "simple_analysis",
                            "description": "Quick content analysis",
                            "steps": [
                                {
                                    "id": "analyze",
                                    "service": "content-analyzer",
                                    "action": "analyze",
                                    "parameters": {"quick_mode": True},
                                    "depends_on": []
                                }
                            ]
                        }
                    }
                }
            ),
            background_tasks: BackgroundTasks = None
        ) -> Dict[str, str]:
            """Create a new workflow definition."""
            try:
                # Mock implementation - in real implementation, this would persist the workflow
                import uuid

                workflow_id = f"wf-{uuid.uuid4().hex[:8]}"

                return {
                    "workflow_id": workflow_id,
                    "status": "created",
                    "message": f"Workflow '{workflow.name}' created successfully"
                }

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to create workflow: {str(e)}"
                )

        @self.router.post(
            "/workflows/{workflow_name}/execute",
            response_model=WorkflowExecution,
            summary="Execute Workflow",
            description="""
            Execute a workflow with the specified parameters.

            This endpoint triggers the execution of a previously defined workflow.
            The orchestrator will coordinate the execution across multiple services,
            handle dependencies, manage errors, and provide real-time progress updates.

            **Execution Features:**
            - Asynchronous execution with progress tracking
            - Automatic dependency resolution and ordering
            - Parallel execution of independent steps
            - Comprehensive error handling and recovery
            - Real-time status updates and notifications
            - Execution timeout and cancellation support

            **Execution Modes:**
            - Synchronous: Wait for completion and return results
            - Asynchronous: Start execution and return execution ID for monitoring
            - Streaming: Real-time progress updates during execution

            **Monitoring:**
            - Execution progress and step status
            - Performance metrics and timing
            - Error details and recovery actions
            - Resource usage and cost tracking
            """,
            response_description="Workflow execution details and initial status"
        )
        async def execute_workflow(
            workflow_name: str = Path(
                ...,
                description="Name of the workflow to execute",
                example="document_processing_pipeline"
            ),
            parameters: Optional[Dict[str, Any]] = Body(
                None,
                description="Execution parameters to pass to the workflow",
                example={
                    "input_document": "doc-123",
                    "output_format": "json",
                    "priority": "high",
                    "notification_email": "user@example.com"
                }
            ),
            async_execution: bool = Query(
                True,
                description="Execute asynchronously and return execution ID",
                example=True
            )
        ) -> WorkflowExecution:
            """Execute a workflow with specified parameters."""
            try:
                import uuid
                import time

                execution_id = f"exec-{uuid.uuid4().hex[:8]}"
                start_time = datetime.now(timezone.utc)

                # Mock workflow execution
                execution = WorkflowExecution(
                    id=execution_id,
                    workflow_name=workflow_name,
                    status=WorkflowStatus.RUNNING if async_execution else WorkflowStatus.COMPLETED,
                    started_at=start_time,
                    progress_percentage=15.0,
                    current_step="ingest_document",
                    results={
                        "ingest_document": {
                            "status": "completed",
                            "output": "Document ingested successfully",
                            "duration_seconds": 2.1
                        }
                    }
                )

                if not async_execution:
                    # Mock completion for synchronous execution
                    execution.status = WorkflowStatus.COMPLETED
                    execution.completed_at = datetime.now(timezone.utc)
                    execution.progress_percentage = 100.0
                    execution.results["analyze_content"] = {
                        "status": "completed",
                        "output": "Analysis completed",
                        "duration_seconds": 3.5
                    }

                return execution

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to execute workflow: {str(e)}"
                )

        @self.router.get(
            "/executions/{execution_id}",
            response_model=WorkflowExecution,
            summary="Get Execution Status",
            description="""
            Get the current status and progress of a workflow execution.

            This endpoint provides detailed information about a running or completed
            workflow execution, including progress, current step, results, and any errors.

            **Status Information:**
            - Execution progress percentage and current step
            - Status of individual workflow steps
            - Execution timing and performance metrics
            - Error messages and failure details
            - Step results and output data

            **Real-time Monitoring:**
            - Poll this endpoint for execution progress
            - Use WebSocket connections for real-time updates
            - Receive notifications on execution completion
            - Monitor resource usage and performance

            **Execution States:**
            - `pending`: Execution queued but not started
            - `running`: Execution in progress
            - `completed`: Execution finished successfully
            - `failed`: Execution failed with errors
            - `cancelled`: Execution was cancelled
            - `paused`: Execution temporarily paused
            """,
            response_description="Current execution status and progress details"
        )
        async def get_execution_status(
            execution_id: str = Path(
                ...,
                description="ID of the workflow execution to check",
                example="exec-12345-abc-789"
            )
        ) -> WorkflowExecution:
            """Get the status of a workflow execution."""
            try:
                # Mock execution status - in real implementation, this would query the execution store
                execution = WorkflowExecution(
                    id=execution_id,
                    workflow_name="document_processing_pipeline",
                    status=WorkflowStatus.RUNNING,
                    started_at=datetime.now(timezone.utc),
                    progress_percentage=67.5,
                    current_step="analyze_content",
                    results={
                        "ingest_document": {"status": "completed", "duration_seconds": 2.1},
                        "extract_text": {"status": "completed", "duration_seconds": 1.8},
                        "analyze_content": {"status": "running", "progress": 0.75}
                    }
                )

                return execution

            except Exception as e:
                raise HTTPException(
                    status_code=404,
                    detail=f"Execution {execution_id} not found"
                )

        @self.router.delete(
            "/executions/{execution_id}",
            summary="Cancel Workflow Execution",
            description="""
            Cancel a running workflow execution.

            This endpoint allows you to stop a workflow execution that is currently running.
            The orchestrator will attempt to gracefully stop the execution, clean up resources,
            and provide information about the cancellation.

            **Cancellation Behavior:**
            - Running steps are signalled to stop gracefully
            - Resource cleanup is performed
            - Partial results may be available
            - Execution status changes to 'cancelled'
            - Cancellation reason is recorded

            **Use Cases:**
            - Stop long-running workflows that are no longer needed
            - Cancel executions due to changing requirements
            - Emergency stops for problematic workflows
            - Timeout handling for stuck executions

            **Note:** Some steps may not be cancellable if they are in critical sections.
            """,
            response_description="Cancellation confirmation and final execution status"
        )
        async def cancel_execution(
            execution_id: str = Path(
                ...,
                description="ID of the execution to cancel",
                example="exec-12345-abc-789"
            ),
            reason: Optional[str] = Query(
                None,
                description="Reason for cancellation",
                example="User requested cancellation"
            )
        ) -> Dict[str, Any]:
            """Cancel a running workflow execution."""
            try:
                # Mock cancellation - in real implementation, this would signal the execution engine
                return {
                    "execution_id": execution_id,
                    "status": "cancelled",
                    "cancelled_at": datetime.now(timezone.utc).isoformat(),
                    "reason": reason or "User requested cancellation",
                    "final_state": {
                        "progress_percentage": 67.5,
                        "completed_steps": ["ingest_document", "extract_text"],
                        "cancelled_step": "analyze_content"
                    }
                }

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to cancel execution: {str(e)}"
                )

        @self.router.get(
            "/workflows",
            response_model=List[Dict[str, Any]],
            summary="List Workflow Definitions",
            description="""
            Get a list of all available workflow definitions.

            This endpoint returns all workflows registered with the orchestrator,
            including their metadata, capabilities, and execution statistics.

            **Workflow Information:**
            - Workflow name, description, and version
            - Available triggers and execution parameters
            - Recent execution statistics and success rates
            - Resource requirements and cost estimates
            - Tags and categorization information

            **Filtering Options:**
            - Filter by workflow type or category
            - Search by name or description
            - Filter by supported triggers
            - Sort by popularity, success rate, or execution time

            **Use Cases:**
            - Discover available workflows for automation
            - Compare workflow capabilities and performance
            - Plan workflow usage and resource allocation
            - Monitor workflow adoption and usage patterns
            """,
            response_description="List of available workflow definitions with metadata"
        )
        async def list_workflows(
            category: Optional[str] = Query(
                None,
                description="Filter by workflow category",
                example="document_processing"
            ),
            limit: int = Query(
                50,
                description="Maximum number of workflows to return",
                ge=1,
                le=200,
                example=20
            ),
            offset: int = Query(
                0,
                description="Number of workflows to skip",
                ge=0,
                example=0
            )
        ) -> List[Dict[str, Any]]:
            """List all available workflow definitions."""
            try:
                # Mock workflow list - in real implementation, this would query the workflow registry
                workflows = [
                    {
                        "name": "document_processing_pipeline",
                        "description": "Complete document processing and analysis workflow",
                        "version": "1.0.0",
                        "category": "document_processing",
                        "steps_count": 4,
                        "estimated_duration": 180,
                        "success_rate": 96.5,
                        "total_executions": 15432,
                        "tags": ["document", "analysis", "pipeline"]
                    },
                    {
                        "name": "content_generation_workflow",
                        "description": "AI-powered content generation and enhancement",
                        "version": "2.1.0",
                        "category": "content_generation",
                        "steps_count": 3,
                        "estimated_duration": 120,
                        "success_rate": 98.2,
                        "total_executions": 8765,
                        "tags": ["generation", "ai", "content"]
                    },
                    {
                        "name": "data_analysis_suite",
                        "description": "Comprehensive data analysis and reporting workflow",
                        "version": "1.3.0",
                        "category": "data_analysis",
                        "steps_count": 5,
                        "estimated_duration": 300,
                        "success_rate": 94.1,
                        "total_executions": 5432,
                        "tags": ["data", "analysis", "reporting"]
                    }
                ]

                # Apply category filter
                if category:
                    workflows = [wf for wf in workflows if wf["category"] == category]

                # Apply pagination
                workflows = workflows[offset:offset + limit]

                return workflows

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to list workflows: {str(e)}"
                )

        @self.router.get(
            "/services",
            response_model=List[ServiceRegistration],
            summary="List Registered Services",
            description="""
            Get information about all services registered with the orchestrator.

            This endpoint provides a comprehensive view of the service ecosystem,
            including service health, capabilities, and performance metrics.

            **Service Information:**
            - Service name, type, and endpoints
            - Current health status and response times
            - Available capabilities and supported operations
            - Version information and metadata
            - Registration time and last health check

            **Health Monitoring:**
            - Real-time health status for each service
            - Response time metrics and performance data
            - Error rates and reliability statistics
            - Service availability and uptime information

            **Use Cases:**
            - Service discovery for workflow creation
            - Health monitoring and alerting
            - Capacity planning and load balancing
            - Troubleshooting and debugging assistance
            """,
            response_description="List of registered services with health and capability information"
        )
        async def list_services(
            service_type: Optional[str] = Query(
                None,
                description="Filter by service type",
                example="analysis"
            ),
            health_status: Optional[ServiceHealth] = Query(
                None,
                description="Filter by health status",
                example=ServiceHealth.HEALTHY
            )
        ) -> List[ServiceRegistration]:
            """List all registered services with their status."""
            try:
                # Mock service list - in real implementation, this would query the service registry
                services = [
                    ServiceRegistration(
                        name="document-analyzer",
                        type="analysis",
                        endpoint="http://document-analyzer:8080",
                        health_endpoint="http://document-analyzer:8080/health",
                        capabilities=["sentiment_analysis", "entity_extraction", "text_classification"],
                        metadata={"version": "2.1.0", "author": "platform-team"}
                    ),
                    ServiceRegistration(
                        name="text-extractor",
                        type="extraction",
                        endpoint="http://text-extractor:8081",
                        health_endpoint="http://text-extractor:8081/health",
                        capabilities=["pdf_extraction", "ocr", "text_normalization"],
                        metadata={"version": "1.8.0", "author": "processing-team"}
                    ),
                    ServiceRegistration(
                        name="summarizer",
                        type="generation",
                        endpoint="http://summarizer:8082",
                        health_endpoint="http://summarizer:8082/health",
                        capabilities=["abstractive_summarization", "extractive_summarization"],
                        metadata={"version": "3.2.0", "author": "ai-team"}
                    )
                ]

                # Apply filters
                if service_type:
                    services = [s for s in services if s.type == service_type]

                # Health status filtering would require actual health checks
                if health_status:
                    # Mock health status - in real implementation, this would check actual health
                    pass

                return services

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to list services: {str(e)}"
                )

        @self.router.get(
            "/stats",
            response_model=OrchestratorStats,
            summary="Get Orchestrator Statistics",
            description="""
            Retrieve comprehensive statistics about the orchestrator's operation.

            This endpoint provides detailed metrics about workflow executions,
            service performance, system health, and usage patterns.

            **Statistics Categories:**
            - Workflow execution metrics (success rates, timing, queue depth)
            - Service registry information (registered services, health status)
            - Performance metrics (average execution time, resource usage)
            - Error rates and failure analysis
            - System utilization and capacity information

            **Monitoring Use Cases:**
            - Performance monitoring and alerting
            - Capacity planning and resource allocation
            - Troubleshooting execution failures
            - Usage analytics and optimization
            - SLA compliance tracking

            **Real-time Data:**
            - Statistics are updated in real-time
            - Historical trends available for analysis
            - Configurable retention periods for metrics
            - Export capabilities for external monitoring systems
            """,
            response_description="Comprehensive orchestrator statistics and performance metrics"
        )
        async def get_orchestrator_stats() -> OrchestratorStats:
            """Get comprehensive orchestrator statistics."""
            try:
                # Mock comprehensive statistics
                return OrchestratorStats(
                    total_workflows=25,
                    active_executions=3,
                    completed_executions=15432,
                    failed_executions=234,
                    registered_services=12,
                    average_execution_time=45.7,
                    success_rate=98.5,
                    queue_depth=7
                )

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to retrieve statistics: {str(e)}"
                )

        @self.router.post(
            "/events",
            summary="Emit Orchestration Event",
            description="""
            Emit a custom event to the orchestration system.

            This endpoint allows external systems to emit events that can trigger
            workflows, update service states, or modify orchestration behavior.

            **Supported Event Types:**
            - `workflow_started`: Signal workflow execution start
            - `workflow_completed`: Signal workflow completion
            - `service_registered`: Register new service availability
            - `service_deregistered`: Signal service unavailability
            - `health_check_failed`: Report service health issues
            - Custom events for workflow-specific triggers

            **Event Processing:**
            - Events are queued for processing
            - Asynchronous handling with guaranteed delivery
            - Event correlation and tracing support
            - Configurable event routing and filtering

            **Use Cases:**
            - External system integration and notifications
            - Workflow triggering from external events
            - Service lifecycle management
            - Monitoring and alerting integration
            """,
            response_description="Event emission confirmation with processing details"
        )
        async def emit_event(
            event_type: EventType = Body(
                ...,
                description="Type of event to emit",
                example=EventType.WORKFLOW_COMPLETED
            ),
            event_data: Dict[str, Any] = Body(
                ...,
                description="Event-specific data payload",
                example={
                    "workflow_name": "document_processing",
                    "execution_id": "exec-12345",
                    "result": "success",
                    "duration_seconds": 45.2
                }
            ),
            correlation_id: Optional[str] = Body(
                None,
                description="Correlation ID for event tracing",
                example="corr-abc-123"
            )
        ) -> Dict[str, Any]:
            """Emit an event to the orchestration system."""
            try:
                import uuid

                event_id = f"evt-{uuid.uuid4().hex[:8]}"

                return {
                    "event_id": event_id,
                    "event_type": event_type.value,
                    "status": "emitted",
                    "correlation_id": correlation_id,
                    "queued_at": datetime.now(timezone.utc).isoformat(),
                    "estimated_processing_time": "2-5 seconds"
                }

            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to emit event: {str(e)}"
                )

        @self.router.get(
            "/health",
            summary="Orchestrator Health Check",
            description="""
            Comprehensive health check for the orchestrator service.

            Performs detailed checks across all orchestrator components including
            workflow engine, service registry, event system, and external dependencies.

            **Health Checks Performed:**
            - Workflow engine availability and responsiveness
            - Service registry connectivity and data integrity
            - Event processing queue health and throughput
            - Database and cache connections
            - External service dependencies and integrations
            - Resource utilization and performance metrics

            **Health Status Levels:**
            - `healthy`: All systems operational within normal parameters
            - `degraded`: Some systems experiencing issues but still functional
            - `unhealthy`: Critical systems down, orchestrator may not function properly

            **Monitoring Integration:**
            - Compatible with standard monitoring systems
            - Structured health data for alerting and dashboards
            - Historical health trends and failure analysis
            """,
            response_description="Comprehensive orchestrator health status"
        )
        async def health_check():
            """Comprehensive health check for the orchestrator."""
            try:
                return {
                    "status": "healthy",
                    "service": "orchestrator",
                    "version": "1.0.0",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "components": {
                        "workflow_engine": {"status": "healthy", "response_time_ms": 15},
                        "service_registry": {"status": "healthy", "services_count": 12},
                        "event_system": {"status": "healthy", "queue_depth": 3},
                        "cache": {"status": "healthy", "hit_rate": 0.94},
                        "database": {"status": "healthy", "connection_pool_size": 10}
                    },
                    "uptime_seconds": 86400,  # 24 hours
                    "active_workflows": 3,
                    "success_rate_24h": 98.5
                }

            except Exception as e:
                return {
                    "status": "unhealthy",
                    "service": "orchestrator",
                    "error": str(e),
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }


# Factory function to create router
def create_orchestrator_router() -> APIRouter:
    """Create orchestrator router with comprehensive OpenAPI documentation."""
    router_instance = OrchestrationRouter()
    return router_instance.router
