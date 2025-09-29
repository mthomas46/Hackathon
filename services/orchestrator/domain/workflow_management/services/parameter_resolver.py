"""Parameter Resolver Domain Service"""

from typing import Dict, Any, List, Optional, Tuple

from ..entities.workflow import Workflow
from ..entities.workflow_parameter import WorkflowParameter


class ParameterResolver:
    """Domain service for resolving workflow parameters."""

    @staticmethod
    def resolve_parameters(
        workflow: Workflow,
        provided_params: Dict[str, Any],
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Resolve all parameters for workflow execution."""
        resolved = {}

        for param in workflow.parameters:
            value = ParameterResolver._resolve_parameter_value(param, provided_params, context)
            resolved[param.name] = value

        return resolved

    @staticmethod
    def _resolve_parameter_value(
        param: WorkflowParameter,
        provided_params: Dict[str, Any],
        context: Optional[Dict[str, Any]]
    ) -> Any:
        """Resolve a single parameter value."""
        # Check if parameter was provided
        if param.name in provided_params:
            value = provided_params[param.name]
            # Validate the provided value
            valid, error = param.validate_value(value)
            if not valid:
                raise ValueError(f"Invalid value for parameter '{param.name}': {error}")
            return value

        # Use default value if available
        if param.default_value is not None:
            return param.default_value

        # Try to resolve from context
        if context and param.name in context:
            value = context[param.name]
            valid, error = param.validate_value(value)
            if valid:
                return value

        # Parameter is required but not provided
        if param.required:
            raise ValueError(f"Required parameter '{param.name}' not provided")

        return None

    @staticmethod
    def validate_parameter_resolution(
        workflow: Workflow,
        resolved_params: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Validate that all required parameters are resolved."""
        errors = []

        for param in workflow.parameters:
            if param.required and resolved_params.get(param.name) is None:
                errors.append(f"Required parameter '{param.name}' could not be resolved")

        return len(errors) == 0, errors

    @staticmethod
    def get_missing_parameters(
        workflow: Workflow,
        provided_params: Dict[str, Any]
    ) -> List[str]:
        """Get list of missing required parameters."""
        missing = []

        for param in workflow.parameters:
            if param.required and param.name not in provided_params:
                # Check if default value exists
                if param.default_value is None:
                    missing.append(param.name)

        return missing
