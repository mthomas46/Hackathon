"""DTOs for execution-related requests/responses."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

from services.mcp_performance_store.domain.value_objects.execution_status import ExecutionStatus


class RecordExecutionRequest(BaseModel):
    """Request to record an execution."""
    
    execution_id: str = Field(..., description="Unique execution ID")
    query: str = Field(..., description="The query that was executed")
    context: Dict[str, Any] = Field(default_factory=dict, description="Execution context")
    
    # MCP composition info
    composition_id: Optional[str] = Field(None, description="Composition ID if applicable")
    mcp_ids: List[str] = Field(default_factory=list, description="List of MCP IDs used")
    
    # Pattern info
    pattern_name: Optional[str] = Field(None, description="LLM pattern used")
    pattern_config: Dict[str, Any] = Field(default_factory=dict, description="Pattern configuration")
    
    # Timing (milliseconds)
    start_time: Optional[datetime] = Field(None, description="Start timestamp")
    end_time: Optional[datetime] = Field(None, description="End timestamp")
    total_duration_ms: float = Field(0.0, description="Total duration in milliseconds")
    interpretation_ms: float = Field(0.0, description="Interpretation time")
    retrieval_ms: float = Field(0.0, description="Retrieval time")
    pattern_execution_ms: float = Field(0.0, description="Pattern execution time")
    composition_ms: float = Field(0.0, description="Composition time")
    
    # Status and results
    status: ExecutionStatus = Field(ExecutionStatus.SUCCESS, description="Execution status")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    error_type: Optional[str] = Field(None, description="Error type")
    
    # Results
    confidence: float = Field(0.0, description="Confidence score 0-1")
    num_sources: int = Field(0, description="Number of sources used")
    response_length: int = Field(0, description="Response length in characters")
    
    # Metadata
    service: Optional[str] = Field(None, description="Service that ran execution")
    user_id: Optional[str] = Field(None, description="User ID")
    session_id: Optional[str] = Field(None, description="Session ID")
    tags: List[str] = Field(default_factory=list, description="Tags")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class ExecutionResponse(BaseModel):
    """Response with execution details."""
    
    execution_id: str
    query: str
    pattern_name: Optional[str]
    status: str
    total_duration_ms: float
    confidence: float
    num_sources: int
    start_time: Optional[datetime]
    end_time: Optional[datetime]
    error_message: Optional[str]
    composition_id: Optional[str]
    
    class Config:
        """Pydantic config."""
        from_attributes = True


class ExecutionListResponse(BaseModel):
    """Response with list of executions."""
    
    executions: List[ExecutionResponse]
    total: int
    limit: int
    offset: int
