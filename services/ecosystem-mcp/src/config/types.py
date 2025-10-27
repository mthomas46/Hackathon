"""
Pydantic models for service registry configuration.

These models provide type-safe access to configuration values
and validate the registry schema on load.
"""

from typing import Dict, Any, List, Optional
from pathlib import Path
from pydantic import BaseModel, Field, validator


# =============================================================================
# REDIS CONFIGURATION MODELS
# =============================================================================

class RedisStreamConfig(BaseModel):
    """Configuration for a single Redis stream."""
    name: str = Field(min_length=1, max_length=255, description="Stream name")
    max_length: int = Field(gt=0, description="Maximum stream length")
    consumer_group: str = Field(min_length=1, max_length=255, description="Consumer group name")
    description: str = Field(description="Stream purpose description")
    
    @validator('name')
    def validate_stream_name(cls, v):
        """Ensure stream name follows conventions."""
        if not v.islower():
            raise ValueError("Stream name must be lowercase")
        if ' ' in v:
            raise ValueError("Stream name cannot contain spaces")
        return v
    
    @validator('consumer_group')
    def validate_consumer_group(cls, v):
        """
        Ensure consumer group name follows conventions.
        
        This validation prevents the exact issue we had today!
        """
        if not v.islower():
            raise ValueError("Consumer group must be lowercase")
        if ' ' in v:
            raise ValueError("Consumer group cannot contain spaces")
        return v


class RedisStreamsConfig(BaseModel):
    """Configuration for all Redis streams."""
    ingestion: RedisStreamConfig
    embedding: RedisStreamConfig
    retry: RedisStreamConfig
    dead_letter: RedisStreamConfig


class RedisRetryConfig(BaseModel):
    """Redis retry configuration."""
    max_retries: int = Field(gt=0, le=10, description="Maximum retry attempts")
    backoff_base: int = Field(gt=1, le=10, description="Exponential backoff base")
    backoff_max_minutes: int = Field(gt=0, le=1440, description="Maximum backoff time")


class RedisConnectionConfig(BaseModel):
    """Redis connection configuration."""
    url: str = Field(description="Redis connection URL")
    host: str = Field(description="Redis host")
    port: int = Field(ge=1, le=65535, description="Redis port")
    database: int = Field(ge=0, le=15, description="Redis database number")
    max_connections: int = Field(gt=0, le=1000, description="Connection pool size")
    connection_timeout_seconds: int = Field(gt=0, description="Connection timeout")
    operation_timeout_seconds: int = Field(gt=0, description="Operation timeout")


class RedisConfig(BaseModel):
    """Complete Redis configuration."""
    connection: RedisConnectionConfig
    streams: RedisStreamsConfig
    retry: RedisRetryConfig


# =============================================================================
# DATABASE CONFIGURATION MODELS
# =============================================================================

class DatabaseConnectionConfig(BaseModel):
    """PostgreSQL connection configuration."""
    host: str = Field(description="Database host")
    port: int = Field(ge=1, le=65535, description="Database port")
    database: str = Field(min_length=1, description="Database name")
    user: str = Field(min_length=1, description="Database user")
    password: str = Field(min_length=1, description="Database password")
    pool_size: int = Field(gt=0, le=100, description="Connection pool size")
    max_overflow: int = Field(ge=0, le=50, description="Max overflow connections")
    connection_timeout_seconds: int = Field(gt=0, description="Connection timeout")
    url: str = Field(description="Full connection string")


class DatabaseContainerConfig(BaseModel):
    """Container-specific database overrides."""
    host: str = Field(description="Container host name")
    url: str = Field(description="Container connection string")


class DocumentsTableConfig(BaseModel):
    """Documents table schema validation."""
    required_columns: List[str] = Field(description="Required column names")


class IngestionJobsTableConfig(BaseModel):
    """Ingestion jobs table schema validation."""
    required_columns: List[str] = Field(description="Required column names")


class DatabaseTablesConfig(BaseModel):
    """Database table validation configuration."""
    required: List[str] = Field(description="Required table names")
    documents: Optional[DocumentsTableConfig] = None
    ingestion_jobs: Optional[IngestionJobsTableConfig] = None


class DatabaseConfig(BaseModel):
    """Complete PostgreSQL configuration."""
    connection: DatabaseConnectionConfig
    container: DatabaseContainerConfig
    tables: DatabaseTablesConfig


# =============================================================================
# CHROMADB CONFIGURATION MODELS
# =============================================================================

class ChromaDBConnectionConfig(BaseModel):
    """ChromaDB connection configuration."""
    path: str = Field(description="Storage path")
    connection_timeout_seconds: int = Field(gt=0, description="Connection timeout")


