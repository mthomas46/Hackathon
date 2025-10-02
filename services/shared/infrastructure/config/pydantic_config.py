"""
Pydantic-Based Configuration Management System

Enhanced configuration management using Pydantic's powerful validation,
settings management, and type safety features.

This module provides:
- Pydantic Settings integration for automatic configuration loading
- Advanced field validation with detailed error messages
- Type-safe configuration with IDE support
- Environment variable validation and transformation
- JSON schema generation for documentation
- Settings sources with proper precedence (env vars, files, defaults)
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, ClassVar
from enum import Enum
from functools import lru_cache

# Import validators at module level for class definitions
try:
    from pydantic import field_validator, model_validator
except ImportError:
    field_validator = None
    model_validator = None

try:
    from pydantic import (
        BaseModel, Field, ValidationError,
        PrivateAttr, ConfigDict
    )
    from pydantic_settings import BaseSettings, SettingsConfigDict
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    # Fallback for systems without pydantic
    class BaseModel:
        pass
    class BaseSettings:
        pass
    Field = lambda *args, **kwargs: None
    ValidationError = Exception
    PrivateAttr = lambda *args, **kwargs: None
    SettingsConfigDict = lambda *args, **kwargs: None


class Environment(str, Enum):
    """Supported deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


class LogLevel(str, Enum):
    """Standardized log levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ServerConfig(BaseModel):
    """Enhanced server configuration with Pydantic validation."""

    model_config = {"validate_assignment": True, "extra": "forbid"}

    host: str = Field(default="0.0.0.0", description="Server bind host")
    port: int = Field(default=8080, ge=1000, le=65535, description="Server port")
    debug: bool = Field(default=False, description="Enable debug mode")
    workers: int = Field(default=1, ge=1, le=32, description="Number of worker processes")
    timeout: int = Field(default=30, ge=1, le=300, description="Request timeout in seconds")
    cors_origins: List[str] = Field(default_factory=lambda: ["*"], description="CORS allowed origins")

    @field_validator('host')
    @classmethod
    def validate_host(cls, v):
        """Validate host format."""
        if not v or not isinstance(v, str):
            raise ValueError('Host must be a non-empty string')
        return v

    @field_validator('cors_origins')
    @classmethod
    def validate_cors_origins(cls, v):
        """Validate CORS origins."""
        for origin in v:
            if origin == "*":
                continue
            if not (origin.startswith("http://") or origin.startswith("https://")):
                raise ValueError(f'CORS origin must start with http:// or https://, got: {origin}')
        return v


class RedisConfig(BaseModel):
    """Enhanced Redis configuration with validation."""

    model_config = {"validate_assignment": True, "extra": "forbid"}

    host: str = Field(default="redis", description="Redis server host")
    port: int = Field(default=6379, ge=1, le=65535, description="Redis server port")
    db: int = Field(default=0, ge=0, le=15, description="Redis database number")
    password: Optional[str] = Field(default=None, description="Redis password")
    ssl: bool = Field(default=False, description="Enable SSL connection")
    max_connections: int = Field(default=10, ge=1, le=1000, description="Maximum connections")
    socket_timeout: Optional[int] = Field(default=None, ge=1, description="Socket timeout")
    socket_connect_timeout: Optional[int] = Field(default=None, ge=1, description="Connection timeout")

    @model_validator(mode='after')
    def validate_connection_params(self):
        """Validate Redis connection parameters."""
        if not self.host or not isinstance(self.host, str):
            raise ValueError('Redis host must be a non-empty string')

        # Could add more sophisticated validation here
        # e.g., check if host is reachable, validate password strength, etc.

        return self


class LoggingConfig(BaseModel):
    """Enhanced logging configuration."""

    model_config = {"validate_assignment": True, "extra": "forbid"}

    level: LogLevel = Field(default=LogLevel.INFO, description="Log level")
    format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    file_path: Optional[str] = Field(default=None, description="Log file path")
    max_size: int = Field(default=10485760, ge=1024, description="Max log file size in bytes")
    backup_count: int = Field(default=5, ge=0, le=100, description="Number of backup files")
    structured: bool = Field(default=True, description="Enable structured logging")
    console: bool = Field(default=True, description="Enable console logging")

    @field_validator('file_path')
    @classmethod
    def validate_file_path(cls, v):
        """Validate log file path."""
        if v is not None:
            path = Path(v)
            if path.is_absolute() and not path.parent.exists():
                # For absolute paths, parent directory should exist
                raise ValueError(f'Log file directory does not exist: {path.parent}')
        return v


class ServiceURL(BaseModel):
    """Service URL configuration with validation."""

    model_config = {"validate_assignment": True}

    base_url: str = Field(..., description="Base URL for the service")
    health_endpoint: str = Field(default="/health", description="Health check endpoint")
    timeout: int = Field(default=30, ge=1, le=300, description="Request timeout")

    @field_validator('base_url')
    @classmethod
    def validate_base_url(cls, v):
        """Validate base URL format."""
        if not v or not isinstance(v, str):
            raise ValueError('Base URL must be a non-empty string')

        if not (v.startswith("http://") or v.startswith("https://")):
            raise ValueError(f'Base URL must start with http:// or https://, got: {v}')

        # Remove trailing slash for consistency
        return v.rstrip('/')


class ServiceDependencies(BaseModel):
    """Service dependency URLs configuration."""

    model_config = {"validate_assignment": True, "extra": "allow"}

    orchestrator_url: str = Field(default="http://orchestrator:5099", description="Orchestrator service URL")
    doc_store_url: str = Field(default="http://doc_store:5087", description="Document store service URL")
    analysis_service_url: str = Field(default="http://analysis-service:5020", description="Analysis service URL")
    source_agent_url: str = Field(default="http://source-agent:5085", description="Source agent service URL")
    frontend_url: str = Field(default="http://frontend:3000", description="Frontend service URL")
    memory_agent_url: str = Field(default="http://memory-agent:5090", description="Memory agent service URL")
    discovery_agent_url: str = Field(default="http://discovery-agent:5045", description="Discovery agent service URL")
    prompt_store_url: str = Field(default="http://prompt_store:5110", description="Prompt store service URL")
    interpreter_url: str = Field(default="http://interpreter:5120", description="Interpreter service URL")
    cli_service_url: str = Field(default="http://cli:5130", description="CLI service URL")
    user_store_url: str = Field(default="http://user-store:5150", description="User store service URL")
    external_service_store_url: str = Field(default="http://external-service-store:5140", description="External service store URL")
    notification_service_url: str = Field(default="http://notification-service:5130", description="Notification service URL")
    llm_gateway_url: str = Field(default="http://llm-gateway:5055", description="LLM gateway service URL")
    summarizer_hub_url: str = Field(default="http://summarizer-hub:5160", description="Summarizer hub service URL")
    github_mcp_url: str = Field(default="http://github-mcp:5030", description="GitHub MCP service URL")
    bedrock_proxy_url: str = Field(default="http://bedrock-proxy:5002", description="Bedrock proxy service URL")
    secure_analyzer_url: str = Field(default="http://secure-analyzer:5070", description="Secure analyzer service URL")
    code_analyzer_url: str = Field(default="http://code-analyzer:5025", description="Code analyzer service URL")
    architecture_digitizer_url: str = Field(default="http://architecture-digitizer:5105", description="Architecture digitizer service URL")
    project_simulation_url: str = Field(default="http://project-simulation:5075", description="Project simulation service URL")
    mock_data_generator_url: str = Field(default="http://mock-data-generator:5065", description="Mock data generator service URL")
    simulation_dashboard_url: str = Field(default="http://simulation-dashboard:8501", description="Simulation dashboard service URL")
    unified_api_dashboard_url: str = Field(default="http://unified-api-dashboard:8000", description="Unified API dashboard service URL")

    # Infrastructure and external services
    redis_url: str = Field(default="redis:6379", description="Redis service connection URL")
    ollama_url: str = Field(default="http://ollama:11434", description="Ollama AI model service URL")
    log_collector_url: str = Field(default="http://log-collector:5080", description="Log collector service URL")
    project_planning_service_url: str = Field(default="http://project-planning-service:5170", description="Project planning service URL")

    # Orchestrator-specific service URLs
    github_agent_url: Optional[str] = Field(default=None, description="GitHub agent service URL")
    jira_agent_url: Optional[str] = Field(default=None, description="JIRA agent service URL")
    confluence_agent_url: Optional[str] = Field(default=None, description="Confluence agent service URL")
    swagger_agent_url: Optional[str] = Field(default=None, description="Swagger agent service URL")
    consistency_engine_url: Optional[str] = Field(default=None, description="Consistency engine service URL")
    reporting_url: Optional[str] = Field(default=None, description="Reporting service URL")


class LimitsConfig(BaseModel):
    """Operational limits configuration."""

    model_config = {"validate_assignment": True, "extra": "allow"}  # Allow service-specific limit fields

    max_items: int = Field(default=1000, ge=1, le=100000, description="Maximum items to process")
    timeout: int = Field(default=30, ge=1, le=3600, description="Operation timeout in seconds")
    max_connections: int = Field(default=10, ge=1, le=1000, description="Maximum concurrent connections")
    max_message_length: int = Field(default=10000, ge=1, le=1000000, description="Maximum message length")
    max_file_size: int = Field(default=104857600, ge=1024, description="Maximum file size in bytes")  # 100MB default
    rate_limit_requests_per_minute: int = Field(default=60, ge=1, le=10000, description="Rate limit requests per minute")
    max_batch_size: int = Field(default=100, ge=1, le=10000, description="Maximum batch size")


class HealthConfig(BaseModel):
    """Health check configuration."""

    model_config = {"validate_assignment": True, "extra": "forbid"}

    check_interval: int = Field(default=30, ge=5, le=300, description="Health check interval in seconds")
    timeout: int = Field(default=10, ge=1, le=60, description="Health check timeout in seconds")
    retries: int = Field(default=3, ge=1, le=10, description="Number of retries")
    enabled: bool = Field(default=True, description="Enable health checks")
    failure_threshold: int = Field(default=3, ge=1, le=10, description="Failure threshold for unhealthy status")


class SecurityConfig(BaseModel):
    """Security configuration."""

    model_config = {"validate_assignment": True, "extra": "forbid"}

    jwt_secret: str = Field(default="change-me-in-production", min_length=10, description="JWT secret key")
    jwt_algorithm: str = Field(default="HS256", description="JWT algorithm")
    token_expiry_hours: int = Field(default=24, ge=1, le=8760, description="Token expiry in hours")  # Max 1 year
    cors_origins: List[str] = Field(default_factory=lambda: ["*"], description="CORS allowed origins")
    enable_auth: bool = Field(default=False, description="Enable authentication")
    enable_ssl: bool = Field(default=False, description="Enable SSL/TLS")
    ssl_cert_path: Optional[str] = Field(default=None, description="SSL certificate path")
    ssl_key_path: Optional[str] = Field(default=None, description="SSL private key path")
    rate_limiting_enabled: bool = Field(default=False, description="Enable rate limiting")
    api_key_required: bool = Field(default=False, description="Require API key authentication")

    @field_validator('jwt_secret')
    @classmethod
    def validate_jwt_secret(cls, v):
        """Validate JWT secret strength."""
        if v == "change-me-in-production":
            raise ValueError('JWT secret must be changed from default value in production')
        if len(v) < 32:
            raise ValueError('JWT secret should be at least 32 characters long for security')
        return v

    @field_validator('ssl_cert_path', 'ssl_key_path')
    @classmethod
    def validate_ssl_paths(cls, v):
        """Validate SSL file paths."""
        if v is not None:
            path = Path(v)
            if not path.exists():
                raise ValueError(f'SSL file does not exist: {v}')
        return v


class ServiceConfig(BaseSettings):
    """
    Unified service configuration using Pydantic Settings.

    This is the main configuration class that all services should use.
    It provides automatic loading from multiple sources with proper precedence.
    """

    # Service metadata
    service_name: str = Field(default="", description="Service name identifier")
    service_version: str = Field(default="1.0.0", description="Service version")
    environment: Environment = Field(default=Environment.DEVELOPMENT, description="Deployment environment")

    # Core configurations
    server: ServerConfig = Field(default_factory=ServerConfig, description="Server configuration")
    redis: RedisConfig = Field(default_factory=RedisConfig, description="Redis configuration")
    logging: LoggingConfig = Field(default_factory=LoggingConfig, description="Logging configuration")
    services: ServiceDependencies = Field(default_factory=ServiceDependencies, description="Service dependencies")

    # Operational configurations
    limits: LimitsConfig = Field(default_factory=LimitsConfig, description="Operational limits")
    health: HealthConfig = Field(default_factory=HealthConfig, description="Health check configuration")
    security: SecurityConfig = Field(default_factory=SecurityConfig, description="Security configuration")

    # Service-specific configuration
    custom: Dict[str, Any] = Field(default_factory=dict, description="Service-specific configuration")

    # Private attributes for internal use
    _config_file_path: Optional[Path] = PrivateAttr(default=None)
    _last_loaded: Optional[float] = PrivateAttr(default=None)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",  # Allow service-specific configuration fields
        # Settings sources with precedence (highest to lowest)
        customise_sources=lambda cls, init_settings, env_settings, file_secret_settings: (
            init_settings,           # 1. Explicit parameters
            env_settings,            # 2. Environment variables
            yaml_config_settings_source,  # 3. YAML config files
            file_secret_settings,     # 4. Secret files
        )
    )

    def __init__(self, service_name: str = "", config_dir: Optional[Path] = None, **kwargs):
        """Initialize service configuration."""
        # Set service name and config directory
        if service_name:
            kwargs['service_name'] = service_name

        if config_dir:
            # Store config directory for YAML loading
            self._config_file_path = config_dir / "config.yaml"

        super().__init__(**kwargs)

    @property
    def config_dir(self) -> Optional[Path]:
        """Get configuration directory."""
        return self._config_file_path.parent if self._config_file_path else None

    def reload(self) -> bool:
        """Reload configuration from sources."""
        try:
            # Force reload by clearing any caches and re-initializing
            if self._config_file_path and self._config_file_path.exists():
                # Re-read YAML config
                import yaml
                with open(self._config_file_path, 'r') as f:
                    yaml_config = yaml.safe_load(f) or {}

                # Update configuration
                for key, value in yaml_config.items():
                    if hasattr(self, key):
                        setattr(self, key, value)

            self._last_loaded = Path(self._config_file_path or Path.cwd()).stat().st_mtime
            return True
        except Exception:
            return False

    def is_stale(self) -> bool:
        """Check if configuration file has been modified since last load."""
        if not self._config_file_path:
            return False

        try:
            current_mtime = self._config_file_path.stat().st_mtime
            return self._last_loaded is None or current_mtime > self._last_loaded
        except (OSError, AttributeError):
            return False

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary."""
        return self.dict()

    def to_json(self, indent: int = 2) -> str:
        """Export configuration as JSON string."""
        return self.json(indent=indent)

    def generate_schema(self) -> Dict[str, Any]:
        """Generate JSON schema for configuration validation."""
        return self.schema()

    @classmethod
    def from_yaml(cls, yaml_path: Union[str, Path], **kwargs) -> "ServiceConfig":
        """Create configuration from YAML file."""
        yaml_path = Path(yaml_path)
        if not yaml_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {yaml_path}")

        import yaml
        with open(yaml_path, 'r') as f:
            config_data = yaml.safe_load(f) or {}

        # Merge with kwargs
        config_data.update(kwargs)

        return cls(**config_data)

    def validate_configuration(self) -> List[str]:
        """Validate configuration and return list of issues."""
        issues = []

        # Environment-specific validations
        if self.environment == Environment.PRODUCTION:
            if self.server.debug:
                issues.append("Debug mode should be disabled in production")

            if self.security.jwt_secret == "change-me-in-production":
                issues.append("JWT secret must be changed from default in production")

            if not self.security.enable_ssl:
                issues.append("SSL should be enabled in production")

        # Cross-field validations
        if self.redis.max_connections > self.limits.max_connections:
            issues.append("Redis max_connections should not exceed general max_connections limit")

        # Service dependency validations
        for service_name, url in self.services.dict().items():
            if url and not (url.startswith("http://") or url.startswith("https://")):
                issues.append(f"Invalid URL format for {service_name}: {url}")

        return issues


