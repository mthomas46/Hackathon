"""Request DTOs for application layer."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


class ValidationHelper:
    """Helper class for common validation operations."""

    @staticmethod
    def validate_required_field(value: Any, field_name: str, errors: List[str]) -> None:
        """Validate that a required field is present and not empty."""
        if not value or not str(value).strip():
            errors.append(f"{field_name} is required")

    @staticmethod
    def validate_max_length(value: str, max_len: int, field_name: str, errors: List[str]) -> None:
        """Validate string length doesn't exceed maximum."""
        if len(value) > max_len:
            errors.append(f"{field_name} too long (max {max_len} characters)")

    @staticmethod
    def validate_enum(value: str, valid_values: List[str], field_name: str, errors: List[str]) -> None:
        """Validate that value is in the allowed set."""
        if value not in valid_values:
            errors.append(f"Invalid {field_name}. Must be one of: {', '.join(valid_values)}")

    @staticmethod
    def validate_range(value: int, min_val: int, max_val: int, field_name: str, errors: List[str]) -> None:
        """Validate that numeric value is within range."""
        if not (min_val <= value <= max_val):
            errors.append(f"{field_name} must be between {min_val} and {max_val}")

    @staticmethod
    def validate_tags(tags: List[str], errors: List[str]) -> None:
        """Validate tag list constraints."""
        for tag in tags:
            if len(tag) > 50:
                errors.append(f"Tag too long: {tag}")
                break

    @staticmethod
    def validate_at_least_one_field(fields: List[Any], errors: List[str]) -> None:
        """Validate that at least one field is provided."""
        if not any(field is not None for field in fields):
            errors.append("At least one field must be provided for update")


@dataclass
class CreateDocumentRequest:
    """DTO for creating a document."""

    title: str
    content: str
    format: str = "markdown"
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    repository_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def validate(self) -> List[str]:
        """Validate the request."""
        errors = []

        # Required field validations
        ValidationHelper.validate_required_field(self.title, "Title", errors)
        ValidationHelper.validate_required_field(self.content, "Content", errors)

        # Length validations
        ValidationHelper.validate_max_length(self.title, 200, "Title", errors)
        if len(self.content) > 10 * 1024 * 1024:  # 10MB
            errors.append("Content too large (max 10MB)")

        # Enum validations
        ValidationHelper.validate_enum(self.format,
                                      ["markdown", "html", "plaintext", "json"],
                                      "format", errors)

        # Optional field validations
        if self.author:
            ValidationHelper.validate_max_length(self.author, 100, "Author name", errors)

        if self.tags:
            ValidationHelper.validate_tags(self.tags, errors)

        return errors


@dataclass
class UpdateDocumentRequest:
    """DTO for updating a document."""

    document_id: str
    title: Optional[str] = None
    content: Optional[str] = None
    format: Optional[str] = None
    author: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

    def validate(self) -> List[str]:
        """Validate the request."""
        errors = []

        # Required field validation
        ValidationHelper.validate_required_field(self.document_id, "Document ID", errors)

        # At least one field validation
        updatable_fields = [self.title, self.content, self.format,
                          self.author, self.tags, self.metadata]
        ValidationHelper.validate_at_least_one_field(updatable_fields, errors)

        # Optional field validations
        if self.title:
            ValidationHelper.validate_max_length(self.title, 200, "Title", errors)

        if self.content and len(self.content) > 10 * 1024 * 1024:  # 10MB
            errors.append("Content too large (max 10MB)")

        if self.format:
            ValidationHelper.validate_enum(self.format,
                                          ["markdown", "html", "plaintext", "json"],
                                          "format", errors)

        if self.author:
            ValidationHelper.validate_max_length(self.author, 100, "Author name", errors)

        if self.tags:
            ValidationHelper.validate_tags(self.tags, errors)

        return errors


@dataclass
class PerformAnalysisRequest:
    """DTO for performing analysis."""

    document_id: str
    analysis_type: str
    configuration: Optional[Dict[str, Any]] = None
    priority: str = "normal"
    timeout_seconds: Optional[int] = None

    def validate(self) -> List[str]:
        """Validate the request."""
        errors = []

        # Required field validations
        ValidationHelper.validate_required_field(self.document_id, "Document ID", errors)
        ValidationHelper.validate_required_field(self.analysis_type, "Analysis type", errors)

        # Enum validations
        valid_types = [
            "semantic_similarity", "sentiment", "content_quality", "trend_analysis",
            "risk_assessment", "maintenance_forecast", "quality_degradation",
            "change_impact", "cross_repository", "automated_remediation",
        ]
        ValidationHelper.validate_enum(self.analysis_type, valid_types, "analysis type", errors)

        ValidationHelper.validate_enum(self.priority,
                                      ["low", "normal", "high", "critical"],
                                      "priority", errors)

        # Range validation
        if self.timeout_seconds is not None:
            ValidationHelper.validate_range(self.timeout_seconds, 10, 3600,
                                          "Timeout", errors)

        # Configuration validation
        if self.configuration and "detectors" in self.configuration:
            detectors = self.configuration["detectors"]
            if not isinstance(detectors, list):
                errors.append("Detectors must be a list")
            elif len(detectors) == 0:
                errors.append("Detectors must be a non-empty list")
            elif len(detectors) > 10:
                errors.append("Too many detectors (max 10)")

        return errors


