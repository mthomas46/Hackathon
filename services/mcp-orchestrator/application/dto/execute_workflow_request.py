"""Execute Workflow Request DTO."""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class ExecuteWorkflowRequest:
    """
    DTO for executing a workflow.
    """
    
    # Required
    workflow_id: str
    
    # Execution options
    async_execution: bool = True  # Execute asynchronously
    notify_on_completion: bool = True
    stream_progress: bool = False  # WebSocket streaming
    
    # Override options (optional)
    override_strategy: Optional[str] = None
    override_patterns: Optional[list] = None
    max_retries: int = 3
    
    # Approval (for workflows requiring it)
    approval_token: Optional[str] = None
    approved_by: Optional[str] = None
    
    # Additional context
    execution_context: Dict[str, Any] = None
    
    def __post_init__(self):
        """Validate and initialize."""
        if not self.workflow_id:
            raise ValueError("workflow_id is required")
        
        if self.execution_context is None:
            self.execution_context = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "async_execution": self.async_execution,
            "notify_on_completion": self.notify_on_completion,
            "stream_progress": self.stream_progress,
            "override_strategy": self.override_strategy,
            "override_patterns": self.override_patterns,
            "max_retries": self.max_retries,
            "approval_token": self.approval_token,
            "approved_by": self.approved_by,
            "execution_context": self.execution_context,
        }

