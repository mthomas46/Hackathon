"""
Configuration Management for MCP Services.

Centralized configuration with environment support and validation.
"""

from dataclasses import dataclass
from typing import Any, Dict, Optional
from enum import Enum
import os
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# ============================================================================
# Enumerations
# ============================================================================

class Environment(Enum):
    """Deployment environment."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TEST = "test"


# ============================================================================
# Configuration Classes
# ============================================================================

@dataclass
class DatabaseConfig:
    """Database configuration."""
    host: str = "localhost"
    port: int = 5432
    database: str = "mcp_db"
    username: str = "postgres"
    password: str = ""
    pool_size: int = 10
    
    def get_connection_string(self) -> str:
        """Get database connection string."""
        return f"postgresql://{self.username}:{self.password}@{self.host}:{self.port}/{self.database}"


@dataclass
class RedisConfig:
    """Redis configuration."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    max_connections: int = 50


@dataclass
class ServiceConfig:
    """Service configuration."""
    name: str
    version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 4
    debug: bool = False
    log_level: str = "INFO"


@dataclass
class MCPConfig:
    """Complete MCP system configuration."""
    environment: Environment
    service: ServiceConfig
    database: Optional[DatabaseConfig] = None
    redis: Optional[RedisConfig] = None
    secrets: Dict[str, str] = None
    
    def __post_init__(self):
        if self.secrets is None:
            self.secrets = {}


# ============================================================================
# Configuration Manager
# ============================================================================

class ConfigManager:
    """
    Manages configuration loading and access.
    
    Supports:
    - Environment variables
    - Config files (JSON/YAML)
    - Environment-specific configs
    - Secret management
    """
    
    def __init__(self, config_dir: str = "config"):
        """
        Initialize configuration manager.
        
        Args:
            config_dir: Directory containing config files
        """
        self.config_dir = Path(config_dir)
        self._config: Optional[MCPConfig] = None
        self._environment = self._detect_environment()
        
        logger.info(f"ConfigManager initialized for environment: {self._environment.value}")
    
    def _detect_environment(self) -> Environment:
        """Detect current environment from env var."""
        env_name = os.getenv("MCP_ENV", "development").lower()
        
        env_map = {
            "dev": Environment.DEVELOPMENT,
            "development": Environment.DEVELOPMENT,
            "staging": Environment.STAGING,
            "stage": Environment.STAGING,
            "prod": Environment.PRODUCTION,
            "production": Environment.PRODUCTION,
            "test": Environment.TEST,
        }
        
        return env_map.get(env_name, Environment.DEVELOPMENT)
    
    def load_config(
        self,
        service_name: str,
        service_version: str = "1.0.0"
    ) -> MCPConfig:
        """
        Load configuration for service.
        
        Args:
            service_name: Name of the service
            service_version: Service version
        
        Returns:
            MCPConfig instance
        """
        # Start with defaults
        config = self._load_defaults(service_name, service_version)
        
        # Load environment-specific config
        config = self._load_environment_config(config)
        
        # Override with environment variables
        config = self._load_from_env_vars(config)
        
        # Validate configuration
        self._validate_config(config)
        
        self._config = config
        logger.info(f"Configuration loaded for {service_name}")
        
        return config
    
    def _load_defaults(self, service_name: str, version: str) -> MCPConfig:
        """Load default configuration."""
        return MCPConfig(
            environment=self._environment,
            service=ServiceConfig(
                name=service_name,
                version=version,
                host=os.getenv("SERVICE_HOST", "0.0.0.0"),
                port=int(os.getenv("SERVICE_PORT", "8000")),
                workers=int(os.getenv("SERVICE_WORKERS", "4")),
                debug=(self._environment == Environment.DEVELOPMENT),
                log_level=os.getenv("LOG_LEVEL", "INFO")
            )
        )
    
    def _load_environment_config(self, config: MCPConfig) -> MCPConfig:
        """Load environment-specific configuration file."""
        config_file = self.config_dir / f"{self._environment.value}.json"
        
        if not config_file.exists():
            logger.warning(f"Config file not found: {config_file}")
            return config
        
        try:
            with open(config_file, 'r') as f:
                env_config = json.load(f)
            
            # Merge configurations
            if "database" in env_config:
                config.database = DatabaseConfig(**env_config["database"])
            
            if "redis" in env_config:
                config.redis = RedisConfig(**env_config["redis"])
            
            logger.info(f"Loaded config from: {config_file}")
        
        except Exception as e:
            logger.error(f"Failed to load config file: {e}")
        
        return config
    
    def _load_from_env_vars(self, config: MCPConfig) -> MCPConfig:
        """Override config with environment variables."""
        # Database overrides
        if os.getenv("DB_HOST"):
            if not config.database:
                config.database = DatabaseConfig()
            config.database.host = os.getenv("DB_HOST")
        
        if os.getenv("DB_PORT"):
            if not config.database:
                config.database = DatabaseConfig()
            config.database.port = int(os.getenv("DB_PORT"))
        
        if os.getenv("DB_NAME"):
            if not config.database:
                config.database = DatabaseConfig()
            config.database.database = os.getenv("DB_NAME")
        
        if os.getenv("DB_USER"):
            if not config.database:
                config.database = DatabaseConfig()
            config.database.username = os.getenv("DB_USER")
        
        if os.getenv("DB_PASSWORD"):
            if not config.database:
                config.database = DatabaseConfig()
            config.database.password = os.getenv("DB_PASSWORD")
        
        # Redis overrides
        if os.getenv("REDIS_HOST"):
            if not config.redis:
                config.redis = RedisConfig()
            config.redis.host = os.getenv("REDIS_HOST")
        
        if os.getenv("REDIS_PORT"):
            if not config.redis:
                config.redis = RedisConfig()
            config.redis.port = int(os.getenv("REDIS_PORT"))
        
        return config
    
    def _validate_config(self, config: MCPConfig):
        """Validate configuration."""
        # Basic validation
        assert config.service.name, "Service name is required"
        assert config.service.port > 0, "Valid port required"
        assert config.service.workers > 0, "At least 1 worker required"
        
        # Production checks
        if config.environment == Environment.PRODUCTION:
            assert not config.service.debug, "Debug mode must be disabled in production"
            assert config.service.log_level != "DEBUG", "Debug logging not allowed in production"
    
    def get_config(self) -> MCPConfig:
        """Get current configuration."""
        if not self._config:
            raise RuntimeError("Configuration not loaded. Call load_config() first.")
        return self._config
    
    def get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """
        Get secret value.
        
        Args:
            key: Secret key
            default: Default value if not found
        
        Returns:
            Secret value or default
        """
        # Try environment variable first
        env_key = f"SECRET_{key.upper()}"
        if os.getenv(env_key):
            return os.getenv(env_key)
        
        # Try config
        if self._config and self._config.secrets:
            return self._config.secrets.get(key, default)
        
        return default


# ============================================================================
# Global Instance
# ============================================================================

# Global config manager instance
_config_manager: Optional[ConfigManager] = None


def get_config_manager() -> ConfigManager:
    """Get global config manager instance."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager


def load_config(service_name: str, service_version: str = "1.0.0") -> MCPConfig:
    """
    Load configuration (convenience function).
    
    Args:
        service_name: Service name
        service_version: Service version
    
    Returns:
        MCPConfig instance
    """
    manager = get_config_manager()
    return manager.load_config(service_name, service_version)


def get_config() -> MCPConfig:
    """Get current configuration (convenience function)."""
    manager = get_config_manager()
    return manager.get_config()

