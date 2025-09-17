"""Service ID Value Object"""

from typing import Union


class ServiceId:
    """Value object representing a service identifier."""

    def __init__(self, value: str):
        if not value or not value.strip():
            raise ValueError("Service ID cannot be empty")
        self._value = value.strip()

    @property
    def value(self) -> str:
        """Get the service ID value."""
        return self._value

    def __str__(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return f"ServiceId({self._value})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ServiceId):
            return NotImplemented
        return self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)
