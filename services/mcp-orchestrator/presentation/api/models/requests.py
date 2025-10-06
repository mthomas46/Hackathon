"""Request models for API endpoints."""

from typing import Dict, Any, Optional, List

from pydantic import BaseModel, Field


class CreateWorkflowRequestModel(BaseModel):
    """Request model for creating a workflow."""
    
    original_query: str = Field(..., description="Natural language query", min_length=1)
    parsed_query_id: Optional[str] = Field(None, description="ID from MCP Interpreter")
    query_intent: Optional[str] = Field(None, description="Query intent")
    query_complexity: Optional[int] = Field(None, ge=1, le=10, description="Complexity (1-10)")
    required_tiers: Optional[List[int]] = Field(None, description="Required MCP tiers")
    
    user_id: Optional[str] = Field(None, description="User ID")
    session_id: Optional[str] = Field(None, description="Session ID")
    
    execution_strategy: Optional[str] = Field(None, description="Execution strategy")
    patterns_to_apply: Optional[List[str]] = Field(None, description="LLM patterns")
    max_duration_seconds: Optional[int] = Field(None, ge=1, description="Max duration")
    max_cost: Optional[float] = Field(None, ge=0, description="Max cost")
    requires_approval: bool = Field(False, description="Requires human approval")
    
    client_ids: Optional[List[str]] = Field(None, description="Client filters")
    project_ids: Optional[List[str]] = Field(None, description="Project filters")
    team_ids: Optional[List[str]] = Field(None, description="Team filters")
    
    context: Dict[str, Any] = Field(default_factory=dict, description="Additional context")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "original_query": "What coding patterns does Team Alpha use?",
                "parsed_query_id": "query-123",
                "query_intent": "search",
                "query_complexity": 5,
                "required_tiers": [2, 3],
                "user_id": "user-456",
                "requires_approval": False
            }
        }


class ExecuteWorkflowRequestModel(BaseModel):
    """Request model for executing a workflow."""
    
    workflow_id: str = Field(..., description="Workflow ID to execute")
    async_execution: bool = Field(True, description="Execute asynchronously")
    notify_on_completion: bool = Field(True, description="Send notification")
    stream_progress: bool = Field(False, description="Stream progress via WebSocket")
    
    override_strategy: Optional[str] = Field(None, description="Override execution strategy")
    override_patterns: Optional[List[str]] = Field(None, description="Override patterns")
    max_retries: int = Field(3, ge=0, le=10, description="Max retries")
    
    approval_token: Optional[str] = Field(None, description="Approval token")
    approved_by: Optional[str] = Field(None, description="Approver ID")
    
    execution_context: Dict[str, Any] = Field(default_factory=dict, description="Execution context")
    
    class Config:
        json_schema_extra = {
            "example": {
                "workflow_id": "workflow-789",
                "async_execution": True,
                "notify_on_completion": True,
                "max_retries": 3
            }
        }

