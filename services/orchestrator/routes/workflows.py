"""Workflow Routes for Orchestrator Service with LangGraph Integration"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, field_validator
from typing import Dict, Any, Optional, List

from ..modules.workflow_handlers import workflow_handlers

router = APIRouter()

class WorkflowRunRequest(BaseModel):
    """Request model for executing a workflow."""
    workflow_type: str = "generic"
    workflow_id: Optional[str] = None
    parameters: Optional[Dict[str, Any]] = {}
    context: Optional[Dict[str, Any]] = {}
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None
    priority: str = "normal"

    @field_validator('correlation_id')
    @classmethod
    def validate_correlation_id(cls, v):
        if v and len(v) > 255:
            raise ValueError('Correlation ID too long (max 255 characters)')
        return v

    @field_validator('priority')
    @classmethod
    def validate_priority(cls, v):
        if v not in ["low", "normal", "high", "critical"]:
            raise ValueError('Priority must be one of: low, normal, high, critical')
        return v

class LangGraphWorkflowRequest(BaseModel):
    """Request model for LangGraph workflow execution."""
    workflow_type: str
    parameters: Dict[str, Any]
    user_id: Optional[str] = None
    tags: Optional[List[str]] = []


class ToolDiscoveryRequest(BaseModel):
    """Request model for automatic tool discovery."""
    services: Optional[List[str]] = None  # List of service names to discover tools for
    tool_categories: Optional[List[str]] = None  # Filter by tool categories
    dry_run: bool = False  # Test mode without actual registration
    auto_register: bool = True  # Automatically register discovered tools

@router.post("/workflows/run")
async def run_workflow(req: WorkflowRunRequest):
    """Execute a workflow using the enhanced workflow handlers."""
    try:
        result = await workflow_handlers.handle_workflow_run(req)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")

@router.post("/workflows/ai/{workflow_type}")
async def run_langgraph_workflow(workflow_type: str, req: LangGraphWorkflowRequest):
    """Execute a LangGraph workflow directly."""
    try:
        # Create a workflow request for the LangGraph handler
        workflow_req = WorkflowRunRequest(
            workflow_type=workflow_type,
            parameters=req.parameters,
            user_id=req.user_id,
            correlation_id=f"lg-{workflow_type}-{req.parameters.get('id', 'auto')}"
        )

        result = await workflow_handlers.handle_workflow_run(workflow_req)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"LangGraph workflow execution failed: {str(e)}"
        )

@router.post("/workflows/ai/document-analysis")
async def run_document_analysis_workflow(req: LangGraphWorkflowRequest):
    """Execute document analysis workflow using LangGraph."""
    try:
        workflow_req = WorkflowRunRequest(
            workflow_type="document_analysis",
            parameters=req.parameters,
            user_id=req.user_id,
            correlation_id=f"doc-analysis-{req.parameters.get('doc_id', 'auto')}"
        )

        result = await workflow_handlers.handle_workflow_run(workflow_req)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Document analysis workflow failed: {str(e)}"
        )

@router.post("/workflows/ai/code-documentation")
async def run_code_documentation_workflow(req: LangGraphWorkflowRequest):
    """Execute code documentation workflow using LangGraph."""
    try:
        workflow_req = WorkflowRunRequest(
            workflow_type="code_documentation",
            parameters=req.parameters,
            user_id=req.user_id,
            correlation_id=f"code-doc-{req.parameters.get('repo_url', 'auto').replace('/', '-')}"
        )

        result = await workflow_handlers.handle_workflow_run(workflow_req)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Code documentation workflow failed: {str(e)}"
        )

@router.post("/workflows/ai/quality-assurance")
async def run_quality_assurance_workflow(req: LangGraphWorkflowRequest):
    """Execute quality assurance workflow using LangGraph."""
    try:
        workflow_req = WorkflowRunRequest(
            workflow_type="quality_assurance",
            parameters=req.parameters,
            user_id=req.user_id,
            correlation_id=f"qa-{req.parameters.get('target', 'auto')}"
        )

        result = await workflow_handlers.handle_workflow_run(workflow_req)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Quality assurance workflow failed: {str(e)}"
        )

@router.get("/workflows/history")
async def get_workflow_history():
    """Get workflow execution history."""
    return {
        "items": [
            {
                "correlation_id": "wf-001",
                "status": "completed",
                "start_time": "2024-01-01T00:00:00Z",
                "end_time": "2024-01-01T00:01:00Z"
            }
        ],
        "total": 1
    }

@router.get("/workflows")
async def list_workflows():
    """List available workflows."""
    return {
        "workflows": [
            {"name": "document-analysis", "description": "Analyze documents"},
            {"name": "code-review", "description": "Review code changes"}
        ]
    }


@router.post("/tools/discover")
async def discover_tools(req: ToolDiscoveryRequest):
    """Automatically discover and register LangGraph tools from ecosystem services.

    This endpoint orchestrates automatic tool discovery across all ecosystem services
    by coordinating with the discovery-agent service. It can discover tools for specific
    services or all services in the ecosystem.

    The discovery process:
    1. Identifies running services in the ecosystem
    2. Fetches OpenAPI specs from each service
    3. Analyzes endpoints for LangGraph tool potential
    4. Categorizes tools by functionality
    5. Registers tools with the orchestrator (unless dry_run=True)

    Parameters:
    - services: Optional list of service names to discover tools for
    - tool_categories: Optional categories to filter tools by
    - dry_run: Test mode without actual registration
    - auto_register: Automatically register discovered tools
    """
    try:
        from services.shared.clients import ServiceClients
        from services.shared.responses import create_success_response

        client = ServiceClients()
        discovery_agent_url = "http://llm-discovery-agent:5045"

        # Default services to discover if none specified
        if not req.services:
            req.services = [
                "prompt_store", "document_store", "code_analyzer",
                "summarizer_hub", "analysis_service", "notification_service",
                "source_agent", "secure_analyzer"
            ]

        results = []
        total_tools = 0

        for service_name in req.services:
            try:
                # Map service names to their Docker container URLs
                service_url_map = {
                    "prompt_store": "http://llm-prompt-store:5110",
                    "document_store": "http://llm-document-store:5140",
                    "code_analyzer": "http://llm-code-analyzer:5150",
                    "summarizer_hub": "http://llm-summarizer-hub:5160",
                    "analysis_service": "http://llm-analysis-service:5020",
                    "notification_service": "http://llm-notification-service:5210",
                    "source_agent": "http://llm-source-agent:5000",
                    "secure_analyzer": "http://llm-secure-analyzer:5070"
                }

                service_url = service_url_map.get(service_name)
                if not service_url:
                    results.append({
                        "service_name": service_name,
                        "status": "error",
                        "error": f"Unknown service: {service_name}"
                    })
                    continue

                # Call discovery-agent to discover tools for this service
                discovery_payload = {
                    "service_name": service_name,
                    "service_url": service_url,
                    "tool_categories": req.tool_categories,
                    "dry_run": req.dry_run
                }

                response = await client.post_json(
                    f"{discovery_agent_url}/discover/tools",
                    discovery_payload
                )

                if response.get("success"):
                    tools_discovered = response["data"]["tools_discovered"]
                    total_tools += tools_discovered

                    results.append({
                        "service_name": service_name,
                        "status": "success",
                        "tools_discovered": tools_discovered,
                        "tool_categories": response["data"].get("categories", []),
                        "registration_status": response["data"].get("registration_status", "pending")
                    })
                else:
                    results.append({
                        "service_name": service_name,
                        "status": "error",
                        "error": response.get("message", "Unknown error")
                    })

            except Exception as e:
                results.append({
                    "service_name": service_name,
                    "status": "error",
                    "error": str(e)
                })

        summary = {
            "total_services": len(req.services),
            "successful_discoveries": len([r for r in results if r["status"] == "success"]),
            "failed_discoveries": len([r for r in results if r["status"] == "error"]),
            "total_tools_discovered": total_tools,
            "dry_run": req.dry_run
        }

        return create_success_response(
            f"Tool discovery completed: {total_tools} tools discovered from {summary['successful_discoveries']} services",
            {
                "summary": summary,
                "results": results
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Tool discovery failed: {str(e)}"
        )
