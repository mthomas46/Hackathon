"""Domain exceptions for Doc Store service."""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class DocStoreException(Exception):
    """Base exception for Doc Store domain errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize Doc Store exception."""
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """String representation of exception."""
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


# Document-related exceptions
class DocumentException(DocStoreException):
    """Exception for document-related errors."""
    pass


class DocumentNotFoundException(DocumentException):
    """Exception raised when a document is not found."""

    def __init__(self, document_id: str, details: Optional[Dict[str, Any]] = None):
        """Initialize document not found exception."""
        message = f"Document not found: {document_id}"
        super().__init__(message, details or {"document_id": document_id})


class DocumentValidationException(DocumentException):
    """Exception raised when document validation fails."""

    def __init__(self, message: str, validation_errors: Optional[list] = None):
        """Initialize document validation exception."""
        super().__init__(message, {"validation_errors": validation_errors or []})
        self.validation_errors = validation_errors or []


class DocumentSizeExceededException(DocumentException):
    """Exception raised when document size exceeds limits."""

    def __init__(self, size: int, max_size: int, details: Optional[Dict[str, Any]] = None):
        """Initialize document size exceeded exception."""
        message = f"Document size {size} bytes exceeds maximum allowed size {max_size} bytes"
        super().__init__(message, details or {"size": size, "max_size": max_size})


class DocumentContentTypeException(DocumentException):
    """Exception raised when document content type is not supported."""

    def __init__(self, content_type: str, supported_types: Optional[list] = None):
        """Initialize document content type exception."""
        message = f"Unsupported content type: {content_type}"
        details = {"content_type": content_type}
        if supported_types:
            details["supported_types"] = supported_types
        super().__init__(message, details)


# Versioning-related exceptions
class VersioningException(DocStoreException):
    """Exception for versioning-related errors."""
    pass


class VersionNotFoundException(VersioningException):
    """Exception raised when a document version is not found."""

    def __init__(self, document_id: str, version: str, details: Optional[Dict[str, Any]] = None):
        """Initialize version not found exception."""
        message = f"Version {version} not found for document {document_id}"
        super().__init__(message, details or {"document_id": document_id, "version": version})


class VersionConflictException(VersioningException):
    """Exception raised when version conflicts occur."""

    def __init__(self, document_id: str, details: Optional[Dict[str, Any]] = None):
        """Initialize version conflict exception."""
        message = f"Version conflict detected for document {document_id}"
        super().__init__(message, details or {"document_id": document_id})


# Tagging-related exceptions
class TaggingException(DocStoreException):
    """Exception for tagging-related errors."""
    pass


class TagNotFoundException(TaggingException):
    """Exception raised when a tag is not found."""

    def __init__(self, tag_id: str, details: Optional[Dict[str, Any]] = None):
        """Initialize tag not found exception."""
        message = f"Tag not found: {tag_id}"
        super().__init__(message, details or {"tag_id": tag_id})


class InvalidTagException(TaggingException):
    """Exception raised when a tag is invalid."""

    def __init__(self, tag: str, reason: str, details: Optional[Dict[str, Any]] = None):
        """Initialize invalid tag exception."""
        message = f"Invalid tag '{tag}': {reason}"
        super().__init__(message, details or {"tag": tag, "reason": reason})


# Relationship-related exceptions
class RelationshipsException(DocStoreException):
    """Exception for relationship-related errors."""
    pass


class RelationshipNotFoundException(RelationshipsException):
    """Exception raised when a relationship is not found."""

    def __init__(self, source_id: str, target_id: str, details: Optional[Dict[str, Any]] = None):
        """Initialize relationship not found exception."""
        message = f"Relationship not found between {source_id} and {target_id}"
        super().__init__(message, details or {"source_id": source_id, "target_id": target_id})


class CircularReferenceException(RelationshipsException):
    """Exception raised when circular references are detected."""

    def __init__(self, document_ids: list, details: Optional[Dict[str, Any]] = None):
        """Initialize circular reference exception."""
        message = f"Circular reference detected: {' -> '.join(document_ids)}"
        super().__init__(message, details or {"document_ids": document_ids})


# Bulk operation-related exceptions
class BulkOperationException(DocStoreException):
    """Exception for bulk operation-related errors."""
    pass


class BulkOperationTimeoutException(BulkOperationException):
    """Exception raised when bulk operations timeout."""

    def __init__(self, operation_id: str, timeout_seconds: int, details: Optional[Dict[str, Any]] = None):
        """Initialize bulk operation timeout exception."""
        message = f"Bulk operation {operation_id} timed out after {timeout_seconds} seconds"
        super().__init__(message, details or {"operation_id": operation_id, "timeout_seconds": timeout_seconds})


# Analytics-related exceptions
class AnalyticsException(DocStoreException):
    """Exception for analytics-related errors."""
    pass


class InvalidAnalyticsQueryException(AnalyticsException):
    """Exception raised when analytics queries are invalid."""

    def __init__(self, query: str, reason: str, details: Optional[Dict[str, Any]] = None):
        """Initialize invalid analytics query exception."""
        message = f"Invalid analytics query: {reason}"
        super().__init__(message, details or {"query": query, "reason": reason})


# Lifecycle-related exceptions
class LifecycleException(DocStoreException):
    """Exception for lifecycle-related errors."""
    pass


class InvalidLifecycleTransitionException(LifecycleException):
    """Exception raised when lifecycle transitions are invalid."""

    def __init__(self, current_state: str, target_state: str, details: Optional[Dict[str, Any]] = None):
        """Initialize invalid lifecycle transition exception."""
        message = f"Invalid lifecycle transition from {current_state} to {target_state}"
        super().__init__(message, details or {"current_state": current_state, "target_state": target_state})


# Notification-related exceptions
class NotificationsException(DocStoreException):
    """Exception for notification-related errors."""
    pass


class NotificationDeliveryException(NotificationsException):
    """Exception raised when notification delivery fails."""

    def __init__(self, notification_id: str, recipient: str, details: Optional[Dict[str, Any]] = None):
        """Initialize notification delivery exception."""
        message = f"Failed to deliver notification {notification_id} to {recipient}"
        super().__init__(message, details or {"notification_id": notification_id, "recipient": recipient})


# Helper functions for creating exceptions
def create_document_not_found_error(document_id: str) -> DocumentNotFoundException:
    """Create a document not found error."""
    return DocumentNotFoundException(document_id)


def create_validation_error(message: str, errors: Optional[list] = None) -> DocumentValidationException:
    """Create a validation error."""
    return DocumentValidationException(message, errors)


def create_version_conflict_error(document_id: str) -> VersionConflictException:
    """Create a version conflict error."""
    return VersionConflictException(document_id)


def create_bulk_timeout_error(operation_id: str, timeout: int) -> BulkOperationTimeoutException:
    """Create a bulk operation timeout error."""
    return BulkOperationTimeoutException(operation_id, timeout)
