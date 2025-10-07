"""
DTO for orchestration execution response.
"""
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime


class ExecutionResponse(BaseModel):
    """Response containing orchestration execution details."""
    
    execution_id: str = Field(..., description="Unique execution ID")
    timestamp: datetime = Field(..., description="Execution timestamp")
    
    # Query Information
    query: str = Field(..., description="The original user query")
    mcp_id: str = Field(..., description="ID of the MCP")
    mcp_version: str = Field(..., description="Version of the MCP")
    pattern_used: str = Field(..., description="LLM pattern used")
    composition_id: Optional[str] = Field(None, description="Composition ID if applicable")
    
    # Performance Metrics
    latency_ms: int = Field(..., description="Execution latency in milliseconds")
    token_usage: int = Field(..., description="Total tokens used")
    cost_cents: float = Field(..., description="Execution cost in cents")
    success: bool = Field(..., description="Whether execution succeeded")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    # Quality Metrics
    accuracy_score: float = Field(..., description="Accuracy score (0-1)")
    confidence: float = Field(..., description="Confidence score (0-1)")
    hallucination_detected: bool = Field(..., description="Whether hallucination was detected")
    citation_count: int = Field(..., description="Number of citations provided")
    user_satisfaction: Optional[float] = Field(None, description="User satisfaction score")
    quality_score: float = Field(..., description="Calculated quality score (0-1)")
    
    # Context (optionally truncated for performance)
    prompt_preview: str = Field(..., description="Preview of the prompt (first 200 chars)")
    response_preview: str = Field(..., description="Preview of the response (first 200 chars)")
    context_length: int = Field(..., description="Length of context in tokens")
    sources_count: int = Field(..., description="Number of retrieved sources")
    
    # Environment
    environment: str = Field(..., description="Environment")
    user_id: Optional[str] = Field(None, description="User ID")
    session_id: Optional[str] = Field(None, description="Session ID")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        json_schema_extra = {
            "example": {
                "execution_id": "exec-123e4567-e89b-12d3-a456-426614174000",
                "timestamp": "2025-10-07T00:00:00Z",
                "query": "What is the weather like today?",
                "mcp_id": "mcp-weather-001",
                "mcp_version": "1.0.0",
                "pattern_used": "chain-of-thought",
                "latency_ms": 1250,
                "token_usage": 450,
                "cost_cents": 0.015,
                "success": True,
                "accuracy_score": 0.92,
                "confidence": 0.88,
                "hallucination_detected": False,
                "citation_count": 3,
                "quality_score": 0.87,
                "prompt_preview": "You are a weather assistant...",
                "response_preview": "The weather today is...",
                "context_length": 350,
                "sources_count": 2,
                "environment": "production",
                "tags": ["weather", "query"]
            }
        }
