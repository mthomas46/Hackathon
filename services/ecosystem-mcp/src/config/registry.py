"""
Configuration Registry Loader.

Loads and validates the central service registry configuration.
Provides type-safe access to configuration values with caching.

Usage:
    from src.config.registry import get_registry
    
    registry = get_registry()
    stream_name = registry.redis.streams.ingestion.name
    consumer_group = registry.redis.streams.ingestion.consumer_group
"""

import yaml
import logging
from pathlib import Path
from typing import Optional
from datetime import datetime

from .types import ServiceRegistry

logger = logging.getLogger(__name__)


class RegistryLoader:
    """
    Loads and caches the service registry.
    
    Implements singleton pattern to ensure only one registry instance exists.
    """
    
    _instance: Optional['RegistryLoader'] = None
    _registry: Optional[ServiceRegistry] = None
    _loaded_at: Optional[datetime] = None
    
    def __new__(cls):
        """Singleton pattern - only one instance."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def load(
        self, 
        config_path: Optional[Path] = None,
        force_reload: bool = False
    ) -> ServiceRegistry:
        """
        Load service registry from YAML file.
        
        Args:
            config_path: Path to registry YAML file (auto-detected if None)
            force_reload: Force reload even if already cached
        
        Returns:
            Parsed and validated ServiceRegistry
        
        Raises:
            FileNotFoundError: If registry file not found
            ValueError: If registry is invalid
        """
        # Return cached registry if available
        if self._registry is not None and not force_reload:
            logger.debug(
                f"Using cached registry loaded at {self._loaded_at}"
            )
            return self._registry
        
        # Determine config path
        if config_path is None:
            config_path = self._find_registry_file()
        
        if not config_path.exists():
            raise FileNotFoundError(
                f"❌ Service registry not found: {config_path}\n"
                f"This file is REQUIRED for service startup.\n"
                f"Expected location: services/ecosystem-mcp/config/service_registry.yaml"
            )
        
        logger.info(f"📖 Loading service registry from: {config_path}")
        
        # Load YAML
        try:
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
        except Exception as e:
            raise ValueError(
                f"❌ Failed to parse registry YAML: {e}\n"
                f"File: {config_path}"
            ) from e
        
        if config_data is None:
            raise ValueError(
                f"❌ Registry file is empty: {config_path}"
            )
        
        # Validate and parse with Pydantic
        try:
            self._registry = ServiceRegistry(**config_data)
            self._loaded_at = datetime.utcnow()
            
            logger.info(
                f"✅ Service registry loaded successfully: "
                f"v{self._registry.version} "
                f"(environment: {self._registry.environment})"
            )
            
            # Log important configuration
            logger.debug(
                f"   Redis consumer group: "
                f"{self._registry.redis.streams.ingestion.consumer_group}"
            )
            logger.debug(
                f"   Database: {self._registry.database.connection.database}"
            )
            logger.debug(
                f"   API port: {self._registry.services.ecosystem_mcp.ports.api}"
            )
            
            return self._registry
            
        except Exception as e:
            raise ValueError(
                f"❌ Invalid registry configuration: {e}\n"
                f"File: {config_path}\n"
                f"Please check the registry schema and fix validation errors."
            ) from e
    
    def _find_registry_file(self) -> Path:
        """
        Auto-detect registry file location.
        
        Searches in order:
        1. config/service_registry.yaml (relative to current directory)
        2. ../config/service_registry.yaml (one level up)
        3. services/ecosystem-mcp/config/service_registry.yaml (from repo root)
        
        Returns:
            Path to registry file
        
        Raises:
            FileNotFoundError: If registry file cannot be found
        """
        search_paths = [
            Path("config/service_registry.yaml"),
            Path("../config/service_registry.yaml"),
            Path(__file__).parent.parent.parent / "config" / "service_registry.yaml",
            Path.cwd() / "config" / "service_registry.yaml",
        ]
        
        for path in search_paths:
            if path.exists():
                logger.debug(f"Found registry at: {path}")
                return path.resolve()
        
        raise FileNotFoundError(
            f"❌ Could not find service_registry.yaml in any of these locations:\n" +
            "\n".join(f"  - {p}" for p in search_paths) +
            "\n\nPlease ensure the registry file exists at one of these paths."
        )
    
    def get_redis_stream_name(self, stream_key: str) -> str:
        """
        Get Redis stream name from registry.
        
        Args:
            stream_key: Stream key ('ingestion', 'embedding', 'retry', 'dead_letter')
        
        Returns:
            Stream name
        
        Raises:
            ValueError: If stream key is unknown
        """
        registry = self.load()
        stream_map = {
            "ingestion": registry.redis.streams.ingestion.name,
            "embedding": registry.redis.streams.embedding.name,
            "retry": registry.redis.streams.retry.name,
            "dead_letter": registry.redis.streams.dead_letter.name
        }
        
        if stream_key not in stream_map:
            raise ValueError(
                f"Unknown stream key: {stream_key}\n"
                f"Valid keys: {', '.join(stream_map.keys())}"
            )
        
        return stream_map[stream_key]
    
    def get_redis_consumer_group(self, stream_key: str) -> str:
        """
        Get Redis consumer group name for a stream.
        
        Args:
            stream_key: Stream key ('ingestion', 'embedding', 'retry', 'dead_letter')
        
        Returns:
            Consumer group name
        
        Raises:
            ValueError: If stream key is unknown
        """
        registry = self.load()
        stream_map = {
            "ingestion": registry.redis.streams.ingestion.consumer_group,
            "embedding": registry.redis.streams.embedding.consumer_group,
            "retry": registry.redis.streams.retry.consumer_group,
            "dead_letter": registry.redis.streams.dead_letter.consumer_group
        }
        
        if stream_key not in stream_map:
            raise ValueError(
                f"Unknown stream key: {stream_key}\n"
                f"Valid keys: {', '.join(stream_map.keys())}"
            )
        
        return stream_map[stream_key]
    
    def get_database_url(self, use_container: bool = False) -> str:
        """
        Get database connection URL.
        
        Args:
            use_container: If True, return container URL (for Docker)
        
        Returns:
            Database connection URL
        """
        registry = self.load()
        
        if use_container:
            return registry.database.container.url
        else:
            return registry.database.connection.url
    
    def get_service_port(self, service_name: str, port_type: str = "api") -> int:
        """
        Get service port number.
        
        Args:
            service_name: Service name (e.g., 'ecosystem_mcp')
            port_type: Port type ('api', 'metrics', 'ui', 'main')
        
        Returns:
            Port number
        
        Raises:
            ValueError: If service or port type not found
        """
        registry = self.load()
        
        # Get service config
        service_map = {
            "ecosystem_mcp": registry.services.ecosystem_mcp,
            "ecosystem_mcp_embedding": registry.services.ecosystem_mcp_embedding,
            "ecosystem_mcp_dashboard": registry.services.ecosystem_mcp_dashboard,
            "postgres": registry.services.postgres,
            "redis": registry.services.redis,
            "ollama": registry.services.ollama,
        }
        
        if service_name not in service_map:
            raise ValueError(
                f"Unknown service: {service_name}\n"
                f"Valid services: {', '.join(service_map.keys())}"
            )
        
        service = service_map[service_name]
        port = getattr(service.ports, port_type, None)
        
        if port is None:
            raise ValueError(
                f"Service '{service_name}' has no port '{port_type}'"
            )
        
        return port
    
    def get_worker_config(self, worker_type: str) -> dict:
        """
        Get worker configuration.
        
        Args:
            worker_type: Worker type ('ingestion', 'retry')
        
        Returns:
            Worker configuration dict
        
        Raises:
            ValueError: If worker type not found
        """
        registry = self.load()
        
        worker_map = {
            "ingestion": registry.workers.ingestion,
            "retry": registry.workers.retry,
        }
        
        if worker_type not in worker_map:
            raise ValueError(
                f"Unknown worker type: {worker_type}\n"
                f"Valid types: {', '.join(worker_map.keys())}"
            )
        
        return worker_map[worker_type].dict()
    
    def clear_cache(self):
        """Clear cached registry (force reload on next access)."""
        self._registry = None
        self._loaded_at = None
        logger.info("Registry cache cleared")
    
    @property
    def is_loaded(self) -> bool:
        """Check if registry is currently loaded."""
        return self._registry is not None
    
    @property
    def loaded_at(self) -> Optional[datetime]:
        """Get timestamp when registry was loaded."""
        return self._loaded_at


# =============================================================================
# GLOBAL REGISTRY ACCESSOR
# =============================================================================

def get_registry(
    config_path: Optional[Path] = None,
    force_reload: bool = False
) -> ServiceRegistry:
    """
    Get global service registry instance.
    
    This is the main function that should be used by services to access
    the configuration registry.
    
    Args:
        config_path: Path to registry YAML file (auto-detected if None)
        force_reload: Force reload even if already cached
    
    Returns:
        Validated ServiceRegistry instance
    
    Example:
        >>> from src.config.registry import get_registry
        >>> registry = get_registry()
        >>> stream_name = registry.redis.streams.ingestion.name
        >>> print(stream_name)  # "ingestion_queue"
    """
    loader = RegistryLoader()
    return loader.load(config_path=config_path, force_reload=force_reload)


# =============================================================================
# CONVENIENCE FUNCTIONS
# =============================================================================

def get_redis_stream_name(stream_key: str) -> str:
    """Convenience function to get Redis stream name."""
    loader = RegistryLoader()
    return loader.get_redis_stream_name(stream_key)


def get_redis_consumer_group(stream_key: str) -> str:
    """Convenience function to get Redis consumer group name."""
    loader = RegistryLoader()
    return loader.get_redis_consumer_group(stream_key)


def get_database_url(use_container: bool = False) -> str:
    """Convenience function to get database URL."""
    loader = RegistryLoader()
    return loader.get_database_url(use_container=use_container)


def get_service_port(service_name: str, port_type: str = "api") -> int:
    """Convenience function to get service port."""
    loader = RegistryLoader()
    return loader.get_service_port(service_name, port_type)


def get_worker_config(worker_type: str) -> dict:
    """Convenience function to get worker config."""
    loader = RegistryLoader()
    return loader.get_worker_config(worker_type)

