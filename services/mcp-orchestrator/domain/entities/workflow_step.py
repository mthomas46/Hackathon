"""Workflow Step Entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
import uuid

from services.mcp_orchestrator.domain.entities.mcp_query import MCPQuery
from services.mcp_orchestrator.domain.value_objects.llm_pattern import LLMPattern


@dataclass
class WorkflowStep:
    """
    Represents a single step in a workflow execution.
    
    A step may involve multiple MCP queries and apply
    specific LLM patterns.
    """
    
    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = ""
    name: str = ""
    description: str = ""
    
    # Execution order
    sequence_number: int = 0
    depends_on_steps: List[str] = field(default_factory=list)  # Step IDs
    
    # Patterns to apply
    patterns: List[LLMPattern] = field(default_factory=list)
    
    # MCP queries in this step
    queries: List[MCPQuery] = field(default_factory=list)
    
    # Execution state
    status: str = "pending"  # pending, ready, executing, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: float = 0.0
    
    # Results
    result_data: Optional[Dict[str, Any]] = None
    confidence_score: float = 0.0
    error_message: Optional[str] = None
    
    # Metadata
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate the step."""
        if not self.workflow_id:
            raise ValueError("WorkflowStep must have a workflow_id")
        if not self.name:
            raise ValueError("WorkflowStep must have a name")
    
    def add_query(self, query: MCPQuery) -> None:
        """Add an MCP query to this step."""
        if not isinstance(query, MCPQuery):
            raise TypeError("query must be an MCPQuery")
        query.step_id = self.id
        self.queries.append(query)
    
    def is_ready_to_execute(self, completed_steps: set) -> bool:
        """
        Check if step is ready to execute.
        
        Args:
            completed_steps: Set of completed step IDs
        
        Returns:
            True if all dependencies are met
        """
        if self.status != "pending":
            return False
        
        # Check if all dependencies are completed
        for dep_id in self.depends_on_steps:
            if dep_id not in completed_steps:
                return False
        
        return True
    
    def start_execution(self) -> None:
        """Mark step as started."""
        self.status = "executing"
        self.started_at = datetime.now(timezone.utc)
    
    def complete_execution(
        self,
        result: Dict[str, Any],
        confidence: float = 1.0
    ) -> None:
        """
        Mark step as completed.
        
        Args:
            result: Step result data
            confidence: Overall confidence score
        """
        self.status = "completed"
        self.completed_at = datetime.now(timezone.utc)
        self.result_data = result
        self.confidence_score = confidence
        
        if self.started_at:
            duration = (self.completed_at - self.started_at).total_seconds() * 1000
            self.duration_ms = duration
    
    def fail_execution(self, error: str) -> None:
        """
        Mark step as failed.
        
        Args:
            error: Error message
        """
        self.status = "failed"
        self.completed_at = datetime.now(timezone.utc)
        self.error_message = error
        
        if self.started_at:
            duration = (self.completed_at - self.started_at).total_seconds() * 1000
            self.duration_ms = duration
    
    def get_successful_queries(self) -> List[MCPQuery]:
        """Get all successful queries."""
        return [q for q in self.queries if q.is_successful()]
    
    def get_failed_queries(self) -> List[MCPQuery]:
        """Get all failed queries."""
        return [q for q in self.queries if q.status == "failed"]
    
    def all_queries_completed(self) -> bool:
        """Check if all queries are completed."""
        return all(q.is_completed() for q in self.queries)
    
    def any_query_successful(self) -> bool:
        """Check if at least one query succeeded."""
        return any(q.is_successful() for q in self.queries)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "sequence_number": self.sequence_number,
            "depends_on_steps": self.depends_on_steps,
            "patterns": [p.value for p in self.patterns],
            "queries": [q.to_dict() for q in self.queries],
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "result_data": self.result_data,
            "confidence_score": self.confidence_score,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata,
        }

