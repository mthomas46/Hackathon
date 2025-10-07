"""
DTO for recording an orchestration execution.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


class RecordExecutionRequest(BaseModel):
    """Request to record a new orchestration execution."""
    
    # Query Information
    query: str = Field(..., description="The original user query")
    mcp_id: str = Field(..., description="ID of the MCP that executed the query")
    mcp_version: str = Field(..., description="Version of the MCP")
    pattern_used: str = Field(..., description="LLM pattern used")
    composition_id: Optional[str] = Field(None, description="ID if part of a composition")
    
    # Performance Metrics
    latency_ms: int = Field(..., ge=0, description="Execution latency in milliseconds")
    token_usage: int = Field(..., ge=0, description="Total tokens used")
    cost_cents: float = Field(..., ge=0.0, description="Execution cost in cents")
    success: bool = Field(..., description="Whether execution succeeded")
    error: Optional[str] = Field(None, description="Error message if failed")
    
    # Quality Metrics
    accuracy_score: float = Field(..., ge=0.0, le=1.0, description="Accuracy score (0-1)")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score (0-1)")
    hallucination_detected: bool = Field(default=False, description="Whether hallucination was detected")
    citation_count: int = Field(default=0, ge=0, description="Number of citations provided")
    user_satisfaction: Optional[float] = Field(None, ge=0.0, le=1.0, description="User satisfaction score")
    
    # Context
    prompt: str = Field(..., description="Full prompt sent to the LLM")
    response: str = Field(..., description="Response received from the LLM")
    context_length: int = Field(..., ge=0, description="Length of context in tokens")
    retrieved_sources: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Sources retrieved for context"
    )
    
    # Environment
    environment: str = Field(default="production", description="Environment (dev, staging, prod)")
    user_id: Optional[str] = Field(None, description="ID of the user who initiated the query")
    session_id: Optional[str] = Field(None, description="Session ID")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
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
                "prompt": "You are a weather assistant...",
                "response": "The weather today is...",
                "context_length": 350,
                "environment": "production"
            }
        }
