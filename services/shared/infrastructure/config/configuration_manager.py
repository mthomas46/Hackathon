"""
Centralized Configuration Management Library

This module provides a standardized configuration management system for all services
in the LLM Documentation Ecosystem. It supports loading configuration from multiple
sources with proper precedence and validation.

Features:
- YAML file loading with environment variable substitution
- Environment variable overrides
- Configuration validation and type checking
- Service-specific configuration management
- Environment-specific configuration profiles
- Pydantic integration with enhanced validation (optional)
- Feature flags for gradual migration
- Hot-reload capabilities (future enhancement)
"""

import os
import yaml
import json
from pathlib import Path
from typing import Dict, Any, Optional, List, Type, TypeVar, Union, Callable
from dataclasses import dataclass, field, asdict
from abc import ABC, abstractmethod
import re
from enum import Enum

# Feature flags for Pydantic integration
# Pydantic is now enabled by default for enhanced validation
# Set USE_PYDANTIC_CONFIG=false to use legacy dataclass mode
USE_PYDANTIC_CONFIG = os.environ.get('USE_PYDANTIC_CONFIG', 'true').lower() in ('true', '1', 'yes', 'on', '')

# Try to import Pydantic components
try:
    from .pydantic_config import create_service_config as _pydantic_create_config, PYDANTIC_AVAILABLE
except ImportError:
    PYDANTIC_AVAILABLE = False
    _pydantic_create_config = None

# Configuration monitoring will be initialized lazily to avoid circular imports
_config_monitor_initialized = False

def _ensure_monitoring():
    """Ensure configuration monitoring is initialized."""
    global _config_monitor_initialized
    if not _config_monitor_initialized:
        try:
            from .config_monitor import patch_config_loading
            patch_config_loading()
            _config_monitor_initialized = True
        except ImportError:
            pass  # Monitoring not available


T = TypeVar('T')


