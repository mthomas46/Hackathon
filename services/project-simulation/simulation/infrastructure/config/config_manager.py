"""Configuration Manager - Centralized Configuration Management.

Provides centralized configuration management with environment-specific
overrides, validation, and dynamic loading capabilities for the Project
Simulation Service.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union
from dataclasses import dataclass, field
from dotenv import load_dotenv

from services.project_simulation.simulation.infrastructure.logging import get_simulation_logger


@dataclass
class ServiceConfig:
    """Service configuration settings."""
    name: str = "project-simulation"
    version: str = "1.0.0"
    environment: str = "development"
    host: str = "0.0.0.0"
    port: int = 5075
    debug: bool = False
    reload: bool = False
    log_level: str = "INFO"


@dataclass
class DatabaseConfig:
    """Database configuration settings."""
    url: str = "sqlite:///./data/project_simulation.db"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600


@dataclass
class RedisConfig:
    """Redis configuration settings."""
    url: str = "redis://localhost:6379/0"
    db: int = 0
    max_connections: int = 20
    socket_timeout: int = 5
    socket_connect_timeout: int = 5


@dataclass
class EcosystemConfig:
    """Ecosystem service configuration."""
    mock_data_generator_url: str = "http://localhost:5001"
    analysis_service_url: str = "http://localhost:5002"
    interpreter_url: str = "http://localhost:5003"
    doc_store_url: str = "http://localhost:5004"
    llm_gateway_url: str = "http://localhost:5005"
    notification_service_url: str = "http://localhost:5006"
    log_collector_url: str = "http://localhost:5007"
    discovery_agent_url: str = "http://localhost:5008"
    orchestrator_url: str = "http://localhost:5099"
    frontend_url: str = "http://localhost:3000"


@dataclass
class ExternalServicesConfig:
    """External services configuration."""
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama2"


@dataclass
class DevelopmentConfig:
    """Development-specific configuration."""
    enable_swagger: bool = True
    enable_redoc: bool = True
    enable_cors: bool = True
    cors_origins: List[str] = field(default_factory=lambda: ["*"])
    auto_reload: bool = False
    debug_mode: bool = False


@dataclass
class SecurityConfig:
    """Security configuration."""
    rate_limit_enabled: bool = True
    jwt_secret: Optional[str] = None
    api_key: Optional[str] = None
    enable_circuit_breaker: bool = True
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_recovery_timeout: int = 60


@dataclass
class LoggingConfig:
    """Logging configuration."""
    format: str = "json"
    level: str = "INFO"
    enable_console: bool = True
    enable_file: bool = True
    log_file: Optional[str] = None
    enable_correlation_id: bool = True


@dataclass
class MonitoringConfig:
    """Monitoring configuration."""
    enable_metrics: bool = True
    metrics_port: int = 8001
    enable_health_checks: bool = True
    enable_profiling: bool = False
    profiling_output_dir: str = "./profiling/"


@dataclass
class FeatureFlags:
    """Feature flags for experimental features."""
    enable_advanced_analytics: bool = False
    enable_real_time_updates: bool = False
    enable_extended_logging: bool = False
    enable_detailed_metrics: bool = False


@dataclass
class TestingConfig:
    """Testing configuration."""
    database_url: str = "sqlite:///./data/project_simulation_test.db"
    use_mock_services: bool = False
    mock_data_enabled: bool = True


@dataclass
class DockerConfig:
    """Docker configuration."""
    image_tag: str = "latest"
    build_context: str = "."
    compose_file: str = "docker-compose.yml"


@dataclass
class Config:
    """Main configuration class containing all settings."""
    service: ServiceConfig = field(default_factory=ServiceConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    ecosystem: EcosystemConfig = field(default_factory=EcosystemConfig)
    external: ExternalServicesConfig = field(default_factory=ExternalServicesConfig)
    development: DevelopmentConfig = field(default_factory=DevelopmentConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    features: FeatureFlags = field(default_factory=FeatureFlags)
    testing: TestingConfig = field(default_factory=TestingConfig)
    docker: DockerConfig = field(default_factory=DockerConfig)


class ConfigManager:
    """Centralized configuration manager with environment-specific loading."""

    def __init__(self, config_dir: Optional[str] = None):
        """Initialize configuration manager."""
        self.logger = get_simulation_logger()
        self.config_dir = Path(config_dir) if config_dir else Path(__file__).parent.parent.parent / "config"
        self.config = Config()
        self._loaded = False

    def load_config(self, environment: Optional[str] = None) -> Config:
        """Load configuration for the specified environment."""
        if self._loaded:
            return self.config

        # Determine environment
        environment = environment or os.getenv("ENVIRONMENT", "development")

        # Load base configuration
        self._load_base_config()

        # Load environment-specific configuration
        self._load_environment_config(environment)

        # Load from environment variables (highest priority)
        self._load_from_environment()

        # Validate configuration
        self._validate_config()

        self._loaded = True
        self.logger.info("Configuration loaded successfully", environment=environment)

        return self.config

    def _load_base_config(self):
        """Load base configuration file."""
        base_config_file = self.config_dir / "base.yaml"
        if base_config_file.exists():
            self._load_yaml_config(base_config_file)
        else:
            self.logger.warning("Base configuration file not found", file=str(base_config_file))

    def _load_environment_config(self, environment: str):
        """Load environment-specific configuration."""
        env_config_file = self.config_dir / f"{environment}.yaml"
        env_env_file = self.config_dir / f"{environment}.env"

        # Try YAML first
        if env_config_file.exists():
            self._load_yaml_config(env_config_file)
        elif env_env_file.exists():
            self._load_env_config(env_env_file)
        else:
            self.logger.warning(f"No configuration file found for environment: {environment}")

    def _load_yaml_config(self, config_file: Path):
        """Load configuration from YAML file."""
        try:
            import yaml
            with open(config_file, 'r') as f:
                config_data = yaml.safe_load(f)
            self._apply_config_data(config_data)
        except ImportError:
            self.logger.warning("PyYAML not installed, skipping YAML config loading")
        except Exception as e:
            self.logger.error("Failed to load YAML config", error=str(e), file=str(config_file))

    def _load_env_config(self, env_file: Path):
        """Load configuration from environment file."""
        try:
            load_dotenv(env_file)
            self.logger.info("Environment configuration loaded", file=str(env_file))
        except Exception as e:
            self.logger.error("Failed to load environment config", error=str(e), file=str(env_file))

    def _load_from_environment(self):
        """Load configuration from environment variables."""
        # Service configuration
        self.config.service.name = os.getenv("SERVICE_NAME", self.config.service.name)
        self.config.service.version = os.getenv("SERVICE_VERSION", self.config.service.version)
        self.config.service.environment = os.getenv("ENVIRONMENT", self.config.service.environment)
        self.config.service.host = os.getenv("HOST", self.config.service.host)
        self.config.service.port = int(os.getenv("PORT", self.config.service.port))
        self.config.service.debug = os.getenv("DEBUG", "").lower() == "true"
        self.config.service.reload = os.getenv("RELOAD", "").lower() == "true"
        self.config.service.log_level = os.getenv("LOG_LEVEL", self.config.service.log_level)

        # Database configuration
        self.config.database.url = os.getenv("DATABASE_URL", self.config.database.url)

        # Redis configuration
        self.config.redis.url = os.getenv("REDIS_URL", self.config.redis.url)

        # Ecosystem service URLs
        self.config.ecosystem.mock_data_generator_url = os.getenv("MOCK_DATA_GENERATOR_URL", self.config.ecosystem.mock_data_generator_url)
        self.config.ecosystem.analysis_service_url = os.getenv("ANALYSIS_SERVICE_URL", self.config.ecosystem.analysis_service_url)
        self.config.ecosystem.interpreter_url = os.getenv("INTERPRETER_URL", self.config.ecosystem.interpreter_url)
        self.config.ecosystem.doc_store_url = os.getenv("DOC_STORE_URL", self.config.ecosystem.doc_store_url)
        self.config.ecosystem.llm_gateway_url = os.getenv("LLM_GATEWAY_URL", self.config.ecosystem.llm_gateway_url)
        self.config.ecosystem.notification_service_url = os.getenv("NOTIFICATION_SERVICE_URL", self.config.ecosystem.notification_service_url)
        self.config.ecosystem.log_collector_url = os.getenv("LOG_COLLECTOR_URL", self.config.ecosystem.log_collector_url)
        self.config.ecosystem.discovery_agent_url = os.getenv("DISCOVERY_AGENT_URL", self.config.ecosystem.discovery_agent_url)
        self.config.ecosystem.orchestrator_url = os.getenv("ORCHESTRATOR_URL", self.config.ecosystem.orchestrator_url)
        self.config.ecosystem.frontend_url = os.getenv("FRONTEND_URL", self.config.ecosystem.frontend_url)

        # External services
        self.config.external.ollama_base_url = os.getenv("OLLAMA_BASE_URL", self.config.external.ollama_base_url)
        self.config.external.ollama_model = os.getenv("OLLAMA_MODEL", self.config.external.ollama_model)

        # Development features
        self.config.development.enable_swagger = os.getenv("ENABLE_SWAGGER", "true").lower() == "true"
        self.config.development.enable_redoc = os.getenv("ENABLE_REDOC", "true").lower() == "true"
        self.config.development.enable_cors = os.getenv("ENABLE_CORS", "true").lower() == "true"
        cors_origins = os.getenv("CORS_ORIGINS", "")
        if cors_origins:
            self.config.development.cors_origins = [origin.strip() for origin in cors_origins.split(",")]
        self.config.development.auto_reload = os.getenv("AUTO_RELOAD", "").lower() == "true"
        self.config.development.debug_mode = os.getenv("DEBUG_MODE", "").lower() == "true"

        # Security
        self.config.security.rate_limit_enabled = os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true"
        self.config.security.jwt_secret = os.getenv("JWT_SECRET")
        self.config.security.api_key = os.getenv("API_KEY")

        # Logging
        self.config.logging.format = os.getenv("LOG_FORMAT", self.config.logging.format)
        self.config.logging.level = os.getenv("LOG_LEVEL", self.config.logging.level)
        self.config.logging.enable_console = os.getenv("ENABLE_CONSOLE_LOGGING", "true").lower() == "true"
        self.config.logging.enable_file = os.getenv("ENABLE_FILE_LOGGING", "true").lower() == "true"
        self.config.logging.log_file = os.getenv("LOG_FILE")
        self.config.logging.enable_correlation_id = os.getenv("ENABLE_CORRELATION_ID", "true").lower() == "true"

        # Monitoring
        self.config.monitoring.enable_metrics = os.getenv("ENABLE_METRICS", "true").lower() == "true"
        self.config.monitoring.metrics_port = int(os.getenv("METRICS_PORT", self.config.monitoring.metrics_port))
        self.config.monitoring.enable_health_checks = os.getenv("ENABLE_HEALTH_CHECKS", "true").lower() == "true"
        self.config.monitoring.enable_profiling = os.getenv("ENABLE_PROFILING", "false").lower() == "true"
        self.config.monitoring.profiling_output_dir = os.getenv("PROFILING_OUTPUT_DIR", self.config.monitoring.profiling_output_dir)

        # Feature flags
        self.config.features.enable_advanced_analytics = os.getenv("ENABLE_ADVANCED_ANALYTICS", "false").lower() == "true"
        self.config.features.enable_real_time_updates = os.getenv("ENABLE_REAL_TIME_UPDATES", "false").lower() == "true"
        self.config.features.enable_extended_logging = os.getenv("ENABLE_EXTENDED_LOGGING", "false").lower() == "true"
        self.config.features.enable_detailed_metrics = os.getenv("ENABLE_DETAILED_METRICS", "false").lower() == "true"

        # Testing
        self.config.testing.database_url = os.getenv("TEST_DATABASE_URL", self.config.testing.database_url)
        self.config.testing.use_mock_services = os.getenv("USE_MOCK_SERVICES", "false").lower() == "true"
        self.config.testing.mock_data_enabled = os.getenv("MOCK_DATA_ENABLED", "true").lower() == "true"

        # Docker
        self.config.docker.image_tag = os.getenv("DOCKER_IMAGE_TAG", self.config.docker.image_tag)
        self.config.docker.compose_file = os.getenv("DOCKER_COMPOSE_FILE", self.config.docker.compose_file)

    def _apply_config_data(self, config_data: Dict[str, Any]):
        """Apply configuration data to the config object."""
        # This would map the flat config data to the nested dataclass structure
        # Implementation would depend on the structure of the config files
        pass

    def _validate_config(self):
        """Validate the loaded configuration."""
        # Basic validation
        if not self.config.service.name:
            raise ValueError("Service name is required")

        if not self.config.database.url:
            raise ValueError("Database URL is required")

        # Validate URLs
        self._validate_urls()

        # Validate security settings
        if self.config.security.rate_limit_enabled and not self.config.security.api_key:
            self.logger.warning("Rate limiting enabled but no API key configured")

    def _validate_urls(self):
        """Validate service URLs."""
        from urllib.parse import urlparse

        urls_to_validate = [
            self.config.database.url,
            self.config.redis.url,
            self.config.ecosystem.mock_data_generator_url,
            self.config.ecosystem.analysis_service_url,
            self.config.ecosystem.interpreter_url,
            self.config.ecosystem.doc_store_url,
            self.config.ecosystem.llm_gateway_url,
            self.config.external.ollama_base_url
        ]

        for url in urls_to_validate:
            try:
                parsed = urlparse(url)
                if not parsed.scheme or not parsed.netloc:
                    self.logger.warning(f"Invalid URL format: {url}")
            except Exception as e:
                self.logger.error(f"URL validation error for {url}: {str(e)}")

    def get_service_urls(self) -> Dict[str, str]:
        """Get all service URLs as a dictionary."""
        return {
            "mock_data_generator": self.config.ecosystem.mock_data_generator_url,
            "analysis_service": self.config.ecosystem.analysis_service_url,
            "interpreter": self.config.ecosystem.interpreter_url,
            "doc_store": self.config.ecosystem.doc_store_url,
            "llm_gateway": self.config.ecosystem.llm_gateway_url,
            "notification_service": self.config.ecosystem.notification_service_url,
            "log_collector": self.config.ecosystem.log_collector_url,
            "discovery_agent": self.config.ecosystem.discovery_agent_url,
            "orchestrator": self.config.ecosystem.orchestrator_url,
            "frontend": self.config.ecosystem.frontend_url
        }

    def is_development_mode(self) -> bool:
        """Check if running in development mode."""
        return self.config.service.environment == "development"

    def is_production_mode(self) -> bool:
        """Check if running in production mode."""
        return self.config.service.environment == "production"

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        # This would recursively convert the dataclass to a dictionary
        # Implementation depends on the dataclass structure
        return {}

    def save_to_file(self, file_path: str):
        """Save current configuration to a file."""
        config_dict = self.to_dict()
        with open(file_path, 'w') as f:
            json.dump(config_dict, f, indent=2)

    def reload_config(self):
        """Reload configuration from sources."""
        self._loaded = False
        return self.load_config(self.config.service.environment)


# Global configuration instance
_config_manager: Optional[ConfigManager] = None
_config: Optional[Config] = None


def get_config_manager() -> ConfigManager:
    """Get the global configuration manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def get_config() -> Config:
    """Get the current configuration."""
    global _config
    if _config is None:
        manager = get_config_manager()
        _config = manager.load_config()
    return _config


def reload_config() -> Config:
    """Reload the configuration."""
    global _config
    manager = get_config_manager()
    _config = manager.reload_config()
    return _config


# Convenience functions for common config access
def get_service_name() -> str:
    """Get the service name."""
    return get_config().service.name


def get_environment() -> str:
    """Get the current environment."""
    return get_config().service.environment


def get_database_url() -> str:
    """Get the database URL."""
    return get_config().database.url


def get_service_urls() -> Dict[str, str]:
    """Get all service URLs."""
    return get_config_manager().get_service_urls()


def is_development() -> bool:
    """Check if running in development mode."""
    return get_config().service.environment == "development"


def is_production() -> bool:
    """Check if running in production mode."""
    return get_config().service.environment == "production"


__all__ = [
    'ConfigManager',
    'get_config_manager',
    'get_config',
    'reload_config',
    'get_service_name',
    'get_environment',
    'get_database_url',
    'get_service_urls',
    'is_development',
    'is_production'
]
