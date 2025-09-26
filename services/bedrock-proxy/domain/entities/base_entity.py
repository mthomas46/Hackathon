"""Base entity class for common domain entity functionality."""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional


@dataclass
class BaseEntity:
    """Base class for domain entities with common initialization patterns."""

    metadata: Optional[Dict[str, Any]] = None
    created_at: Optional[datetime] = None

    def __post_init__(self):
        """Initialize common entity fields."""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.metadata is None:
            self.metadata = {}

    def to_dict_common(self) -> Dict[str, Any]:
        """Convert common fields to dictionary representation."""
        return {
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict_common(cls, data: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Extract common fields from dictionary for entity creation."""
        return {
            'created_at': datetime.fromisoformat(data['created_at']) if data.get('created_at') else None,
            'metadata': data.get('metadata', {}),
            **kwargs
        }
