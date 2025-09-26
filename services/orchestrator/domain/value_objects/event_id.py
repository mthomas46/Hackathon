"""Event ID value object."""

import uuid
from typing import Union


class EventId:
    """Value object representing a unique event identifier."""

    def __init__(self, value: Union[str, uuid.UUID]):
        """Initialize EventId with string or UUID value."""
        if isinstance(value, str):
            try:
                self._value = uuid.UUID(value)
            except ValueError:
                raise ValueError(f"Invalid UUID string: {value}")
        elif isinstance(value, uuid.UUID):
            self._value = value
        else:
            raise TypeError(f"EventId must be string or UUID, got {type(value)}")

    @property
    def value(self) -> uuid.UUID:
        """Get the UUID value."""
        return self._value

    def __str__(self) -> str:
        """String representation."""
        return str(self._value)

    def __eq__(self, other) -> bool:
        """Check equality with another EventId."""
        if not isinstance(other, EventId):
            return NotImplemented
        return self._value == other._value

    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash(self._value)

    @classmethod
    def generate(cls) -> 'EventId':
        """Generate a new unique EventId."""
        return cls(uuid.uuid4())
