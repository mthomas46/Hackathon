"""Application Configuration Service - Centralized configuration management."""

import os
import json
import yaml
from typing import Dict, Any, Optional, List, Union
from pathlib import Path
from dataclasses import dataclass, field
from abc import ABC, abstractmethod

from .application_service import ApplicationService, ServiceContext


class ConfigurationSource(ABC):
    """Abstract base class for configuration sources."""

    @abstractmethod
    def load(self) -> Dict[str, Any]:
        """Load configuration from source."""
        pass

    @abstractmethod
    def save(self, config: Dict[str, Any]) -> None:
        """Save configuration to source."""
        pass

    @abstractmethod
    def can_save(self) -> bool:
        """Check if source supports saving."""
        pass


class FileConfigurationSource(ConfigurationSource):
    """File-based configuration source."""

    def __init__(self, file_path: Union[str, Path], format_type: str = "auto"):
        """Initialize file configuration source."""
        self.file_path = Path(file_path)
        self.format_type = format_type

        if self.format_type == "auto":
            if self.file_path.suffix.lower() in ['.yaml', '.yml']:
                self.format_type = "yaml"
            elif self.file_path.suffix.lower() == '.json':
                self.format_type = "json"
            else:
                self.format_type = "json"  # Default

    def load(self) -> Dict[str, Any]:
        """Load configuration from file."""
        if not self.file_path.exists():
            return {}

        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                if self.format_type == "yaml":
                    import yaml
                    return yaml.safe_load(f) or {}
                else:
                    return json.load(f) or {}
        except Exception as e:
            raise ValueError(f"Failed to load configuration from {self.file_path}: {e}")

    def save(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.file_path, 'w', encoding='utf-8') as f:
                if self.format_type == "yaml":
                    import yaml
                    yaml.dump(config, f, default_flow_style=False, indent=2)
                else:
                    json.dump(config, f, indent=2, ensure_ascii=False)

        except Exception as e:
            raise ValueError(f"Failed to save configuration to {self.file_path}: {e}")

    def can_save(self) -> bool:
        """Check if file can be saved."""
        try:
            # Check if directory is writable
            if self.file_path.exists():
                return os.access(self.file_path, os.W_OK)
            else:
                return os.access(self.file_path.parent, os.W_OK)
        except Exception:
            return False


class EnvironmentConfigurationSource(ConfigurationSource):
    """Environment variable configuration source."""

    def __init__(self, prefix: str = ""):
        """Initialize environment configuration source."""
        self.prefix = prefix.upper()

    def load(self) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}

        for key, value in os.environ.items():
            if self.prefix and key.startswith(self.prefix):
                # Remove prefix and convert to nested structure
                clean_key = key[len(self.prefix):].lstrip('_')
                self._set_nested_value(config, clean_key, value)
            elif not self.prefix:
                # No prefix, use all environment variables
                self._set_nested_value(config, key, value)

        return config

    def _set_nested_value(self, config: Dict[str, Any], key: str, value: str) -> None:
        """Set nested value in configuration dictionary."""
        parts = key.lower().split('_')
        current = config

        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]

        # Try to convert value to appropriate type
        final_value = self._convert_value(value)
        current[parts[-1]] = final_value

    def _convert_value(self, value: str) -> Union[str, int, float, bool]:
        """Convert string value to appropriate type."""
        # Try boolean
        if value.lower() in ['true', 'false']:
            return value.lower() == 'true'

        # Try integer
        try:
            return int(value)
        except ValueError:
            pass

        # Try float
        try:
            return float(value)
        except ValueError:
            pass

        # Return as string
        return value

    def save(self, config: Dict[str, Any]) -> None:
        """Save configuration to environment variables."""
        # This is not typically supported for environment variables
        raise NotImplementedError("Cannot save to environment variables")

    def can_save(self) -> bool:
        """Environment variables don't support saving."""
        return False