class ChromaDBCollectionConfig(BaseModel):
    """ChromaDB collection configuration."""
    name: str = Field(min_length=1, description="Collection name")
    distance_metric: str = Field(description="Distance metric (cosine, l2, ip)")
    embedding_dimension: int = Field(gt=0, le=4096, description="Embedding dimension")
    
    @validator('distance_metric')
    def validate_distance_metric(cls, v):
        """Ensure valid distance metric."""
        allowed = ['cosine', 'l2', 'ip']
        if v not in allowed:
            raise ValueError(f"Distance metric must be one of {allowed}")
        return v


class ChromaDBCollectionsConfig(BaseModel):
    """ChromaDB collections configuration."""
    main: ChromaDBCollectionConfig


class ChromaDBConfig(BaseModel):
    """Complete ChromaDB configuration."""
    connection: ChromaDBConnectionConfig
    collections: ChromaDBCollectionsConfig


# =============================================================================
# OLLAMA CONFIGURATION MODELS
# =============================================================================

class OllamaModelsConfig(BaseModel):
    """Ollama model configuration."""
    small: str = Field(description="Small model for fast queries")
    medium: str = Field(description="Medium model for complex queries")
    embedding: str = Field(description="Embedding model")


class OllamaContainerConfig(BaseModel):
    """Container Ollama configuration."""
    enabled: bool = Field(description="Enable container Ollama")
    base_url: str = Field(description="Base URL")
    host: str = Field(description="Host")
    port: int = Field(ge=1, le=65535, description="Port")
    timeout_seconds: int = Field(gt=0, description="Request timeout")
    models: OllamaModelsConfig


class OllamaDesktopConfig(BaseModel):
    """Desktop Ollama configuration."""
    model_config = {"protected_namespaces": ()}
    
    enabled: bool = Field(description="Enable desktop Ollama")
    base_url: str = Field(description="Base URL")
    model: str = Field(description="Model name")
    use_for_rag: bool = Field(description="Use for RAG queries")
    description: str = Field(description="Configuration description")


class OllamaPerformanceConfig(BaseModel):
    """Ollama performance settings."""
    num_ctx: int = Field(gt=0, description="Context window size")
    num_threads: int = Field(gt=0, description="Thread count")
    num_batch: int = Field(gt=0, description="Batch size")
    keep_alive_minutes: int = Field(gt=0, description="Keep alive duration")
    flash_attention: bool = Field(description="Enable flash attention")
    max_queue: int = Field(gt=0, description="Max queue size")
    num_parallel: int = Field(gt=0, description="Parallel requests")


class OllamaConfig(BaseModel):
    """Complete Ollama configuration."""
    container: OllamaContainerConfig
    desktop: OllamaDesktopConfig
    performance: OllamaPerformanceConfig


# =============================================================================
# SERVICE CONFIGURATION MODELS
# =============================================================================

class ServicePortsConfig(BaseModel):
    """Service port configuration."""
    api: Optional[int] = Field(None, ge=1, le=65535, description="API port")
    metrics: Optional[int] = Field(None, ge=1, le=65535, description="Metrics port")
    ui: Optional[int] = Field(None, ge=1, le=65535, description="UI port")
    internal: Optional[int] = Field(None, ge=1, le=65535, description="Internal port")
    main: Optional[int] = Field(None, ge=1, le=65535, description="Main port")


class ServiceEndpointsConfig(BaseModel):
    """Service endpoint configuration."""
    health: Optional[str] = Field(None, description="Health check endpoint")
    ready: Optional[str] = Field(None, description="Readiness endpoint")
    metrics: Optional[str] = Field(None, description="Metrics endpoint")
    embed: Optional[str] = Field(None, description="Embed endpoint")


class ServiceConfig(BaseModel):
    """Individual service configuration."""
    name: str = Field(min_length=1, description="Service name")
    container_name: str = Field(min_length=1, description="Container name")
    ports: ServicePortsConfig
    endpoints: Optional[ServiceEndpointsConfig] = None
    network: str = Field(min_length=1, description="Docker network")
    image: Optional[str] = Field(None, description="Docker image")


class ServicesConfig(BaseModel):
    """All services configuration."""
    ecosystem_mcp: ServiceConfig
    ecosystem_mcp_embedding: ServiceConfig
    ecosystem_mcp_dashboard: ServiceConfig
    postgres: ServiceConfig
    redis: ServiceConfig
    ollama: ServiceConfig


# =============================================================================
# WORKER CONFIGURATION MODELS
# =============================================================================

class CircuitBreakerConfig(BaseModel):
    """Circuit breaker configuration."""
    failure_threshold: int = Field(gt=0, description="Failure threshold")
    reset_timeout_seconds: int = Field(gt=0, description="Reset timeout")


class WorkerConfig(BaseModel):
    """Worker configuration."""
    consumer_name_prefix: str = Field(min_length=1, description="Consumer name prefix")
    consumer_group: str = Field(min_length=1, description="Consumer group name")
    poll_interval_seconds: int = Field(gt=0, description="Poll interval")
    batch_size: int = Field(gt=0, description="Batch size")
    max_retries: Optional[int] = Field(None, gt=0, description="Max retries")
    timeout_seconds: Optional[int] = Field(None, gt=0, description="Timeout")
    heartbeat_interval_seconds: Optional[int] = Field(None, gt=0, description="Heartbeat interval")
    circuit_breaker: Optional[CircuitBreakerConfig] = None