def yaml_config_settings_source(settings_cls):
    """
    Custom settings source for YAML configuration files.

    Loads configuration from YAML files with environment variable substitution.
    Supports service-specific and environment-specific config files.
    """
    def load_yaml_config():
        # Get service name from environment or settings
        service_name = os.environ.get('SERVICE_NAME', '')
        if not service_name:
            # Try to infer from current directory
            cwd = Path.cwd()
            if cwd.name.startswith('services/'):
                service_name = cwd.name
            elif 'services' in str(cwd) and cwd.parent.name == 'services':
                service_name = cwd.name

        if not service_name:
            return {}

        # Determine config directory
        config_dir = Path.cwd()
        if 'services' in str(config_dir) and config_dir.parent.name == 'services':
            config_dir = config_dir.parent.parent
        elif (config_dir / 'services').exists():
            pass  # already in project root
        else:
            # Look for services directory in parent directories
            for parent in config_dir.parents:
                if (parent / 'services').exists():
                    config_dir = parent
                    break

        if not (config_dir / 'services').exists():
            return {}

        service_config_dir = config_dir / 'services' / service_name
        if not service_config_dir.exists():
            return {}

        # Load base config
        base_config = {}
        config_file = service_config_dir / 'config.yaml'
        if config_file.exists():
            import yaml
            with open(config_file, 'r') as f:
                base_config = yaml.safe_load(f) or {}

        # Load environment-specific config
        env = os.environ.get('ENVIRONMENT', 'development')
        env_config_file = service_config_dir / f'config.{env}.yaml'
        if env_config_file.exists():
            import yaml
            with open(env_config_file, 'r') as f:
                env_config = yaml.safe_load(f) or {}
                # Deep merge environment config over base config
                _deep_merge_yaml(base_config, env_config)

        # Process environment variable substitution
        _process_env_vars(base_config)

        return base_config

    return load_yaml_config


