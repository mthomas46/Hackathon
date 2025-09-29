"""Query Domain Entities.

Core domain entities for query interpretation and intent recognition.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, List
from uuid import uuid4


class QueryIntent(Enum):
    """Enumeration of supported query intents."""

    WORKFLOW_EXECUTION = "workflow_execution"
    DOCUMENT_ANALYSIS = "document_analysis"
    CONTENT_GENERATION = "content_generation"
    GENERAL_QUERY = "general_query"
    UNKNOWN = "unknown"


@dataclass
class UserQuery:
    """Domain entity representing a user query."""

    query: str
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        """Validate query entity."""
        if not self.query or not self.query.strip():
            raise ValueError("Query cannot be empty")
        if len(self.query) > 10000:  # Reasonable limit
            raise ValueError("Query too long (max 10000 characters)")

    def get_cleaned_query(self) -> str:
        """Get cleaned and normalized query text."""
        return self.query.strip()

    def has_context(self) -> bool:
        """Check if query has additional context."""
        return bool(self.context and self.context.get('documents'))


@dataclass
class QueryResult:
    """Domain entity representing query interpretation results."""

    intent: QueryIntent
    confidence: float
    entities: Dict[str, Any]
    response_text: str
    query_id: str
    processed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    processing_time_ms: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate query result."""
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")
        if not self.entities:
            self.entities = {}

    def is_high_confidence(self) -> bool:
        """Check if result has high confidence."""
        return self.confidence >= 0.8

    def get_primary_entity(self) -> Optional[str]:
        """Get the primary identified entity."""
        return self.entities.get("primary", self.entities.get("workflow"))

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "intent": self.intent.value,
            "confidence": self.confidence,
            "entities": self.entities,
            "response_text": self.response_text,
            "query_id": self.query_id,
            "processed_at": self.processed_at.isoformat(),
            "processing_time_ms": self.processing_time_ms,
            "metadata": self.metadata,
        }
