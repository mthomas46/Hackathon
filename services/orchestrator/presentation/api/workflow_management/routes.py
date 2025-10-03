"""Workflow Management API Routes"""

from fastapi import APIRouter, HTTPException, Depends
from typing import Optional
from datetime import datetime
import uuid
import os

from .dtos import (
    CreateWorkflowRequest, ExecuteWorkflowRequest, GetWorkflowRequest,
    ListWorkflowsRequest, WorkflowResponse, WorkflowExecutionResponse,
    WorkflowListResponse, ExecutionListResponse
)

# Import WorkflowLogger for comprehensive logging
try:
    from services.shared.infrastructure.logging.workflow_logger import WorkflowLogger
    
    workflow_logger = WorkflowLogger(
        service_name="orchestrator",
        log_collector_url=os.getenv("LOG_COLLECTOR_URL", "http://log-collector:5040"),
        fail_silently=True,
        enable_performance_metrics=True
    )
except Exception as e:
    print(f"Warning: WorkflowLogger initialization failed: {e}")
    workflow_logger = None

# Import domain/application services (will be injected via dependency injection)
# These will be available through the container in main.py

router = APIRouter()


def get_workflow_container():
    """Dependency injection for workflow management services."""
    # This will be replaced with actual dependency injection in main.py
    from ....main import container
    return container


@router.post("", response_model=WorkflowResponse)
async def create_workflow(
    request: CreateWorkflowRequest,
    container = Depends(get_workflow_container)
):
    """Create a new workflow with full logging support."""
    # Generate workflow tracking ID
    workflow_id_tracking = f"wf-create-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
    start_time = datetime.utcnow()
    
    # Log workflow creation start
    if workflow_logger:
        try:
            await workflow_logger.log_workflow_start(
                workflow_id=workflow_id_tracking,
                operation="workflow_creation",
                context={
                    "workflow_name": request.name,
                    "workflow_type": request.workflow_type,
                    "actions_count": len(request.actions) if request.actions else 0,
                    "parameters_count": len(request.parameters) if request.parameters else 0
                }
            )
        except Exception as e:
            print(f"Logging failed: {e}")
    
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

        # Log command creation
        if workflow_logger:
            await workflow_logger.log_workflow_step(
                workflow_id=workflow_id_tracking,
                step_name="create_workflow_command",
                step_data={
                    "workflow_name": request.name,
                    "workflow_type": request.workflow_type
                }
            )

        # Execute use case
        result = await container.create_workflow_use_case.execute(command)

        if not result.success:
            # Log failure
            if workflow_logger:
                await workflow_logger.log_error(
                    workflow_id=workflow_id_tracking,
                    error=Exception(result.error_message),
                    context={"stage": "workflow_creation", "use_case": "CreateWorkflowUseCase"}
                )
            raise HTTPException(status_code=400, detail=result.error_message)

        # Log successful creation
        if workflow_logger:
            await workflow_logger.log_workflow_step(
                workflow_id=workflow_id_tracking,
                step_name="workflow_created",
                step_data={
                    "created_workflow_id": str(result.workflow.workflow_id),
                    "workflow_status": str(result.workflow.status)
                }
            )

        # Convert to response
        response = WorkflowResponse(
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
        
        # Log completion
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        if workflow_logger:
            await workflow_logger.log_workflow_complete(
                workflow_id=workflow_id_tracking,
                duration_ms=duration_ms,
                success=True,
                metrics={
                    "workflow_id": str(result.workflow.workflow_id),
                    "actions_count": len(result.workflow.actions) if result.workflow.actions else 0
                }
            )
        
        return response

    except HTTPException:
        raise
    except Exception as e:
        # Log error
        if workflow_logger:
            await workflow_logger.log_error(
                workflow_id=workflow_id_tracking,
                error=e,
                context={"endpoint": "/workflows", "operation": "create"}
            )
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")


@router.post("/{workflow_id}/execute", response_model=WorkflowExecutionResponse)
async def execute_workflow(
    workflow_id: str,
    request: ExecuteWorkflowRequest,
    container = Depends(get_workflow_container)
):
    """Execute a workflow with comprehensive logging and tracking."""
    # Use correlation_id as workflow_id if provided, otherwise generate new one
    workflow_id_tracking = request.correlation_id if request.correlation_id else f"wf-exec-{datetime.utcnow().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"
    start_time = datetime.utcnow()
    
    # Log workflow execution start
    if workflow_logger:
        try:
            await workflow_logger.log_workflow_start(
                workflow_id=workflow_id_tracking,
                operation="workflow_execution",
                context={
                    "workflow_id": workflow_id,
                    "user_id": request.user_id,
                    "parameters_count": len(request.parameters) if request.parameters else 0,
                    "priority": request.priority
                },
                user_id=request.user_id
            )
        except Exception as e:
            print(f"Logging failed: {e}")
    
    try:
        # Validate workflow_id matches
        if request.workflow_id != workflow_id:
            if workflow_logger:
                await workflow_logger.log_error(
                    workflow_id=workflow_id_tracking,
                    error=ValueError("Workflow ID mismatch"),
                    context={"expected": workflow_id, "received": request.workflow_id}
                )
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

        # Log command creation
        if workflow_logger:
            await workflow_logger.log_workflow_step(
                workflow_id=workflow_id_tracking,
                step_name="create_execution_command",
                step_data={
                    "workflow_id": workflow_id,
                    "correlation_id": request.correlation_id
                }
            )

        # Execute use case
        if workflow_logger:
            await workflow_logger.log_workflow_step(
                workflow_id=workflow_id_tracking,
                step_name="execute_workflow_use_case_start",
                step_data={"workflow_id": workflow_id}
            )
        
        result = await container.execute_workflow_use_case.execute(command)

        if not result.success:
            # Log failure
            if workflow_logger:
                await workflow_logger.log_error(
                    workflow_id=workflow_id_tracking,
                    error=Exception(result.error_message),
                    context={"stage": "workflow_execution", "use_case": "ExecuteWorkflowUseCase"}
                )
            raise HTTPException(status_code=400, detail=result.error_message)

        # Log successful execution
        if workflow_logger:
            await workflow_logger.log_workflow_step(
                workflow_id=workflow_id_tracking,
                step_name="workflow_executed",
                step_data={
                    "execution_id": str(result.execution.execution_id),
                    "status": result.execution.status.value,
                    "has_results": bool(result.execution.results)
                }
            )

        # Convert to response
        response = WorkflowExecutionResponse(
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
        
        # Log completion with performance metrics
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        if workflow_logger:
            await workflow_logger.log_workflow_complete(
                workflow_id=workflow_id_tracking,
                duration_ms=duration_ms,
                success=True,
                metrics={
                    "execution_id": str(result.execution.execution_id),
                    "execution_duration_seconds": result.execution.duration_seconds,
                    "status": result.execution.status.value,
                    "results_count": len(result.execution.results) if result.execution.results else 0
                }
            )
            
            # Also log as performance metric
            await workflow_logger.log_performance_metric(
                workflow_id=workflow_id_tracking,
                metric_name="workflow_execution_time",
                metric_value=duration_ms,
                unit="ms",
                context={
                    "workflow_id": workflow_id,
                    "execution_id": str(result.execution.execution_id)
                }
            )
        
        return response

    except HTTPException:
        raise
    except Exception as e:
        # Log error
        if workflow_logger:
            await workflow_logger.log_error(
                workflow_id=workflow_id_tracking,
                error=e,
                context={"endpoint": f"/workflows/{workflow_id}/execute", "operation": "execute"}
            )
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
