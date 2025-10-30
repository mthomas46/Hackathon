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


# ⚡ PHASE 2: Additional specific exceptions for better error handling

class RedisError(StorageError):
    """Redis operation failed."""
    pass


class ProgressTrackingError(EcosystemMCPError):
    """Progress tracking operation failed (non-critical)."""
    pass


class JobTimeoutError(IngestionError):
    """Job exceeded timeout threshold."""
    pass


class WorkerHeartbeatError(EcosystemMCPError):
    """Worker heartbeat update failed (non-critical)."""
    pass


class MetadataUpdateError(IngestionError):
    """Job metadata update failed (non-critical)."""
    pass


class GitOperationError(EcosystemMCPError):
    """Git operation failed."""
    pass


class FileProcessingError(IngestionError):
    """File processing operation failed."""
    pass


class EmbeddingGenerationError(ModelError):
    """Embedding generation failed."""
    pass

