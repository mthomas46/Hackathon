"""Domain validators for business rule validation."""

from typing import List, Dict, Any
from abc import ABC, abstractmethod

from ..entities import Document, Analysis, Finding, Repository


class ValidationResult:
    """Result of validation operation."""

    def __init__(self, is_valid: bool = True, errors: List[str] = None):
        """Initialize validation result."""
        self.is_valid = is_valid
        self.errors = errors or []

    def add_error(self, error: str) -> None:
        """Add validation error."""
        self.errors.append(error)
        self.is_valid = False

    def merge(self, other: 'ValidationResult') -> None:
        """Merge another validation result."""
        self.errors.extend(other.errors)
        self.is_valid = self.is_valid and other.is_valid


class DomainValidator(ABC):
    """Abstract base class for domain validators."""

    @abstractmethod
    def validate(self, entity) -> ValidationResult:
        """Validate domain entity."""
        pass


class DocumentValidator(DomainValidator):
    """Validator for Document entities."""

    def __init__(self, max_title_length: int = 200,
                 max_content_size_mb: float = 10.0,
                 min_word_count: int = 1):
        """Initialize document validator."""
        self.max_title_length = max_title_length
        self.max_content_size_mb = max_content_size_mb * 1024 * 1024  # Convert to bytes
        self.min_word_count = min_word_count

    def validate(self, document: Document) -> ValidationResult:
        """Validate document entity."""
        result = ValidationResult()

        # Title validation
        if not document.title or not document.title.strip():
            result.add_error("Document title cannot be empty")

        if len(document.title) > self.max_title_length:
            result.add_error(f"Document title too long (max {self.max_title_length} characters)")

        # Content validation
        if not document.content.text or not document.content.text.strip():
            result.add_error("Document content cannot be empty")

        # Content size validation
        content_size = len(document.content.text.encode('utf-8'))
        if content_size > self.max_content_size_mb:
            result.add_error(f"Document content too large (max {self.max_content_size_mb / (1024*1024):.1f} MB)")

        # Word count validation
        word_count = len(document.content.text.split())
        if word_count < self.min_word_count:
            result.add_error(f"Document too short (minimum {self.min_word_count} words)")

        # Metadata validation
        if document.metadata.created_at > document.metadata.updated_at:
            result.add_error("Created date cannot be after updated date")

        # Repository ID validation
        if document.repository_id and len(document.repository_id) > 200:
            result.add_error("Repository ID too long (max 200 characters)")

        return result

    def validate_for_creation(self, document: Document) -> ValidationResult:
        """Validate document for creation."""
        result = self.validate(document)

        # Additional creation-specific validations
        if document.id.value.startswith('temp_'):
            result.add_error("Cannot create document with temporary ID")

        return result

    def validate_for_update(self, document: Document,
                           original_document: Document) -> ValidationResult:
        """Validate document for update."""
        result = self.validate(document)

        # Ensure version consistency
        if document.version == original_document.version:
            result.add_error("Version must be incremented for updates")

        return result


class AnalysisValidator(DomainValidator):
    """Validator for Analysis entities."""

    def __init__(self, max_analysis_types: int = 10,
                 max_timeout_seconds: int = 3600):
        """Initialize analysis validator."""
        self.max_analysis_types = max_analysis_types
        self.max_timeout_seconds = max_timeout_seconds

    def validate(self, analysis: Analysis) -> ValidationResult:
        """Validate analysis entity."""
        result = ValidationResult()

        # Analysis type validation
        if not analysis.analysis_type:
            result.add_error("Analysis type cannot be empty")

        # Configuration validation
        if 'detectors' in analysis.configuration:
            detectors = analysis.configuration['detectors']
            if len(detectors) > self.max_analysis_types:
                result.add_error(f"Too many detectors (max {self.max_analysis_types})")

            if len(detectors) == 0:
                result.add_error("At least one detector must be specified")

        # Timeout validation
        if 'timeout_seconds' in analysis.configuration:
            timeout = analysis.configuration['timeout_seconds']
            if timeout < 10:
                result.add_error("Timeout too short (minimum 10 seconds)")
            if timeout > self.max_timeout_seconds:
                result.add_error(f"Timeout too long (maximum {self.max_timeout_seconds} seconds)")

        # Status validation
        valid_statuses = ['pending', 'running', 'completed', 'failed', 'cancelled']
        if analysis.status.value not in valid_statuses:
            result.add_error(f"Invalid status: {analysis.status.value}")

        # Timing validation
        if analysis.started_at and analysis.completed_at:
            if analysis.started_at > analysis.completed_at:
                result.add_error("Start time cannot be after completion time")

        return result

    def validate_for_execution(self, analysis: Analysis) -> ValidationResult:
        """Validate analysis for execution."""
        result = self.validate(analysis)

        # Must be in pending status
        if analysis.status.value != 'pending':
            result.add_error(f"Cannot execute analysis in {analysis.status.value} status")

        # Must have valid configuration
        if not analysis.configuration.get('detectors'):
            result.add_error("No detectors configured for analysis")

        return result


