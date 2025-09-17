"""Domain exceptions for Analysis Service."""

from typing import Dict, Any, Optional


class DomainException(Exception):
    """Base exception for domain layer errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize domain exception."""
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def __str__(self) -> str:
        """String representation of exception."""
        if self.details:
            return f"{self.message} - Details: {self.details}"
        return self.message


class ValidationException(DomainException):
    """Exception for validation failures."""

    def __init__(self, message: str, validation_errors: Optional[list] = None):
        """Initialize validation exception."""
        super().__init__(message, {"validation_errors": validation_errors or []})
        self.validation_errors = validation_errors or []


class BusinessRuleViolation(DomainException):
    """Exception for business rule violations."""

    def __init__(self, rule_name: str, message: str, details: Optional[Dict[str, Any]] = None):
        """Initialize business rule violation."""
        super().__init__(message, details or {})
        self.rule_name = rule_name


class DocumentException(DomainException):
    """Base exception for document-related errors."""
    pass


class DocumentNotFoundException(DocumentException):
    """Exception when document is not found."""

    def __init__(self, document_id: str):
        """Initialize document not found exception."""
        super().__init__(f"Document not found: {document_id}", {"document_id": document_id})
        self.document_id = document_id


class DocumentValidationException(DocumentException):
    """Exception for document validation failures."""

    def __init__(self, document_id: str, validation_errors: list):
        """Initialize document validation exception."""
        message = f"Document validation failed for {document_id}"
        super().__init__(message, {
            "document_id": document_id,
            "validation_errors": validation_errors
        })
        self.document_id = document_id
        self.validation_errors = validation_errors


class DocumentSizeExceededException(DocumentException):
    """Exception when document size exceeds limits."""

    def __init__(self, document_id: str, size_bytes: int, max_size_bytes: int):
        """Initialize document size exceeded exception."""
        message = f"Document size {size_bytes} bytes exceeds maximum {max_size_bytes} bytes"
        super().__init__(message, {
            "document_id": document_id,
            "size_bytes": size_bytes,
            "max_size_bytes": max_size_bytes
        })
        self.document_id = document_id
        self.size_bytes = size_bytes
        self.max_size_bytes = max_size_bytes


class AnalysisException(DomainException):
    """Base exception for analysis-related errors."""
    pass


class AnalysisNotFoundException(AnalysisException):
    """Exception when analysis is not found."""

    def __init__(self, analysis_id: str):
        """Initialize analysis not found exception."""
        super().__init__(f"Analysis not found: {analysis_id}", {"analysis_id": analysis_id})
        self.analysis_id = analysis_id


class AnalysisExecutionException(AnalysisException):
    """Exception during analysis execution."""

    def __init__(self, analysis_id: str, analysis_type: str, error_message: str):
        """Initialize analysis execution exception."""
        message = f"Analysis execution failed for {analysis_type}: {error_message}"
        super().__init__(message, {
            "analysis_id": analysis_id,
            "analysis_type": analysis_type,
            "error_message": error_message
        })
        self.analysis_id = analysis_id
        self.analysis_type = analysis_type
        self.error_message = error_message


class AnalysisTimeoutException(AnalysisException):
    """Exception when analysis times out."""

    def __init__(self, analysis_id: str, timeout_seconds: int):
        """Initialize analysis timeout exception."""
        message = f"Analysis timed out after {timeout_seconds} seconds"
        super().__init__(message, {
            "analysis_id": analysis_id,
            "timeout_seconds": timeout_seconds
        })
        self.analysis_id = analysis_id
        self.timeout_seconds = timeout_seconds


class AnalysisAlreadyRunningException(AnalysisException):
    """Exception when trying to start an already running analysis."""

    def __init__(self, analysis_id: str):
        """Initialize analysis already running exception."""
        super().__init__(f"Analysis is already running: {analysis_id}", {"analysis_id": analysis_id})
        self.analysis_id = analysis_id


class FindingException(DomainException):
    """Base exception for finding-related errors."""
    pass


