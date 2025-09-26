"""Request ID value object."""

import uuid
from typing import Union


class RequestId:
    """Value object representing a unique request identifier."""

    def __init__(self, value: Union[str, uuid.UUID]):
        """Initialize RequestId.

        Args:
            value: String or UUID representing the request ID

        Raises:
            ValueError: If the value is not a valid UUID
        """
        if isinstance(value, str):
            try:
                self._value = uuid.UUID(value)
            except ValueError:
                raise ValueError(f"Invalid UUID string: {value}")
        elif isinstance(value, uuid.UUID):
            self._value = value
        else:
            raise ValueError(f"RequestId must be string or UUID, got {type(value)}")

    @property
    def value(self) -> uuid.UUID:
        """Get the UUID value."""
        return self._value

    def __str__(self) -> str:
        """String representation."""
        return str(self._value)

    def __repr__(self) -> str:
        """Detailed string representation."""
        return f"RequestId({self._value})"

    def __eq__(self, other) -> bool:
        """Check equality."""
        if not isinstance(other, RequestId):
            return False
        return self._value == other._value

    def __hash__(self) -> int:
        """Hash for use in sets and dictionaries."""
        return hash(self._value)

    @classmethod
    def generate(cls) -> 'RequestId':
        """Generate a new random RequestId."""
        return cls(uuid.uuid4())
