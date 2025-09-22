"""Workflow Management API Routes"""

import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from services.shared.core.constants_new import ServiceNames

# Import domain/application services (will be injected via dependency injection)
# These will be available through the container in main.py
from services.shared.utilities.logging_client import get_log_collector_client

from .dtos import (
    CreateWorkflowRequest,
    ExecuteWorkflowRequest,
    ExecutionListResponse,
    GetWorkflowRequest,
    ListWorkflowsRequest,
    WorkflowExecutionResponse,
    WorkflowListResponse,
    WorkflowResponse,
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


def get_workflow_container():
    """Dependency injection for workflow management services."""
    # This will be replaced with actual dependency injection in main.py
    from ....main import container

    return container


@router.post("", response_model=WorkflowResponse)
async def create_workflow(request: CreateWorkflowRequest, container=Depends(get_workflow_container)):
    """Create a new workflow."""
    start_time = time.time()
    request_id = f"workflow_creation_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log workflow creation start
        if logger:
            await logger.log_business_event(
                "workflow_creation_started",
                {
                    "request_id": request_id,
                    "operation": "workflow_lifecycle_management",
                    "workflow_type": request.workflow_type,
                    "workflow_name": request.name,
                    "actions_count": len(request.actions) if request.actions else 0,
                    "parameters_count": len(request.parameters) if request.parameters else 0,
                    "tags_count": len(request.tags) if request.tags else 0,
                    "workflow_definition": True,
                },
            )

            await logger.log_info(
                "Initiating workflow creation",
                {
                    "request_id": request_id,
                    "workflow_name": request.name,
                    "workflow_type": request.workflow_type,
                    "actions_provided": bool(request.actions),
                    "parameters_configured": bool(request.parameters),
                    "tags_assigned": bool(request.tags),
                    "orchestration_engine_activated": True,
                },
            )

        # Create command
        from ....application.workflow_management.commands import CreateWorkflowCommand

        command = CreateWorkflowCommand(
            name=request.name,
            description=request.description,
            workflow_type=request.workflow_type,
            parameters=request.parameters,
            actions=request.actions,
            tags=request.tags,
        )

        # Execute use case
        result = await container.create_workflow_use_case.execute(command)

        if not result.success:
            response_time = time.time() - start_time

            # Log workflow creation failed
            if logger:
                await logger.log_business_event(
                    "workflow_creation_failed",
                    {
                        "request_id": request_id,
                        "operation": "workflow_lifecycle_management",
                        "workflow_type": request.workflow_type,
                        "workflow_name": request.name,
                        "response_time_seconds": response_time,
                        "error_message": result.error_message,
                        "validation_failed": True,
                    },
                )

            raise HTTPException(status_code=400, detail=result.error_message)

        # Convert to response
        workflow_id = result.workflow.id if hasattr(result.workflow, "id") else result.workflow.get("id")
        response_time = time.time() - start_time

        # Log successful workflow creation
        if logger:
            await logger.log_business_event(
                "workflow_created",
                {
                    "request_id": request_id,
                    "workflow_id": workflow_id,
                    "operation": "workflow_lifecycle_management",
                    "response_time_seconds": response_time,
                    "success": True,
                    "workflow_type": request.workflow_type,
                    "workflow_name": request.name,
                    "actions_defined": len(request.actions) if request.actions else 0,
                    "workflow_ready_for_execution": True,
                },
            )

            await logger.log_performance_metric(
                "workflow_creation",
                response_time,
                {
                    "request_id": request_id,
                    "workflow_id": workflow_id,
                    "workflow_type": request.workflow_type,
                    "creation_success": True,
                    "definition_processing_time": response_time,
                },
            )
        return WorkflowResponse(
            workflow_id=result.workflow.workflow_id,
            name=result.workflow.name,
            description=result.workflow.description,
            workflow_type=result.workflow.workflow_type,
            status=result.workflow.status,
            parameters=result.workflow.parameters,
            actions=result.workflow.actions,
            tags=result.workflow.tags,
            created_at=result.workflow.created_at,
            updated_at=result.workflow.updated_at,
        )

    except Exception as e:
        error_time = time.time() - start_time

        # Log workflow creation failure
        if logger:
            await logger.log_error(
                f"Workflow creation failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "workflow_lifecycle_management",
                    "workflow_type": request.workflow_type,
                    "workflow_name": request.name,
                    "actions_count": len(request.actions) if request.actions else 0,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "workflow_creation_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "workflow_creation_error",
                {
                    "request_id": request_id,
                    "operation": "workflow_lifecycle_management",
                    "workflow_type": request.workflow_type,
                    "workflow_name": request.name,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")


@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    workflow_id: str, request: ExecuteWorkflowRequest, container=Depends(get_workflow_container)
):
    """Execute a workflow."""
    start_time = time.time()
    request_id = f"workflow_execution_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Validate workflow_id matches
        if request.workflow_id != workflow_id:
            response_time = time.time() - start_time

            # Log workflow ID mismatch
            if logger:
                await logger.log_business_event(
                    "workflow_execution_rejected",
                    {
                        "request_id": request_id,
                        "workflow_id": workflow_id,
                        "operation": "workflow_execution_control",
                        "response_time_seconds": response_time,
                        "error_type": "workflow_id_mismatch",
                        "request_workflow_id": request.workflow_id,
                        "path_workflow_id": workflow_id,
                        "validation_failed": True,
                    },
                )

            raise HTTPException(status_code=400, detail="Workflow ID mismatch")

        # Log workflow execution start
        if logger:
            await logger.log_business_event(
                "workflow_execution_started",
                {
                    "request_id": request_id,
                    "workflow_id": workflow_id,
                    "operation": "workflow_execution_control",
                    "execution_priority": request.priority,
                    "parameters_count": len(request.parameters) if request.parameters else 0,
                    "user_initiated": bool(request.user_id),
                    "correlation_tracking": bool(request.correlation_id),
                    "orchestration_engine_execution": True,
                },
            )

            await logger.log_info(
                "Initiating workflow execution",
                {
                    "request_id": request_id,
                    "workflow_id": workflow_id,
                    "execution_priority": request.priority,
                    "user_id": request.user_id,
                    "correlation_id": request.correlation_id,
                    "parameters_provided": bool(request.parameters),
                    "orchestration_runtime_activated": True,
                },
            )

        # Create command
        from ....application.workflow_management.commands import ExecuteWorkflowCommand

        command = ExecuteWorkflowCommand(
            workflow_id=workflow_id,
            parameters=request.parameters,
            user_id=request.user_id,
            correlation_id=request.correlation_id,
            priority=request.priority,
        )

        # Execute use case
        result = await container.execute_workflow_use_case.execute(command)

        if not result.success:
            response_time = time.time() - start_time

            # Log workflow execution failed
            if logger:
                await logger.log_business_event(
                    "workflow_execution_failed",
                    {
                        "request_id": request_id,
                        "workflow_id": workflow_id,
                        "operation": "workflow_execution_control",
                        "response_time_seconds": response_time,
                        "error_message": result.error_message,
                        "execution_preparation_failed": True,
                    },
                )

            raise HTTPException(status_code=400, detail=result.error_message)

        # Convert to response
        execution_id = (
            result.execution.execution_id
            if hasattr(result.execution, "execution_id")
            else result.execution.get("execution_id")
        )
        response_time = time.time() - start_time

        # Log successful workflow execution initiation
        if logger:
            await logger.log_business_event(
                "workflow_execution_initiated",
                {
                    "request_id": request_id,
                    "workflow_id": workflow_id,
                    "execution_id": execution_id,
                    "operation": "workflow_execution_control",
                    "response_time_seconds": response_time,
                    "success": True,
                    "execution_priority": request.priority,
                    "execution_status": "running",
                    "orchestration_runtime_active": True,
                },
            )

            await logger.log_performance_metric(
                "workflow_execution_initiation",
                response_time,
                {
                    "request_id": request_id,
                    "workflow_id": workflow_id,
                    "execution_id": execution_id,
                    "execution_success": True,
                    "orchestration_startup_time": response_time,
                },
            )
        return WorkflowExecutionResponse(
            execution_id=result.execution.execution_id,
            workflow_id=result.execution.workflow_id,
            status=result.execution.status.value,
            parameters=result.execution.parameters,
            results=result.execution.results,
            started_at=result.execution.started_at,
            completed_at=result.execution.completed_at,
            duration_seconds=result.execution.duration_seconds,
            error_message=result.execution.error_message,
        )

    except Exception as e:
        error_time = time.time() - start_time

        # Log workflow execution failure
        if logger:
            await logger.log_error(
                f"Workflow execution failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "workflow_execution_control",
                    "workflow_id": workflow_id,
                    "execution_priority": request.priority,
                    "user_id": request.user_id,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "workflow_execution_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "workflow_execution_error",
                {
                    "request_id": request_id,
                    "operation": "workflow_execution_control",
                    "workflow_id": workflow_id,
                    "execution_priority": request.priority,
                    "user_id": request.user_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to execute workflow: {str(e)}")


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(workflow_id: str, container=Depends(get_workflow_container)):
    """Get a workflow by ID."""
    start_time = time.time()
    request_id = f"workflow_retrieval_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log workflow retrieval start
        if logger:
            await logger.log_business_event(
                "workflow_retrieval_started",
                {
                    "request_id": request_id,
                    "workflow_id": workflow_id,
                    "operation": "workflow_definition_access",
                    "data_scope": "workflow_configuration",
                    "workflow_cache_access": True,
                },
            )

            await logger.log_info(
                "Retrieving workflow definition",
                {
                    "request_id": request_id,
                    "workflow_id": workflow_id,
                    "access_mode": "workflow_metadata_retrieval",
                    "configuration_access": True,
                },
            )

        # Create query
        from ....application.workflow_management.queries import GetWorkflowQuery

        query = GetWorkflowQuery(workflow_id=workflow_id)

        # Execute use case
        result = await container.get_workflow_use_case.execute(query)

        if not result.success:
            response_time = time.time() - start_time

            if "not found" in result.error_message.lower():
                # Log workflow not found
                if logger:
                    await logger.log_business_event(
                        "workflow_not_found",
                        {
                            "request_id": request_id,
                            "workflow_id": workflow_id,
                            "operation": "workflow_definition_access",
                            "response_time_seconds": response_time,
                            "result_status": "not_found",
                            "workflow_lookup_failed": True,
                        },
                    )

                raise HTTPException(status_code=404, detail=result.error_message)

            # Log other workflow retrieval errors
            if logger:
                await logger.log_business_event(
                    "workflow_retrieval_failed",
                    {
                        "request_id": request_id,
                        "workflow_id": workflow_id,
                        "operation": "workflow_definition_access",
                        "response_time_seconds": response_time,
                        "error_message": result.error_message,
                        "workflow_access_denied": True,
                    },
                )

            raise HTTPException(status_code=400, detail=result.error_message)

        # Convert to response
        response_time = time.time() - start_time

        # Log successful workflow retrieval
        if logger:
            await logger.log_business_event(
                "workflow_retrieved",
                {
                    "request_id": request_id,
                    "workflow_id": workflow_id,
                    "operation": "workflow_definition_access",
                    "response_time_seconds": response_time,
                    "success": True,
                    "workflow_type": result.workflow.workflow_type,
                    "workflow_status": str(result.workflow.status),
                    "actions_count": len(result.workflow.actions) if result.workflow.actions else 0,
                    "cache_hit": True,
                },
            )

            await logger.log_performance_metric(
                "workflow_retrieval",
                response_time,
                {
                    "request_id": request_id,
                    "workflow_id": workflow_id,
                    "retrieval_success": True,
                    "workflow_access_time": response_time,
                },
            )

        return WorkflowResponse(
            workflow_id=result.workflow.workflow_id,
            name=result.workflow.name,
            description=result.workflow.description,
            workflow_type=result.workflow.workflow_type,
            status=result.workflow.status,
            parameters=result.workflow.parameters,
            actions=result.workflow.actions,
            tags=result.workflow.tags,
            created_at=result.workflow.created_at,
            updated_at=result.workflow.updated_at,
        )

    except HTTPException:
        raise
    except Exception as e:
        error_time = time.time() - start_time

        # Log workflow retrieval failure
        if logger:
            await logger.log_error(
                f"Workflow retrieval failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "workflow_definition_access",
                    "workflow_id": workflow_id,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "workflow_retrieval_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "workflow_retrieval_error",
                {
                    "request_id": request_id,
                    "operation": "workflow_definition_access",
                    "workflow_id": workflow_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to get workflow: {str(e)}")


@router.get("", response_model=WorkflowListResponse)
async def list_workflows(
    workflow_type: Optional[str] = None, limit: int = 50, offset: int = 0, container=Depends(get_workflow_container)
):
    """List workflows with optional filtering."""
    start_time = time.time()
    request_id = f"workflows_listing_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log workflows listing start
        if logger:
            filters_applied = bool(workflow_type)
            await logger.log_business_event(
                "workflows_listing_started",
                {
                    "request_id": request_id,
                    "operation": "workflow_inventory_management",
                    "query_type": "workflow_list",
                    "pagination_enabled": True,
                    "filters_applied": filters_applied,
                    "workflow_type_filter": workflow_type,
                    "limit": limit,
                    "offset": offset,
                },
            )

            await logger.log_info(
                "Listing workflow definitions",
                {
                    "request_id": request_id,
                    "pagination_limit": limit,
                    "pagination_offset": offset,
                    "filters_active": filters_applied,
                    "inventory_scope": "filtered_workflows" if filters_applied else "all_workflows",
                },
            )

        # Create query
        from ....application.workflow_management.queries import ListWorkflowsQuery

        query = ListWorkflowsQuery(
            name_filter=workflow_type, limit=limit, offset=offset  # Use workflow_type as name filter
        )

        # Execute use case
        workflows = await container.list_workflows_use_case.execute(query)

        # Convert to response
        workflow_responses = []
        for workflow in workflows:
            workflow_responses.append(
                WorkflowResponse(
                    workflow_id=workflow.workflow_id,
                    name=workflow.name,
                    description=workflow.description,
                    workflow_type=workflow.workflow_type,
                    status=workflow.status,
                    parameters=workflow.parameters,
                    actions=workflow.actions,
                    tags=workflow.tags,
                    created_at=workflow.created_at,
                    updated_at=workflow.updated_at,
                )
            )

        response_time = time.time() - start_time

        # Log successful workflows listing
        if logger:
            await logger.log_business_event(
                "workflows_listed",
                {
                    "request_id": request_id,
                    "operation": "workflow_inventory_management",
                    "response_time_seconds": response_time,
                    "success": True,
                    "workflows_returned": len(workflow_responses),
                    "filters_applied": filters_applied,
                    "limit": limit,
                    "offset": offset,
                    "total_available": len(workflow_responses),
                },
            )

            await logger.log_performance_metric(
                "workflows_listing",
                response_time,
                {
                    "request_id": request_id,
                    "workflows_returned": len(workflow_responses),
                    "filters_used": filters_applied,
                    "listing_success": True,
                },
            )

        return WorkflowListResponse(
            workflows=workflow_responses,
            total=len(workflow_responses),  # For now, just return the count
            limit=limit,
            offset=offset,
        )

    except Exception as e:
        error_time = time.time() - start_time

        # Log workflows listing failure
        if logger:
            await logger.log_error(
                f"Workflows listing failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "workflow_inventory_management",
                    "workflow_type_filter": workflow_type,
                    "limit": limit,
                    "offset": offset,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "workflows_listing_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "workflows_listing_failed",
                {
                    "request_id": request_id,
                    "operation": "workflow_inventory_management",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to list workflows: {str(e)}")


@router.get("/executions", response_model=ExecutionListResponse)
async def list_executions(
    workflow_id: Optional[str] = None, limit: int = 50, offset: int = 0, container=Depends(get_workflow_container)
):
    """List workflow executions with optional filtering."""
    start_time = time.time()
    request_id = f"executions_listing_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log executions listing start
        if logger:
            filters_applied = bool(workflow_id)
            await logger.log_business_event(
                "executions_listing_started",
                {
                    "request_id": request_id,
                    "operation": "workflow_execution_history",
                    "query_type": "execution_list",
                    "pagination_enabled": True,
                    "filters_applied": filters_applied,
                    "workflow_id_filter": workflow_id,
                    "limit": limit,
                    "offset": offset,
                },
            )

            await logger.log_info(
                "Listing workflow execution history",
                {
                    "request_id": request_id,
                    "pagination_limit": limit,
                    "pagination_offset": offset,
                    "filters_active": filters_applied,
                    "history_scope": "single_workflow_executions" if filters_applied else "all_workflow_executions",
                },
            )

        # Create query
        from ....application.workflow_management.queries import ListWorkflowExecutionsQuery

        query = ListWorkflowExecutionsQuery(workflow_id=workflow_id, limit=limit, offset=offset)

        # Execute use case
        result = await container.list_workflow_executions_use_case.execute(query)

        if not result.success:
            response_time = time.time() - start_time

            # Log executions listing failed
            if logger:
                await logger.log_business_event(
                    "executions_listing_failed",
                    {
                        "request_id": request_id,
                        "operation": "workflow_execution_history",
                        "response_time_seconds": response_time,
                        "error_message": result.error_message,
                        "execution_history_access_denied": True,
                    },
                )

            raise HTTPException(status_code=400, detail=result.error_message)

        # Convert to response
        executions = []
        for execution in result.executions:
            executions.append(
                WorkflowExecutionResponse(
                    execution_id=execution.execution_id,
                    workflow_id=execution.workflow_id,
                    status=execution.status.value,
                    parameters=execution.parameters,
                    results=execution.results,
                    started_at=execution.started_at,
                    completed_at=execution.completed_at,
                    duration_seconds=execution.duration_seconds,
                    error_message=execution.error_message,
                )
            )

        response_time = time.time() - start_time

        # Log successful executions listing
        if logger:
            await logger.log_business_event(
                "executions_listed",
                {
                    "request_id": request_id,
                    "operation": "workflow_execution_history",
                    "response_time_seconds": response_time,
                    "success": True,
                    "executions_returned": len(executions),
                    "filters_applied": filters_applied,
                    "limit": limit,
                    "offset": offset,
                    "total_available": result.total,
                },
            )

            await logger.log_performance_metric(
                "executions_listing",
                response_time,
                {
                    "request_id": request_id,
                    "executions_returned": len(executions),
                    "filters_used": filters_applied,
                    "listing_success": True,
                },
            )

        return ExecutionListResponse(executions=executions, total=result.total, limit=limit, offset=offset)

    except Exception as e:
        error_time = time.time() - start_time

        # Log executions listing failure
        if logger:
            await logger.log_error(
                f"Executions listing failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "workflow_execution_history",
                    "workflow_id_filter": workflow_id,
                    "limit": limit,
                    "offset": offset,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "executions_listing_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "executions_listing_failed",
                {
                    "request_id": request_id,
                    "operation": "workflow_execution_history",
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to list executions: {str(e)}")


@router.get("/executions/{execution_id}", response_model=WorkflowExecutionResponse)
async def get_execution(execution_id: str, container=Depends(get_workflow_container)):
    """Get a workflow execution by ID."""
    start_time = time.time()
    request_id = f"execution_detail_{int(time.time() * 1000)}"
    logger = await get_logger_client()

    try:
        # Log execution detail retrieval start
        if logger:
            await logger.log_business_event(
                "execution_detail_started",
                {
                    "request_id": request_id,
                    "execution_id": execution_id,
                    "operation": "workflow_execution_monitoring",
                    "query_type": "execution_detail",
                    "data_scope": "single_execution_lifecycle",
                },
            )

            await logger.log_info(
                "Retrieving workflow execution details",
                {
                    "request_id": request_id,
                    "execution_id": execution_id,
                    "detail_level": "full_execution_lifecycle",
                    "includes_performance_data": True,
                    "includes_error_context": True,
                },
            )

        # Create query
        from ....application.workflow_management.queries import GetWorkflowExecutionQuery

        query = GetWorkflowExecutionQuery(execution_id=execution_id)

        # Execute use case
        result = await container.get_workflow_execution_use_case.execute(query)

        if not result.success:
            response_time = time.time() - start_time

            if "not found" in result.error_message.lower():
                # Log execution not found
                if logger:
                    await logger.log_business_event(
                        "execution_not_found",
                        {
                            "request_id": request_id,
                            "execution_id": execution_id,
                            "operation": "workflow_execution_monitoring",
                            "response_time_seconds": response_time,
                            "result_status": "not_found",
                            "execution_lookup_failed": True,
                        },
                    )

                raise HTTPException(status_code=404, detail=result.error_message)

            # Log other execution retrieval errors
            if logger:
                await logger.log_business_event(
                    "execution_detail_failed",
                    {
                        "request_id": request_id,
                        "execution_id": execution_id,
                        "operation": "workflow_execution_monitoring",
                        "response_time_seconds": response_time,
                        "error_message": result.error_message,
                        "execution_access_denied": True,
                    },
                )

            raise HTTPException(status_code=400, detail=result.error_message)

        # Convert to response
        response_time = time.time() - start_time

        # Log successful execution detail retrieval
        if logger:
            await logger.log_business_event(
                "execution_detail_retrieved",
                {
                    "request_id": request_id,
                    "execution_id": execution_id,
                    "operation": "workflow_execution_monitoring",
                    "response_time_seconds": response_time,
                    "success": True,
                    "workflow_id": result.execution.workflow_id,
                    "execution_status": result.execution.status.value,
                    "execution_duration": result.execution.duration_seconds,
                    "has_results": bool(result.execution.results),
                    "has_errors": bool(result.execution.error_message),
                },
            )

            await logger.log_performance_metric(
                "execution_detail_retrieval",
                response_time,
                {
                    "request_id": request_id,
                    "execution_id": execution_id,
                    "retrieval_success": True,
                    "execution_access_time": response_time,
                },
            )

        return WorkflowExecutionResponse(
            execution_id=result.execution.execution_id,
            workflow_id=result.execution.workflow_id,
            status=result.execution.status.value,
            parameters=result.execution.parameters,
            results=result.execution.results,
            started_at=result.execution.started_at,
            completed_at=result.execution.completed_at,
            duration_seconds=result.execution.duration_seconds,
            error_message=result.execution.error_message,
        )

    except HTTPException:
        raise
    except Exception as e:
        error_time = time.time() - start_time

        # Log execution detail retrieval failure
        if logger:
            await logger.log_error(
                f"Execution detail retrieval failed: {str(e)}",
                {
                    "request_id": request_id,
                    "operation": "workflow_execution_monitoring",
                    "execution_id": execution_id,
                    "error_type": type(e).__name__,
                    "response_time_seconds": error_time,
                    "execution_detail_failed": True,
                },
                error=e,
            )

            await logger.log_business_event(
                "execution_detail_error",
                {
                    "request_id": request_id,
                    "operation": "workflow_execution_monitoring",
                    "execution_id": execution_id,
                    "error_type": type(e).__name__,
                    "error_message": str(e),
                    "response_time_seconds": error_time,
                },
            )

        raise HTTPException(status_code=500, detail=f"Failed to get execution: {str(e)}")