class WorkersConfig(BaseModel):
    """All workers configuration."""
    ingestion: WorkerConfig
    retry: WorkerConfig


# =============================================================================
# VALIDATION CONFIGURATION MODELS
# =============================================================================

class PreflightChecksConfig(BaseModel):
    """Preflight checks configuration."""
    required: List[str] = Field(description="Required checks")
    optional: List[str] = Field(description="Optional checks")


class RuntimeChecksConfig(BaseModel):
    """Runtime checks configuration."""
    enabled: bool = Field(description="Enable runtime checks")
    frequency_seconds: int = Field(gt=0, description="Check frequency")
    checks: List[str] = Field(description="Check names")


class FailFastConfig(BaseModel):
    """Fail-fast configuration."""
    enabled: bool = Field(description="Enable fail-fast")
    critical_mismatches: List[str] = Field(description="Critical mismatch types")


class SeverityConfig(BaseModel):
    """Severity level configuration."""
    critical: str
    high: str
    medium: str
    low: str


class ValidationConfig(BaseModel):
    """Complete validation configuration."""
    preflight_checks: PreflightChecksConfig
    runtime_checks: RuntimeChecksConfig
    fail_fast: FailFastConfig
    severity: SeverityConfig


# =============================================================================
# TOP-LEVEL REGISTRY MODEL
# =============================================================================

class ServiceIdentityConfig(BaseModel):
    """Service identity configuration."""
    canonical_name: str = Field(min_length=1, description="Canonical service name")
    display_name: str = Field(min_length=1, description="Display name")
    description: str = Field(description="Service description")
    version: str = Field(min_length=1, description="Service version")


class CursorConfig(BaseModel):
    """Cursor IDE integration configuration."""
    model_config = {"protected_namespaces": ()}
    
    enabled: bool = Field(description="Enable Cursor integration")
    mcp_url: str = Field(description="MCP server URL")
    model: str = Field(description="Model name")
    complexity_threshold: float = Field(ge=0.0, le=1.0, description="Complexity threshold")
    fallback_enabled: bool = Field(description="Enable fallback")


class EmbeddingServiceConfig(BaseModel):
    """Embedding service configuration."""
    model_config = {"protected_namespaces": ()}
    
    enabled: bool = Field(description="Enable embedding service")
    base_url: str = Field(description="Base URL")
    container_url: str = Field(description="Container URL")
    model_name: str = Field(description="Model name")
    cache_enabled: bool = Field(description="Enable cache")
    cache_ttl_seconds: int = Field(gt=0, description="Cache TTL")
    timeout_seconds: int = Field(gt=0, description="Request timeout")


class EnvironmentConfig(BaseModel):
    """Environment-specific configuration."""
    log_level: str
    preflight_mode: str
    fail_fast: bool
    redis: Optional[Dict[str, Any]] = None
    database: Optional[Dict[str, Any]] = None


class EnvironmentsConfig(BaseModel):
    """All environments configuration."""
    development: EnvironmentConfig
    test: EnvironmentConfig
    production: EnvironmentConfig


class MetadataConfig(BaseModel):
    """Registry metadata."""
    baseline_created: str
    created_by: str
    source: str
    issues_found: List[str]
    fixes_needed: int
    priority_fixes: List[str]


class ChangelogEntry(BaseModel):
    """Changelog entry."""
    version: str
    date: str
    phase: str
    changes: List[str]
    author: str
    notes: str


class ServiceRegistry(BaseModel):
    """
    Complete service registry configuration.
    
    This is the root model that represents the entire service_registry.yaml file.
    All configuration values are validated against this schema.
    """
    version: str = Field(min_length=1, description="Registry version")
    generated_at: str = Field(description="Generation timestamp")
    environment: str = Field(description="Environment name")
    
    service_identity: ServiceIdentityConfig
    redis: RedisConfig
    database: DatabaseConfig
    chromadb: ChromaDBConfig
    ollama: OllamaConfig
    cursor: CursorConfig
    embedding_service: EmbeddingServiceConfig
    services: ServicesConfig
    workers: WorkersConfig
    
    docker: Optional[Dict[str, Any]] = None
    validation: ValidationConfig
    environments: EnvironmentsConfig
    metadata: MetadataConfig
    changelog: List[ChangelogEntry]
    notes: str
    
    @validator('environment')
    def validate_environment(cls, v):
        """Ensure environment is valid."""
        allowed = ['development', 'test', 'production']
        if v not in allowed:
            raise ValueError(f"Environment must be one of {allowed}, got: {v}")
        return v
    
    class Config:
        """Pydantic config."""
        extra = "allow"  # Allow additional fields for extensibility

