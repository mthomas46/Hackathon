"""Workflow Parameter Entity"""

from typing import Any, Optional, List, Dict
from dataclasses import dataclass, field

from ..value_objects.parameter_value import ParameterType


@dataclass
class WorkflowParameter:
    """Entity representing a workflow parameter."""

    name: str
    param_type: ParameterType
    description: str = ""
    required: bool = True
    default_value: Optional[Any] = None
    validation_rules: Dict[str, Any] = field(default_factory=dict)
    allowed_values: Optional[List[Any]] = None

    def __post_init__(self):
        """Validate parameter after initialization."""
        if not self.name or not self.name.strip():
            raise ValueError("Parameter name cannot be empty")

        if not isinstance(self.param_type, ParameterType):
            raise ValueError("Invalid parameter type")

    def validate_value(self, value: Any) -> tuple[bool, str]:
        """Validate a parameter value against this parameter definition."""
        if value is None:
            if self.required:
                return False, f"Parameter '{self.name}' is required"
            return True, ""

        # Type validation
        if self.param_type == ParameterType.STRING and not isinstance(value, str):
            return False, f"Parameter '{self.name}' must be a string"
        elif self.param_type == ParameterType.INTEGER and not isinstance(value, int):
            return False, f"Parameter '{self.name}' must be an integer"
        elif self.param_type == ParameterType.FLOAT and not isinstance(value, (int, float)):
            return False, f"Parameter '{self.name}' must be a number"
        elif self.param_type == ParameterType.BOOLEAN and not isinstance(value, bool):
            return False, f"Parameter '{self.name}' must be a boolean"
        elif self.param_type == ParameterType.ARRAY and not isinstance(value, list):
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

    def get_default_value(self) -> Any:
        """Get the default value for this parameter."""
        return self.default_value

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "name": self.name,
            "type": self.param_type.value,
            "description": self.description,
            "required": self.required,
            "default_value": self.default_value,
            "validation_rules": self.validation_rules,
            "allowed_values": self.allowed_values
        }
