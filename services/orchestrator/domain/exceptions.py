"""Domain-specific exceptions for Orchestrator service.

This module defines exceptions specific to the orchestrator domain,
following the shared exception hierarchy for consistent error handling.
"""

from services.shared.domain.exceptions import (
    DomainError,
    ValidationError,
    ServiceError,
    InfrastructureError,
    ExternalServiceError
)


class OrchestratorError(DomainError):
    """Base exception for orchestrator-related errors."""
    pass


class ServiceRegistryError(OrchestratorError):
    """Errors related to service registry operations."""
    pass


class ServiceNotFoundError(ServiceRegistryError):
    """Service not found in registry."""
    pass


class ServiceAlreadyExistsError(ServiceRegistryError):
    """Service already exists in registry."""
    pass


class ServiceRegistrationError(ServiceRegistryError):
    """Error during service registration."""
    pass


class ServiceDiscoveryError(ServiceRegistryError):
    """Error during service discovery."""
    pass


class WorkflowError(OrchestratorError):
    """Errors related to workflow operations."""
    pass


class WorkflowNotFoundError(WorkflowError):
    """Workflow not found."""
    pass


class WorkflowExecutionError(WorkflowError):
    """Error during workflow execution."""
    pass


class WorkflowValidationError(ValidationError):
    """Workflow validation error."""
    pass


class HealthCheckError(OrchestratorError):
    """Errors related to health checking."""
    pass


class ServiceUnhealthyError(HealthCheckError):
    """Service is in unhealthy state."""
    pass


class HealthCheckTimeoutError(HealthCheckError):
    """Health check operation timed out."""
    pass


class IngestionError(OrchestratorError):
    """Errors related to data ingestion."""
    pass


class IngestionSourceError(IngestionError):
    """Error with ingestion source."""
    pass


class DocumentProcessingError(IngestionError):
    """Error during document processing."""
    pass


class QueryProcessingError(OrchestratorError):
    """Errors related to query processing."""
    pass


class InvalidQueryError(ValidationError):
    """Query is invalid or malformed."""
    pass


class QueryExecutionError(QueryProcessingError):
    """Error during query execution."""
    pass


class ReportingError(OrchestratorError):
    """Errors related to reporting operations."""
    pass


class ReportGenerationError(ReportingError):
    """Error during report generation."""
    pass


class ReportNotFoundError(ReportingError):
    """Report not found."""
    pass


class InfrastructureError(OrchestratorError):
    """Errors related to infrastructure operations."""
    pass


class EventStreamingError(InfrastructureError):
    """Error with event streaming."""
    pass


class SagaExecutionError(InfrastructureError):
    """Error during saga execution."""
    pass


class TracingError(InfrastructureError):
    """Error with distributed tracing."""
    pass


class ExternalServiceCommunicationError(ExternalServiceError):
    """Error communicating with external services."""
    pass


class PeerSynchronizationError(ExternalServiceCommunicationError):
    """Error synchronizing with peer orchestrators."""
    pass


class RedisConnectionError(InfrastructureError):
    """Redis connection error."""
    pass


class DatabaseConnectionError(InfrastructureError):
    """Database connection error."""
    pass
