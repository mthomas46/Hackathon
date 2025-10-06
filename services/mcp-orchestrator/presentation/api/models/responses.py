"""Response models for API endpoints."""

from typing import Dict, Any, Optional, List

from pydantic import BaseModel, Field


class WorkflowResponseModel(BaseModel):
    """Response model for workflow details."""
    
    workflow_id: str
    name: str
    description: str
    original_query: str
    parsed_query_id: str
    query_intent: str
    query_complexity: int
    state: str
    progress: float
    execution_plan: Optional[Dict[str, Any]]
    applied_patterns: List[str]
    final_result: Optional[Dict[str, Any]]
    confidence_score: float
    error_message: Optional[str]
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    duration_ms: float
    user_id: Optional[str]
    session_id: Optional[str]
    metadata: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "workflow_id": "wf-123",
                "name": "Workflow for: What coding patterns...",
                "state": "ready",
                "progress": 0.25,
                "query_intent": "search",
                "confidence_score": 0.8
            }
        }


class WorkflowSummaryResponseModel(BaseModel):
    """Lightweight workflow summary."""
    
    workflow_id: str
    original_query: str
    state: str
    progress: float
    query_intent: str
    confidence_score: float
    created_at: str
    duration_ms: float
    user_id: Optional[str]


class ExecutionResultModel(BaseModel):
    """Result of workflow execution."""
    
    workflow_id: str
    execution_id: str
    success: bool
    state: str
    message: str
    result_data: Optional[Dict[str, Any]]
    confidence_score: float
    steps_completed: int
    steps_total: int
    queries_executed: int
    patterns_applied: List[str]
    started_at: str
    completed_at: str
    duration_ms: float
    error_message: Optional[str]
    failed_step: Optional[str]
    
    class Config:
        json_schema_extra = {
            "example": {
                "workflow_id": "wf-123",
                "execution_id": "exec-456",
                "success": True,
                "state": "completed",
                "message": "Workflow executed successfully",
                "steps_completed": 3,
                "steps_total": 3
            }
        }


class HealthResponseModel(BaseModel):
    """Health check response."""
    
    status: str
    service: str
    version: str
    timestamp: str
    checks: Dict[str, Any]
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "service": "mcp-orchestrator",
                "version": "1.0.0",
                "checks": {
                    "redis": "healthy",
                    "mcp_gateway": "healthy"
                }
            }
        }