@dataclass
class CreateFindingRequest:
    """DTO for creating a finding."""

    document_id: str
    analysis_id: str
    title: str
    description: str
    severity: str
    category: str
    location: Optional[Dict[str, Any]] = None
    suggestion: Optional[str] = None
    confidence: float = 0.8
    metadata: Optional[Dict[str, Any]] = None

    def validate(self) -> List[str]:
        """Validate the request."""
        errors = []

        # Required field validations
        required_fields = ["document_id", "analysis_id", "title",
                          "description", "severity", "category"]
        for field_name in required_fields:
            value = getattr(self, field_name)
            ValidationHelper.validate_required_field(value, field_name.replace('_', ' ').title(), errors)

        # Length validations
        ValidationHelper.validate_max_length(self.title, 200, "Title", errors)
        ValidationHelper.validate_max_length(self.description, 1000, "Description", errors)

        # Enum validations
        ValidationHelper.validate_enum(self.severity,
                                      ["info", "low", "medium", "high", "critical"],
                                      "severity", errors)

        valid_categories = ["consistency", "quality", "security", "performance", "usability"]
        ValidationHelper.validate_enum(self.category, valid_categories, "category", errors)

        # Range validation for confidence
        if not (0.0 <= self.confidence <= 1.0):
            errors.append("Confidence must be between 0.0 and 1.0")

        # Optional field validation
        if self.suggestion:
            ValidationHelper.validate_max_length(self.suggestion, 500, "Suggestion", errors)

        return errors


@dataclass
class UpdateFindingRequest:
    """DTO for updating a finding."""

    finding_id: str
    title: Optional[str] = None
    description: Optional[str] = None
    severity: Optional[str] = None
    category: Optional[str] = None
    location: Optional[Dict[str, Any]] = None
    suggestion: Optional[str] = None
    confidence: Optional[float] = None
    resolved: Optional[bool] = None
    resolved_by: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

    def validate(self) -> List[str]:
        """Validate the request."""
        errors = []

        # Required field validation
        ValidationHelper.validate_required_field(self.finding_id, "Finding ID", errors)

        # At least one field validation
        updatable_fields = [self.title, self.description, self.severity, self.category,
                          self.location, self.suggestion, self.confidence, self.resolved,
                          self.resolved_by, self.metadata]
        ValidationHelper.validate_at_least_one_field(updatable_fields, errors)

        # Optional field validations
        if self.title:
            ValidationHelper.validate_max_length(self.title, 200, "Title", errors)

        if self.description:
            ValidationHelper.validate_max_length(self.description, 1000, "Description", errors)

        if self.severity:
            ValidationHelper.validate_enum(self.severity,
                                          ["info", "low", "medium", "high", "critical"],
                                          "severity", errors)

        if self.category:
            valid_categories = ["consistency", "quality", "security", "performance", "usability"]
            ValidationHelper.validate_enum(self.category, valid_categories, "category", errors)

        if self.confidence is not None and not (0.0 <= self.confidence <= 1.0):
            errors.append("Confidence must be between 0.0 and 1.0")

        if self.suggestion:
            ValidationHelper.validate_max_length(self.suggestion, 500, "Suggestion", errors)

        if self.resolved_by:
            ValidationHelper.validate_max_length(self.resolved_by, 100, "Resolver name", errors)

        return errors


@dataclass
class GetDocumentsRequest:
    """DTO for getting documents with filtering."""

    author: Optional[str] = None
    tags: Optional[List[str]] = None
    repository_id: Optional[str] = None
    created_after: Optional[datetime] = None
    updated_after: Optional[datetime] = None
    limit: int = 50
    offset: int = 0

    def validate(self) -> List[str]:
        """Validate the request."""
        errors = []

        if self.limit < 1 or self.limit > 1000:
            errors.append("Limit must be between 1 and 1000")

        if self.offset < 0:
            errors.append("Offset must be non-negative")

        if self.tags:
            for tag in self.tags:
                if len(tag) > 50:
                    errors.append(f"Tag too long: {tag}")
                    break

        return errors


@dataclass
class GetFindingsRequest:
    """DTO for getting findings with filtering."""

    document_id: Optional[str] = None
    category: Optional[str] = None
    severity: Optional[str] = None
    resolved: Optional[bool] = None
    confidence_min: Optional[float] = None
    created_after: Optional[datetime] = None
    limit: int = 50
    offset: int = 0

    def validate(self) -> List[str]:
        """Validate the request."""
        errors = []

        if self.limit < 1 or self.limit > 1000:
            errors.append("Limit must be between 1 and 1000")

        if self.offset < 0:
            errors.append("Offset must be non-negative")

        if self.severity and self.severity not in [
            "info",
            "low",
            "medium",
            "high",
            "critical",
        ]:
            errors.append("Invalid severity")

        if self.category:
            valid_categories = [
                "consistency",
                "quality",
                "security",
                "performance",
                "usability",
            ]
            if self.category not in valid_categories:
                errors.append(f"Invalid category. Must be one of: {', '.join(valid_categories)}")

        if self.confidence_min is not None and not 0.0 <= self.confidence_min <= 1.0:
            errors.append("Confidence minimum must be between 0.0 and 1.0")

        return errors
