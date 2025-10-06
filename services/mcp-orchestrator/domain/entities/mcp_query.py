"""MCP Query Entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import uuid


@dataclass
class MCPQuery:
    """
    Represents a query to a specific MCP instance.
    
    Part of a larger workflow, this entity tracks a single
    query to a single MCP.
    """
    
    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = ""  # Parent workflow
    step_id: str = ""  # Parent step
    
    # MCP targeting
    mcp_id: str = ""  # Target MCP instance ID
    mcp_tier: int = 0  # MCP tier (0-4)
    
    # Query details
    query_text: str = ""
    query_context: Dict[str, Any] = field(default_factory=dict)
    
    # Execution
    status: str = "pending"  # pending, executing, completed, failed
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: float = 0.0
    
    # Results
    response_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    confidence_score: float = 0.0
    
    # Metadata
    retry_count: int = 0
    max_retries: int = 3
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    
    def __post_init__(self):
        """Validate the query."""
        if not self.workflow_id:
            raise ValueError("MCPQuery must have a workflow_id")
        if not self.mcp_id:
            raise ValueError("MCPQuery must have an mcp_id")
        if not self.query_text:
            raise ValueError("MCPQuery must have query_text")
    
    def start_execution(self) -> None:
        """Mark query as started."""
        self.status = "executing"
        self.started_at = datetime.now(timezone.utc)
    
    def complete_execution(
        self,
        response: Dict[str, Any],
        confidence: float = 1.0
    ) -> None:
        """
        Mark query as completed successfully.
        
        Args:
            response: Query response data
            confidence: Confidence score (0.0-1.0)
        """
        self.status = "completed"
        self.completed_at = datetime.now(timezone.utc)
        self.response_data = response
        self.confidence_score = confidence
        
        if self.started_at:
            duration = (self.completed_at - self.started_at).total_seconds() * 1000
            self.duration_ms = duration
    
    def fail_execution(self, error: str) -> None:
        """
        Mark query as failed.
        
        Args:
            error: Error message
        """
        self.status = "failed"
        self.completed_at = datetime.now(timezone.utc)
        self.error_message = error
        
        if self.started_at:
            duration = (self.completed_at - self.started_at).total_seconds() * 1000
            self.duration_ms = duration
    
    def can_retry(self) -> bool:
        """Check if query can be retried."""
        return self.status == "failed" and self.retry_count < self.max_retries
    
    def retry(self) -> None:
        """Retry the query."""
        if not self.can_retry():
            raise ValueError("Cannot retry query")
        
        self.retry_count += 1
        self.status = "pending"
        self.started_at = None
        self.completed_at = None
        self.error_message = None
    
    def is_completed(self) -> bool:
        """Check if query is completed (success or failure)."""
        return self.status in {"completed", "failed"}
    
    def is_successful(self) -> bool:
        """Check if query completed successfully."""
        return self.status == "completed"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "step_id": self.step_id,
            "mcp_id": self.mcp_id,
            "mcp_tier": self.mcp_tier,
            "query_text": self.query_text,
            "query_context": self.query_context,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "response_data": self.response_data,
            "error_message": self.error_message,
            "confidence_score": self.confidence_score,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_at": self.created_at.isoformat(),
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "MCPQuery":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            workflow_id=data["workflow_id"],
            step_id=data.get("step_id", ""),
            mcp_id=data["mcp_id"],
            mcp_tier=data.get("mcp_tier", 0),
            query_text=data["query_text"],
            query_context=data.get("query_context", {}),
            status=data.get("status", "pending"),
            started_at=datetime.fromisoformat(data["started_at"]) if data.get("started_at") else None,
            completed_at=datetime.fromisoformat(data["completed_at"]) if data.get("completed_at") else None,
            duration_ms=data.get("duration_ms", 0.0),
            response_data=data.get("response_data"),
            error_message=data.get("error_message"),
            confidence_score=data.get("confidence_score", 0.0),
            retry_count=data.get("retry_count", 0),
            max_retries=data.get("max_retries", 3),
            created_at=datetime.fromisoformat(data["created_at"]),
        )

