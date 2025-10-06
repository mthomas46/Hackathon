"""Workflow State Value Object."""

from enum import Enum
from typing import Dict


class WorkflowState(str, Enum):
    """
    Represents the lifecycle state of a workflow execution.
    
    Tracks the progress of a multi-step query workflow
    across multiple MCPs.
    """
    
    PENDING = "pending"             # Workflow created, not started
    PLANNING = "planning"           # Analyzing query, selecting MCPs
    READY = "ready"                 # Plan complete, ready to execute
    EXECUTING = "executing"         # Actively running queries
    AGGREGATING = "aggregating"     # Combining results from MCPs
    REFINING = "refining"           # Self-critique/refinement phase
    COMPLETED = "completed"         # Successfully finished
    FAILED = "failed"               # Execution failed
    CANCELLED = "cancelled"         # Manually cancelled
    TIMEOUT = "timeout"             # Exceeded time limit
    
    @property
    def is_terminal(self) -> bool:
        """Check if this is a terminal state."""
        return self in {
            WorkflowState.COMPLETED,
            WorkflowState.FAILED,
            WorkflowState.CANCELLED,
            WorkflowState.TIMEOUT,
        }
    
    @property
    def is_active(self) -> bool:
        """Check if workflow is actively processing."""
        return self in {
            WorkflowState.PLANNING,
            WorkflowState.EXECUTING,
            WorkflowState.AGGREGATING,
            WorkflowState.REFINING,
        }
    
    @property
    def is_successful(self) -> bool:
        """Check if workflow completed successfully."""
        return self == WorkflowState.COMPLETED
    
    @property
    def progress_percentage(self) -> float:
        """Get approximate progress percentage."""
        percentages: Dict[WorkflowState, float] = {
            WorkflowState.PENDING: 0.0,
            WorkflowState.PLANNING: 0.15,
            WorkflowState.READY: 0.25,
            WorkflowState.EXECUTING: 0.60,
            WorkflowState.AGGREGATING: 0.85,
            WorkflowState.REFINING: 0.95,
            WorkflowState.COMPLETED: 1.0,
            WorkflowState.FAILED: 0.0,
            WorkflowState.CANCELLED: 0.0,
            WorkflowState.TIMEOUT: 0.0,
        }
        return percentages.get(self, 0.0)
    
    def can_transition_to(self, new_state: "WorkflowState") -> bool:
        """
        Check if transition to new state is valid.
        
        Args:
            new_state: Target state
        
        Returns:
            True if transition is allowed
        """
        # Terminal states cannot transition
        if self.is_terminal:
            return False
        
        # Valid transitions
        valid_transitions: Dict[WorkflowState, set] = {
            WorkflowState.PENDING: {
                WorkflowState.PLANNING,
                WorkflowState.CANCELLED,
            },
            WorkflowState.PLANNING: {
                WorkflowState.READY,
                WorkflowState.FAILED,
                WorkflowState.CANCELLED,
                WorkflowState.TIMEOUT,
            },
            WorkflowState.READY: {
                WorkflowState.EXECUTING,
                WorkflowState.CANCELLED,
            },
            WorkflowState.EXECUTING: {
                WorkflowState.AGGREGATING,
                WorkflowState.FAILED,
                WorkflowState.CANCELLED,
                WorkflowState.TIMEOUT,
            },
            WorkflowState.AGGREGATING: {
                WorkflowState.REFINING,
                WorkflowState.COMPLETED,
                WorkflowState.FAILED,
                WorkflowState.CANCELLED,
            },
            WorkflowState.REFINING: {
                WorkflowState.COMPLETED,
                WorkflowState.FAILED,
                WorkflowState.CANCELLED,
                WorkflowState.TIMEOUT,
            },
        }
        
        allowed = valid_transitions.get(self, set())
        return new_state in allowed

