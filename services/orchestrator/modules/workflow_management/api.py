#!/usr/bin/env python3
"""
Workflow Management API

REST API endpoints for workflow management operations.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime

from fastapi import APIRouter, HTTPException, BackgroundTasks, Query, Body
from pydantic import BaseModel, Field

from services.orchestrator.modules.workflow_management.service import WorkflowManagementService
from services.orchestrator.modules.workflow_management.models import (
    WorkflowDefinition, WorkflowExecution, WorkflowStatus, WorkflowExecutionStatus,
    WORKFLOW_TEMPLATES
)
from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget


# Pydantic models for API requests/responses

class WorkflowParameterModel(BaseModel):
    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type (string, integer, float, boolean, array, object)")
    description: str = Field("", description="Parameter description")
    required: bool = Field(True, description="Whether parameter is required")
    default_value: Optional[Any] = Field(None, description="Default value")
    validation_rules: Dict[str, Any] = Field(default_factory=dict, description="Validation rules")
    allowed_values: Optional[List[Any]] = Field(None, description="Allowed values")


class WorkflowActionModel(BaseModel):
    action_type: str = Field(..., description="Action type")
    name: str = Field(..., description="Action name")
    description: str = Field("", description="Action description")
    config: Dict[str, Any] = Field(..., description="Action configuration")
    condition: Optional[str] = Field(None, description="Conditional execution expression")
    depends_on: List[str] = Field(default_factory=list, description="Action dependencies")
    retry_count: int = Field(0, description="Number of retries")
    retry_delay: float = Field(1.0, description="Delay between retries")
    timeout_seconds: int = Field(30, description="Action timeout")


class WorkflowCreateRequest(BaseModel):
    name: str = Field(..., description="Workflow name")
    description: str = Field("", description="Workflow description")
    tags: List[str] = Field(default_factory=list, description="Workflow tags")
    parameters: List[WorkflowParameterModel] = Field(default_factory=list, description="Workflow parameters")
    actions: List[WorkflowActionModel] = Field(default_factory=list, description="Workflow actions")
    timeout_seconds: int = Field(300, description="Workflow timeout")
    notify_on_completion: bool = Field(False, description="Send notifications on completion")
    notification_channels: List[str] = Field(default_factory=list, description="Notification channels")


class WorkflowUpdateRequest(BaseModel):
    name: Optional[str] = Field(None, description="Workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    tags: Optional[List[str]] = Field(None, description="Workflow tags")
    status: Optional[str] = Field(None, description="Workflow status")
    parameters: Optional[List[WorkflowParameterModel]] = Field(None, description="Workflow parameters")
    actions: Optional[List[WorkflowActionModel]] = Field(None, description="Workflow actions")


class WorkflowExecuteRequest(BaseModel):
    parameters: Dict[str, Any] = Field(..., description="Execution parameters")


class WorkflowTemplateCreateRequest(BaseModel):
    template_name: str = Field(..., description="Template name")
    customizations: Dict[str, Any] = Field(default_factory=dict, description="Template customizations")


class WorkflowListResponse(BaseModel):
    workflows: List[Dict[str, Any]] = Field(..., description="List of workflows")
    total: int = Field(..., description="Total number of workflows")
    page: int = Field(1, description="Current page")
    page_size: int = Field(50, description="Page size")


class WorkflowExecutionResponse(BaseModel):
    execution_id: str = Field(..., description="Execution ID")
    workflow_id: str = Field(..., description="Workflow ID")
    status: str = Field(..., description="Execution status")
    started_at: Optional[str] = Field(None, description="Start time")
    completed_at: Optional[str] = Field(None, description="Completion time")
    execution_time_seconds: float = Field(0.0, description="Execution time")
    input_parameters: Dict[str, Any] = Field(..., description="Input parameters")
    action_results: Dict[str, Any] = Field(default_factory=dict, description="Action results")
    output_data: Dict[str, Any] = Field(default_factory=dict, description="Output data")
    error_message: Optional[str] = Field(None, description="Error message")


# Global service instance
workflow_service = WorkflowManagementService()

# API Router
router = APIRouter(prefix="/workflows", tags=["Workflow Management"])


# Workflow Definition Endpoints

@router.post("/", response_model=Dict[str, Any])
async def create_workflow(
    request: WorkflowCreateRequest,
    background_tasks: BackgroundTasks,
    created_by: str = "api_user"
) -> Dict[str, Any]:
    """Create a new workflow definition."""
    try:
        # Convert request to dictionary
        workflow_data = request.dict()

        # Create workflow
        success, message, workflow = await workflow_service.create_workflow(workflow_data, created_by)

        if not success:
            raise HTTPException(status_code=400, detail=message)

        # Schedule cleanup task
        background_tasks.add_task(workflow_service.cleanup_completed_executions)

        return {
            "success": True,
            "message": message,
            "workflow": {
                "workflow_id": workflow.workflow_id,
                "name": workflow.name,
                "description": workflow.description,
                "version": workflow.version,
                "status": workflow.status.value,
                "created_at": workflow.created_at.isoformat(),
                "parameters_count": len(workflow.parameters),
                "actions_count": len(workflow.actions)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        fire_and_forget("error", f"Failed to create workflow: {e}", ServiceNames.ORCHESTRATOR)
        raise HTTPException(status_code=500, detail=f"Failed to create workflow: {str(e)}")


@router.post("/from-template", response_model=Dict[str, Any])
async def create_workflow_from_template(
    request: WorkflowTemplateCreateRequest,
    background_tasks: BackgroundTasks,
    created_by: str = "api_user"
) -> Dict[str, Any]:
    """Create a workflow from a predefined template."""
    try:
        # Create workflow from template
        success, message, workflow = await workflow_service.create_workflow_from_template(
            request.template_name, request.customizations, created_by
        )

        if not success:
            raise HTTPException(status_code=400, detail=message)

        # Schedule cleanup task
        background_tasks.add_task(workflow_service.cleanup_completed_executions)

        return {
            "success": True,
            "message": message,
            "workflow": {
                "workflow_id": workflow.workflow_id,
                "name": workflow.name,
                "description": workflow.description,
                "version": workflow.version,
                "status": workflow.status.value,
                "created_at": workflow.created_at.isoformat(),
                "template_used": request.template_name
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        fire_and_forget("error", f"Failed to create workflow from template: {e}", ServiceNames.ORCHESTRATOR)
        raise HTTPException(status_code=500, detail=f"Failed to create workflow from template: {str(e)}")


@router.get("/", response_model=WorkflowListResponse)
async def list_workflows(
    status: Optional[str] = Query(None, description="Filter by status"),
    created_by: Optional[str] = Query(None, description="Filter by creator"),
    name_contains: Optional[str] = Query(None, description="Search by name"),
    tags: Optional[str] = Query(None, description="Filter by tags (comma-separated)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(50, ge=1, le=100, description="Page size")
) -> WorkflowListResponse:
    """List workflow definitions with optional filters."""
    try:
        # Build filters
        filters = {}
        if status:
            filters["status"] = status
        if created_by:
            filters["created_by"] = created_by
        if name_contains:
            filters["name_contains"] = name_contains
        if tags:
            filters["tags"] = [tag.strip() for tag in tags.split(",")]

        # Get workflows
        workflows = await workflow_service.list_workflows(filters)

        # Paginate results
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        paginated_workflows = workflows[start_idx:end_idx]

        # Convert to response format
        workflow_list = []
        for workflow in paginated_workflows:
            workflow_list.append({
                "workflow_id": workflow.workflow_id,
                "name": workflow.name,
                "description": workflow.description,
                "version": workflow.version,
                "status": workflow.status.value,
                "created_by": workflow.created_by,
                "created_at": workflow.created_at.isoformat(),
                "updated_at": workflow.updated_at.isoformat(),
                "tags": workflow.tags,
                "parameters_count": len(workflow.parameters),
                "actions_count": len(workflow.actions),
                "total_executions": workflow.total_executions,
                "successful_executions": workflow.successful_executions,
                "average_execution_time": workflow.average_execution_time
            })

        return WorkflowListResponse(
            workflows=workflow_list,
            total=len(workflows),
            page=page,
            page_size=page_size
        )

    except Exception as e:
        fire_and_forget("error", f"Failed to list workflows: {e}", ServiceNames.ORCHESTRATOR)
        raise HTTPException(status_code=500, detail=f"Failed to list workflows: {str(e)}")


@router.get("/search")
async def search_workflows(
    query: str = Query(..., description="Search query"),
    limit: int = Query(50, ge=1, le=100, description="Maximum results")
) -> Dict[str, Any]:
    """Search workflows by name, description, or tags."""
    try:
        workflows = await workflow_service.search_workflows(query, limit)

        # Convert to response format
        results = []
        for workflow in workflows:
            results.append({
                "workflow_id": workflow.workflow_id,
                "name": workflow.name,
                "description": workflow.description,
                "version": workflow.version,
                "status": workflow.status.value,
                "tags": workflow.tags,
                "relevance_score": 1.0  # Would be calculated based on search relevance
            })

        return {
            "query": query,
            "total_results": len(results),
            "workflows": results
        }

    except Exception as e:
        fire_and_forget("error", f"Failed to search workflows: {e}", ServiceNames.ORCHESTRATOR)
        raise HTTPException(status_code=500, detail=f"Failed to search workflows: {str(e)}")


@router.get("/{workflow_id}")
async def get_workflow(workflow_id: str) -> Dict[str, Any]:
    """Get a specific workflow definition."""
    try:
        workflow = await workflow_service.get_workflow(workflow_id)

        if not workflow:
            raise HTTPException(status_code=404, detail="Workflow not found")

        return {
            "workflow_id": workflow.workflow_id,
            "name": workflow.name,
            "description": workflow.description,
            "version": workflow.version,
            "status": workflow.status.value,
            "created_by": workflow.created_by,
            "created_at": workflow.created_at.isoformat(),
            "updated_at": workflow.updated_at.isoformat(),
            "tags": workflow.tags,
            "parameters": [p.to_dict() for p in workflow.parameters],
            "actions": [a.to_dict() for a in workflow.actions],
            "timeout_seconds": workflow.timeout_seconds,
            "max_concurrent_actions": workflow.max_concurrent_actions,
            "notify_on_completion": workflow.notify_on_completion,
            "notification_channels": workflow.notification_channels,
            "execution_statistics": {
                "total_executions": workflow.total_executions,
                "successful_executions": workflow.successful_executions,
                "failed_executions": workflow.failed_executions,
                "success_rate": (workflow.successful_executions / workflow.total_executions * 100) if workflow.total_executions > 0 else 0,
                "average_execution_time": workflow.average_execution_time
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        fire_and_forget("error", f"Failed to get workflow: {e}", ServiceNames.ORCHESTRATOR)
        raise HTTPException(status_code=500, detail=f"Failed to get workflow: {str(e)}")


@router.put("/{workflow_id}")
async def update_workflow(
    workflow_id: str,
    request: WorkflowUpdateRequest,
    background_tasks: BackgroundTasks,
    updated_by: str = "api_user"
) -> Dict[str, Any]:
    """Update an existing workflow definition."""
    try:
        # Convert request to dictionary, excluding None values
        updates = {k: v for k, v in request.dict().items() if v is not None}

        # Convert parameter and action models to dictionaries
        if "parameters" in updates:
            updates["parameters"] = [p.dict() for p in updates["parameters"]]

        if "actions" in updates:
            updates["actions"] = [a.dict() for a in updates["actions"]]

        success, message = await workflow_service.update_workflow(workflow_id, updates, updated_by)

        if not success:
            raise HTTPException(status_code=400, detail=message)

        # Schedule cleanup task
        background_tasks.add_task(workflow_service.cleanup_completed_executions)

        return {
            "success": True,
            "message": message,
            "workflow_id": workflow_id
        }

    except HTTPException:
        raise
    except Exception as e:
        fire_and_forget("error", f"Failed to update workflow: {e}", ServiceNames.ORCHESTRATOR)
        raise HTTPException(status_code=500, detail=f"Failed to update workflow: {str(e)}")


@router.delete("/{workflow_id}")
async def delete_workflow(workflow_id: str) -> Dict[str, Any]:
    """Delete a workflow definition."""
    try:
        success, message = await workflow_service.delete_workflow(workflow_id)

        if not success:
            raise HTTPException(status_code=400, detail=message)

        return {
            "success": True,
            "message": message,
            "workflow_id": workflow_id
        }

    except HTTPException:
        raise
    except Exception as e:
        fire_and_forget("error", f"Failed to delete workflow: {e}", ServiceNames.ORCHESTRATOR)
        raise HTTPException(status_code=500, detail=f"Failed to delete workflow: {str(e)}")


# Workflow Execution Endpoints

@router.post("/{workflow_id}/execute", response_model=Dict[str, Any])
async def execute_workflow(
    workflow_id: str,
    request: WorkflowExecuteRequest,
    background_tasks: BackgroundTasks,
    initiated_by: str = "api_user"
) -> Dict[str, Any]:
    """Execute a workflow with given parameters."""
    try:
        success, message, execution = await workflow_service.execute_workflow(
            workflow_id, request.parameters, initiated_by
        )

        if not success:
            raise HTTPException(status_code=400, detail=message)

        # Schedule cleanup task
        background_tasks.add_task(workflow_service.cleanup_completed_executions)

        return {
            "success": True,
            "message": message,
            "execution": {
                "execution_id": execution.execution_id,
                "workflow_id": execution.workflow_id,
                "status": execution.status.value,
                "started_at": execution.started_at.isoformat() if execution.started_at else None,
                "input_parameters": execution.input_parameters
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        fire_and_forget("error", f"Failed to execute workflow: {e}", ServiceNames.ORCHESTRATOR)
        raise HTTPException(status_code=500, detail=f"Failed to execute workflow: {str(e)}")


@router.get("/executions/{execution_id}", response_model=WorkflowExecutionResponse)
async def get_execution(execution_id: str) -> WorkflowExecutionResponse:
    """Get a specific workflow execution."""
    try:
        execution = await workflow_service.get_execution(execution_id)

        if not execution:
            raise HTTPException(status_code=404, detail="Execution not found")

        return WorkflowExecutionResponse(
            execution_id=execution.execution_id,
            workflow_id=execution.workflow_id,
            status=execution.status.value,
            started_at=execution.started_at.isoformat() if execution.started_at else None,
            completed_at=execution.completed_at.isoformat() if execution.completed_at else None,
            execution_time_seconds=execution.execution_time_seconds,
            input_parameters=execution.input_parameters,
            action_results=execution.action_results,
            output_data=execution.output_data,
            error_message=execution.error_message
        )

    except HTTPException:
        raise
    except Exception as e:
        fire_and_forget("error", f"Failed to get execution: {e}", ServiceNames.ORCHESTRATOR)
        raise HTTPException(status_code=500, detail=f"Failed to get execution: {str(e)}")


@router.get("/{workflow_id}/executions")
async def list_workflow_executions(
    workflow_id: str,
    status: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=500, description="Maximum results")
) -> Dict[str, Any]:
    """List executions for a specific workflow."""
    try:
        # Convert status string to enum
        status_enum = WorkflowExecutionStatus(status) if status else None

        executions = await workflow_service.list_executions(workflow_id, status_enum, limit)

        # Convert to response format
        execution_list = []
        for execution in executions:
            execution_list.append({
                "execution_id": execution.execution_id,
                "status": execution.status.value,
                "started_at": execution.started_at.isoformat() if execution.started_at else None,
                "completed_at": execution.completed_at.isoformat() if execution.completed_at else None,
                "execution_time_seconds": execution.execution_time_seconds,
                "initiated_by": execution.initiated_by,
                "completed_actions": execution.completed_actions,
                "failed_actions": execution.failed_actions
            })

        return {
            "workflow_id": workflow_id,
            "executions": execution_list,
            "total": len(execution_list)
        }

    except Exception as e:
        fire_and_forget("error", f"Failed to list executions: {e}", ServiceNames.ORCHESTRATOR)
        raise HTTPException(status_code=500, detail=f"Failed to list executions: {str(e)}")


@router.post("/executions/{execution_id}/cancel")
async def cancel_execution(execution_id: str, cancelled_by: str = "api_user") -> Dict[str, Any]:
    """Cancel a running workflow execution."""
    try:
        success, message = await workflow_service.cancel_execution(execution_id, cancelled_by)

        if not success:
            raise HTTPException(status_code=400, detail=message)

        return {
            "success": True,
            "message": message,
            "execution_id": execution_id
        }

    except HTTPException:
        raise
    except Exception as e:
        fire_and_forget("error", f"Failed to cancel execution: {e}", ServiceNames.ORCHESTRATOR)
        raise HTTPException(status_code=500, detail=f"Failed to cancel execution: {str(e)}")


# Workflow Templates and Statistics

@router.get("/templates")
async def get_workflow_templates() -> Dict[str, Any]:
    """Get available workflow templates."""
    try:
        templates = {}

        for template_name, template_data in WORKFLOW_TEMPLATES.items():
            templates[template_name] = {
                "name": template_data["name"],
                "description": template_data["description"],
                "parameters_count": len(template_data["parameters"]),
                "actions_count": len(template_data["actions"])
            }

        return {
            "templates": templates,
            "total_templates": len(templates)
        }

    except Exception as e:
        fire_and_forget("error", f"Failed to get templates: {e}", ServiceNames.ORCHESTRATOR)
        raise HTTPException(status_code=500, detail=f"Failed to get templates: {str(e)}")


@router.get("/templates/{template_name}")
async def get_workflow_template(template_name: str) -> Dict[str, Any]:
    """Get detailed information about a specific template."""
    try:
        if template_name not in WORKFLOW_TEMPLATES:
            raise HTTPException(status_code=404, detail="Template not found")

        template = WORKFLOW_TEMPLATES[template_name]

        return {
            "template_name": template_name,
            "name": template["name"],
            "description": template["description"],
            "parameters": template["parameters"],
            "actions": template["actions"]
        }

    except HTTPException:
        raise
    except Exception as e:
        fire_and_forget("error", f"Failed to get template: {e}", ServiceNames.ORCHESTRATOR)
        raise HTTPException(status_code=500, detail=f"Failed to get template: {str(e)}")


@router.get("/statistics")
async def get_workflow_statistics() -> Dict[str, Any]:
    """Get comprehensive workflow statistics."""
    try:
        stats = workflow_service.get_workflow_statistics()

        return {
            "summary": stats,
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        fire_and_forget("error", f"Failed to get statistics: {e}", ServiceNames.ORCHESTRATOR)
        raise HTTPException(status_code=500, detail=f"Failed to get statistics: {str(e)}")


@router.get("/activity")
async def get_recent_activity(limit: int = Query(20, ge=1, le=100, description="Maximum results")) -> Dict[str, Any]:
    """Get recent workflow activity."""
    try:
        activity = workflow_service.get_recent_activity(limit)

        return {
            "activity": activity,
            "total": len(activity),
            "generated_at": datetime.now().isoformat()
        }

    except Exception as e:
        fire_and_forget("error", f"Failed to get activity: {e}", ServiceNames.ORCHESTRATOR)
        raise HTTPException(status_code=500, detail=f"Failed to get activity: {str(e)}")


# Health check endpoint
@router.get("/health")
async def workflow_health_check() -> Dict[str, Any]:
    """Health check for workflow management service."""
    try:
        # Check database connectivity
        stats = workflow_service.get_workflow_statistics()

        return {
            "status": "healthy",
            "service": "workflow_management",
            "timestamp": datetime.now().isoformat(),
            "database_connected": True,
            "active_executions": len(workflow_service.active_executions),
            "total_workflows": stats.get("workflows", {}).get("total_workflows", 0)
        }

    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "workflow_management",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }


# Example usage endpoint
@router.post("/examples/create-sample-workflow")
async def create_sample_workflow(created_by: str = "api_user") -> Dict[str, Any]:
    """Create a sample workflow for demonstration purposes."""
    try:
        # Create a sample document analysis workflow
        workflow_data = {
            "name": "Sample Document Analysis",
            "description": "A sample workflow that demonstrates document analysis capabilities",
            "tags": ["sample", "analysis", "documentation"],
            "parameters": [
                {
                    "name": "document_url",
                    "type": "string",
                    "description": "URL of the document to analyze",
                    "required": True
                },
                {
                    "name": "analysis_depth",
                    "type": "string",
                    "description": "Depth of analysis",
                    "required": False,
                    "default_value": "standard",
                    "allowed_values": ["basic", "standard", "deep"]
                }
            ],
            "actions": [
                {
                    "action_type": "service_call",
                    "name": "Fetch Document",
                    "description": "Fetch the document from the provided URL",
                    "config": {
                        "service": "source_agent",
                        "endpoint": "/fetch",
                        "method": "POST",
                        "parameters": {
                            "url": "{{document_url}}",
                            "type": "document"
                        }
                    }
                },
                {
                    "action_type": "service_call",
                    "name": "Analyze Document",
                    "description": "Analyze the document content",
                    "config": {
                        "service": "analysis_service",
                        "endpoint": "/analyze",
                        "method": "POST",
                        "parameters": {
                            "content": "{{fetch_document.content}}",
                            "depth": "{{analysis_depth}}"
                        }
                    },
                    "depends_on": ["fetch_document"]
                },
                {
                    "action_type": "service_call",
                    "name": "Generate Summary",
                    "description": "Generate a summary of the analysis",
                    "config": {
                        "service": "summarizer_hub",
                        "endpoint": "/summarize",
                        "method": "POST",
                        "parameters": {
                            "content": "{{analyze_document.results}}",
                            "max_length": 500
                        }
                    },
                    "depends_on": ["analyze_document"]
                }
            ]
        }

        success, message, workflow = await workflow_service.create_workflow(workflow_data, created_by)

        if not success:
            raise HTTPException(status_code=400, detail=message)

        return {
            "success": True,
            "message": "Sample workflow created successfully",
            "workflow": {
                "workflow_id": workflow.workflow_id,
                "name": workflow.name,
                "description": workflow.description,
                "parameters_count": len(workflow.parameters),
                "actions_count": len(workflow.actions)
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        fire_and_forget("error", f"Failed to create sample workflow: {e}", ServiceNames.ORCHESTRATOR)
        raise HTTPException(status_code=500, detail=f"Failed to create sample workflow: {str(e)}")
