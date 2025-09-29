"""Summary domain entity.

This module contains the Summary entity and related value objects
for the summarizer-hub domain.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4
from enum import Enum


class SummaryType(Enum):
    """Enumeration of summary types."""
    BRIEF = "brief"
    COMPREHENSIVE = "comprehensive"
    EXECUTIVE = "executive"
    TECHNICAL = "technical"


@dataclass(frozen=True)
class SummaryId:
    """Value object for Summary ID."""
    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("Summary ID cannot be empty")

    @classmethod
    def generate(cls) -> 'SummaryId':
        """Generate a new SummaryId."""
        return cls(str(uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass
class SummaryMetrics:
    """Value object for summary quality metrics."""
    compression_ratio: float = 0.0
    readability_score: float = 0.0
    coherence_score: float = 0.0
    factual_accuracy: float = 0.0
    key_points_coverage: float = 0.0
    custom_metrics: Dict[str, float] = field(default_factory=dict)


@dataclass
class Summary:
    """Summary entity.

    Represents a generated summary of a document with associated metadata
    and quality metrics.
    """

    id: SummaryId
    document_id: str  # Reference to the source document
    content: str
    summary_type: SummaryType
    provider: str  # AI provider/model used
    metrics: SummaryMetrics = field(default_factory=SummaryMetrics)
    created_at: datetime = field(default_factory=datetime.now)
    model_version: Optional[str] = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)

    def __post_init__(self):
        if not self.content or not self.content.strip():
            raise ValueError("Summary content cannot be empty")

        if not self.document_id:
            raise ValueError("Document ID is required")

        # Calculate basic compression ratio if not provided
        if self.metrics.compression_ratio == 0.0 and hasattr(self, '_source_length'):
            source_length = getattr(self, '_source_length', len(self.content) * 3)  # Estimate
            self.metrics.compression_ratio = len(self.content) / source_length

    def update_content(self, new_content: str) -> None:
        """Update the summary content."""
        if not new_content or not new_content.strip():
            raise ValueError("New content cannot be empty")

        self.content = new_content.strip()

    def update_metrics(self, **kwargs) -> None:
        """Update summary quality metrics."""
        for key, value in kwargs.items():
            if hasattr(self.metrics, key):
                setattr(self.metrics, key, value)
            else:
                self.metrics.custom_metrics[key] = value

    def add_tag(self, tag: str) -> None:
        """Add a tag to the summary."""
        if tag not in self.tags:
            self.tags.append(tag)

    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the summary."""
        if tag in self.tags:
            self.tags.remove(tag)

    def get_quality_score(self) -> float:
        """Calculate overall quality score based on metrics."""
        scores = [
            self.metrics.readability_score,
            self.metrics.coherence_score,
            self.metrics.factual_accuracy,
            self.metrics.key_points_coverage,
        ]

        # Filter out zero scores and calculate average
        valid_scores = [s for s in scores if s > 0]
        return sum(valid_scores) / len(valid_scores) if valid_scores else 0.0

    def is_high_quality(self, threshold: float = 0.8) -> bool:
        """Check if the summary meets quality threshold."""
        return self.get_quality_score() >= threshold

    @classmethod
    def create(
        cls,
        document_id: str,
        content: str,
        summary_type: SummaryType,
        provider: str,
        model_version: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        source_length: Optional[int] = None,
    ) -> 'Summary':
        """Factory method to create a new summary."""
        summary_id = SummaryId.generate()

        # Store source length for compression ratio calculation
        instance = cls(
            id=summary_id,
            document_id=document_id,
            content=content,
            summary_type=summary_type,
            provider=provider,
            model_version=model_version,
            parameters=parameters or {},
        )

        # Set compression ratio if source length provided
        if source_length:
            instance._source_length = source_length
            instance.metrics.compression_ratio = len(content) / source_length

        return instance
