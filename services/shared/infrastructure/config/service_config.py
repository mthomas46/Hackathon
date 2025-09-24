"""Service-Specific Configuration Classes.

This module provides standardized configuration classes for different
types of services in the LLM Documentation Ecosystem.
"""

import os
from typing import Any, Dict, List, Optional

from pydantic import BaseSettings, Field, validator

from .base_config import BaseConfig


class ServiceConfig(BaseSettings):
    """Standardized base configuration for all services."""

    # Service identity
    service_name: str = Field(..., description="Unique service name")
    service_version: str = Field(default="1.0.0", description="Service version")
    service_description: Optional[str] = Field(None, description="Service description")

    # Server configuration
    host: str = Field(default="127.0.0.1", description="Server host")
    port: int = Field(default=8000, gt=0, le=65535, description="Server port")
    debug: bool = Field(default=False, description="Debug mode")
    reload: bool = Field(default=False, description="Auto-reload on changes")

    # Database configuration
    database_url: Optional[str] = Field(None, description="Database connection URL")
    database_pool_size: int = Field(default=10, gt=0, description="Database connection pool size")
    database_max_overflow: int = Field(default=20, ge=0, description="Max overflow connections")
    database_echo: bool = Field(default=False, description="Log database queries")

    # Redis/Cache configuration
    redis_url: Optional[str] = Field(None, description="Redis connection URL")
    cache_ttl: int = Field(default=300, gt=0, description="Default cache TTL in seconds")
    cache_enabled: bool = Field(default=True, description="Enable caching")

    # External services
    discovery_agent_url: Optional[str] = Field(None, description="Service discovery URL")
    shared_service_url: Optional[str] = Field(None, description="Shared services URL")

    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json/text)")
    log_file: Optional[str] = Field(None, description="Log file path")

    # Security
    secret_key: str = Field(..., description="Application secret key")
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:3000"], description="CORS allowed origins")
    jwt_secret: Optional[str] = Field(None, description="JWT signing secret")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")

    # Performance
    max_concurrent_requests: int = Field(default=100, gt=0, description="Max concurrent requests")
    request_timeout: int = Field(default=30, gt=0, description="Request timeout in seconds")

    # Monitoring
    metrics_enabled: bool = Field(default=True, description="Enable metrics collection")
    health_check_interval: int = Field(default=30, gt=0, description="Health check interval")

    class Config:
        """Pydantic configuration."""
        env_prefix = "SERVICE_"
        case_sensitive = False
        json_encoders = {}

    @validator('secret_key', pre=True, always=True)
    def validate_secret_key(cls, v):
        """Validate and set secret key."""
        if not v:
            # Try environment variable
            env_key = os.getenv('SERVICE_SECRET_KEY') or os.getenv('SECRET_KEY')
            if env_key:
                return env_key

            # Generate a random key for development
            if cls().debug:
                import secrets
                return secrets.token_hex(32)

            raise ValueError('secret_key is required and not found in environment')
        return v

    @validator('database_url', pre=True, always=True)
    def validate_database_url(cls, v):
        """Validate and set database URL."""
        if not v:
            return os.getenv('DATABASE_URL') or "sqlite:///./app.db"
        return v

    @validator('redis_url', pre=True, always=True)
    def validate_redis_url(cls, v):
        """Validate and set Redis URL."""
        if not v:
            return os.getenv('REDIS_URL') or "redis://localhost:6379"
        return v

    @validator('cors_origins', pre=True)
    def validate_cors_origins(cls, v):
        """Validate CORS origins."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(',')]
        return v or []

    def get_database_config(self) -> Dict[str, Any]:
        """Get database-specific configuration."""
        return {
            'url': self.database_url,
            'pool_size': self.database_pool_size,
            'max_overflow': self.database_max_overflow,
            'echo': self.database_echo
        }

    def get_cache_config(self) -> Dict[str, Any]:
        """Get cache-specific configuration."""
        return {
            'url': self.redis_url,
            'ttl': self.cache_ttl,
            'enabled': self.cache_enabled
        }

    def get_service_urls(self) -> Dict[str, Optional[str]]:
        """Get external service URLs."""
        return {
            'discovery_agent': self.discovery_agent_url,
            'shared_service': self.shared_service_url
        }


# Specialized service configurations

class AnalysisServiceConfig(ServiceConfig):
    """Configuration for analysis service."""

    # Analysis-specific settings
    max_concurrent_analyses: int = Field(default=5, gt=0, description="Max concurrent analyses")
    analysis_timeout: int = Field(default=300, gt=0, description="Analysis timeout in seconds")
    supported_detectors: List[str] = Field(
        default_factory=lambda: ["quality", "sentiment", "consistency"],
        description="Supported analysis detectors"
    )

    # Model settings
    model_cache_size: int = Field(default=100, gt=0, description="Model cache size")
    enable_gpu: bool = Field(default=False, description="Enable GPU acceleration")

    # Storage settings
    analysis_results_ttl: int = Field(default=604800, gt=0, description="Analysis results TTL (seconds)")


class DocStoreConfig(ServiceConfig):
    """Configuration for document store service."""

    # Document settings
    max_document_size: int = Field(default=10485760, gt=0, description="Max document size in bytes")  # 10MB
    supported_formats: List[str] = Field(
        default_factory=lambda: ["markdown", "html", "plaintext", "json"],
        description="Supported document formats"
    )

    # Storage settings
    backup_interval: int = Field(default=3600, gt=0, description="Backup interval in seconds")
    compression_enabled: bool = Field(default=True, description="Enable document compression")

    # Indexing settings
    enable_full_text_search: bool = Field(default=True, description="Enable full-text search")
    index_batch_size: int = Field(default=1000, gt=0, description="Indexing batch size")


class OrchestratorConfig(ServiceConfig):
    """Configuration for orchestrator service."""

    # Workflow settings
    max_concurrent_workflows: int = Field(default=50, gt=0, description="Max concurrent workflows")
    workflow_timeout: int = Field(default=1800, gt=0, description="Workflow timeout in seconds")

    # Service registry settings
    registry_ttl: int = Field(default=300, gt=0, description="Service registry TTL")
    health_check_interval: int = Field(default=30, gt=0, description="Health check interval")

    # Event streaming settings
    event_buffer_size: int = Field(default=1000, gt=0, description="Event buffer size")
    enable_event_persistence: bool = Field(default=True, description="Enable event persistence")


class PromptStoreConfig(ServiceConfig):
    """Configuration for prompt store service."""

    # Prompt settings
    max_prompt_size: int = Field(default=8192, gt=0, description="Max prompt size in characters")
    enable_versioning: bool = Field(default=True, description="Enable prompt versioning")

    # A/B testing settings
    ab_test_sample_size: int = Field(default=1000, gt=0, description="A/B test sample size")
    ab_test_confidence_level: float = Field(default=0.95, gt=0, le=1, description="A/B test confidence level")

    # Caching settings
    prompt_cache_ttl: int = Field(default=3600, gt=0, description="Prompt cache TTL")


class DiscoveryAgentConfig(ServiceConfig):
    """Configuration for service discovery agent."""

    # Discovery settings
    discovery_interval: int = Field(default=30, gt=0, description="Service discovery interval")
    heartbeat_timeout: int = Field(default=90, gt=0, description="Service heartbeat timeout")

    # Registry settings
    max_services: int = Field(default=1000, gt=0, description="Max registered services")
    enable_service_auth: bool = Field(default=True, description="Enable service authentication")

    # Monitoring settings
    metrics_retention: int = Field(default=604800, gt=0, description="Metrics retention period")


class FrontendConfig(ServiceConfig):
    """Configuration for frontend service."""

    # Web settings
    static_files_dir: str = Field(default="./static", description="Static files directory")
    templates_dir: str = Field(default="./templates", description="Templates directory")

    # API settings
    api_timeout: int = Field(default=30, gt=0, description="API request timeout")
    enable_caching: bool = Field(default=True, description="Enable response caching")

    # UI settings
    theme: str = Field(default="light", description="Default UI theme")
    language: str = Field(default="en", description="Default language")


class CLIConfig(ServiceConfig):
    """Configuration for CLI service."""

    # Command settings
    max_command_timeout: int = Field(default=300, gt=0, description="Max command timeout")
    enable_parallel_execution: bool = Field(default=True, description="Enable parallel command execution")

    # Output settings
    output_format: str = Field(default="table", description="Default output format")
    enable_colors: bool = Field(default=True, description="Enable colored output")

    # History settings
    command_history_size: int = Field(default=1000, gt=0, description="Command history size")


class SummarizerHubConfig(ServiceConfig):
    """Configuration for summarizer hub service."""

    # Summarization settings
    max_text_length: int = Field(default=50000, gt=0, description="Max text length for summarization")
    supported_languages: List[str] = Field(
        default_factory=lambda: ["en", "es", "fr", "de"],
        description="Supported languages"
    )

    # Model settings
    default_model: str = Field(default="bart-large-cnn", description="Default summarization model")
    enable_model_caching: bool = Field(default=True, description="Enable model caching")

    # Performance settings
    max_concurrent_summaries: int = Field(default=10, gt=0, description="Max concurrent summaries")


class DocStoreConfig(ServiceConfig):
    """Configuration for document store service."""

    # Document settings
    max_document_size: int = Field(default=10485760, gt=0, description="Max document size in bytes (10MB)")
    supported_formats: List[str] = Field(
        default_factory=lambda: ["markdown", "html", "plaintext", "json"],
        description="Supported document formats"
    )
    enable_content_hashing: bool = Field(default=True, description="Enable content hashing for duplicates")

    # Storage settings
    backup_interval: int = Field(default=3600, gt=0, description="Backup interval in seconds")
    compression_enabled: bool = Field(default=True, description="Enable document compression")
    max_versions_per_document: int = Field(default=10, gt=0, description="Max versions to keep per document")

    # Search settings
    enable_full_text_search: bool = Field(default=True, description="Enable full-text search")
    search_index_batch_size: int = Field(default=1000, gt=0, description="Search indexing batch size")
    search_timeout: int = Field(default=30, gt=0, description="Search query timeout")

    # Analytics settings
    enable_usage_analytics: bool = Field(default=True, description="Enable usage analytics collection")
    analytics_retention_days: int = Field(default=90, gt=0, description="Analytics data retention")

    # Lifecycle settings
    enable_automatic_cleanup: bool = Field(default=True, description="Enable automatic cleanup")
    cleanup_batch_size: int = Field(default=100, gt=0, description="Cleanup batch size")

    # Tagging settings
    max_tags_per_document: int = Field(default=50, gt=0, description="Max tags per document")
    enable_tag_suggestions: bool = Field(default=True, description="Enable tag suggestions")

    # Bulk operations settings
    max_bulk_operation_size: int = Field(default=1000, gt=0, description="Max items in bulk operations")
    bulk_operation_timeout: int = Field(default=300, gt=0, description="Bulk operation timeout")


# Configuration factory functions

def create_service_config(service_type: str, **overrides) -> ServiceConfig:
    """Create service configuration based on service type.

    Args:
        service_type: Type of service (analysis-service, doc-store, etc.)
        **overrides: Configuration overrides

    Returns:
        Service-specific configuration instance
    """
    config_classes = {
        'analysis-service': AnalysisServiceConfig,
        'doc-store': DocStoreConfig,
        'orchestrator': OrchestratorConfig,
        'prompt-store': PromptStoreConfig,
        'discovery-agent': DiscoveryAgentConfig,
        'frontend': FrontendConfig,
        'cli': CLIConfig,
        'summarizer-hub': SummarizerHubConfig,
    }

    config_class = config_classes.get(service_type, ServiceConfig)
    return config_class(**overrides)


def load_service_config(
    service_type: str,
    config_file: Optional[str] = None,
    env_prefix: str = "SERVICE_",
    **overrides
) -> ServiceConfig:
    """Load service configuration from multiple sources.

    Args:
        service_type: Type of service
        config_file: Optional configuration file path
        env_prefix: Environment variable prefix
        **overrides: Configuration overrides

    Returns:
        Loaded service configuration
    """
    from .base_config import ConfigLoader

    loader = ConfigLoader()

    # Load from environment
    loader.add_environment_source(env_prefix)

    # Load from config file if provided
    if config_file and os.path.exists(config_file):
        loader.add_file_source(config_file)

    return loader.load(
        lambda **kwargs: create_service_config(service_type, **kwargs),
        **overrides
    )
