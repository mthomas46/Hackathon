"""Validators for application commands."""

import re

from ..handlers.commands import (
    CreateDocumentCommand,
    CreateFindingCommand,
    PerformAnalysisCommand,
    UpdateDocumentCommand,
)
from .base_validator import BaseValidator, ValidationResult


class CreateDocumentCommandValidator(BaseValidator):
    """Validator for CreateDocumentCommand."""

    async def validate(self, command: CreateDocumentCommand) -> ValidationResult:
        """Validate CreateDocumentCommand."""
        errors = []

        # Validate each field
        errors.extend(self._validate_title(command.title))
        errors.extend(self._validate_content(command.content))
        errors.extend(self._validate_author(command.author))
        errors.extend(self._validate_tags(command.tags))
        errors.extend(self._validate_metadata(command.metadata))

        if errors:
            return ValidationResult.failure(errors)

        return ValidationResult.success()

    def _validate_title(self, title) -> list:
        """Validate document title."""
        errors = []

        if not title or not isinstance(title, str):
            errors.append(
                self.create_error(
                    "Document title is required and must be a string",
                    "INVALID_TITLE",
                    "title",
                )
            )
        elif len(title.strip()) == 0:
            errors.append(self.create_error("Document title cannot be empty", "EMPTY_TITLE", "title"))
        elif len(title) > 200:
            errors.append(
                self.create_error(
                    "Document title cannot exceed 200 characters",
                    "TITLE_TOO_LONG",
                    "title",
                )
            )

        return errors

    def _validate_content(self, content) -> list:
        """Validate document content."""
        errors = []

        if not content or not isinstance(content, str):
            errors.append(
                self.create_error(
                    "Document content is required and must be a string",
                    "INVALID_CONTENT",
                    "content",
                )
            )
        elif len(content.strip()) == 0:
            errors.append(self.create_error("Document content cannot be empty", "EMPTY_CONTENT", "content"))

        return errors

    def _validate_author(self, author) -> list:
        """Validate document author."""
        errors = []

        if author and not isinstance(author, str):
            errors.append(self.create_error("Document author must be a string", "INVALID_AUTHOR", "author"))
        elif author and len(author) > 100:
            errors.append(
                self.create_error(
                    "Document author cannot exceed 100 characters",
                    "AUTHOR_TOO_LONG",
                    "author",
                )
            )

        return errors

    def _validate_tags(self, tags) -> list:
        """Validate document tags."""
        errors = []

        if tags:
            if not isinstance(tags, list):
                errors.append(self.create_error("Document tags must be a list", "INVALID_TAGS", "tags"))
            else:
                errors.extend(self._validate_individual_tags(tags))

        return errors

    def _validate_individual_tags(self, tags) -> list:
        """Validate individual tag items."""
        errors = []

        for i, tag in enumerate(tags):
            if not isinstance(tag, str):
                errors.append(
                    self.create_error(
                        f"Tag at index {i} must be a string",
                        "INVALID_TAG_TYPE",
                        f"tags[{i}]",
                    )
                )
            elif len(tag) > 50:
                errors.append(
                    self.create_error(
                        f"Tag '{tag}' exceeds maximum length of 50 characters",
                        "TAG_TOO_LONG",
                        f"tags[{i}]",
                    )
                )
            elif not re.match(r"^[a-zA-Z0-9_-]+$", tag):
                errors.append(
                    self.create_error(
                        f"Tag '{tag}' contains invalid characters. Only alphanumeric, underscore, and hyphen are allowed",
                        "INVALID_TAG_FORMAT",
                        f"tags[{i}]",
                    )
                )

        return errors

    def _validate_metadata(self, metadata) -> list:
        """Validate document metadata."""
        errors = []

        if metadata:
            if not isinstance(metadata, dict):
                errors.append(
                    self.create_error(
                        "Document metadata must be a dictionary",
                        "INVALID_METADATA",
                        "metadata",
                    )
                )
            elif len(str(metadata)) > 10000:  # Rough size check
                errors.append(
                    self.create_error(
                        "Document metadata is too large",
                        "METADATA_TOO_LARGE",
                        "metadata",
                    )
                )

        return errors


