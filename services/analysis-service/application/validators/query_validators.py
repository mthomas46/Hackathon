"""Validators for application queries."""

from typing import Any, Dict, List, Optional

from .base_validator import BaseValidator, ValidationResult, ValidationError, ValidationSeverity
from ..handlers.queries import (
    GetDocumentQuery,
    GetAnalysisQuery,
    ListFindingsQuery,
    GetDocumentByIdQuery,
    GetAnalysisByIdQuery
)


class GetDocumentQueryValidator(BaseValidator):
    """Validator for GetDocumentQuery."""

    async def validate(self, query: GetDocumentQuery) -> ValidationResult:
        """Validate GetDocumentQuery."""
        errors = []

        # Validate document_id
        if not query.document_id or not isinstance(query.document_id, str):
            errors.append(self.create_error(
                "Document ID is required and must be a string",
                "INVALID_DOCUMENT_ID",
                "document_id"
            ))
        elif not query.document_id.strip():
            errors.append(self.create_error(
                "Document ID cannot be empty",
                "EMPTY_DOCUMENT_ID",
                "document_id"
            ))
        elif len(query.document_id) > 500:
            errors.append(self.create_error(
                "Document ID is too long",
                "DOCUMENT_ID_TOO_LONG",
                "document_id"
            ))

        # Validate include_related if provided
        if hasattr(query, 'include_related') and query.include_related is not None:
            if not isinstance(query.include_related, bool):
                errors.append(self.create_error(
                    "include_related must be a boolean",
                    "INVALID_INCLUDE_RELATED",
                    "include_related"
                ))

        if errors:
            return ValidationResult.failure(errors)

        return ValidationResult.success()


class GetAnalysisQueryValidator(BaseValidator):
    """Validator for GetAnalysisQuery."""

    async def validate(self, query: GetAnalysisQuery) -> ValidationResult:
        """Validate GetAnalysisQuery."""
        errors = []

        # Validate analysis_id
        if not query.analysis_id or not isinstance(query.analysis_id, str):
            errors.append(self.create_error(
                "Analysis ID is required and must be a string",
                "INVALID_ANALYSIS_ID",
                "analysis_id"
            ))
        elif not query.analysis_id.strip():
            errors.append(self.create_error(
                "Analysis ID cannot be empty",
                "EMPTY_ANALYSIS_ID",
                "analysis_id"
            ))
        elif len(query.analysis_id) > 500:
            errors.append(self.create_error(
                "Analysis ID is too long",
                "ANALYSIS_ID_TOO_LONG",
                "analysis_id"
            ))

        # Validate include_details if provided
        if hasattr(query, 'include_details') and query.include_details is not None:
            if not isinstance(query.include_details, bool):
                errors.append(self.create_error(
                    "include_details must be a boolean",
                    "INVALID_INCLUDE_DETAILS",
                    "include_details"
                ))

        if errors:
            return ValidationResult.failure(errors)

        return ValidationResult.success()


