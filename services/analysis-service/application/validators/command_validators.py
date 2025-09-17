"""Validators for application commands."""

import re
from typing import Any, Dict, List, Optional

from .base_validator import BaseValidator, ValidationResult, ValidationError, ValidationSeverity
from ..handlers.commands import (
    CreateDocumentCommand,
    UpdateDocumentCommand,
    PerformAnalysisCommand,
    CreateFindingCommand,
    UpdateFindingCommand,
    DeleteDocumentCommand
)


class CreateDocumentCommandValidator(BaseValidator):
    """Validator for CreateDocumentCommand."""

    async def validate(self, command: CreateDocumentCommand) -> ValidationResult:
        """Validate CreateDocumentCommand."""
        errors = []

        # Validate title
        if not command.title or not isinstance(command.title, str):
            errors.append(self.create_error(
                "Document title is required and must be a string",
                "INVALID_TITLE",
                "title"
            ))
        elif len(command.title.strip()) == 0:
            errors.append(self.create_error(
                "Document title cannot be empty",
                "EMPTY_TITLE",
                "title"
            ))
        elif len(command.title) > 200:
            errors.append(self.create_error(
                "Document title cannot exceed 200 characters",
                "TITLE_TOO_LONG",
                "title"
            ))

        # Validate content
        if not command.content or not isinstance(command.content, str):
            errors.append(self.create_error(
                "Document content is required and must be a string",
                "INVALID_CONTENT",
                "content"
            ))
        elif len(command.content.strip()) == 0:
            errors.append(self.create_error(
                "Document content cannot be empty",
                "EMPTY_CONTENT",
                "content"
            ))

        # Validate author
        if command.author and not isinstance(command.author, str):
            errors.append(self.create_error(
                "Document author must be a string",
                "INVALID_AUTHOR",
                "author"
            ))
        elif command.author and len(command.author) > 100:
            errors.append(self.create_error(
                "Document author cannot exceed 100 characters",
                "AUTHOR_TOO_LONG",
                "author"
            ))

        # Validate tags
        if command.tags:
            if not isinstance(command.tags, list):
                errors.append(self.create_error(
                    "Document tags must be a list",
                    "INVALID_TAGS",
                    "tags"
                ))
            else:
                for i, tag in enumerate(command.tags):
                    if not isinstance(tag, str):
                        errors.append(self.create_error(
                            f"Tag at index {i} must be a string",
                            "INVALID_TAG_TYPE",
                            f"tags[{i}]"
                        ))
                    elif len(tag) > 50:
                        errors.append(self.create_error(
                            f"Tag '{tag}' exceeds maximum length of 50 characters",
                            "TAG_TOO_LONG",
                            f"tags[{i}]"
                        ))
                    elif not re.match(r'^[a-zA-Z0-9_-]+$', tag):
                        errors.append(self.create_error(
                            f"Tag '{tag}' contains invalid characters. Only alphanumeric, underscore, and hyphen are allowed",
                            "INVALID_TAG_FORMAT",
                            f"tags[{i}]"
                        ))

        # Validate metadata
        if command.metadata:
            if not isinstance(command.metadata, dict):
                errors.append(self.create_error(
                    "Document metadata must be a dictionary",
                    "INVALID_METADATA",
                    "metadata"
                ))
            elif len(str(command.metadata)) > 10000:  # Rough size check
                errors.append(self.create_error(
                    "Document metadata is too large",
                    "METADATA_TOO_LARGE",
                    "metadata"
                ))

        if errors:
            return ValidationResult.failure(errors)

        return ValidationResult.success()


