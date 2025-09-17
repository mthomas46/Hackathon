#!/usr/bin/env python3
"""
Workflow Management Models

Core data models for workflow definition, storage, and execution.
Supports parameterized workflows with actions and prompts.
"""

import json
import uuid
from typing import Dict, Any, List, Optional, Callable, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from services.shared.constants_new import ServiceNames
from services.shared.logging import fire_and_forget


class WorkflowStatus(Enum):
    """Workflow execution status."""
    DRAFT = "draft"
    ACTIVE = "active"
    ARCHIVED = "archived"
    DEPRECATED = "deprecated"


class WorkflowExecutionStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


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


class ParameterType(Enum):
    """Parameter data types."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    FILE = "file"


@dataclass
class WorkflowParameter:
    """Workflow parameter definition."""
    name: str
    type: ParameterType
    description: str = ""
    required: bool = True
    default_value: Optional[Any] = None
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    allowed_values: Optional[List[Any]] = None

    def validate_value(self, value: Any) -> tuple[bool, str]:
        """Validate a parameter value."""
        if value is None:
            if self.required:
                return False, f"Parameter '{self.name}' is required"
            return True, ""

        # Type validation
        if self.type == ParameterType.STRING and not isinstance(value, str):
            return False, f"Parameter '{self.name}' must be a string"
        elif self.type == ParameterType.INTEGER and not isinstance(value, int):
            return False, f"Parameter '{self.name}' must be an integer"
        elif self.type == ParameterType.FLOAT and not isinstance(value, (int, float)):
            return False, f"Parameter '{self.name}' must be a number"
        elif self.type == ParameterType.BOOLEAN and not isinstance(value, bool):
            return False, f"Parameter '{self.name}' must be a boolean"
        elif self.type == ParameterType.ARRAY and not isinstance(value, list):
            return False, f"Parameter '{self.name}' must be an array"

        # Allowed values validation
        if self.allowed_values and value not in self.allowed_values:
            return False, f"Parameter '{self.name}' must be one of: {self.allowed_values}"

        # Custom validation rules
        if self.validation_rules:
            min_length = self.validation_rules.get("min_length")
            max_length = self.validation_rules.get("max_length")
            pattern = self.validation_rules.get("pattern")

            if min_length and isinstance(value, (str, list)) and len(value) < min_length:
                return False, f"Parameter '{self.name}' must be at least {min_length} characters long"

            if max_length and isinstance(value, (str, list)) and len(value) > max_length:
                return False, f"Parameter '{self.name}' must be at most {max_length} characters long"

            if pattern and isinstance(value, str):
                import re
                if not re.match(pattern, value):
                    return False, f"Parameter '{self.name}' does not match required pattern"

        return True, ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "type": self.type.value,
            "description": self.description,
            "required": self.required,
            "default_value": self.default_value,
            "validation_rules": self.validation_rules,
            "allowed_values": self.allowed_values
        }


@dataclass
class WorkflowAction:
    """Individual action within a workflow."""
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

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
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

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowAction':
        """Create from dictionary."""
        return cls(
            action_id=data.get("action_id", str(uuid.uuid4())),
            action_type=ActionType(data["action_type"]),
            name=data.get("name", ""),
            description=data.get("description", ""),
            config=data.get("config", {}),
            condition=data.get("condition"),
            depends_on=data.get("depends_on", []),
            retry_count=data.get("retry_count", 0),
            retry_delay=data.get("retry_delay", 1.0),
            timeout_seconds=data.get("timeout_seconds", 30),
            on_error=data.get("on_error"),
            continue_on_error=data.get("continue_on_error", False)
        )


@dataclass
class WorkflowDefinition:
    """Complete workflow definition."""
    workflow_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    description: str = ""
    version: str = "1.0.0"

    # Status and metadata
    status: WorkflowStatus = WorkflowStatus.DRAFT
    created_by: str = ""
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    tags: List[str] = field(default_factory=list)

    # Parameters
    parameters: List[WorkflowParameter] = field(default_factory=list)

    # Actions (workflow steps)
    actions: List[WorkflowAction] = field(default_factory=list)

    # Workflow-level configuration
    timeout_seconds: int = 300  # 5 minutes default
    max_concurrent_actions: int = 5
    notify_on_completion: bool = False
    notification_channels: List[str] = field(default_factory=list)

    # Execution statistics
    total_executions: int = 0
    successful_executions: int = 0
    failed_executions: int = 0
    average_execution_time: float = 0.0

    def add_parameter(self, parameter: WorkflowParameter):
        """Add a parameter to the workflow."""
        self.parameters.append(parameter)
        self.updated_at = datetime.now()

    def add_action(self, action: WorkflowAction):
        """Add an action to the workflow."""
        self.actions.append(action)
        self.updated_at = datetime.now()

    def get_parameter(self, name: str) -> Optional[WorkflowParameter]:
        """Get a parameter by name."""
        for param in self.parameters:
            if param.name == name:
                return param
        return None

    def get_action(self, action_id: str) -> Optional[WorkflowAction]:
        """Get an action by ID."""
        for action in self.actions:
            if action.action_id == action_id:
                return action
        return None

    def validate_parameters(self, input_params: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate input parameters against workflow definition."""
        errors = []

        # Check required parameters
        for param in self.parameters:
            if param.name not in input_params:
                if param.required:
                    errors.append(f"Missing required parameter: {param.name}")
                elif param.default_value is not None:
                    input_params[param.name] = param.default_value
            else:
                # Validate parameter value
                valid, error_msg = param.validate_value(input_params[param.name])
                if not valid:
                    errors.append(error_msg)

        # Check for extra parameters
        defined_param_names = {p.name for p in self.parameters}
        for param_name in input_params:
            if param_name not in defined_param_names:
                errors.append(f"Unexpected parameter: {param_name}")

        return len(errors) == 0, errors

    def get_execution_plan(self) -> List[List[str]]:
        """Get execution plan based on action dependencies."""
        # Simple topological sort for action dependencies
        action_map = {action.action_id: action for action in self.actions}
        executed = set()
        result = []

        def can_execute(action: WorkflowAction) -> bool:
            """Check if action can be executed."""
            return all(dep in executed for dep in action.depends_on)

        while len(executed) < len(self.actions):
            current_level = []

            for action in self.actions:
                if action.action_id not in executed and can_execute(action):
                    current_level.append(action.action_id)

            if not current_level:
                # Circular dependency or other issue
                break

            result.append(current_level)
            executed.update(current_level)

        return result

    def update_execution_stats(self, success: bool, execution_time: float):
        """Update execution statistics."""
        self.total_executions += 1

        if success:
            self.successful_executions += 1
        else:
            self.failed_executions += 1

        # Update average execution time
        if self.total_executions == 1:
            self.average_execution_time = execution_time
        else:
            self.average_execution_time = (
                (self.average_execution_time * (self.total_executions - 1)) + execution_time
            ) / self.total_executions

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage/serialization."""
        return {
            "workflow_id": self.workflow_id,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "status": self.status.value,
            "created_by": self.created_by,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "tags": self.tags,
            "parameters": [p.to_dict() for p in self.parameters],
            "actions": [a.to_dict() for a in self.actions],
            "timeout_seconds": self.timeout_seconds,
            "max_concurrent_actions": self.max_concurrent_actions,
            "notify_on_completion": self.notify_on_completion,
            "notification_channels": self.notification_channels,
            "total_executions": self.total_executions,
            "successful_executions": self.successful_executions,
            "failed_executions": self.failed_executions,
            "average_execution_time": self.average_execution_time
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowDefinition':
        """Create from dictionary."""
        workflow = cls(
            workflow_id=data.get("workflow_id", str(uuid.uuid4())),
            name=data.get("name", ""),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            status=WorkflowStatus(data.get("status", "draft")),
            created_by=data.get("created_by", ""),
            tags=data.get("tags", []),
            timeout_seconds=data.get("timeout_seconds", 300),
            max_concurrent_actions=data.get("max_concurrent_actions", 5),
            notify_on_completion=data.get("notify_on_completion", False),
            notification_channels=data.get("notification_channels", []),
            total_executions=data.get("total_executions", 0),
            successful_executions=data.get("successful_executions", 0),
            failed_executions=data.get("failed_executions", 0),
            average_execution_time=data.get("average_execution_time", 0.0)
        )

        # Parse timestamps
        if "created_at" in data:
            workflow.created_at = datetime.fromisoformat(data["created_at"])
        if "updated_at" in data:
            workflow.updated_at = datetime.fromisoformat(data["updated_at"])

        # Parse parameters
        for param_data in data.get("parameters", []):
            workflow.parameters.append(WorkflowParameter(
                name=param_data["name"],
                type=ParameterType(param_data["type"]),
                description=param_data.get("description", ""),
                required=param_data.get("required", True),
                default_value=param_data.get("default_value"),
                validation_rules=param_data.get("validation_rules", {}),
                allowed_values=param_data.get("allowed_values")
            ))

        # Parse actions
        for action_data in data.get("actions", []):
            workflow.actions.append(WorkflowAction.from_dict(action_data))

        return workflow


@dataclass
class WorkflowExecution:
    """Workflow execution instance."""
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    workflow_id: str = ""
    initiated_by: str = ""
    input_parameters: Dict[str, Any] = field(default_factory=dict)

    # Execution status
    status: WorkflowExecutionStatus = WorkflowExecutionStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_seconds: float = 0.0

    # Execution results
    action_results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error_message: Optional[str] = None

    # Execution metadata
    current_action: Optional[str] = None
    completed_actions: List[str] = field(default_factory=list)
    failed_actions: List[str] = field(default_factory=list)

    def start_execution(self):
        """Start workflow execution."""
        self.status = WorkflowExecutionStatus.RUNNING
        self.started_at = datetime.now()

    def complete_execution(self, success: bool = True, output: Dict[str, Any] = None):
        """Complete workflow execution."""
        self.completed_at = datetime.now()
        self.execution_time_seconds = (self.completed_at - self.started_at).total_seconds() if self.started_at else 0

        if success:
            self.status = WorkflowExecutionStatus.COMPLETED
            if output:
                self.output_data.update(output)
        else:
            self.status = WorkflowExecutionStatus.FAILED

    def fail_execution(self, error_message: str):
        """Mark execution as failed."""
        self.status = WorkflowExecutionStatus.FAILED
        self.error_message = error_message
        self.completed_at = datetime.now()
        self.execution_time_seconds = (self.completed_at - self.started_at).total_seconds() if self.started_at else 0

    def update_action_result(self, action_id: str, result: Dict[str, Any]):
        """Update result for a specific action."""
        self.action_results[action_id] = result

        if result.get("success", False):
            if action_id not in self.completed_actions:
                self.completed_actions.append(action_id)
        else:
            if action_id not in self.failed_actions:
                self.failed_actions.append(action_id)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "execution_id": self.execution_id,
            "workflow_id": self.workflow_id,
            "initiated_by": self.initiated_by,
            "input_parameters": self.input_parameters,
            "status": self.status.value,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "execution_time_seconds": self.execution_time_seconds,
            "action_results": self.action_results,
            "output_data": self.output_data,
            "error_message": self.error_message,
            "current_action": self.current_action,
            "completed_actions": self.completed_actions,
            "failed_actions": self.failed_actions
        }


# Predefined workflow templates for common use cases
WORKFLOW_TEMPLATES = {
    "document_analysis": {
        "name": "Document Analysis Workflow",
        "description": "Analyze documents for quality, consistency, and insights",
        "parameters": [
            {
                "name": "document_urls",
                "type": "array",
                "description": "List of document URLs to analyze",
                "required": True
            },
            {
                "name": "analysis_types",
                "type": "array",
                "description": "Types of analysis to perform",
                "required": False,
                "default_value": ["quality", "consistency"],
                "allowed_values": ["quality", "consistency", "sentiment", "topics"]
            }
        ],
        "actions": [
            {
                "action_type": "service_call",
                "name": "Ingest Documents",
                "description": "Ingest documents from provided URLs",
                "config": {
                    "service": "source_agent",
                    "endpoint": "/ingest",
                    "method": "POST",
                    "parameters": {
                        "source_type": "url",
                        "urls": "{{document_urls}}"
                    }
                }
            },
            {
                "action_type": "service_call",
                "name": "Analyze Documents",
                "description": "Run analysis on ingested documents",
                "config": {
                    "service": "analysis_service",
                    "endpoint": "/analyze",
                    "method": "POST",
                    "parameters": {
                        "documents": "{{ingest_result.documents}}",
                        "analysis_types": "{{analysis_types}}"
                    }
                },
                "depends_on": ["ingest"]
            },
            {
                "action_type": "service_call",
                "name": "Generate Summary",
                "description": "Generate summary of analysis results",
                "config": {
                    "service": "summarizer_hub",
                    "endpoint": "/summarize",
                    "method": "POST",
                    "parameters": {
                        "content": "{{analysis_result.findings}}",
                        "content_type": "technical_document"
                    }
                },
                "depends_on": ["analyze"]
            }
        ]
    },

    "pr_confidence_analysis": {
        "name": "PR Confidence Analysis Workflow",
        "description": "Analyze pull request confidence based on requirements and documentation",
        "parameters": [
            {
                "name": "pr_number",
                "type": "integer",
                "description": "Pull request number",
                "required": True
            },
            {
                "name": "repository",
                "type": "string",
                "description": "Repository name (owner/repo)",
                "required": True
            },
            {
                "name": "jira_ticket",
                "type": "string",
                "description": "Associated Jira ticket ID",
                "required": False
            }
        ],
        "actions": [
            {
                "action_type": "service_call",
                "name": "Fetch PR Data",
                "description": "Fetch pull request data from GitHub",
                "config": {
                    "service": "source_agent",
                    "endpoint": "/github/pr",
                    "method": "GET",
                    "parameters": {
                        "pr_number": "{{pr_number}}",
                        "repository": "{{repository}}"
                    }
                }
            },
            {
                "action_type": "service_call",
                "name": "Fetch Jira Data",
                "description": "Fetch Jira ticket data if provided",
                "config": {
                    "service": "source_agent",
                    "endpoint": "/jira/issue",
                    "method": "GET",
                    "parameters": {
                        "issue_id": "{{jira_ticket}}"
                    }
                },
                "condition": "jira_ticket is not None and jira_ticket != ''"
            },
            {
                "action_type": "service_call",
                "name": "Analyze Confidence",
                "description": "Analyze PR confidence against requirements",
                "config": {
                    "service": "analysis_service",
                    "endpoint": "/pr_confidence",
                    "method": "POST",
                    "parameters": {
                        "pr_data": "{{pr_fetch_result}}",
                        "jira_data": "{{jira_fetch_result}}",
                        "repository": "{{repository}}"
                    }
                },
                "depends_on": ["pr_fetch"]
            }
        ]
    }
}


def create_workflow_from_template(template_name: str, customizations: Dict[str, Any] = None) -> WorkflowDefinition:
    """Create a workflow from a predefined template."""
    if template_name not in WORKFLOW_TEMPLATES:
        raise ValueError(f"Unknown workflow template: {template_name}")

    template = WORKFLOW_TEMPLATES[template_name]

    # Create workflow definition
    workflow = WorkflowDefinition(
        name=template["name"],
        description=template["description"]
    )

    # Add parameters
    for param_data in template["parameters"]:
        workflow.add_parameter(WorkflowParameter(
            name=param_data["name"],
            type=ParameterType(param_data["type"]),
            description=param_data["description"],
            required=param_data["required"],
            default_value=param_data.get("default_value"),
            allowed_values=param_data.get("allowed_values")
        ))

    # Add actions
    for action_data in template["actions"]:
        action = WorkflowAction(
            action_type=ActionType(action_data["action_type"]),
            name=action_data["name"],
            description=action_data["description"],
            config=action_data["config"],
            depends_on=action_data.get("depends_on", [])
        )
        workflow.add_action(action)

    # Apply customizations
    if customizations:
        if "name" in customizations:
            workflow.name = customizations["name"]
        if "description" in customizations:
            workflow.description = customizations["description"]
        if "parameters" in customizations:
            # Add additional parameters
            for param_data in customizations["parameters"]:
                workflow.add_parameter(WorkflowParameter(
                    name=param_data["name"],
                    type=ParameterType(param_data["type"]),
                    description=param_data.get("description", ""),
                    required=param_data.get("required", True),
                    default_value=param_data.get("default_value")
                ))

    return workflow
