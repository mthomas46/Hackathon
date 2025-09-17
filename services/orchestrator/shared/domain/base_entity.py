"""Base Entity Class"""

from abc import ABC
from typing import Any, Dict
from dataclasses import dataclass


@dataclass
class BaseEntity(ABC):
    """Base class for all domain entities."""

    def to_dict(self) -> Dict[str, Any]:
        """Convert entity to dictionary representation."""
        result = {}
        for key, value in self.__dict__.items():
            if hasattr(value, 'to_dict'):
                result[key] = value.to_dict()
            elif hasattr(value, 'value'):
                # Handle value objects
                result[key] = value.value
            elif isinstance(value, dict):
                # Handle nested dictionaries
                result[key] = {k: v.value if hasattr(v, 'value') else v for k, v in value.items()}
            elif isinstance(value, list):
                # Handle lists
                result[key] = [item.value if hasattr(item, 'value') else item for item in value]
            else:
                result[key] = value
        return result

    def __eq__(self, other: object) -> bool:
        """Check equality based on all attributes."""
        if not isinstance(other, self.__class__):
            return NotImplemented
        return self.__dict__ == other.__dict__

    def __hash__(self) -> int:
        """Generate hash based on all attributes."""
        return hash(tuple(sorted(self.__dict__.items())))
