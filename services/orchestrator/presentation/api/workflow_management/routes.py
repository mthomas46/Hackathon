"""Workflow Management API Routes"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from .dtos import (
    CreateWorkflowRequest, ExecuteWorkflowRequest, GetWorkflowRequest,
    ListWorkflowsRequest, WorkflowResponse, WorkflowExecutionResponse,
    WorkflowListResponse, ExecutionListResponse
)

# Import domain/application services (will be injected via dependency injection)
# These will be available through the container in main.py

router = APIRouter()


def get_workflow_container():
    """Dependency injection for workflow management services."""
    # This will be replaced with actual dependency injection in main.py
    from ...container import get_container
    container = get_container()
    return container


@router.post("", response_model=WorkflowResponse)
async def create_workflow(
    request: CreateWorkflowRequest,
    container = Depends(get_workflow_container)
):
    """Create a new workflow."""
    try:
        # Create command
        from ....application.workflow_management.commands import CreateWorkflowCommand

        command = CreateWorkflowCommand(
            name=request.name,
            description=request.description,
            workflow_type=request.workflow_type,
            parameters=request.parameters,
            actions=request.actions,
            tags=request.tags
        )

        # Execute use case
        result = await container.create_workflow_use_case.execute(command)

        if not result.success:
            raise HTTPException(status_code=400, detail=result.error_message)

        # Convert to response
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
            updated_at=result.workflow.updated_at
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")


@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    workflow_id: str,
    request: ExecuteWorkflowRequest,
    container = Depends(get_workflow_container)
):
    """Execute a workflow."""
    try:
        # Validate workflow_id matches
        if request.workflow_id != workflow_id:
            raise HTTPException(status_code=400, detail="Workflow ID mismatch")

        # Create command
        from ....application.workflow_management.commands import ExecuteWorkflowCommand

        command = ExecuteWorkflowCommand(
            workflow_id=workflow_id,
            parameters=request.parameters,
            user_id=request.user_id,
            correlation_id=request.correlation_id,
            priority=request.priority
        )

        # Execute use case
        result = await container.execute_workflow_use_case.execute(command)

        if not result.success:
            raise HTTPException(status_code=400, detail=result.error_message)

        # Convert to response
        return WorkflowExecutionResponse(
            execution_id=result.execution.execution_id,
            workflow_id=result.execution.workflow_id,
            status=result.execution.status.value,
            parameters=result.execution.parameters,
            results=result.execution.results,
            started_at=result.execution.started_at,
            completed_at=result.execution.completed_at,
            duration_seconds=result.execution.duration_seconds,
            error_message=result.execution.error_message
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to execute workflow: {str(e)}")


@router.get("/{workflow_id}", response_model=WorkflowResponse)
async def get_workflow(
    workflow_id: str,
    container = Depends(get_workflow_container)
):
    """Get a workflow by ID."""
    try:
        # Create query
        from ....application.workflow_management.queries import GetWorkflowQuery

        query = GetWorkflowQuery(workflow_id=workflow_id)

        # Execute use case
        result = await container.get_workflow_use_case.execute(query)

        if not result.success:
            if "not found" in result.error_message.lower():
                raise HTTPException(status_code=404, detail=result.error_message)
            raise HTTPException(status_code=400, detail=result.error_message)

        # Convert to response
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
            updated_at=result.workflow.updated_at
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get workflow: {str(e)}")


@router.get("", response_model=WorkflowListResponse)
async def list_workflows(
    workflow_type: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    container = Depends(get_workflow_container)
):
    """List workflows with optional filtering."""
    try:
        # Create query
        from ....application.workflow_management.queries import ListWorkflowsQuery

        query = ListWorkflowsQuery(
            name_filter=workflow_type,  # Use workflow_type as name filter
            limit=limit,
            offset=offset
        )

        # Execute use case
        workflows = await container.list_workflows_use_case.execute(query)

        # Convert to response
        workflow_responses = []
        for workflow in workflows:
            workflow_responses.append(WorkflowResponse(
                workflow_id=workflow.workflow_id,
                name=workflow.name,
                description=workflow.description,
                workflow_type=workflow.workflow_type,
                status=workflow.status,
                parameters=workflow.parameters,
                actions=workflow.actions,
                tags=workflow.tags,
                created_at=workflow.created_at,
                updated_at=workflow.updated_at
            ))

        return WorkflowListResponse(
            workflows=workflow_responses,
            total=len(workflow_responses),  # For now, just return the count
            limit=limit,
            offset=offset
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list workflows: {str(e)}")


@router.get("/executions", response_model=ExecutionListResponse)
async def list_executions(
    workflow_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    container = Depends(get_workflow_container)
):
    """List workflow executions with optional filtering."""
    try:
        # Create query
        from ....application.workflow_management.queries import ListWorkflowExecutionsQuery

        query = ListWorkflowExecutionsQuery(
            workflow_id=workflow_id,
            limit=limit,
            offset=offset
        )

        # Execute use case
        result = await container.list_workflow_executions_use_case.execute(query)

        if not result.success:
            raise HTTPException(status_code=400, detail=result.error_message)

        # Convert to response
        executions = []
        for execution in result.executions:
            executions.append(WorkflowExecutionResponse(
                execution_id=execution.execution_id,
                workflow_id=execution.workflow_id,
                status=execution.status.value,
                parameters=execution.parameters,
                results=execution.results,
                started_at=execution.started_at,
                completed_at=execution.completed_at,
                duration_seconds=execution.duration_seconds,
                error_message=execution.error_message
            ))

        return ExecutionListResponse(
            executions=executions,
            total=result.total,
            limit=limit,
            offset=offset
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list executions: {str(e)}")


@router.get("/executions/{execution_id}", response_model=WorkflowExecutionResponse)
async def get_execution(
    execution_id: str,
    container = Depends(get_workflow_container)
):
    """Get a workflow execution by ID."""
    try:
        # Create query
        from ....application.workflow_management.queries import GetWorkflowExecutionQuery

        query = GetWorkflowExecutionQuery(execution_id=execution_id)

        # Execute use case
        result = await container.get_workflow_execution_use_case.execute(query)

        if not result.success:
            if "not found" in result.error_message.lower():
                raise HTTPException(status_code=404, detail=result.error_message)
            raise HTTPException(status_code=400, detail=result.error_message)

        # Convert to response
        return WorkflowExecutionResponse(
            execution_id=result.execution.execution_id,
            workflow_id=result.execution.workflow_id,
            status=result.execution.status.value,
            parameters=result.execution.parameters,
            results=result.execution.results,
            started_at=result.execution.started_at,
            completed_at=result.execution.completed_at,
            duration_seconds=result.execution.duration_seconds,
            error_message=result.execution.error_message
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get execution: {str(e)}")
