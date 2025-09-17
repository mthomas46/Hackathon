"""Execution ID Value Object"""

import uuid
from typing import Union


class ExecutionId:
    """Value object representing a workflow execution identifier."""

    def __init__(self, value: Union[str, uuid.UUID]):
        if isinstance(value, str):
            try:
                self._value = uuid.UUID(value)
            except ValueError:
                raise ValueError(f"Invalid execution ID format: {value}")
        elif isinstance(value, uuid.UUID):
            self._value = value
        else:
            raise TypeError(f"ExecutionId must be str or UUID, got {type(value)}")

    @classmethod
    def generate(cls) -> 'ExecutionId':
        """Generate a new unique execution ID."""
        return cls(uuid.uuid4())

    @property
    def value(self) -> str:
        """Get the string representation of the execution ID."""
        return str(self._value)

    @property
    def uuid(self) -> uuid.UUID:
        """Get the UUID representation of the execution ID."""
        return self._value

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"ExecutionId({self.value})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ExecutionId):
            return NotImplemented
        return self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)
