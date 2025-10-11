"""
Custom exception hierarchy for Ecosystem MCP.

Provides structured exceptions for better error handling and debugging.
"""


class EcosystemMCPError(Exception):
    """Base exception for all Ecosystem MCP errors."""
    pass


class DeploymentError(EcosystemMCPError):
    """Base deployment error."""
    pass


class ServiceStartError(DeploymentError):
    """Service failed to start."""
    pass


class ServiceStopError(DeploymentError):
    """Service failed to stop."""
    pass


class HealthCheckError(EcosystemMCPError):
    """Health check failed."""
    pass


class ConfigurationError(EcosystemMCPError):
    """Configuration is invalid."""
    pass


class DatabaseError(EcosystemMCPError):
    """Database operation failed."""
    pass


class ValidationError(EcosystemMCPError):
    """Validation failed."""
    pass


class StorageError(EcosystemMCPError):
    """Storage operation failed (Redis, ChromaDB, etc)."""
    pass


class ModelError(EcosystemMCPError):
    """AI Model operation failed."""
    pass


class IngestionError(EcosystemMCPError):
    """Document ingestion failed."""
    pass


class ConfigError(EcosystemMCPError):
    """Configuration error."""
    pass