class UpdateDocumentCommandValidator(BaseValidator):
    """Validator for UpdateDocumentCommand."""

    async def validate(self, command: UpdateDocumentCommand) -> ValidationResult:
        """Validate UpdateDocumentCommand."""
        errors = []

        # Validate document_id
        if not command.document_id or not isinstance(command.document_id, str):
            errors.append(
                self.create_error(
                    "Document ID is required and must be a string",
                    "INVALID_DOCUMENT_ID",
                    "document_id",
                )
            )
        elif not command.document_id.strip():
            errors.append(self.create_error("Document ID cannot be empty", "EMPTY_DOCUMENT_ID", "document_id"))

        # Validate title if provided
        if hasattr(command, "title") and command.title is not None:
            if not isinstance(command.title, str):
                errors.append(self.create_error("Document title must be a string", "INVALID_TITLE", "title"))
            elif len(command.title.strip()) == 0:
                errors.append(self.create_error("Document title cannot be empty", "EMPTY_TITLE", "title"))
            elif len(command.title) > 200:
                errors.append(
                    self.create_error(
                        "Document title cannot exceed 200 characters",
                        "TITLE_TOO_LONG",
                        "title",
                    )
                )

        # Validate content if provided
        if hasattr(command, "content") and command.content is not None:
            if not isinstance(command.content, str):
                errors.append(
                    self.create_error(
                        "Document content must be a string",
                        "INVALID_CONTENT",
                        "content",
                    )
                )
            elif len(command.content.strip()) == 0:
                errors.append(self.create_error("Document content cannot be empty", "EMPTY_CONTENT", "content"))

        # Validate tags if provided
        if hasattr(command, "tags") and command.tags is not None:
            if not isinstance(command.tags, list):
                errors.append(self.create_error("Document tags must be a list", "INVALID_TAGS", "tags"))
            else:
                for i, tag in enumerate(command.tags):
                    if not isinstance(tag, str):
                        errors.append(
                            self.create_error(
                                f"Tag at index {i} must be a string",
                                "INVALID_TAG_TYPE",
                                f"tags[{i}]",
                            )
                        )
                    elif len(tag) > 50:
                        errors.append(
                            self.create_error(
                                f"Tag '{tag}' exceeds maximum length of 50 characters",
                                "TAG_TOO_LONG",
                                f"tags[{i}]",
                            )
                        )

        if errors:
            return ValidationResult.failure(errors)

        return ValidationResult.success()


class PerformAnalysisCommandValidator(BaseValidator):
    """Validator for PerformAnalysisCommand."""

    async def validate(self, command: PerformAnalysisCommand) -> ValidationResult:
        """Validate PerformAnalysisCommand."""
        errors = []

        # Validate each field
        errors.extend(self._validate_document_id(command.document_id))
        errors.extend(self._validate_analysis_type(command.analysis_type))
        errors.extend(self._validate_configuration(command.configuration))
        errors.extend(self._validate_timeout_seconds(command.timeout_seconds))

        if errors:
            return ValidationResult.failure(errors)

        return ValidationResult.success()

    def _validate_document_id(self, document_id) -> list:
        """Validate document ID."""
        errors = []

        if not document_id or not isinstance(document_id, str):
            errors.append(
                self.create_error(
                    "Document ID is required and must be a string",
                    "INVALID_DOCUMENT_ID",
                    "document_id",
                )
            )
        elif not document_id.strip():
            errors.append(self.create_error("Document ID cannot be empty", "EMPTY_DOCUMENT_ID", "document_id"))

        return errors

    def _validate_analysis_type(self, analysis_type) -> list:
        """Validate analysis type."""
        errors = []

        if not analysis_type or not isinstance(analysis_type, str):
            errors.append(
                self.create_error(
                    "Analysis type is required and must be a string",
                    "INVALID_ANALYSIS_TYPE",
                    "analysis_type",
                )
            )
        elif analysis_type not in [
            "semantic_similarity",
            "sentiment",
            "content_quality",
            "trend_analysis",
            "risk_assessment",
            "maintenance_forecast",
            "quality_degradation",
            "change_impact",
            "cross_repository",
            "automated_remediation",
        ]:
            errors.append(
                self.create_error(
                    f"Invalid analysis type: {analysis_type}",
                    "UNSUPPORTED_ANALYSIS_TYPE",
                    "analysis_type",
                )
            )

        return errors

    def _validate_configuration(self, configuration) -> list:
        """Validate analysis configuration."""
        errors = []

        if configuration:
            if not isinstance(configuration, dict):
                errors.append(
                    self.create_error(
                        "Analysis configuration must be a dictionary",
                        "INVALID_CONFIGURATION",
                        "configuration",
                    )
                )
            else:
                # Validate nested configuration fields
                errors.extend(self._validate_config_timeout(configuration))
                errors.extend(self._validate_config_priority(configuration))

        return errors

    def _validate_config_timeout(self, configuration) -> list:
        """Validate configuration timeout."""
        errors = []

        if "timeout_seconds" in configuration:
            timeout = configuration["timeout_seconds"]
            if not isinstance(timeout, (int, float)):
                errors.append(
                    self.create_error(
                        "Timeout must be a number",
                        "INVALID_TIMEOUT",
                        "configuration.timeout_seconds",
                    )
                )
            elif timeout < 10 or timeout > 3600:
                errors.append(
                    self.create_error(
                        "Timeout must be between 10 and 3600 seconds",
                        "INVALID_TIMEOUT_RANGE",
                        "configuration.timeout_seconds",
                    )
                )

        return errors

    def _validate_config_priority(self, configuration) -> list:
        """Validate configuration priority."""
        errors = []

        if "priority" in configuration:
            priority = configuration["priority"]
            if priority not in ["low", "normal", "high", "critical"]:
                errors.append(
                    self.create_error(
                        f"Invalid priority: {priority}",
                        "INVALID_PRIORITY",
                        "configuration.priority",
                    )
                )

        return errors

    def _validate_timeout_seconds(self, timeout_seconds) -> list:
        """Validate timeout seconds."""
        errors = []

        if timeout_seconds is not None:
            if not isinstance(timeout_seconds, (int, float)):
                errors.append(self.create_error("Timeout must be a number", "INVALID_TIMEOUT", "timeout_seconds"))
            elif timeout_seconds < 10 or timeout_seconds > 3600:
                errors.append(
                    self.create_error(
                        "Timeout must be between 10 and 3600 seconds",
                        "INVALID_TIMEOUT_RANGE",
                        "timeout_seconds",
                    )
                )

        return errors