class UpdateDocumentCommandValidator(BaseValidator):
    """Validator for UpdateDocumentCommand."""

    async def validate(self, command: UpdateDocumentCommand) -> ValidationResult:
        """Validate UpdateDocumentCommand."""
        errors = []

        # Validate document_id
        if not command.document_id or not isinstance(command.document_id, str):
            errors.append(self.create_error(
                "Document ID is required and must be a string",
                "INVALID_DOCUMENT_ID",
                "document_id"
            ))
        elif not command.document_id.strip():
            errors.append(self.create_error(
                "Document ID cannot be empty",
                "EMPTY_DOCUMENT_ID",
                "document_id"
            ))

        # Validate title if provided
        if hasattr(command, 'title') and command.title is not None:
            if not isinstance(command.title, str):
                errors.append(self.create_error(
                    "Document title must be a string",
                    "INVALID_TITLE",
                    "title"
                ))
            elif len(command.title.strip()) == 0:
                errors.append(self.create_error(
                    "Document title cannot be empty",
                    "EMPTY_TITLE",
                    "title"
                ))
            elif len(command.title) > 200:
                errors.append(self.create_error(
                    "Document title cannot exceed 200 characters",
                    "TITLE_TOO_LONG",
                    "title"
                ))

        # Validate content if provided
        if hasattr(command, 'content') and command.content is not None:
            if not isinstance(command.content, str):
                errors.append(self.create_error(
                    "Document content must be a string",
                    "INVALID_CONTENT",
                    "content"
                ))
            elif len(command.content.strip()) == 0:
                errors.append(self.create_error(
                    "Document content cannot be empty",
                    "EMPTY_CONTENT",
                    "content"
                ))

        # Validate tags if provided
        if hasattr(command, 'tags') and command.tags is not None:
            if not isinstance(command.tags, list):
                errors.append(self.create_error(
                    "Document tags must be a list",
                    "INVALID_TAGS",
                    "tags"
                ))
            else:
                for i, tag in enumerate(command.tags):
                    if not isinstance(tag, str):
                        errors.append(self.create_error(
                            f"Tag at index {i} must be a string",
                            "INVALID_TAG_TYPE",
                            f"tags[{i}]"
                        ))
                    elif len(tag) > 50:
                        errors.append(self.create_error(
                            f"Tag '{tag}' exceeds maximum length of 50 characters",
                            "TAG_TOO_LONG",
                            f"tags[{i}]"
                        ))

        if errors:
            return ValidationResult.failure(errors)

        return ValidationResult.success()


class PerformAnalysisCommandValidator(BaseValidator):
    """Validator for PerformAnalysisCommand."""

    async def validate(self, command: PerformAnalysisCommand) -> ValidationResult:
        """Validate PerformAnalysisCommand."""
        errors = []

        # Validate document_id
        if not command.document_id or not isinstance(command.document_id, str):
            errors.append(self.create_error(
                "Document ID is required and must be a string",
                "INVALID_DOCUMENT_ID",
                "document_id"
            ))
        elif not command.document_id.strip():
            errors.append(self.create_error(
                "Document ID cannot be empty",
                "EMPTY_DOCUMENT_ID",
                "document_id"
            ))

        # Validate analysis_type
        if not command.analysis_type or not isinstance(command.analysis_type, str):
            errors.append(self.create_error(
                "Analysis type is required and must be a string",
                "INVALID_ANALYSIS_TYPE",
                "analysis_type"
            ))
        elif command.analysis_type not in [
            'semantic_similarity', 'sentiment', 'content_quality',
            'trend_analysis', 'risk_assessment', 'maintenance_forecast',
            'quality_degradation', 'change_impact', 'cross_repository',
            'automated_remediation'
        ]:
            errors.append(self.create_error(
                f"Invalid analysis type: {command.analysis_type}",
                "UNSUPPORTED_ANALYSIS_TYPE",
                "analysis_type"
            ))

        # Validate configuration
        if command.configuration:
            if not isinstance(command.configuration, dict):
                errors.append(self.create_error(
                    "Analysis configuration must be a dictionary",
                    "INVALID_CONFIGURATION",
                    "configuration"
                ))
            else:
                # Validate timeout if provided
                if 'timeout_seconds' in command.configuration:
                    timeout = command.configuration['timeout_seconds']
                    if not isinstance(timeout, (int, float)):
                        errors.append(self.create_error(
                            "Timeout must be a number",
                            "INVALID_TIMEOUT",
                            "configuration.timeout_seconds"
                        ))
                    elif timeout < 10 or timeout > 3600:
                        errors.append(self.create_error(
                            "Timeout must be between 10 and 3600 seconds",
                            "INVALID_TIMEOUT_RANGE",
                            "configuration.timeout_seconds"
                        ))

                # Validate priority if provided
                if 'priority' in command.configuration:
                    priority = command.configuration['priority']
                    if priority not in ['low', 'normal', 'high', 'critical']:
                        errors.append(self.create_error(
                            f"Invalid priority: {priority}",
                            "INVALID_PRIORITY",
                            "configuration.priority"
                        ))

        # Validate timeout_seconds
        if hasattr(command, 'timeout_seconds') and command.timeout_seconds is not None:
            if not isinstance(command.timeout_seconds, (int, float)):
                errors.append(self.create_error(
                    "Timeout must be a number",
                    "INVALID_TIMEOUT",
                    "timeout_seconds"
                ))
            elif command.timeout_seconds < 10 or command.timeout_seconds > 3600:
                errors.append(self.create_error(
                    "Timeout must be between 10 and 3600 seconds",
                    "INVALID_TIMEOUT_RANGE",
                    "timeout_seconds"
                ))

        if errors:
            return ValidationResult.failure(errors)

        return ValidationResult.success()


