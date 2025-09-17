"""Service Capability Value Object"""

from typing import Optional


class ServiceCapability:
    """Value object representing a service capability."""

    def __init__(self, name: str, description: Optional[str] = None):
        self._name = name.strip()
        self._description = description.strip() if description else None

        self._validate()

    def _validate(self):
        """Validate capability data."""
        if not self._name:
            raise ValueError("Capability name cannot be empty")

        # Capability names should be snake_case
        if ' ' in self._name or self._name.upper() == self._name:
            raise ValueError("Capability name should be in snake_case format")

    @property
    def name(self) -> str:
        """Get the capability name."""
        return self._name

    @property
    def description(self) -> Optional[str]:
        """Get the capability description."""
        return self._description

    def __str__(self) -> str:
        return self._name

    def __repr__(self) -> str:
        return f"ServiceCapability({self._name})"

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ServiceCapability):
            return NotImplemented
        return self._name == other._name

    def __hash__(self) -> int:
        return hash(self._name)
