"""Workflow Validator Domain Service"""

from typing import List, Tuple, Dict, Any

from ..entities.workflow import Workflow
from ..entities.workflow_parameter import WorkflowParameter
from ..entities.workflow_action import WorkflowAction


class WorkflowValidator:
    """Domain service for validating workflow definitions."""

    @staticmethod
    def validate_workflow(workflow: Workflow) -> Tuple[bool, List[str]]:
        """Validate a complete workflow definition."""
        errors = []

        # Validate basic workflow properties
        if not workflow.name or len(workflow.name.strip()) == 0:
            errors.append("Workflow name is required")

        if not workflow.created_by or len(workflow.created_by.strip()) == 0:
            errors.append("Workflow creator is required")

        # Validate parameters
        param_errors = WorkflowValidator._validate_parameters(workflow.parameters)
        errors.extend(param_errors)

        # Validate actions
        action_errors = WorkflowValidator._validate_actions(workflow.actions)
        errors.extend(action_errors)

        # Validate action dependencies
        dep_errors = WorkflowValidator._validate_dependencies(workflow.actions)
        errors.extend(dep_errors)

        return len(errors) == 0, errors

    @staticmethod
    def _validate_parameters(parameters: List[WorkflowParameter]) -> List[str]:
        """Validate workflow parameters."""
        errors = []

        param_names = set()
        for param in parameters:
            # Check for duplicate names
            if param.name in param_names:
                errors.append(f"Duplicate parameter name: {param.name}")
            param_names.add(param.name)

            # Validate parameter properties
            if not param.name or len(param.name.strip()) == 0:
                errors.append("Parameter name cannot be empty")

            # Validate default value type
            if param.default_value is not None:
                valid, error = param.validate_value(param.default_value)
                if not valid:
                    errors.append(f"Invalid default value for parameter '{param.name}': {error}")

        return errors

    @staticmethod
    def _validate_actions(actions: List[WorkflowAction]) -> List[str]:
        """Validate workflow actions."""
        errors = []

        action_ids = set()
        for action in actions:
            # Check for duplicate IDs
            if action.action_id in action_ids:
                errors.append(f"Duplicate action ID: {action.action_id}")
            action_ids.add(action.action_id)

            # Validate action properties
            if not action.name or len(action.name.strip()) == 0:
                errors.append(f"Action '{action.action_id}' name cannot be empty")

            # Validate retry configuration
            if action.retry_count < 0:
                errors.append(f"Action '{action.action_id}' retry count cannot be negative")

            if action.timeout_seconds <= 0:
                errors.append(f"Action '{action.action_id}' timeout must be positive")

            # Validate action-specific configuration
            config_errors = WorkflowValidator._validate_action_config(action)
            errors.extend(config_errors)

        return errors

    @staticmethod
    def _validate_action_config(action: WorkflowAction) -> List[str]:
        """Validate action-specific configuration."""
        errors = []

        if action.action_type.value == "service_call":
            if not action.config.get("service"):
                errors.append(f"Action '{action.action_id}' missing required 'service' configuration")
            if not action.config.get("endpoint"):
                errors.append(f"Action '{action.action_id}' missing required 'endpoint' configuration")

        elif action.action_type.value == "prompt_execution":
            if not action.config.get("prompt_id"):
                errors.append(f"Action '{action.action_id}' missing required 'prompt_id' configuration")

        elif action.action_type.value == "external_api_call":
            if not action.config.get("url"):
                errors.append(f"Action '{action.action_id}' missing required 'url' configuration")
            if not action.config.get("method"):
                errors.append(f"Action '{action.action_id}' missing required 'method' configuration")

        return errors

    @staticmethod
    def _validate_dependencies(actions: List[WorkflowAction]) -> List[str]:
        """Validate action dependencies."""
        errors = []
        action_ids = {action.action_id for action in actions}

        for action in actions:
            for dep_id in action.depends_on:
                if dep_id not in action_ids:
                    errors.append(f"Action '{action.action_id}' depends on unknown action '{dep_id}'")

        # Check for circular dependencies
        if WorkflowValidator._has_circular_dependencies(actions):
            errors.append("Workflow contains circular dependencies")

        return errors

    @staticmethod
    def _has_circular_dependencies(actions: List[WorkflowAction]) -> bool:
        """Check if actions have circular dependencies."""
        # Build dependency graph
        graph = {action.action_id: set(action.depends_on) for action in actions}

        # Simple cycle detection using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, set()):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        for action_id in graph:
            if action_id not in visited:
                if has_cycle(action_id):
                    return True

        return False
