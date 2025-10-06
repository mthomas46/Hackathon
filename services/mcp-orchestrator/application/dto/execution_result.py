"""Execution Result DTO."""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class ExecutionResult:
    """
    Result of workflow execution.
    
    Returned when workflow execution completes.
    """
    
    # Identity
    workflow_id: str
    execution_id: str
    
    # Status
    success: bool
    state: str
    message: str
    
    # Results
    result_data: Optional[Dict[str, Any]]
    confidence_score: float
    
    # Execution details
    steps_completed: int
    steps_total: int
    queries_executed: int
    patterns_applied: list
    
    # Timing
    started_at: str
    completed_at: str
    duration_ms: float
    
    # Error info (if failed)
    error_message: Optional[str]
    failed_step: Optional[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "workflow_id": self.workflow_id,
            "execution_id": self.execution_id,
            "success": self.success,
            "state": self.state,
            "message": self.message,
            "result_data": self.result_data,
            "confidence_score": self.confidence_score,
            "steps_completed": self.steps_completed,
            "steps_total": self.steps_total,
            "queries_executed": self.queries_executed,
            "patterns_applied": self.patterns_applied,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "duration_ms": self.duration_ms,
            "error_message": self.error_message,
            "failed_step": self.failed_step,
        }
    
    @classmethod
    def success_result(
        cls,
        workflow_id: str,
        execution_id: str,
        result_data: Dict[str, Any],
        workflow,
    ) -> "ExecutionResult":
        """Create a success result."""
        summary = workflow.get_execution_summary()
        
        return cls(
            workflow_id=workflow_id,
            execution_id=execution_id,
            success=True,
            state=workflow.state.value,
            message="Workflow executed successfully",
            result_data=result_data,
            confidence_score=workflow.confidence_score,
            steps_completed=summary.get("completed_steps", 0),
            steps_total=summary.get("total_steps", 0),
            queries_executed=summary.get("total_queries", 0),
            patterns_applied=summary.get("patterns_applied", []),
            started_at=workflow.started_at.isoformat() if workflow.started_at else "",
            completed_at=workflow.completed_at.isoformat() if workflow.completed_at else "",
            duration_ms=workflow.duration_ms,
            error_message=None,
            failed_step=None,
        )
    
    @classmethod
    def failure_result(
        cls,
        workflow_id: str,
        execution_id: str,
        error: str,
        workflow,
        failed_step: Optional[str] = None,
    ) -> "ExecutionResult":
        """Create a failure result."""
        summary = workflow.get_execution_summary()
        
        return cls(
            workflow_id=workflow_id,
            execution_id=execution_id,
            success=False,
            state=workflow.state.value,
            message="Workflow execution failed",
            result_data=None,
            confidence_score=0.0,
            steps_completed=summary.get("completed_steps", 0),
            steps_total=summary.get("total_steps", 0),
            queries_executed=summary.get("total_queries", 0),
            patterns_applied=summary.get("patterns_applied", []),
            started_at=workflow.started_at.isoformat() if workflow.started_at else "",
            completed_at=workflow.completed_at.isoformat() if workflow.completed_at else "",
            duration_ms=workflow.duration_ms,
            error_message=error,
            failed_step=failed_step,
        )

