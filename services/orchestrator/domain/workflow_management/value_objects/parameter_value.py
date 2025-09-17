"""Parameter Value Value Object"""

from typing import Any, Union
from enum import Enum


class ParameterType(Enum):
    """Parameter data types."""
    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    FILE = "file"


class ParameterValue:
    """Value object representing a parameter value with type safety."""

    def __init__(self, value: Any, param_type: ParameterType):
        self._value = value
        self._param_type = param_type
        self._validate()

    def _validate(self):
        """Validate the value against its type."""
        if self._value is None:
            return

        if self._param_type == ParameterType.STRING and not isinstance(self._value, str):
            raise ValueError(f"Parameter must be a string, got {type(self._value)}")
        elif self._param_type == ParameterType.INTEGER and not isinstance(self._value, int):
            raise ValueError(f"Parameter must be an integer, got {type(self._value)}")
        elif self._param_type == ParameterType.FLOAT and not isinstance(self._value, (int, float)):
            raise ValueError(f"Parameter must be a number, got {type(self._value)}")
        elif self._param_type == ParameterType.BOOLEAN and not isinstance(self._value, bool):
            raise ValueError(f"Parameter must be a boolean, got {type(self._value)}")
        elif self._param_type == ParameterType.ARRAY and not isinstance(self._value, list):
            raise ValueError(f"Parameter must be an array, got {type(self._value)}")

    @property
    def value(self) -> Any:
        """Get the parameter value."""
        return self._value

    @property
    def param_type(self) -> ParameterType:
        """Get the parameter type."""
        return self._param_type

    def __str__(self) -> str:
        return str(self._value)

    def __repr__(self) -> str:
        return f"ParameterValue({self._value}, {self._param_type.value})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ParameterValue):
            return NotImplemented
        return self._value == other._value and self._param_type == other._param_type