class InMemoryConfigurationSource(ConfigurationSource):
    """In-memory configuration source for testing and runtime configuration."""

    def __init__(self, initial_config: Optional[Dict[str, Any]] = None):
        """Initialize in-memory configuration source."""
        self.config = initial_config or {}

    def load(self) -> Dict[str, Any]:
        """Load configuration from memory."""
        return self.config.copy()

    def save(self, config: Dict[str, Any]) -> None:
        """Save configuration to memory."""
        self.config = config.copy()

    def can_save(self) -> bool:
        """In-memory source supports saving."""
        return True


@dataclass
class ApplicationConfig:
    """Application configuration with validation and defaults."""

    # Database configuration
    database_url: str = "sqlite:///analysis_service.db"
    database_pool_size: int = 10
    database_max_overflow: int = 20

    # Cache configuration
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300
    cache_max_size: int = 1000

    # Logging configuration
    log_level: str = "INFO"
    log_directory: str = "logs"
    log_max_file_size: int = 10 * 1024 * 1024  # 10MB
    log_backup_count: int = 5

    # Monitoring configuration
    monitoring_enabled: bool = True
    monitoring_collection_interval: int = 30
    metrics_retention_days: int = 7

    # Service configuration
    service_name: str = "analysis-service"
    service_version: str = "1.0.0"
    service_port: int = 5020
    service_host: str = "0.0.0.0"

    # External service configuration
    external_services: Dict[str, Any] = field(default_factory=dict)

    # Feature flags
    features: Dict[str, bool] = field(default_factory=lambda: {
        'advanced_analysis': True,
        'real_time_processing': False,
        'cross_repository_analysis': True,
        'automated_remediation': True,
        'distributed_processing': False
    })

    def __post_init__(self):
        """Validate configuration after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate configuration values."""
        if self.database_pool_size < 1:
            raise ValueError("Database pool size must be at least 1")

        if self.cache_ttl_seconds < 0:
            raise ValueError("Cache TTL cannot be negative")

        if self.service_port < 1 or self.service_port > 65535:
            raise ValueError("Service port must be between 1 and 65535")

        if self.log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            raise ValueError(f"Invalid log level: {self.log_level}")

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            'database_url': self.database_url,
            'database_pool_size': self.database_pool_size,
            'database_max_overflow': self.database_max_overflow,
            'cache_enabled': self.cache_enabled,
            'cache_ttl_seconds': self.cache_ttl_seconds,
            'cache_max_size': self.cache_max_size,
            'log_level': self.log_level,
            'log_directory': self.log_directory,
            'log_max_file_size': self.log_max_file_size,
            'log_backup_count': self.log_backup_count,
            'monitoring_enabled': self.monitoring_enabled,
            'monitoring_collection_interval': self.monitoring_collection_interval,
            'metrics_retention_days': self.metrics_retention_days,
            'service_name': self.service_name,
            'service_version': self.service_version,
            'service_port': self.service_port,
            'service_host': self.service_host,
            'external_services': self.external_services,
            'features': self.features
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApplicationConfig':
        """Create configuration from dictionary."""
        return cls(**data)


