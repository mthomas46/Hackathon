"""Workflow Action Entity"""

from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from enum import Enum
import uuid


class ActionType(Enum):
    """Types of actions that can be executed in a workflow."""
    SERVICE_CALL = "service_call"
    PROMPT_EXECUTION = "prompt_execution"
    CONDITIONAL_BRANCH = "conditional_branch"
    LOOP = "loop"
    WAIT = "wait"
    TRANSFORM_DATA = "transform_data"
    NOTIFICATION = "notification"
    EXTERNAL_API_CALL = "external_api_call"


@dataclass
class WorkflowAction:
    """Entity representing an individual action within a workflow."""

    action_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    action_type: ActionType = ActionType.SERVICE_CALL
    name: str = ""
    description: str = ""

    # Action configuration
    config: Dict[str, Any] = field(default_factory=dict)

    # Conditional execution
    condition: Optional[str] = None  # Python expression for conditional execution
    depends_on: List[str] = field(default_factory=list)  # Action IDs this depends on

    # Retry configuration
    retry_count: int = 0
    retry_delay: float = 1.0
    timeout_seconds: int = 30

    # Error handling
    on_error: Optional[str] = None  # Action to run on error
    continue_on_error: bool = False

    def __post_init__(self):
        """Validate action after initialization."""
        # Basic validation - domain validation will handle comprehensive validation
        if self.retry_count < 0:
            raise ValueError("Retry count cannot be negative")

        if self.timeout_seconds <= 0:
            raise ValueError("Timeout must be positive")

    def can_execute(self, previous_results: Dict[str, Any]) -> bool:
        """Check if this action can be executed based on conditions and dependencies."""
        # Check dependencies
        for dep_id in self.depends_on:
            if dep_id not in previous_results:
                return False
            dep_result = previous_results[dep_id]
            if hasattr(dep_result, 'status') and dep_result.status != 'completed':
                return False

        # Check condition if present
        if self.condition:
            try:
                # Evaluate condition in a safe context
                context = {"results": previous_results}
                result = eval(self.condition, {"__builtins__": {}}, context)
                return bool(result)
            except Exception:
                return False

        return True

    def get_required_services(self) -> List[str]:
        """Get list of services required by this action."""
        services = []
        if self.action_type == ActionType.SERVICE_CALL:
            service_name = self.config.get("service")
            if service_name:
                services.append(service_name)
        elif self.action_type == ActionType.EXTERNAL_API_CALL:
            # External APIs don't require internal services
            pass
        return services

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "action_id": self.action_id,
            "action_type": self.action_type.value,
            "name": self.name,
            "description": self.description,
            "config": self.config,
            "condition": self.condition,
            "depends_on": self.depends_on,
            "retry_count": self.retry_count,
            "retry_delay": self.retry_delay,
            "timeout_seconds": self.timeout_seconds,
            "on_error": self.on_error,
            "continue_on_error": self.continue_on_error
        }
