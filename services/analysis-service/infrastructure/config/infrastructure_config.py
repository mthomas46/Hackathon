"""Main infrastructure configuration."""

from typing import Optional
from dataclasses import dataclass, field

from .database_config import DatabaseConfig
from .cache_config import CacheConfig
from .external_service_config import ExternalServiceConfig


@dataclass
class InfrastructureConfig:
    """Main configuration class for all infrastructure components."""

    # Component configurations
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    external_services: ExternalServiceConfig = field(default_factory=ExternalServiceConfig)

    # Environment settings
    environment: str = "development"
    debug_mode: bool = False
    log_level: str = "INFO"

    # Feature flags
    enable_caching: bool = True
    enable_metrics: bool = True
    enable_tracing: bool = False

    # Performance settings
    max_concurrent_requests: int = 100
    request_timeout: int = 30

    @classmethod
    def from_env(cls) -> 'InfrastructureConfig':
        """Create configuration from environment variables."""
        return cls(
            database=DatabaseConfig.from_env(),
            cache=CacheConfig.from_env(),
            external_services=ExternalServiceConfig.from_env(),
            environment=os.getenv('ENVIRONMENT', 'development'),
            debug_mode=os.getenv('DEBUG', 'false').lower() == 'true',
            log_level=os.getenv('LOG_LEVEL', 'INFO'),
            enable_caching=os.getenv('ENABLE_CACHING', 'true').lower() == 'true',
            enable_metrics=os.getenv('ENABLE_METRICS', 'true').lower() == 'true',
            enable_tracing=os.getenv('ENABLE_TRACING', 'false').lower() == 'true',
            max_concurrent_requests=int(os.getenv('MAX_CONCURRENT_REQUESTS', '100')),
            request_timeout=int(os.getenv('REQUEST_TIMEOUT', '30'))
        )

    @classmethod
    def for_testing(cls) -> 'InfrastructureConfig':
        """Create configuration for testing."""
        return cls(
            database=DatabaseConfig(sqlite_path=":memory:"),
            cache=CacheConfig(redis_host=None),  # Disable caching for tests
            external_services=ExternalServiceConfig(),
            environment="testing",
            debug_mode=True,
            log_level="DEBUG",
            enable_caching=False,
            enable_metrics=False,
            enable_tracing=False
        )

    @classmethod
    def for_development(cls) -> 'InfrastructureConfig':
        """Create configuration for development."""
        return cls(
            database=DatabaseConfig(sqlite_path="analysis_dev.db"),
            cache=CacheConfig(),
            external_services=ExternalServiceConfig(),
            environment="development",
            debug_mode=True,
            log_level="DEBUG"
        )

    @classmethod
    def for_production(cls) -> 'InfrastructureConfig':
        """Create configuration for production."""
        return cls(
            database=DatabaseConfig.from_env(),
            cache=CacheConfig.from_env(),
            external_services=ExternalServiceConfig.from_env(),
            environment="production",
            debug_mode=False,
            log_level="WARNING"
        )

    def validate(self) -> list[str]:
        """Validate entire configuration."""
        errors = []

        # Validate component configurations
        errors.extend(self.database.validate())
        errors.extend(self.cache.validate())
        errors.extend(self.external_services.validate())

        # Validate main settings
        valid_environments = ["development", "testing", "staging", "production"]
        if self.environment not in valid_environments:
            errors.append(f"Invalid environment: {self.environment}")

        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            errors.append(f"Invalid log level: {self.log_level}")

        if self.max_concurrent_requests < 1:
            errors.append("Max concurrent requests must be >= 1")

        if self.request_timeout < 1:
            errors.append("Request timeout must be >= 1")

        return errors

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment == "development"

    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.environment == "testing"

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment == "production"

    def get_feature_flags(self) -> dict:
        """Get feature flags."""
        return {
            'caching': self.enable_caching,
            'metrics': self.enable_metrics,
            'tracing': self.enable_tracing
        }

    def get_performance_settings(self) -> dict:
        """Get performance settings."""
        return {
            'max_concurrent_requests': self.max_concurrent_requests,
            'request_timeout': self.request_timeout
        }