class ConfigurationService(ApplicationService):
    """Application configuration service with multiple sources."""

    def __init__(
        self,
        config_file: Optional[str] = None,
        env_prefix: str = "ANALYSIS_SERVICE",
        sources: Optional[List[ConfigurationSource]] = None
    ):
        """Initialize configuration service."""
        super().__init__("configuration_service")

        self.config_file = config_file or "config/analysis_service.yaml"
        self.env_prefix = env_prefix

        # Initialize configuration sources
        if sources is None:
            sources = [
                EnvironmentConfigurationSource(env_prefix),
                FileConfigurationSource(self.config_file),
                InMemoryConfigurationSource()  # For runtime overrides
            ]

        self.sources = sources
        self._config: Optional[ApplicationConfig] = None
        self._last_load_time = 0
        self._cache_ttl = 60  # Cache config for 60 seconds

    async def load_config(self, force_reload: bool = False) -> ApplicationConfig:
        """Load configuration from all sources."""
        current_time = __import__('time').time()

        # Return cached config if still valid
        if (not force_reload and self._config and
            current_time - self._last_load_time < self._cache_ttl):
            return self._config

        async with self.operation_context("load_config"):
            # Load from all sources (environment takes precedence)
            config_data = {}

            for source in reversed(self.sources):  # Reverse order for precedence
                try:
                    source_config = source.load()
                    config_data.update(source_config)
                except Exception as e:
                    self.logger.warning(f"Failed to load from {source.__class__.__name__}: {e}")

            # Create configuration object
            self._config = ApplicationConfig.from_dict(config_data)
            self._last_load_time = current_time

            self.logger.info("Configuration loaded successfully")
            return self._config

    async def save_config(self, config: ApplicationConfig) -> None:
        """Save configuration to writable sources."""
        async with self.operation_context("save_config"):
            config_data = config.to_dict()

            saved_to_any = False
            for source in self.sources:
                if source.can_save():
                    try:
                        source.save(config_data)
                        saved_to_any = True
                        self.logger.info(f"Configuration saved to {source.__class__.__name__}")
                    except Exception as e:
                        self.logger.error(f"Failed to save to {source.__class__.__name__}: {e}")

            if not saved_to_any:
                raise ValueError("No writable configuration sources available")

            # Update cached config
            self._config = config
            self._last_load_time = __import__('time').time()

    async def update_config(self, updates: Dict[str, Any]) -> ApplicationConfig:
        """Update configuration with new values."""
        async with self.operation_context("update_config"):
            config = await self.load_config()

            # Update configuration object
            for key, value in updates.items():
                if hasattr(config, key):
                    setattr(config, key, value)
                else:
                    self.logger.warning(f"Unknown configuration key: {key}")

            # Validate updated configuration
            config._validate()

            # Save updated configuration
            await self.save_config(config)

            self.logger.info(f"Configuration updated: {list(updates.keys())}")
            return config

    async def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        config = await self.load_config()

        # Support nested keys with dot notation
        keys = key.split('.')
        value = config.to_dict()

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    async def set_config_value(self, key: str, value: Any) -> None:
        """Set configuration value by key."""
        updates = {key: value}
        await self.update_config(updates)

    async def reload_config(self) -> ApplicationConfig:
        """Force reload configuration from sources."""
        return await self.load_config(force_reload=True)

    async def get_config_summary(self) -> Dict[str, Any]:
        """Get configuration summary for monitoring."""
        config = await self.load_config()

        return {
            'service_name': config.service_name,
            'service_version': config.service_version,
            'database_configured': bool(config.database_url),
            'cache_enabled': config.cache_enabled,
            'monitoring_enabled': config.monitoring_enabled,
            'features_enabled': [k for k, v in config.features.items() if v],
            'external_services_count': len(config.external_services),
            'last_loaded': self._last_load_time
        }

    async def validate_config(self, config: ApplicationConfig) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []

        # Check database URL format
        if not config.database_url.startswith(('sqlite://', 'postgresql://', 'mysql://')):
            issues.append("Invalid database URL format")

        # Check service port range
        if not (1 <= config.service_port <= 65535):
            issues.append(f"Service port {config.service_port} is out of valid range (1-65535)")

        # Check log level validity
        if config.log_level not in ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']:
            issues.append(f"Invalid log level: {config.log_level}")

        # Check cache configuration
        if config.cache_max_size < 10:
            issues.append("Cache max size should be at least 10")

        if config.cache_ttl_seconds < 0:
            issues.append("Cache TTL cannot be negative")

        return issues

    async def health_check(self) -> Dict[str, Any]:
        """Perform health check."""
        health = await super().health_check()

        # Add configuration-specific health info
        try:
            config_summary = await self.get_config_summary()
            validation_issues = await self.validate_config(await self.load_config())

            health['configuration'] = {
                'sources_count': len(self.sources),
                'writable_sources': sum(1 for s in self.sources if s.can_save()),
                'validation_issues': len(validation_issues),
                'cache_ttl_seconds': self._cache_ttl,
                'last_load_time': self._last_load_time
            }

            if validation_issues:
                health['configuration']['issues'] = validation_issues[:5]  # First 5 issues

        except Exception as e:
            health['configuration'] = {'error': str(e)}

        return health


# Global configuration service instance
configuration_service = ConfigurationService()

# Create application config instance
app_config = ApplicationConfig()
