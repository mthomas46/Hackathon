"""Base Value Object Class"""

from abc import ABC
from typing import Any


class BaseValueObject(ABC):
    """Base class for all value objects."""

    def __eq__(self, other: object) -> bool:
        """Check equality based on all attributes."""
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        """Generate hash based on all attributes."""
        return hash(tuple(sorted(self.__dict__.items())))

    def __repr__(self) -> str:
        """String representation of value object."""
        attrs = ', '.join(f'{k}={v}' for k, v in self.__dict__.items())
        return f"{self.__class__.__name__}({attrs})"
