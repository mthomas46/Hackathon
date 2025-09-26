"""Workflow ID value object."""

import uuid
from typing import Union


class WorkflowId:
    """Value object representing a unique workflow identifier."""

    def __init__(self, value: Union[str, uuid.UUID]):
        """Initialize WorkflowId with string or UUID value."""
        if isinstance(value, str):
            try:
                self._value = uuid.UUID(value)
            except ValueError:
                raise ValueError(f"Invalid UUID string: {value}")
        elif isinstance(value, uuid.UUID):
            self._value = value
        else:
            raise TypeError(f"WorkflowId must be string or UUID, got {type(value)}")

    @property
    def value(self) -> uuid.UUID:
        """Get the UUID value."""
        return self._value

    def __str__(self) -> str:
        """String representation."""
        return str(self._value)

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"WorkflowId({self._value})"

    def __eq__(self, other) -> bool:
        """Check equality with another WorkflowId."""
        if not isinstance(other, WorkflowId):
            return NotImplemented
        return self._value == other._value

    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash(self._value)

    @classmethod
    def generate(cls) -> 'WorkflowId':
        """Generate a new unique WorkflowId."""
        return cls(uuid.uuid4())