class ListFindingsQueryValidator(BaseValidator):
    """Validator for ListFindingsQuery."""

    async def validate(self, query: ListFindingsQuery) -> ValidationResult:
        """Validate ListFindingsQuery."""
        errors = []
        warnings = []

        # Validate document_id if provided
        if hasattr(query, 'document_id') and query.document_id is not None:
            if not isinstance(query.document_id, str):
                errors.append(self.create_error(
                    "Document ID must be a string",
                    "INVALID_DOCUMENT_ID",
                    "document_id"
                ))
            elif not query.document_id.strip():
                errors.append(self.create_error(
                    "Document ID cannot be empty",
                    "EMPTY_DOCUMENT_ID",
                    "document_id"
                ))
            elif len(query.document_id) > 500:
                errors.append(self.create_error(
                    "Document ID is too long",
                    "DOCUMENT_ID_TOO_LONG",
                    "document_id"
                ))

        # Validate analysis_id if provided
        if hasattr(query, 'analysis_id') and query.analysis_id is not None:
            if not isinstance(query.analysis_id, str):
                errors.append(self.create_error(
                    "Analysis ID must be a string",
                    "INVALID_ANALYSIS_ID",
                    "analysis_id"
                ))
            elif not query.analysis_id.strip():
                errors.append(self.create_error(
                    "Analysis ID cannot be empty",
                    "EMPTY_ANALYSIS_ID",
                    "analysis_id"
                ))
            elif len(query.analysis_id) > 500:
                errors.append(self.create_error(
                    "Analysis ID is too long",
                    "ANALYSIS_ID_TOO_LONG",
                    "analysis_id"
                ))

        # Validate severity if provided
        if hasattr(query, 'severity') and query.severity is not None:
            if not isinstance(query.severity, str):
                errors.append(self.create_error(
                    "Severity must be a string",
                    "INVALID_SEVERITY",
                    "severity"
                ))
            elif query.severity not in ['critical', 'high', 'medium', 'low', 'info']:
                errors.append(self.create_error(
                    f"Invalid severity: {query.severity}",
                    "UNSUPPORTED_SEVERITY",
                    "severity"
                ))

        # Validate category if provided
        if hasattr(query, 'category') and query.category is not None:
            if not isinstance(query.category, str):
                errors.append(self.create_error(
                    "Category must be a string",
                    "INVALID_CATEGORY",
                    "category"
                ))
            elif len(query.category) > 50:
                errors.append(self.create_error(
                    "Category is too long",
                    "CATEGORY_TOO_LONG",
                    "category"
                ))

        # Validate pagination parameters
        if hasattr(query, 'page') and query.page is not None:
            if not isinstance(query.page, int) or query.page < 1:
                errors.append(self.create_error(
                    "Page must be a positive integer",
                    "INVALID_PAGE",
                    "page"
                ))

        if hasattr(query, 'page_size') and query.page_size is not None:
            if not isinstance(query.page_size, int) or query.page_size < 1:
                errors.append(self.create_error(
                    "Page size must be a positive integer",
                    "INVALID_PAGE_SIZE",
                    "page_size"
                ))
            elif query.page_size > 100:
                warnings.append(self.create_warning(
                    "Large page size may impact performance",
                    "LARGE_PAGE_SIZE",
                    "page_size"
                ))

        # Validate date filters
        if hasattr(query, 'from_date') and query.from_date is not None:
            if hasattr(query, 'to_date') and query.to_date is not None:
                if query.from_date > query.to_date:
                    errors.append(self.create_error(
                        "From date cannot be after to date",
                        "INVALID_DATE_RANGE",
                        "from_date"
                    ))

        # Validate sort parameters
        if hasattr(query, 'sort_by') and query.sort_by is not None:
            valid_sort_fields = ['created_at', 'severity', 'category', 'confidence']
            if query.sort_by not in valid_sort_fields:
                errors.append(self.create_error(
                    f"Invalid sort field: {query.sort_by}",
                    "INVALID_SORT_FIELD",
                    "sort_by"
                ))

        if hasattr(query, 'sort_order') and query.sort_order is not None:
            if query.sort_order not in ['asc', 'desc']:
                errors.append(self.create_error(
                    f"Invalid sort order: {query.sort_order}",
                    "INVALID_SORT_ORDER",
                    "sort_order"
                ))

        # Check for conflicting parameters
        if (hasattr(query, 'document_id') and query.document_id and
            hasattr(query, 'analysis_id') and query.analysis_id):
            warnings.append(self.create_warning(
                "Filtering by both document_id and analysis_id may return no results",
                "CONFLICTING_FILTERS"
            ))

        if errors:
            return ValidationResult.failure(errors, warnings)
        elif warnings:
            return ValidationResult.success(metadata={'warnings': warnings})

        return ValidationResult.success()


class GetDocumentByIdQueryValidator(GetDocumentQueryValidator):
    """Validator for GetDocumentByIdQuery."""

    async def validate(self, query: GetDocumentByIdQuery) -> ValidationResult:
        """Validate GetDocumentByIdQuery."""
        # Reuse parent validation
        result = await super().validate(query)
        if not result.is_valid:
            return result

        # Additional validation for document ID format
        if hasattr(query, 'document_id') and query.document_id:
            # Check for potentially dangerous patterns
            dangerous_patterns = ['../', '..\\', '<script', 'javascript:', 'eval(']
            for pattern in dangerous_patterns:
                if pattern in query.document_id.lower():
                    return ValidationResult.failure([
                        self.create_error(
                            "Document ID contains potentially dangerous characters",
                            "SUSPICIOUS_DOCUMENT_ID",
                            "document_id"
                        )
                    ])

        return ValidationResult.success()


class GetAnalysisByIdQueryValidator(GetAnalysisQueryValidator):
    """Validator for GetAnalysisByIdQuery."""

    async def validate(self, query: GetAnalysisByIdQuery) -> ValidationResult:
        """Validate GetAnalysisByIdQuery."""
        # Reuse parent validation
        result = await super().validate(query)
        if not result.is_valid:
            return result

        # Additional validation for analysis ID format
        if hasattr(query, 'analysis_id') and query.analysis_id:
            # Check for potentially dangerous patterns
            dangerous_patterns = ['../', '..\\', '<script', 'javascript:', 'eval(']
            for pattern in dangerous_patterns:
                if pattern in query.analysis_id.lower():
                    return ValidationResult.failure([
                        self.create_error(
                            "Analysis ID contains potentially dangerous characters",
                            "SUSPICIOUS_ANALYSIS_ID",
                            "analysis_id"
                        )
                    ])

        return ValidationResult.success()