class CreateFindingCommandValidator(BaseValidator):
    """Validator for CreateFindingCommand."""

    async def validate(self, command: CreateFindingCommand) -> ValidationResult:
        """Validate CreateFindingCommand."""
        errors = []

        # Validate document_id
        if not command.document_id or not isinstance(command.document_id, str):
            errors.append(self.create_error(
                "Document ID is required and must be a string",
                "INVALID_DOCUMENT_ID",
                "document_id"
            ))

        # Validate analysis_id
        if not command.analysis_id or not isinstance(command.analysis_id, str):
            errors.append(self.create_error(
                "Analysis ID is required and must be a string",
                "INVALID_ANALYSIS_ID",
                "analysis_id"
            ))

        # Validate severity
        if not command.severity or not isinstance(command.severity, str):
            errors.append(self.create_error(
                "Finding severity is required and must be a string",
                "INVALID_SEVERITY",
                "severity"
            ))
        elif command.severity not in ['critical', 'high', 'medium', 'low', 'info']:
            errors.append(self.create_error(
                f"Invalid severity: {command.severity}",
                "UNSUPPORTED_SEVERITY",
                "severity"
            ))

        # Validate category
        if not command.category or not isinstance(command.category, str):
            errors.append(self.create_error(
                "Finding category is required and must be a string",
                "INVALID_CATEGORY",
                "category"
            ))
        elif len(command.category) > 50:
            errors.append(self.create_error(
                "Finding category cannot exceed 50 characters",
                "CATEGORY_TOO_LONG",
                "category"
            ))

        # Validate description
        if not command.description or not isinstance(command.description, str):
            errors.append(self.create_error(
                "Finding description is required and must be a string",
                "INVALID_DESCRIPTION",
                "description"
            ))
        elif len(command.description) > 1000:
            errors.append(self.create_error(
                "Finding description cannot exceed 1000 characters",
                "DESCRIPTION_TOO_LONG",
                "description"
            ))

        # Validate confidence
        if command.confidence is not None:
            if not isinstance(command.confidence, (int, float)):
                errors.append(self.create_error(
                    "Finding confidence must be a number",
                    "INVALID_CONFIDENCE",
                    "confidence"
                ))
            elif command.confidence < 0.0 or command.confidence > 1.0:
                errors.append(self.create_error(
                    "Finding confidence must be between 0.0 and 1.0",
                    "CONFIDENCE_OUT_OF_RANGE",
                    "confidence"
                ))

        # Validate location if provided
        if command.location:
            if not isinstance(command.location, dict):
                errors.append(self.create_error(
                    "Finding location must be a dictionary",
                    "INVALID_LOCATION",
                    "location"
                ))

        # Validate suggestion if provided
        if command.suggestion and len(command.suggestion) > 500:
            errors.append(self.create_error(
                "Finding suggestion cannot exceed 500 characters",
                "SUGGESTION_TOO_LONG",
                "suggestion"
            ))

        if errors:
            return ValidationResult.failure(errors)

        return ValidationResult.success()