class FindingNotFoundException(FindingException):
    """Exception when finding is not found."""

    def __init__(self, finding_id: str):
        """Initialize finding not found exception."""
        super().__init__(f"Finding not found: {finding_id}", {"finding_id": finding_id})
        self.finding_id = finding_id


class FindingAlreadyResolvedException(FindingException):
    """Exception when trying to resolve an already resolved finding."""

    def __init__(self, finding_id: str):
        """Initialize finding already resolved exception."""
        super().__init__(f"Finding is already resolved: {finding_id}", {"finding_id": finding_id})
        self.finding_id = finding_id


class RepositoryException(DomainException):
    """Base exception for repository-related errors."""
    pass


class RepositoryNotFoundException(RepositoryException):
    """Exception when repository is not found."""

    def __init__(self, repository_id: str):
        """Initialize repository not found exception."""
        super().__init__(f"Repository not found: {repository_id}", {"repository_id": repository_id})
        self.repository_id = repository_id


class RepositoryConnectionException(RepositoryException):
    """Exception when repository connection fails."""

    def __init__(self, repository_id: str, url: str, error_message: str):
        """Initialize repository connection exception."""
        message = f"Failed to connect to repository {repository_id} at {url}: {error_message}"
        super().__init__(message, {
            "repository_id": repository_id,
            "url": url,
            "error_message": error_message
        })
        self.repository_id = repository_id
        self.url = url
        self.error_message = error_message


class RepositorySyncException(RepositoryException):
    """Exception during repository synchronization."""

    def __init__(self, repository_id: str, error_message: str):
        """Initialize repository sync exception."""
        message = f"Repository synchronization failed for {repository_id}: {error_message}"
        super().__init__(message, {
            "repository_id": repository_id,
            "error_message": error_message
        })
        self.repository_id = repository_id
        self.error_message = error_message


class ExternalServiceException(DomainException):
    """Base exception for external service errors."""
    pass


class SemanticAnalysisException(ExternalServiceException):
    """Exception during semantic analysis."""

    def __init__(self, service_name: str, error_message: str):
        """Initialize semantic analysis exception."""
        message = f"Semantic analysis failed in {service_name}: {error_message}"
        super().__init__(message, {
            "service_name": service_name,
            "error_message": error_message
        })
        self.service_name = service_name
        self.error_message = error_message


class SentimentAnalysisException(ExternalServiceException):
    """Exception during sentiment analysis."""

    def __init__(self, service_name: str, error_message: str):
        """Initialize sentiment analysis exception."""
        message = f"Sentiment analysis failed in {service_name}: {error_message}"
        super().__init__(message, {
            "service_name": service_name,
            "error_message": error_message
        })
        self.service_name = service_name
        self.error_message = error_message


class ConfigurationException(DomainException):
    """Exception for configuration-related errors."""

    def __init__(self, config_key: str, error_message: str):
        """Initialize configuration exception."""
        message = f"Configuration error for {config_key}: {error_message}"
        super().__init__(message, {
            "config_key": config_key,
            "error_message": error_message
        })
        self.config_key = config_key
        self.error_message = error_message


class AuthorizationException(DomainException):
    """Exception for authorization failures."""

    def __init__(self, resource: str, action: str, user_id: Optional[str] = None):
        """Initialize authorization exception."""
        message = f"Access denied: {action} on {resource}"
        details = {"resource": resource, "action": action}
        if user_id:
            details["user_id"] = user_id
        super().__init__(message, details)
        self.resource = resource
        self.action = action
        self.user_id = user_id


class ResourceLimitExceededException(DomainException):
    """Exception when resource limits are exceeded."""

    def __init__(self, resource_type: str, current_count: int, max_limit: int):
        """Initialize resource limit exceeded exception."""
        message = f"Resource limit exceeded for {resource_type}: {current_count}/{max_limit}"
        super().__init__(message, {
            "resource_type": resource_type,
            "current_count": current_count,
            "max_limit": max_limit
        })
        self.resource_type = resource_type
        self.current_count = current_count
        self.max_limit = max_limit