class Environment(Enum):
    """Supported deployment environments."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class ServerConfig:
    """Standard server configuration."""
    host: str = "0.0.0.0"
    port: int = 8080
    debug: bool = False
    workers: int = 1
    timeout: int = 30

    def __post_init__(self):
        # Convert string port to int if needed
        if isinstance(self.port, str):
            self.port = int(self.port)


@dataclass
class RedisConfig:
    """Standard Redis configuration."""
    host: str = "redis"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False
    max_connections: int = 10

    def __post_init__(self):
        if isinstance(self.port, str):
            self.port = int(self.port)


@dataclass
class LoggingConfig:
    """Standard logging configuration."""
    level: str = "INFO"
    format: str = "json"
    file_path: Optional[str] = None
    max_size: int = 10485760  # 10MB
    backup_count: int = 5
    structured: bool = True
    console: bool = True


@dataclass
class ServiceDependencies:
    """Service dependency URLs and configurations."""
    orchestrator_url: str = "http://orchestrator:5099"
    doc_store_url: str = "http://doc_store:5087"
    analysis_service_url: str = "http://analysis-service:5020"
    source_agent_url: str = "http://source-agent:5085"
    frontend_url: str = "http://frontend:3000"
    memory_agent_url: str = "http://memory-agent:5090"
    discovery_agent_url: str = "http://discovery-agent:5045"
    prompt_store_url: str = "http://prompt_store:5110"
    interpreter_url: str = "http://interpreter:5120"
    cli_service_url: str = "http://cli:5130"
    user_store_url: str = "http://user-store:5150"
    external_service_store_url: str = "http://external-service-store:5140"
    notification_service_url: str = "http://notification-service:5130"
    llm_gateway_url: str = "http://llm-gateway:5055"
    summarizer_hub_url: str = "http://summarizer-hub:5160"
    github_mcp_url: str = "http://github-mcp:5030"
    bedrock_proxy_url: str = "http://bedrock-proxy:5002"
    secure_analyzer_url: str = "http://secure-analyzer:5070"
    code_analyzer_url: str = "http://code-analyzer:5025"
    architecture_digitizer_url: str = "http://architecture-digitizer:5105"
    project_simulation_url: str = "http://project-simulation:5075"
    mock_data_generator_url: str = "http://mock-data-generator:5065"
    simulation_dashboard_url: str = "http://simulation-dashboard:8501"
    unified_api_dashboard_url: str = "http://unified-api-dashboard:8000"


@dataclass
class BaseServiceConfig:
    """Base configuration class that all services should inherit from."""

    # Service metadata
    service_name: str = ""
    service_version: str = "1.0.0"
    environment: Environment = Environment.DEVELOPMENT

    # Standard configurations
    server: ServerConfig = field(default_factory=ServerConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    services: ServiceDependencies = field(default_factory=ServiceDependencies)

    # Common limits and timeouts
    limits: Dict[str, Any] = field(default_factory=lambda: {
        "max_items": 1000,
        "timeout": 30,
        "max_connections": 10,
        "max_message_length": 1000,
        "max_file_size": 10485760  # 10MB
    })

    # Health check configuration
    health: Dict[str, Any] = field(default_factory=lambda: {
        "check_interval": 30,
        "timeout": 10,
        "enabled": True
    })

    # Security configuration
    security: Dict[str, Any] = field(default_factory=lambda: {
        "cors_origins": ["*"],
        "jwt_secret": "change-me-in-production",
        "token_expiry_hours": 24,
        "rate_limiting": {
            "enabled": False,
            "requests_per_minute": 60
        }
    })

    # Custom service-specific configuration
    custom: Dict[str, Any] = field(default_factory=dict)


class ConfigurationError(Exception):
    """Configuration-related errors."""
    pass


class ConfigurationValidator(ABC):
    """Abstract base class for configuration validators."""

    @abstractmethod
    def validate(self, config: BaseServiceConfig) -> List[str]:
        """Validate configuration and return list of error messages."""
        pass


class StandardConfigurationValidator(ConfigurationValidator):
    """Standard configuration validator."""

    def validate(self, config: BaseServiceConfig) -> List[str]:
        """Validate configuration against standard rules."""
        errors = []

        # Validate server configuration
        if config.server.port < 1 or config.server.port > 65535:
            errors.append(f"Invalid server port: {config.server.port}")

        if config.server.timeout < 1:
            errors.append(f"Invalid server timeout: {config.server.timeout}")

        # Validate Redis configuration
        if config.redis.port < 1 or config.redis.port > 65535:
            errors.append(f"Invalid Redis port: {config.redis.port}")

        # Validate logging configuration
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if config.logging.level.upper() not in valid_log_levels:
            errors.append(f"Invalid log level: {config.logging.level}")

        # Validate service URLs
        for attr_name in dir(config.services):
            if not attr_name.startswith('_'):
                url = getattr(config.services, attr_name)
                if isinstance(url, str) and not url.startswith(('http://', 'https://')):
                    errors.append(f"Invalid service URL for {attr_name}: {url}")

        # Validate limits
        if config.limits.get("max_items", 0) < 1:
            errors.append("max_items must be positive")
        if config.limits.get("timeout", 0) < 1:
            errors.append("timeout must be positive")

        return errors


class ConfigurationManager:
    """
    Centralized configuration management system.

    Supports loading configuration from:
    1. YAML files with environment variable substitution
    2. Environment variables
    3. Default values
    4. Environment-specific overrides
    """

    def __init__(self,
                 service_name: str,
                 config_class: Type[BaseServiceConfig],
                 config_dir: Optional[Path] = None,
                 validators: Optional[List[ConfigurationValidator]] = None):
        self.service_name = service_name
        self.config_class = config_class
        self.config_dir = config_dir or Path(f"services/{service_name}")
        self.validators = validators or [StandardConfigurationValidator()]

        # Configuration sources in order of precedence (highest to lowest)
        self.config_sources = [
            self._load_environment_variables,
            self._load_environment_specific_config,
            self._load_service_config,
            self._load_base_config,
            self._load_defaults
        ]

    def load_config(self,
                   environment: Optional[Environment] = None,
                   validate: bool = True) -> BaseServiceConfig:
        """
        Load and merge configuration from all sources.

        Args:
            environment: Deployment environment (auto-detected if None)
            validate: Whether to validate the final configuration

        Returns:
            Merged and validated configuration object
        """
        if environment is None:
            environment = self._detect_environment()

        # Start with empty config
        config_dict = {}

        # Load from each source in precedence order
        for source_func in self.config_sources:
            try:
                source_config = source_func(environment)
                self._deep_merge(config_dict, source_config)
            except Exception as e:
                print(f"Warning: Failed to load config from {source_func.__name__}: {e}")

        # Convert to configuration object
        config = self._dict_to_config(config_dict)

        # Set service name and environment
        config.service_name = self.service_name
        config.environment = environment

        # Validate if requested
        if validate:
            self._validate_config(config)

        return config

    def _detect_environment(self) -> Environment:
        """Auto-detect deployment environment from environment variables."""
        env_str = os.environ.get("ENVIRONMENT", "development").lower()
        try:
            return Environment(env_str)
        except ValueError:
            print(f"Warning: Unknown environment '{env_str}', defaulting to development")
            return Environment.DEVELOPMENT

    def _load_defaults(self, environment: Environment) -> Dict[str, Any]:
        """Load default configuration values."""
        return asdict(self.config_class())

    def _load_base_config(self, environment: Environment) -> Dict[str, Any]:
        """Load shared base configuration."""
        base_config_path = Path("services/shared/base_config.yaml")
        if base_config_path.exists():
            return self._load_yaml_with_env_substitution(base_config_path)
        return {}

    def _load_service_config(self, environment: Environment) -> Dict[str, Any]:
        """Load service-specific configuration."""
        service_config_path = self.config_dir / "config.yaml"
        if service_config_path.exists():
            return self._load_yaml_with_env_substitution(service_config_path)
        return {}

    def _load_environment_specific_config(self, environment: Environment) -> Dict[str, Any]:
        """Load environment-specific configuration overrides."""
        env_config_path = self.config_dir / f"config.{environment.value}.yaml"
        if env_config_path.exists():
            return self._load_yaml_with_env_substitution(env_config_path)
        return {}

    def _load_environment_variables(self, environment: Environment) -> Dict[str, Any]:
        """Load configuration from environment variables."""
        config = {}

        # Map common environment variables to config paths
        env_mappings = {
            "SERVER_API_HOST": "server.host",
            "SERVER_API_PORT": "server.port",
            "REDIS_API_HOST": "redis.host",
            "REDIS_API_PORT": "redis.port",
            "LOG_LEVEL": "logging.level",
            "DEBUG": "server.debug",
            # Service URL mappings
            "ORCHESTRATOR_URL": "services.orchestrator_url",
            "DOC_STORE_URL": "services.doc_store_url",
            "ANALYSIS_SERVICE_URL": "services.analysis_service_url",
            "SOURCE_AGENT_URL": "services.source_agent_url",
            "FRONTEND_URL": "services.frontend_url",
            "MEMORY_AGENT_URL": "services.memory_agent_url",
            "DISCOVERY_AGENT_URL": "services.discovery_agent_url",
            "PROMPT_STORE_URL": "services.prompt_store_url",
            "INTERPRETER_URL": "services.interpreter_url",
            "CLI_SERVICE_URL": "services.cli_service_url",
            "USER_STORE_URL": "services.user_store_url",
            "EXTERNAL_SERVICE_STORE_URL": "services.external_service_store_url",
            "NOTIFICATION_SERVICE_URL": "services.notification_service_url",
            "LLM_GATEWAY_URL": "services.llm_gateway_url",
            "SUMMARIZER_HUB_URL": "services.summarizer_hub_url",
            "GITHUB_MCP_URL": "services.github_mcp_url",
            "BEDROCK_PROXY_URL": "services.bedrock_proxy_url",
            "SECURE_ANALYZER_URL": "services.secure_analyzer_url",
            "CODE_ANALYZER_URL": "services.code_analyzer_url",
            "ARCHITECTURE_DIGITIZER_URL": "services.architecture_digitizer_url",
            "PROJECT_SIMULATION_URL": "services.project_simulation_url",
            "MOCK_DATA_GENERATOR_URL": "services.mock_data_generator_url",
            "SIMULATION_DASHBOARD_URL": "services.simulation_dashboard_url",
            "UNIFIED_API_DASHBOARD_URL": "services.unified_api_dashboard_url",
        }

        for env_var, config_path in env_mappings.items():
            value = os.environ.get(env_var)
            if value is not None:
                self._set_nested_value(config, config_path, self._convert_value(value))

        return config

    def _load_yaml_with_env_substitution(self, file_path: Path) -> Dict[str, Any]:
        """Load YAML file with environment variable substitution."""
        try:
            with open(file_path, 'r') as f:
                content = f.read()

            # Substitute environment variables in ${VAR_NAME:-default} format
            def replace_env_var(match):
                var_expr = match.group(1)
                if ':-' in var_expr:
                    var_name, default_value = var_expr.split(':-', 1)
                    return os.environ.get(var_name, default_value)
                else:
                    return os.environ.get(var_expr, "")

            content = re.sub(r'\$\{([^}]+)\}', replace_env_var, content)

            return yaml.safe_load(content) or {}
        except Exception as e:
            raise ConfigurationError(f"Failed to load config from {file_path}: {e}")

    def _convert_value(self, value: str) -> Union[str, int, float, bool]:
        """Convert string value to appropriate type."""
        # Try boolean conversion
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'

        # Try integer conversion
        try:
            return int(value)
        except ValueError:
            pass

        # Try float conversion
        try:
            return float(value)
        except ValueError:
            pass

        # Return as string
        return value

    def _set_nested_value(self, config: Dict[str, Any], path: str, value: Any):
        """Set a value in a nested dictionary using dot notation."""
        keys = path.split('.')
        current = config

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        current[keys[-1]] = value

    def _deep_merge(self, base: Dict[str, Any], update: Dict[str, Any]):
        """Deep merge two dictionaries."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value

    def _dict_to_config(self, config_dict: Dict[str, Any]) -> BaseServiceConfig:
        """Convert dictionary to configuration object."""
        # Handle nested objects
        if 'server' in config_dict and isinstance(config_dict['server'], dict):
            config_dict['server'] = ServerConfig(**config_dict['server'])
        if 'redis' in config_dict and isinstance(config_dict['redis'], dict):
            config_dict['redis'] = RedisConfig(**config_dict['redis'])
        if 'logging' in config_dict and isinstance(config_dict['logging'], dict):
            config_dict['logging'] = LoggingConfig(**config_dict['logging'])
        if 'services' in config_dict and isinstance(config_dict['services'], dict):
            config_dict['services'] = ServiceDependencies(**config_dict['services'])

        return self.config_class(**config_dict)

    def _validate_config(self, config: BaseServiceConfig):
        """Validate configuration using all validators."""
        all_errors = []

        for validator in self.validators:
            errors = validator.validate(config)
            all_errors.extend(errors)

        if all_errors:
            error_msg = f"Configuration validation failed:\n" + "\n".join(f"  - {error}" for error in all_errors)
            raise ConfigurationError(error_msg)

    def save_config(self, config: BaseServiceConfig, file_path: Optional[Path] = None):
        """Save configuration to file."""
        if file_path is None:
            file_path = self.config_dir / "config.generated.yaml"

        config_dict = asdict(config)

        # Convert nested dataclasses back to dicts for YAML serialization
        for key, value in config_dict.items():
            if hasattr(value, '__dataclass_fields__'):
                config_dict[key] = asdict(value)

        with open(file_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, indent=2)

    def get_config_template(self) -> str:
        """Generate a configuration template for the service."""
        default_config = self.config_class()
        config_dict = asdict(default_config)

        # Add comments and examples
        template = f"""# Configuration for {self.service_name} service
# Generated template - customize as needed

"""

        def dict_to_yaml(obj, prefix=""):
            result = ""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    if isinstance(value, dict):
                        result += f"{prefix}{key}:\n{dict_to_yaml(value, prefix + '  ')}"
                    elif isinstance(value, list):
                        result += f"{prefix}{key}:\n"
                        for item in value:
                            result += f"{prefix}  - {item}\n"
                    else:
                        # Add environment variable suggestion for sensitive/configurable values
                        env_var = f"${{{key.upper()}:${value}}}"
                        result += f"{prefix}{key}: {env_var}\n"
            return result

        template += dict_to_yaml(config_dict)
        return template


