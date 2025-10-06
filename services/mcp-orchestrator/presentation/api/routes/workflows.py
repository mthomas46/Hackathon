"""Workflow API routes."""

import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status

from services.mcp_orchestrator.application.dto.create_workflow_request import CreateWorkflowRequest
from services.mcp_orchestrator.application.dto.execute_workflow_request import ExecuteWorkflowRequest
from services.mcp_orchestrator.application.use_cases.create_workflow_use_case import CreateWorkflowUseCase
from services.mcp_orchestrator.application.use_cases.execute_workflow_use_case import ExecuteWorkflowUseCase
from services.mcp_orchestrator.application.use_cases.get_workflow_use_case import GetWorkflowUseCase
from services.mcp_orchestrator.presentation.api.models.requests import (
    CreateWorkflowRequestModel,
    ExecuteWorkflowRequestModel,
)
from services.mcp_orchestrator.presentation.api.models.responses import (
    WorkflowResponseModel,
    WorkflowSummaryResponseModel,
    ExecutionResultModel,
)
from services.mcp_orchestrator.presentation.dependencies import (
    get_create_workflow_use_case,
    get_execute_workflow_use_case,
    get_get_workflow_use_case,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/workflows", tags=["Workflows"])


@router.post(
    "",
    response_model=WorkflowResponseModel,
    status_code=status.HTTP_201_CREATED,
    summary="Create Workflow",
    description="Create and plan a new workflow from a natural language query"
)
async def create_workflow(
    request: CreateWorkflowRequestModel,
    use_case: CreateWorkflowUseCase = Depends(get_create_workflow_use_case)
) -> WorkflowResponseModel:
    """Create a new workflow with intelligent planning."""
    try:
        # Convert API model to DTO
        dto = CreateWorkflowRequest(
            original_query=request.original_query,
            parsed_query_id=request.parsed_query_id,
            query_intent=request.query_intent,
            query_complexity=request.query_complexity,
            required_tiers=request.required_tiers,
            user_id=request.user_id,
            session_id=request.session_id,
            execution_strategy=request.execution_strategy,
            patterns_to_apply=request.patterns_to_apply,
            max_duration_seconds=request.max_duration_seconds,
            max_cost=request.max_cost,
            requires_approval=request.requires_approval,
            client_ids=request.client_ids,
            project_ids=request.project_ids,
            team_ids=request.team_ids,
            context=request.context,
            metadata=request.metadata,
        )
        
        # Execute use case
        response = await use_case.execute(dto)
        
        # Convert DTO to API model
        return WorkflowResponseModel(**response.to_dict())
        
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error creating workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create workflow"
        )


@router.post(
    "/{workflow_id}/execute",
    response_model=ExecutionResultModel,
    status_code=status.HTTP_200_OK,
    summary="Execute Workflow",
    description="Execute a workflow with the configured execution plan"
)
async def execute_workflow(
    workflow_id: str,
    request: ExecuteWorkflowRequestModel,
    use_case: ExecuteWorkflowUseCase = Depends(get_execute_workflow_use_case)
) -> ExecutionResultModel:
    """Execute a workflow."""
    try:
        # Validate workflow_id matches
        if request.workflow_id != workflow_id:
            raise ValueError("Workflow ID mismatch")
        
        # Convert API model to DTO
        dto = ExecuteWorkflowRequest(
            workflow_id=workflow_id,
            async_execution=request.async_execution,
            notify_on_completion=request.notify_on_completion,
            stream_progress=request.stream_progress,
            override_strategy=request.override_strategy,
            override_patterns=request.override_patterns,
            max_retries=request.max_retries,
            approval_token=request.approval_token,
            approved_by=request.approved_by,
            execution_context=request.execution_context,
        )
        
        # Execute use case
        result = await use_case.execute(dto)
        
        # Convert DTO to API model
        return ExecutionResultModel(**result.to_dict())
        
    except ValueError as e:
        logger.warning(f"Validation error: {e}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"Error executing workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to execute workflow"
        )


@router.get(
    "/{workflow_id}",
    response_model=WorkflowResponseModel,
    status_code=status.HTTP_200_OK,
    summary="Get Workflow",
    description="Get workflow details by ID"
)
async def get_workflow(
    workflow_id: str,
    use_case: GetWorkflowUseCase = Depends(get_get_workflow_use_case)
) -> WorkflowResponseModel:
    """Get workflow by ID."""
    try:
        response = await use_case.execute(workflow_id)
        
        if not response:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Workflow {workflow_id} not found"
            )
        
        return WorkflowResponseModel(**response.to_dict())
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting workflow: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get workflow"
        )


@router.get(
    "/user/{user_id}",
    response_model=List[WorkflowSummaryResponseModel],
    status_code=status.HTTP_200_OK,
    summary="Get User Workflows",
    description="Get all workflows for a user"
)
async def get_user_workflows(
    user_id: str,
    limit: Optional[int] = None,
    use_case: GetWorkflowUseCase = Depends(get_get_workflow_use_case)
) -> List[WorkflowSummaryResponseModel]:
    """Get user's workflows."""
    try:
        summaries = await use_case.get_user_workflows(user_id, limit)
        return [WorkflowSummaryResponseModel(**s.to_dict()) for s in summaries]
        
    except Exception as e:
        logger.error(f"Error getting user workflows: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get user workflows"
        )


@router.get(
    "",
    response_model=List[WorkflowSummaryResponseModel],
    status_code=status.HTTP_200_OK,
    summary="Get Active Workflows",
    description="Get all active workflows"
)
async def get_active_workflows(
    limit: Optional[int] = None,
    use_case: GetWorkflowUseCase = Depends(get_get_workflow_use_case)
) -> List[WorkflowSummaryResponseModel]:
    """Get active workflows."""
    try:
        summaries = await use_case.get_active_workflows(limit)
        return [WorkflowSummaryResponseModel(**s.to_dict()) for s in summaries]
        
    except Exception as e:
        logger.error(f"Error getting active workflows: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get active workflows"
        )

