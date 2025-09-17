"""Finding domain entity."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from .document import DocumentId


class Severity(Enum):
    """Finding severity levels."""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True)
class FindingId:
    """Value object for finding identifier."""
    value: str

    def __post_init__(self):
        if not self.value or not isinstance(self.value, str):
            raise ValueError("Finding ID must be a non-empty string")


@dataclass
class Finding:
    """Finding domain entity."""
    id: FindingId
    document_id: DocumentId
    analysis_id: str
    title: str
    description: str
    severity: Severity
    category: str
    location: Optional[Dict[str, Any]] = None  # line numbers, positions, etc.
    suggestion: Optional[str] = None
    confidence: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None

    def __post_init__(self):
        if not self.title or not isinstance(self.title, str):
            raise ValueError("Finding title must be a non-empty string")
        if len(self.title) > 200:
            raise ValueError("Finding title too long (max 200 characters)")

        if not self.description or not isinstance(self.description, str):
            raise ValueError("Finding description must be a non-empty string")

        if not self.category or not isinstance(self.category, str):
            raise ValueError("Finding category must be a non-empty string")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Confidence must be between 0.0 and 1.0")

    def resolve(self, resolved_by: str) -> None:
        """Mark finding as resolved."""
        if self.resolved_at is not None:
            raise ValueError("Finding is already resolved")

        self.resolved_at = datetime.now()
        self.resolved_by = resolved_by

    def is_resolved(self) -> bool:
        """Check if finding is resolved."""
        return self.resolved_at is not None

    @property
    def age_days(self) -> int:
        """Get age of finding in days."""
        resolved_time = self.resolved_at if self.resolved_at else datetime.now()
        return (resolved_time - self.created_at).days

    @property
    def severity_score(self) -> int:
        """Get numerical severity score for sorting."""
        severity_scores = {
            Severity.INFO: 1,
            Severity.LOW: 2,
            Severity.MEDIUM: 3,
            Severity.HIGH: 4,
            Severity.CRITICAL: 5
        }
        return severity_scores[self.severity]

    def to_dict(self) -> Dict[str, Any]:
        """Convert finding to dictionary representation."""
        return {
            'id': self.id.value,
            'document_id': self.document_id.value,
            'analysis_id': self.analysis_id,
            'title': self.title,
            'description': self.description,
            'severity': self.severity.value,
            'category': self.category,
            'location': self.location,
            'suggestion': self.suggestion,
            'confidence': self.confidence,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'resolved_by': self.resolved_by,
            'age_days': self.age_days,
            'is_resolved': self.is_resolved()
        }
