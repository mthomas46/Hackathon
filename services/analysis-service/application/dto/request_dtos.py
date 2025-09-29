"""Request DTOs for application layer."""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from datetime import datetime


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

        if not self.title or not self.title.strip():
            errors.append("Title is required")

        if not self.content or not self.content.strip():
            errors.append("Content is required")

        if len(self.title) > 200:
            errors.append("Title too long (max 200 characters)")

        if len(self.content) > 10 * 1024 * 1024:  # 10MB
            errors.append("Content too large (max 10MB)")

        if self.format not in ["markdown", "html", "plaintext", "json"]:
            errors.append("Invalid format")

        if self.author and len(self.author) > 100:
            errors.append("Author name too long (max 100 characters)")

        if self.tags:
            for tag in self.tags:
                if len(tag) > 50:
                    errors.append(f"Tag too long: {tag}")
                    break

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

        if not self.document_id or not self.document_id.strip():
            errors.append("Document ID is required")

        # At least one field should be provided for update
        updatable_fields = [self.title, self.content, self.format, self.author, self.tags, self.metadata]
        if not any(field is not None for field in updatable_fields):
            errors.append("At least one field must be provided for update")

        if self.title and len(self.title) > 200:
            errors.append("Title too long (max 200 characters)")

        if self.content and len(self.content) > 10 * 1024 * 1024:  # 10MB
            errors.append("Content too large (max 10MB)")

        if self.format and self.format not in ["markdown", "html", "plaintext", "json"]:
            errors.append("Invalid format")

        if self.author and len(self.author) > 100:
            errors.append("Author name too long (max 100 characters)")

        if self.tags:
            for tag in self.tags:
                if len(tag) > 50:
                    errors.append(f"Tag too long: {tag}")
                    break

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

        if not self.document_id or not self.document_id.strip():
            errors.append("Document ID is required")

        if not self.analysis_type or not self.analysis_type.strip():
            errors.append("Analysis type is required")

        valid_types = [
            "semantic_similarity", "sentiment", "content_quality",
            "trend_analysis", "risk_assessment", "maintenance_forecast",
            "quality_degradation", "change_impact", "cross_repository",
            "automated_remediation"
        ]

        if self.analysis_type not in valid_types:
            errors.append(f"Invalid analysis type. Must be one of: {', '.join(valid_types)}")

        if self.priority not in ["low", "normal", "high", "critical"]:
            errors.append("Invalid priority. Must be one of: low, normal, high, critical")

        if self.timeout_seconds is not None and (self.timeout_seconds < 10 or self.timeout_seconds > 3600):
            errors.append("Timeout must be between 10 and 3600 seconds")

        if self.configuration:
            if 'detectors' in self.configuration:
                detectors = self.configuration['detectors']
                if not isinstance(detectors, list) or len(detectors) == 0:
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

        required_fields = ['document_id', 'analysis_id', 'title', 'description', 'severity', 'category']
        for field in required_fields:
            value = getattr(self, field)
            if not value or not str(value).strip():
                errors.append(f"{field} is required")

        if len(self.title) > 200:
            errors.append("Title too long (max 200 characters)")

        if len(self.description) > 1000:
            errors.append("Description too long (max 1000 characters)")

        if self.severity not in ["info", "low", "medium", "high", "critical"]:
            errors.append("Invalid severity")

        valid_categories = ['consistency', 'quality', 'security', 'performance', 'usability']
        if self.category not in valid_categories:
            errors.append(f"Invalid category. Must be one of: {', '.join(valid_categories)}")

        if not 0.0 <= self.confidence <= 1.0:
            errors.append("Confidence must be between 0.0 and 1.0")

        if self.suggestion and len(self.suggestion) > 500:
            errors.append("Suggestion too long (max 500 characters)")

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

        if not self.finding_id or not self.finding_id.strip():
            errors.append("Finding ID is required")

        # At least one field should be provided for update
        updatable_fields = [
            self.title, self.description, self.severity, self.category,
            self.location, self.suggestion, self.confidence, self.resolved,
            self.resolved_by, self.metadata
        ]
        if not any(field is not None for field in updatable_fields):
            errors.append("At least one field must be provided for update")

        if self.title and len(self.title) > 200:
            errors.append("Title too long (max 200 characters)")

        if self.description and len(self.description) > 1000:
            errors.append("Description too long (max 1000 characters)")

        if self.severity and self.severity not in ["info", "low", "medium", "high", "critical"]:
            errors.append("Invalid severity")

        if self.category:
            valid_categories = ['consistency', 'quality', 'security', 'performance', 'usability']
            if self.category not in valid_categories:
                errors.append(f"Invalid category. Must be one of: {', '.join(valid_categories)}")

        if self.confidence is not None and not 0.0 <= self.confidence <= 1.0:
            errors.append("Confidence must be between 0.0 and 1.0")

        if self.suggestion and len(self.suggestion) > 500:
            errors.append("Suggestion too long (max 500 characters)")

        if self.resolved_by and len(self.resolved_by) > 100:
            errors.append("Resolver name too long (max 100 characters)")

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

        if self.severity and self.severity not in ["info", "low", "medium", "high", "critical"]:
            errors.append("Invalid severity")

        if self.category:
            valid_categories = ['consistency', 'quality', 'security', 'performance', 'usability']
            if self.category not in valid_categories:
                errors.append(f"Invalid category. Must be one of: {', '.join(valid_categories)}")

        if self.confidence_min is not None and not 0.0 <= self.confidence_min <= 1.0:
            errors.append("Confidence minimum must be between 0.0 and 1.0")

        return errors
