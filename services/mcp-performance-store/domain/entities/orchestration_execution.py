"""
Orchestration Execution Entity.

Represents a single execution of an MCP orchestration, including all performance
metrics, prompts, responses, and quality indicators.
"""
from datetime import datetime
from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field
import uuid


class OrchestrationExecution(BaseModel):
    """
    Entity representing a single orchestration execution.
    
    Tracks complete execution details including performance metrics,
    quality scores, and full audit trail of prompts and responses.
    """
    
    # Identity
    execution_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Query Information
    query: str = Field(..., description="The original user query")
    mcp_id: str = Field(..., description="ID of the MCP that executed the query")
    mcp_version: str = Field(..., description="Version of the MCP")
    pattern_used: str = Field(..., description="LLM pattern used (e.g., 'chain-of-thought')")
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
    environment: str = Field(..., description="Environment (dev, staging, prod)")
    user_id: Optional[str] = Field(None, description="ID of the user who initiated the query")
    session_id: Optional[str] = Field(None, description="Session ID")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    
    class Config:
        """Pydantic configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return self.dict()
    
    def calculate_quality_score(self) -> float:
        """
        Calculate overall quality score.
        
        Combines accuracy, confidence, and other quality metrics
        into a single score (0-1).
        """
        # Base score from accuracy and confidence
        base_score = (self.accuracy_score * 0.5) + (self.confidence * 0.3)
        
        # Penalties
        hallucination_penalty = 0.2 if self.hallucination_detected else 0.0
        error_penalty = 0.3 if not self.success else 0.0
        
        # Bonuses
        citation_bonus = min(0.1, self.citation_count * 0.02)
        satisfaction_bonus = (self.user_satisfaction or 0.0) * 0.1
        
        quality_score = base_score - hallucination_penalty - error_penalty + citation_bonus + satisfaction_bonus
        
        return max(0.0, min(1.0, quality_score))
    
    def is_anomalous(self, baseline_latency_ms: int, threshold_factor: float = 2.0) -> bool:
        """
        Check if this execution is anomalous based on latency.
        
        Args:
            baseline_latency_ms: Expected baseline latency
            threshold_factor: How many times the baseline to consider anomalous
        
        Returns:
            True if execution latency is anomalous
        """
        return self.latency_ms > (baseline_latency_ms * threshold_factor)
    
    def __repr__(self) -> str:
        return (
            f"OrchestrationExecution(execution_id={self.execution_id}, "
            f"mcp_id={self.mcp_id}, pattern={self.pattern_used}, "
            f"latency={self.latency_ms}ms, success={self.success})"
        )
