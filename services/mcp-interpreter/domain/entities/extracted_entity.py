"""Extracted Entity - Domain Layer."""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional

from services.mcp_interpreter.domain.value_objects.entity_type import EntityType


@dataclass
class ExtractedEntity:
    """
    Represents an entity extracted from a natural language query.
    
    Entities are the "nouns" of the query - the things being referenced.
    """
    
    # Entity details
    text: str                           # Original text from query
    entity_type: EntityType             # Type of entity
    normalized_value: str               # Normalized/standardized value
    
    # Position in query
    start_pos: int = 0                  # Start character position
    end_pos: int = 0                    # End character position
    
    # Confidence
    confidence: float = 1.0             # Confidence score (0.0-1.0)
    
    # Additional metadata
    attributes: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate the entity."""
        if not self.text:
            raise ValueError("ExtractedEntity must have text")
        if not isinstance(self.entity_type, EntityType):
            raise TypeError("entity_type must be an instance of EntityType")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
    
    @property
    def is_organizational(self) -> bool:
        """Check if entity is organizational."""
        return self.entity_type.is_organizational
    
    @property
    def is_technical(self) -> bool:
        """Check if entity is technical."""
        return self.entity_type.is_technical
    
    @property
    def is_temporal(self) -> bool:
        """Check if entity is time-related."""
        return self.entity_type.is_temporal
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "text": self.text,
            "entity_type": self.entity_type.value,
            "normalized_value": self.normalized_value,
            "start_pos": self.start_pos,
            "end_pos": self.end_pos,
            "confidence": self.confidence,
            "attributes": self.attributes,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ExtractedEntity":
        """Create from dictionary."""
        return cls(
            text=data["text"],
            entity_type=EntityType(data["entity_type"]),
            normalized_value=data["normalized_value"],
            start_pos=data.get("start_pos", 0),
            end_pos=data.get("end_pos", 0),
            confidence=data.get("confidence", 1.0),
            attributes=data.get("attributes", {}),
        )
    
    def __repr__(self) -> str:
        """String representation."""
        return (
            f"ExtractedEntity(text='{self.text}', "
            f"type={self.entity_type.value}, "
            f"confidence={self.confidence:.2f})"
        )