# Convenience functions for common use cases
def create_service_config_manager(service_name: str,
                                config_class: Optional[Type[BaseServiceConfig]] = None) -> ConfigurationManager:
    """Create a configuration manager for a service."""
    if config_class is None:
        config_class = BaseServiceConfig

    return ConfigurationManager(
        service_name=service_name,
        config_class=config_class,
        config_dir=Path(f"services/{service_name}")
    )


def load_service_config(service_name: str,
                       config_class: Optional[Type[BaseServiceConfig]] = None,
                       environment: Optional[Environment] = None) -> Union[BaseServiceConfig, Any]:
    """
    Load configuration for a service.

    Pydantic configuration (enhanced validation) is now the default.
    Set USE_PYDANTIC_CONFIG=false to use legacy dataclass mode.

    Args:
        service_name: Name of the service
        config_class: Configuration class to use (for dataclass mode only)
        environment: Deployment environment

    Returns:
        Configuration object (Pydantic ServiceConfig by default, BaseServiceConfig for legacy)
    """
    # Ensure monitoring is initialized
    _ensure_monitoring()

    # Try Pydantic first (now the default)
    if PYDANTIC_AVAILABLE and _pydantic_create_config is not None:
        if USE_PYDANTIC_CONFIG:
            print(f"🔧 Loading {service_name} configuration with Pydantic (enhanced validation)")
            try:
                return _pydantic_create_config(service_name, environment=environment)
            except TypeError as e:
                if "multiple values for keyword argument" in str(e):
                    # Handle service_name conflict - don't pass it as parameter
                    print(f"⚠️  Retrying Pydantic config without service_name parameter")
                    try:
                        return _pydantic_create_config(service_name, environment=environment)
                    except Exception:
                        pass
                print(f"⚠️  Pydantic config loading failed for {service_name}, falling back to dataclass: {e}")
                # Fall back to dataclass mode on error
            except Exception as e:
                print(f"⚠️  Pydantic config loading failed for {service_name}, falling back to dataclass: {e}")
                # Fall back to dataclass mode on error
        else:
            print(f"📋 Skipping Pydantic for {service_name} (legacy mode requested)")

    # Use traditional dataclass-based configuration
    print(f"📋 Loading {service_name} configuration with dataclass (legacy mode)")
    manager = create_service_config_manager(service_name, config_class)
    return manager.load_config(environment)
