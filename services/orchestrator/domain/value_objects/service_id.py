"""Service ID value object."""

import uuid
from typing import Union


class ServiceId:
    """Value object representing a unique service identifier."""

    def __init__(self, value: Union[str, uuid.UUID]):
        """Initialize ServiceId with string or UUID value."""
        if isinstance(value, str):
            try:
                self._value = uuid.UUID(value)
            except ValueError:
                raise ValueError(f"Invalid UUID string: {value}")
        elif isinstance(value, uuid.UUID):
            self._value = value
        else:
            raise TypeError(f"ServiceId must be string or UUID, got {type(value)}")

    @property
    def value(self) -> uuid.UUID:
        """Get the UUID value."""
        return self._value

    def __str__(self) -> str:
        """String representation."""
        return str(self._value)

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"ServiceId({self._value})"

    def __eq__(self, other) -> bool:
        """Check equality with another ServiceId."""
        if not isinstance(other, ServiceId):
            return NotImplemented
        return self._value == other._value

    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash(self._value)

    @classmethod
    def generate(cls) -> 'ServiceId':
        """Generate a new unique ServiceId."""
        return cls(uuid.uuid4())
