"""Workflow Entity - Core Aggregate Root."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
import uuid

from services.mcp_orchestrator.domain.entities.execution_plan import ExecutionPlan
from services.mcp_orchestrator.domain.value_objects.workflow_state import WorkflowState
from services.mcp_orchestrator.domain.value_objects.llm_pattern import LLMPattern


@dataclass
class Workflow:
    """
    Core aggregate root for query workflow orchestration.
    
    Represents a complete workflow from query interpretation
    through execution to result aggregation.
    """
    
    # Identity
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    
    # Source query (from interpreter)
    original_query: str = ""
    parsed_query_id: str = ""  # From MCP Interpreter
    query_intent: str = ""
    query_complexity: int = 5
    
    # Execution plan
    execution_plan: Optional[ExecutionPlan] = None
    
    # State tracking
    state: WorkflowState = WorkflowState.PENDING
    progress: float = 0.0  # 0.0-1.0
    
    # Patterns applied
    applied_patterns: List[LLMPattern] = field(default_factory=list)
    
    # Results
    final_result: Optional[Dict[str, Any]] = None
    confidence_score: float = 0.0
    error_message: Optional[str] = None
    
    # Timing
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_ms: float = 0.0
    
    # User context
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate the workflow."""
        if not self.original_query:
            raise ValueError("Workflow must have an original_query")
    
    def transition_to(self, new_state: WorkflowState) -> None:
        """
        Transition to a new state.
        
        Args:
            new_state: Target state
        
        Raises:
            ValueError: If transition is invalid
        """
        if not self.state.can_transition_to(new_state):
            raise ValueError(
                f"Invalid state transition: {self.state.value} -> {new_state.value}"
            )
        
        self.state = new_state
        self.progress = new_state.progress_percentage
        
        # Track timing
        if new_state == WorkflowState.EXECUTING and not self.started_at:
            self.started_at = datetime.now(timezone.utc)
        
        if new_state.is_terminal and not self.completed_at:
            self.completed_at = datetime.now(timezone.utc)
            if self.started_at:
                duration = (self.completed_at - self.started_at).total_seconds() * 1000
                self.duration_ms = duration
    
    def set_execution_plan(self, plan: ExecutionPlan) -> None:
        """
        Set the execution plan.
        
        Args:
            plan: Execution plan to use
        """
        if not isinstance(plan, ExecutionPlan):
            raise TypeError("plan must be an ExecutionPlan")
        
        plan.workflow_id = self.id
        self.execution_plan = plan
        
        # Extract patterns from steps
        all_patterns = []
        for step in plan.steps:
            all_patterns.extend(step.patterns)
        self.applied_patterns = list(set(all_patterns))  # Unique patterns
    
    def complete_successfully(
        self,
        result: Dict[str, Any],
        confidence: float = 1.0
    ) -> None:
        """
        Mark workflow as successfully completed.
        
        Args:
            result: Final aggregated result
            confidence: Overall confidence score
        """
        self.final_result = result
        self.confidence_score = confidence
        self.transition_to(WorkflowState.COMPLETED)
    
    def fail(self, error: str) -> None:
        """
        Mark workflow as failed.
        
        Args:
            error: Error message
        """
        self.error_message = error
        self.transition_to(WorkflowState.FAILED)
    
    def cancel(self) -> None:
        """Cancel the workflow."""
        self.transition_to(WorkflowState.CANCELLED)
    
    def update_progress(self) -> None:
        """Update progress based on execution plan."""
        if not self.execution_plan:
            return
        
        plan_progress = self.execution_plan.calculate_progress()
        state_progress = self.state.progress_percentage
        
        # Combine plan progress with state progress
        self.progress = (state_progress + plan_progress) / 2.0
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """
        Get summary of workflow execution.
        
        Returns:
            Summary dictionary
        """
        summary = {
            "workflow_id": self.id,
            "state": self.state.value,
            "progress": self.progress,
            "duration_ms": self.duration_ms,
            "confidence_score": self.confidence_score,
            "patterns_applied": [p.value for p in self.applied_patterns],
        }
        
        if self.execution_plan:
            summary["total_steps"] = len(self.execution_plan.steps)
            summary["completed_steps"] = self.execution_plan.get_completed_step_count()
            summary["total_queries"] = self.execution_plan.get_total_query_count()
            summary["strategy"] = self.execution_plan.strategy.value
        
        if self.error_message:
            summary["error"] = self.error_message
        
        return summary
    
    def requires_human_approval(self) -> bool:
        """Check if workflow requires human approval."""
        if not self.execution_plan:
            return False
        
        return self.execution_plan.requires_approval
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "original_query": self.original_query,
            "parsed_query_id": self.parsed_query_id,
            "query_intent": self.query_intent,
            "query_complexity": self.query_complexity,
            "execution_plan": self.execution_plan.to_dict() if self.execution_plan else None,
            "state": self.state.value,
            "progress": self.progress,
            "applied_patterns": [p.value for p in self.applied_patterns],
            "final_result": self.final_result,
            "confidence_score": self.confidence_score,
            "error_message": self.error_message,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "user_id": self.user_id,
            "session_id": self.session_id,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_parsed_query(
        cls,
        parsed_query_data: Dict[str, Any],
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> "Workflow":
        """
        Create a workflow from parsed query data (from MCP Interpreter).
        
        Args:
            parsed_query_data: Parsed query from interpreter
            user_id: Optional user ID
            session_id: Optional session ID
        
        Returns:
            New Workflow instance
        """
        return cls(
            name=f"Workflow for: {parsed_query_data['original_query'][:50]}...",
            original_query=parsed_query_data["original_query"],
            parsed_query_id=parsed_query_data["query_id"],
            query_intent=parsed_query_data["intent"],
            query_complexity=parsed_query_data.get("estimated_complexity", 5),
            user_id=user_id,
            session_id=session_id,
        )

