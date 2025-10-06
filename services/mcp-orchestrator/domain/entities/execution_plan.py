"""Execution Plan Entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, Set
import uuid

from services.mcp_orchestrator.domain.entities.workflow_step import WorkflowStep
from services.mcp_orchestrator.domain.value_objects.execution_strategy import ExecutionStrategy
from services.mcp_orchestrator.domain.value_objects.mcp_selection_criteria import MCPSelectionCriteria


@dataclass
class ExecutionPlan:
    """
    Execution plan for a workflow.
    
    Defines the steps, MCPs, and strategies for executing a query workflow.
    """
    
    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = ""
    
    # Strategy
    strategy: ExecutionStrategy = ExecutionStrategy.SEQUENTIAL
    
    # MCP selection
    selection_criteria: Optional[MCPSelectionCriteria] = None
    selected_mcp_ids: List[str] = field(default_factory=list)
    
    # Execution steps
    steps: List[WorkflowStep] = field(default_factory=list)
    
    # Plan metadata
    estimated_duration_ms: float = 0.0
    estimated_cost: float = 0.0
    confidence_score: float = 0.0
    
    # State
    is_approved: bool = False
    requires_approval: bool = False
    
    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    approved_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate the plan."""
        if not self.workflow_id:
            raise ValueError("ExecutionPlan must have a workflow_id")
    
    def add_step(self, step: WorkflowStep) -> None:
        """
        Add a step to the plan.
        
        Args:
            step: Workflow step to add
        """
        if not isinstance(step, WorkflowStep):
            raise TypeError("step must be a WorkflowStep")
        
        step.workflow_id = self.workflow_id
        step.sequence_number = len(self.steps)
        self.steps.append(step)
    
    def get_step_by_id(self, step_id: str) -> Optional[WorkflowStep]:
        """Get a step by ID."""
        for step in self.steps:
            if step.id == step_id:
                return step
        return None
    
    def get_steps_in_order(self) -> List[WorkflowStep]:
        """Get steps sorted by sequence number."""
        return sorted(self.steps, key=lambda s: s.sequence_number)
    
    def get_ready_steps(self) -> List[WorkflowStep]:
        """
        Get steps that are ready to execute.
        
        Returns:
            List of steps ready for execution
        """
        completed_steps = {s.id for s in self.steps if s.status == "completed"}
        return [
            step for step in self.steps
            if step.is_ready_to_execute(completed_steps)
        ]
    
    def get_total_query_count(self) -> int:
        """Get total number of MCP queries across all steps."""
        return sum(len(step.queries) for step in self.steps)
    
    def get_completed_step_count(self) -> int:
        """Get number of completed steps."""
        return sum(1 for step in self.steps if step.status == "completed")
    
    def is_complete(self) -> bool:
        """Check if all steps are completed."""
        return all(step.status == "completed" for step in self.steps)
    
    def has_failures(self) -> bool:
        """Check if any steps failed."""
        return any(step.status == "failed" for step in self.steps)
    
    def approve(self, approved_by: str) -> None:
        """
        Approve the execution plan.
        
        Args:
            approved_by: User/system that approved
        """
        self.is_approved = True
        self.approved_at = datetime.now(timezone.utc)
        self.approved_by = approved_by
    
    def calculate_progress(self) -> float:
        """
        Calculate overall progress (0.0-1.0).
        
        Returns:
            Progress percentage as decimal
        """
        if not self.steps:
            return 0.0
        
        total_progress = sum(
            0.0 if step.status == "pending" else
            0.5 if step.status == "executing" else
            1.0 if step.status == "completed" else
            0.0  # failed
            for step in self.steps
        )
        
        return total_progress / len(self.steps)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "workflow_id": self.workflow_id,
            "strategy": self.strategy.value,
            "selection_criteria": self.selection_criteria.__dict__ if self.selection_criteria else None,
            "selected_mcp_ids": self.selected_mcp_ids,
            "steps": [step.to_dict() for step in self.steps],
            "estimated_duration_ms": self.estimated_duration_ms,
            "estimated_cost": self.estimated_cost,
            "confidence_score": self.confidence_score,
            "is_approved": self.is_approved,
            "requires_approval": self.requires_approval,
            "created_at": self.created_at.isoformat(),
            "approved_at": self.approved_at.isoformat() if self.approved_at else None,
            "approved_by": self.approved_by,
            "metadata": self.metadata,
        }

