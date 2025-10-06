"""Workflow Response DTOs."""

from dataclasses import dataclass
from typing import Dict, Any, Optional, List


@dataclass
class WorkflowResponse:
    """
    Complete workflow response DTO.
    
    Returns full workflow details including execution plan.
    """
    
    # Identity
    workflow_id: str
    name: str
    description: str
    
    # Query
    original_query: str
    parsed_query_id: str
    query_intent: str
    query_complexity: int
    
    # State
    state: str
    progress: float
    
    # Execution
    execution_plan: Optional[Dict[str, Any]]
    applied_patterns: List[str]
    
    # Results
    final_result: Optional[Dict[str, Any]]
    confidence_score: float
    error_message: Optional[str]
    
    # Timing
    created_at: str
    started_at: Optional[str]
    completed_at: Optional[str]
    duration_ms: float
    
    # Context
    user_id: Optional[str]
    session_id: Optional[str]
    
    # Metadata
    metadata: Dict[str, Any]
    
    @classmethod
    def from_entity(cls, workflow) -> "WorkflowResponse":
        """Create from Workflow entity."""
        workflow_dict = workflow.to_dict()
        return cls(
            workflow_id=workflow_dict["id"],
            name=workflow_dict["name"],
            description=workflow_dict["description"],
            original_query=workflow_dict["original_query"],
            parsed_query_id=workflow_dict["parsed_query_id"],
            query_intent=workflow_dict["query_intent"],
            query_complexity=workflow_dict["query_complexity"],
            state=workflow_dict["state"],
            progress=workflow_dict["progress"],
            execution_plan=workflow_dict["execution_plan"],
            applied_patterns=workflow_dict["applied_patterns"],
            final_result=workflow_dict["final_result"],
            confidence_score=workflow_dict["confidence_score"],
            error_message=workflow_dict["error_message"],
            created_at=workflow_dict["created_at"],
            started_at=workflow_dict["started_at"],
            completed_at=workflow_dict["completed_at"],
            duration_ms=workflow_dict["duration_ms"],
            user_id=workflow_dict["user_id"],
            session_id=workflow_dict["session_id"],
            metadata=workflow_dict["metadata"],
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "original_query": self.original_query,
            "parsed_query_id": self.parsed_query_id,
            "query_intent": self.query_intent,
            "query_complexity": self.query_complexity,
            "state": self.state,
            "progress": self.progress,
            "execution_plan": self.execution_plan,
            "applied_patterns": self.applied_patterns,
            "final_result": self.final_result,
            "confidence_score": self.confidence_score,
            "error_message": self.error_message,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "metadata": self.metadata,
        }


@dataclass
class WorkflowSummaryResponse:
    """
    Lightweight workflow summary DTO.
    
    Used for listing workflows without full details.
    """
    
    workflow_id: str
    original_query: str
    state: str
    progress: float
    query_intent: str
    confidence_score: float
    created_at: str
    duration_ms: float
    user_id: Optional[str]
    
    @classmethod
    def from_entity(cls, workflow) -> "WorkflowSummaryResponse":
        """Create from Workflow entity."""
        summary = workflow.get_execution_summary()
        workflow_dict = workflow.to_dict()
        
        return cls(
            workflow_id=summary["workflow_id"],
            original_query=workflow_dict["original_query"][:100],  # Truncate
            state=summary["state"],
            progress=summary["progress"],
            query_intent=workflow_dict["query_intent"],
            confidence_score=summary["confidence_score"],
            created_at=workflow_dict["created_at"],
            duration_ms=summary["duration_ms"],
            user_id=workflow_dict["user_id"],
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "original_query": self.original_query,
            "state": self.state,
            "progress": self.progress,
            "query_intent": self.query_intent,
            "confidence_score": self.confidence_score,
            "created_at": self.created_at,
            "duration_ms": self.duration_ms,
            "user_id": self.user_id,
        }