class FindingValidator(DomainValidator):
    """Validator for Finding entities."""

    def __init__(self, max_title_length: int = 200,
                 max_description_length: int = 1000,
                 min_confidence: float = 0.0,
                 max_confidence: float = 1.0):
        """Initialize finding validator."""
        self.max_title_length = max_title_length
        self.max_description_length = max_description_length
        self.min_confidence = min_confidence
        self.max_confidence = max_confidence

    def validate(self, finding: Finding) -> ValidationResult:
        """Validate finding entity."""
        result = ValidationResult()

        # Title validation
        if not finding.title or not finding.title.strip():
            result.add_error("Finding title cannot be empty")

        if len(finding.title) > self.max_title_length:
            result.add_error(f"Finding title too long (max {self.max_title_length} characters)")

        # Description validation
        if not finding.description or not finding.description.strip():
            result.add_error("Finding description cannot be empty")

        if len(finding.description) > self.max_description_length:
            result.add_error(f"Finding description too long (max {self.max_description_length} characters)")

        # Category validation
        valid_categories = ['consistency', 'quality', 'security', 'performance', 'usability']
        if finding.category not in valid_categories:
            result.add_error(f"Invalid category: {finding.category}")

        # Severity validation
        valid_severities = ['info', 'low', 'medium', 'high', 'critical']
        if finding.severity.value not in valid_severities:
            result.add_error(f"Invalid severity: {finding.severity.value}")

        # Confidence validation
        if not (self.min_confidence <= finding.confidence <= self.max_confidence):
            result.add_error(f"Confidence must be between {self.min_confidence} and {self.max_confidence}")

        # Timing validation
        if finding.resolved_at and finding.created_at > finding.resolved_at:
            result.add_error("Created date cannot be after resolved date")

        return result

    def validate_for_resolution(self, finding: Finding) -> ValidationResult:
        """Validate finding for resolution."""
        result = self.validate(finding)

        # Must not already be resolved
        if finding.is_resolved():
            result.add_error("Finding is already resolved")

        return result


class RepositoryValidator(DomainValidator):
    """Validator for Repository entities."""

    def __init__(self, max_name_length: int = 100,
                 max_url_length: int = 500):
        """Initialize repository validator."""
        self.max_name_length = max_name_length
        self.max_url_length = max_url_length

    def validate(self, repository: Repository) -> ValidationResult:
        """Validate repository entity."""
        result = ValidationResult()

        # Name validation
        if not repository.name or not repository.name.strip():
            result.add_error("Repository name cannot be empty")

        if len(repository.name) > self.max_name_length:
            result.add_error(f"Repository name too long (max {self.max_name_length} characters)")

        # URL validation
        if not repository.url or not repository.url.strip():
            result.add_error("Repository URL cannot be empty")

        if len(repository.url) > self.max_url_length:
            result.add_error(f"Repository URL too long (max {self.max_url_length} characters)")

        # Basic URL format validation
        if not repository.url.startswith(('http://', 'https://', 'ssh://', 'git@')):
            result.add_error("Repository URL must be a valid URL")

        # Provider validation
        valid_providers = ['github', 'gitlab', 'bitbucket', 'azure_devops', 'local']
        if repository.provider not in valid_providers:
            result.add_error(f"Invalid provider: {repository.provider}")

        # Default branch validation
        if not repository.default_branch or not repository.default_branch.strip():
            result.add_error("Default branch cannot be empty")

        # Timing validation
        if repository.created_at > repository.updated_at:
            result.add_error("Created date cannot be after updated date")

        return result

    def validate_for_sync(self, repository: Repository) -> ValidationResult:
        """Validate repository for synchronization."""
        result = self.validate(repository)

        # Check if sync is needed
        if repository.is_synced_recently:
            result.add_error("Repository was recently synced")

        return result
