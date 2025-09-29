"""Domain specifications for business rules."""

from abc import ABC, abstractmethod
from typing import Any

from ..entities import Document, Analysis, Finding


class Specification(ABC):
    """Base class for domain specifications."""

    @abstractmethod
    def is_satisfied_by(self, candidate: Any) -> bool:
        """Check if candidate satisfies the specification."""
        pass

    def __and__(self, other: 'Specification') -> 'Specification':
        """Combine specifications with AND logic."""
        return AndSpecification(self, other)

    def __or__(self, other: 'Specification') -> 'Specification':
        """Combine specifications with OR logic."""
        return OrSpecification(self, other)

    def __invert__(self) -> 'Specification':
        """Negate specification."""
        return NotSpecification(self)


class AndSpecification(Specification):
    """AND combination of specifications."""

    def __init__(self, left: Specification, right: Specification):
        """Initialize AND specification."""
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: Any) -> bool:
        """Check if candidate satisfies both specifications."""
        return self.left.is_satisfied_by(candidate) and self.right.is_satisfied_by(candidate)


class OrSpecification(Specification):
    """OR combination of specifications."""

    def __init__(self, left: Specification, right: Specification):
        """Initialize OR specification."""
        self.left = left
        self.right = right

    def is_satisfied_by(self, candidate: Any) -> bool:
        """Check if candidate satisfies either specification."""
        return self.left.is_satisfied_by(candidate) or self.right.is_satisfied_by(candidate)


class NotSpecification(Specification):
    """NOT specification."""

    def __init__(self, specification: Specification):
        """Initialize NOT specification."""
        self.specification = specification

    def is_satisfied_by(self, candidate: Any) -> bool:
        """Check if candidate does not satisfy the specification."""
        return not self.specification.is_satisfied_by(candidate)


class DocumentSpecifications:
    """Specifications for Document entities."""

    @staticmethod
    def has_author(author: str) -> Specification:
        """Specification for documents with specific author."""
        class HasAuthorSpec(Specification):
            def is_satisfied_by(self, candidate: Document) -> bool:
                return candidate.metadata.author == author
        return HasAuthorSpec()

    @staticmethod
    def is_recent(days: int = 30) -> Specification:
        """Specification for recently updated documents."""
        from datetime import datetime, timedelta

        class IsRecentSpec(Specification):
            def __init__(self, days: int):
                self.cutoff_date = datetime.now() - timedelta(days=days)

            def is_satisfied_by(self, candidate: Document) -> bool:
                return candidate.metadata.updated_at >= self.cutoff_date
        return IsRecentSpec(days)

    @staticmethod
    def has_tag(tag: str) -> Specification:
        """Specification for documents with specific tag."""
        class HasTagSpec(Specification):
            def is_satisfied_by(self, candidate: Document) -> bool:
                return tag in candidate.metadata.tags
        return HasTagSpec()

    @staticmethod
    def word_count_above(count: int) -> Specification:
        """Specification for documents with word count above threshold."""
        class WordCountAboveSpec(Specification):
            def is_satisfied_by(self, candidate: Document) -> bool:
                return candidate.word_count > count
        return WordCountAboveSpec()


class AnalysisSpecifications:
    """Specifications for Analysis entities."""

    @staticmethod
    def has_status(status: str) -> Specification:
        """Specification for analyses with specific status."""
        class HasStatusSpec(Specification):
            def is_satisfied_by(self, candidate: Analysis) -> bool:
                return candidate.status.value == status
        return HasStatusSpec()

    @staticmethod
    def is_completed() -> Specification:
        """Specification for completed analyses."""
        class IsCompletedSpec(Specification):
            def is_satisfied_by(self, candidate: Analysis) -> bool:
                return candidate.is_completed()
        return IsCompletedSpec()

    @staticmethod
    def has_analysis_type(analysis_type: str) -> Specification:
        """Specification for analyses of specific type."""
        class HasAnalysisTypeSpec(Specification):
            def is_satisfied_by(self, candidate: Analysis) -> bool:
                return candidate.analysis_type == analysis_type
        return HasAnalysisTypeSpec()


class FindingSpecifications:
    """Specifications for Finding entities."""

    @staticmethod
    def has_severity(severity: str) -> Specification:
        """Specification for findings with specific severity."""
        class HasSeveritySpec(Specification):
            def is_satisfied_by(self, candidate: Finding) -> bool:
                return candidate.severity.value == severity
        return HasSeveritySpec()

    @staticmethod
    def has_category(category: str) -> Specification:
        """Specification for findings with specific category."""
        class HasCategorySpec(Specification):
            def is_satisfied_by(self, candidate: Finding) -> bool:
                return candidate.category == category
        return HasCategorySpec()

    @staticmethod
    def is_unresolved() -> Specification:
        """Specification for unresolved findings."""
        class IsUnresolvedSpec(Specification):
            def is_satisfied_by(self, candidate: Finding) -> bool:
                return not candidate.is_resolved()
        return IsUnresolvedSpec()

    @staticmethod
    def confidence_above(threshold: float) -> Specification:
        """Specification for findings with confidence above threshold."""
        class ConfidenceAboveSpec(Specification):
            def is_satisfied_by(self, candidate: Finding) -> bool:
                return candidate.confidence >= threshold
        return ConfidenceAboveSpec()