def _deep_merge_yaml(base: Dict[str, Any], update: Dict[str, Any]) -> None:
    """Deep merge YAML configurations."""
    for key, value in update.items():
        if key in base and isinstance(base[key], dict) and isinstance(value, dict):
            _deep_merge_yaml(base[key], value)
        else:
            base[key] = value


def _transform_yaml_field_names(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Transform YAML field names from dash-separated to underscore-separated.

    YAML often uses dashes (source-agent_url) but Python/Pydantic uses underscores (source_agent_url).
    """
    if not isinstance(config, dict):
        return config

    transformed = {}
    for key, value in config.items():
        # Convert dashes to underscores in field names
        python_key = key.replace('-', '_')

        # Recursively transform nested dictionaries and lists
        if isinstance(value, dict):
            transformed[python_key] = _transform_yaml_field_names(value)
        elif isinstance(value, list):
            transformed[python_key] = [
                _transform_yaml_field_names(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            transformed[python_key] = value

    return transformed


def _process_env_vars(config: Dict[str, Any]) -> None:
    """Process environment variable substitution in configuration."""
    if isinstance(config, dict):
        for key, value in config.items():
            if isinstance(value, str) and value.startswith('${') and '}' in value:
                # Handle ${VAR_NAME:-default} format
                var_expr = value[2:-1]  # Remove ${}
                if ':-' in var_expr:
                    var_name, default_value = var_expr.split(':-', 1)
                    config[key] = os.environ.get(var_name, default_value)
                else:
                    config[key] = os.environ.get(var_expr, '')
            elif isinstance(value, (dict, list)):
                _process_env_vars(value)
    elif isinstance(config, list):
        for item in config:
            _process_env_vars(item)


@lru_cache(maxsize=32)
def create_service_config(
    service_name: str,
    config_dir: Optional[Path] = None,
    environment: Optional[Environment] = None,
    **kwargs
) -> ServiceConfig:
    """
    Create a service configuration instance.

    This is the main entry point for creating service configurations.
    It handles YAML loading, environment variables, and validation.

    Args:
        service_name: Name of the service
        config_dir: Directory containing configuration files
        environment: Deployment environment
        **kwargs: Additional configuration overrides

    Returns:
        Configured ServiceConfig instance
    """
    if not PYDANTIC_AVAILABLE:
        raise ImportError("Pydantic is required for ServiceConfig. Install with: pip install pydantic pydantic-settings")

    # Set environment if provided
    if environment:
        os.environ['ENVIRONMENT'] = environment.value

    # Determine config directory
    if config_dir is None:
        config_dir = Path.cwd()
        if 'services' in str(config_dir) and config_dir.parent.name == 'services':
            config_dir = config_dir.parent.parent
        elif (config_dir / 'services').exists():
            pass  # already in project root
        else:
            # Look for services directory in parent directories
            for parent in config_dir.parents:
                if (parent / 'services').exists():
                    config_dir = parent
                    break

    service_config_dir = config_dir / 'services' / service_name

    # Load YAML configuration if it exists
    config_data = {}
    config_file = service_config_dir / 'config.yaml'
    if config_file.exists():
        import yaml
        with open(config_file, 'r') as f:
            config_data = yaml.safe_load(f) or {}

        # Transform field names from YAML format (dashes) to Python format (underscores)
        config_data = _transform_yaml_field_names(config_data)

    # Load environment-specific config
    env = os.environ.get('ENVIRONMENT', 'development')
    env_config_file = service_config_dir / f'config.{env}.yaml'
    if env_config_file.exists():
        import yaml
        with open(env_config_file, 'r') as f:
            env_config = yaml.safe_load(f) or {}
            # Transform field names in environment config too
            env_config = _transform_yaml_field_names(env_config)
            # Deep merge environment config over base config
            _deep_merge_yaml(config_data, env_config)

    # Process environment variable substitution
    _process_env_vars(config_data)

    # Merge with kwargs (kwargs take precedence)
    config_data.update(kwargs)

    # Remove service_name from config_data if it conflicts with parameter
    config_data_copy = config_data.copy()
    if 'service_name' in config_data_copy and config_data_copy['service_name'] != service_name:
        print(f"⚠️  service_name in config ({config_data_copy['service_name']}) differs from parameter ({service_name}), using parameter")
    config_data_copy.pop('service_name', None)  # Remove to avoid conflict

    # Create configuration instance
    config = ServiceConfig(
        service_name=service_name,
        _config_file_path=config_file,
        **config_data_copy
    )

    # Validate configuration
    issues = config.validate_configuration()
    if issues:
        print("⚠️  Configuration validation warnings:")
        for issue in issues:
            print(f"  - {issue}")

    return config


# Backwards compatibility aliases
BaseServiceConfig = ServiceConfig
load_service_config = create_service_config


if __name__ == "__main__":
    # Example usage and testing
    print("🔧 Testing Pydantic Configuration System")
    print("=" * 50)

    if not PYDANTIC_AVAILABLE:
        print("❌ Pydantic not available. Install with: pip install pydantic pydantic-settings")
        exit(1)

    try:
        # Test basic configuration
        config = ServiceConfig(service_name="test-service")
        print("✅ Basic configuration created")
        print(f"  Service: {config.service_name}")
        print(f"  Port: {config.server.port}")
        print(f"  Environment: {config.environment}")

        # Test validation
        issues = config.validate_configuration()
        print(f"✅ Validation completed ({len(issues)} issues)")

        # Test JSON schema generation
        schema = config.generate_schema()
        print(f"✅ JSON schema generated ({len(schema)} fields)")

        print("\n🎉 Pydantic configuration system ready!")

    except Exception as e:
        print(f"❌ Configuration system test failed: {e}")
        import traceback
        traceback.print_exc()