class CreateFindingCommandValidator(BaseValidator):
    """Validator for CreateFindingCommand."""

    async def validate(self, command: CreateFindingCommand) -> ValidationResult:
        """Validate CreateFindingCommand."""
        errors = []

        # Validate each field
        errors.extend(self._validate_document_id(command.document_id))
        errors.extend(self._validate_analysis_id(command.analysis_id))
        errors.extend(self._validate_severity(command.severity))
        errors.extend(self._validate_category(command.category))
        errors.extend(self._validate_description(command.description))
        errors.extend(self._validate_confidence(command.confidence))
        errors.extend(self._validate_location(command.location))
        errors.extend(self._validate_suggestion(command.suggestion))

        if errors:
            return ValidationResult.failure(errors)

        return ValidationResult.success()

    def _validate_document_id(self, document_id) -> list:
        """Validate document ID."""
        errors = []

        if not document_id or not isinstance(document_id, str):
            errors.append(
                self.create_error(
                    "Document ID is required and must be a string",
                    "INVALID_DOCUMENT_ID",
                    "document_id",
                )
            )

        return errors

    def _validate_analysis_id(self, analysis_id) -> list:
        """Validate analysis ID."""
        errors = []

        if not analysis_id or not isinstance(analysis_id, str):
            errors.append(
                self.create_error(
                    "Analysis ID is required and must be a string",
                    "INVALID_ANALYSIS_ID",
                    "analysis_id",
                )
            )

        return errors

    def _validate_severity(self, severity) -> list:
        """Validate finding severity."""
        errors = []

        if not severity or not isinstance(severity, str):
            errors.append(
                self.create_error(
                    "Finding severity is required and must be a string",
                    "INVALID_SEVERITY",
                    "severity",
                )
            )
        elif severity not in ["critical", "high", "medium", "low", "info"]:
            errors.append(
                self.create_error(
                    f"Invalid severity: {severity}",
                    "UNSUPPORTED_SEVERITY",
                    "severity",
                )
            )

        return errors

    def _validate_category(self, category) -> list:
        """Validate finding category."""
        errors = []

        if not category or not isinstance(category, str):
            errors.append(
                self.create_error(
                    "Finding category is required and must be a string",
                    "INVALID_CATEGORY",
                    "category",
                )
            )
        elif len(category) > 50:
            errors.append(
                self.create_error(
                    "Finding category cannot exceed 50 characters",
                    "CATEGORY_TOO_LONG",
                    "category",
                )
            )

        return errors

    def _validate_description(self, description) -> list:
        """Validate finding description."""
        errors = []

        if not description or not isinstance(description, str):
            errors.append(
                self.create_error(
                    "Finding description is required and must be a string",
                    "INVALID_DESCRIPTION",
                    "description",
                )
            )
        elif len(description) > 1000:
            errors.append(
                self.create_error(
                    "Finding description cannot exceed 1000 characters",
                    "DESCRIPTION_TOO_LONG",
                    "description",
                )
            )

        return errors

    def _validate_confidence(self, confidence) -> list:
        """Validate finding confidence."""
        errors = []

        if confidence is not None:
            if not isinstance(confidence, (int, float)):
                errors.append(
                    self.create_error(
                        "Finding confidence must be a number",
                        "INVALID_CONFIDENCE",
                        "confidence",
                    )
                )
            elif confidence < 0.0 or confidence > 1.0:
                errors.append(
                    self.create_error(
                        "Finding confidence must be between 0.0 and 1.0",
                        "CONFIDENCE_OUT_OF_RANGE",
                        "confidence",
                    )
                )

        return errors

    def _validate_location(self, location) -> list:
        """Validate finding location."""
        errors = []

        if location:
            if not isinstance(location, dict):
                errors.append(
                    self.create_error(
                        "Finding location must be a dictionary",
                        "INVALID_LOCATION",
                        "location",
                    )
                )

        return errors

    def _validate_suggestion(self, suggestion) -> list:
        """Validate finding suggestion."""
        errors = []

        if suggestion and len(suggestion) > 500:
            errors.append(
                self.create_error(
                    "Finding suggestion cannot exceed 500 characters",
                    "SUGGESTION_TOO_LONG",
                    "suggestion",
                )
            )

        return errors
