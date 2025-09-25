"""Domain-specific exceptions for the Discovery Agent service.

This module defines custom exception types for the Discovery Agent domain,
providing granular error handling and meaningful error messages for different
failure scenarios in service discovery, tool analysis, and security scanning.
"""

from typing import Any, Dict, Optional


class DiscoveryAgentException(Exception):
    """Base exception for all Discovery Agent domain errors."""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ServiceDiscoveryException(DiscoveryAgentException):
    """Exception raised when service discovery operations fail."""

    def __init__(self, service_name: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Failed to discover service '{service_name}': {reason}"
        super().__init__(message, details)
        self.service_name = service_name


class OpenAPISpecException(DiscoveryAgentException):
    """Exception raised when OpenAPI specification processing fails."""

    def __init__(self, url: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Failed to process OpenAPI spec from '{url}': {reason}"
        super().__init__(message, details)
        self.url = url


class EndpointExtractionException(DiscoveryAgentException):
    """Exception raised when endpoint extraction from OpenAPI spec fails."""

    def __init__(self, spec_url: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Failed to extract endpoints from OpenAPI spec '{spec_url}': {reason}"
        super().__init__(message, details)
        self.spec_url = spec_url


class ToolGenerationException(DiscoveryAgentException):
    """Exception raised when tool generation from endpoints fails."""

    def __init__(self, endpoint_path: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Failed to generate tool for endpoint '{endpoint_path}': {reason}"
        super().__init__(message, details)
        self.endpoint_path = endpoint_path


class SemanticAnalysisException(DiscoveryAgentException):
    """Exception raised when semantic analysis of tools fails."""

    def __init__(self, tool_name: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Failed to analyze semantics for tool '{tool_name}': {reason}"
        super().__init__(message, details)
        self.tool_name = tool_name


class LLMAnalysisException(DiscoveryAgentException):
    """Exception raised when LLM-powered analysis fails."""

    def __init__(self, operation: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"LLM analysis failed for operation '{operation}': {reason}"
        super().__init__(message, details)
        self.operation = operation


class SecurityScanException(DiscoveryAgentException):
    """Exception raised when security scanning of tools fails."""

    def __init__(self, tool_name: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Security scan failed for tool '{tool_name}': {reason}"
        super().__init__(message, details)
        self.tool_name = tool_name


class ToolRegistrationException(DiscoveryAgentException):
    """Exception raised when tool registration with orchestrator fails."""

    def __init__(self, tool_name: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Failed to register tool '{tool_name}' with orchestrator: {reason}"
        super().__init__(message, details)
        self.tool_name = tool_name


class WorkflowRegistrationException(DiscoveryAgentException):
    """Exception raised when workflow registration fails."""

    def __init__(self, workflow_name: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Failed to register workflow '{workflow_name}': {reason}"
        super().__init__(message, details)
        self.workflow_name = workflow_name


class ToolValidationException(DiscoveryAgentException):
    """Exception raised when tool validation fails."""

    def __init__(self, tool_name: str, validation_errors: list, details: Optional[Dict[str, Any]] = None):
        message = f"Tool '{tool_name}' failed validation: {', '.join(validation_errors)}"
        super().__init__(message, details)
        self.tool_name = tool_name
        self.validation_errors = validation_errors


class CategorizationException(DiscoveryAgentException):
    """Exception raised when tool categorization fails."""

    def __init__(self, tool_name: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Failed to categorize tool '{tool_name}': {reason}"
        super().__init__(message, details)
        self.tool_name = tool_name


class MonitoringException(DiscoveryAgentException):
    """Exception raised when monitoring operations fail."""

    def __init__(self, operation: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Monitoring operation '{operation}' failed: {reason}"
        super().__init__(message, details)
        self.operation = operation


class ConfigurationException(DiscoveryAgentException):
    """Exception raised when configuration-related operations fail."""

    def __init__(self, config_key: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Configuration error for '{config_key}': {reason}"
        super().__init__(message, details)
        self.config_key = config_key


class HealthCheckException(DiscoveryAgentException):
    """Exception raised when service health checks fail."""

    def __init__(self, service_name: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Health check failed for service '{service_name}': {reason}"
        super().__init__(message, details)
        self.service_name = service_name


class TimeoutException(DiscoveryAgentException):
    """Exception raised when operations timeout."""

    def __init__(self, operation: str, timeout_seconds: int, details: Optional[Dict[str, Any]] = None):
        message = f"Operation '{operation}' timed out after {timeout_seconds} seconds"
        super().__init__(message, details)
        self.operation = operation
        self.timeout_seconds = timeout_seconds


class NetworkException(DiscoveryAgentException):
    """Exception raised when network operations fail."""

    def __init__(self, operation: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Network operation '{operation}' failed: {reason}"
        super().__init__(message, details)
        self.operation = operation


class ParsingException(DiscoveryAgentException):
    """Exception raised when data parsing operations fail."""

    def __init__(self, data_type: str, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Failed to parse {data_type}: {reason}"
        super().__init__(message, details)
        self.data_type = data_type


class ValidationException(DiscoveryAgentException):
    """Exception raised when data validation fails."""

    def __init__(self, field: str, value: Any, reason: str, details: Optional[Dict[str, Any]] = None):
        message = f"Validation failed for field '{field}' with value '{value}': {reason}"
        super().__init__(message, details)
        self.field = field
        self.value = value


class ResourceNotFoundException(DiscoveryAgentException):
    """Exception raised when requested resources are not found."""

    def __init__(self, resource_type: str, resource_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"{resource_type} '{resource_id}' not found"
        super().__init__(message, details)
        self.resource_type = resource_type
        self.resource_id = resource_id
