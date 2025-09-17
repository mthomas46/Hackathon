"""Cache configuration management."""

import os
from typing import Optional
from dataclasses import dataclass


@dataclass
class CacheConfig:
    """Configuration for caching layer."""

    # Redis configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_ssl: bool = False

    # Cache settings
    default_ttl: int = 3600  # 1 hour
    max_memory: str = "256mb"
    enable_compression: bool = True

    # Cache keys
    document_cache_prefix: str = "doc:"
    analysis_cache_prefix: str = "analysis:"
    finding_cache_prefix: str = "finding:"

    # Performance settings
    connection_pool_size: int = 10
    connection_timeout: int = 5
    retry_on_timeout: bool = True
    max_retries: int = 3

    @classmethod
    def from_env(cls) -> 'CacheConfig':
        """Create configuration from environment variables."""
        return cls(
            redis_host=os.getenv('REDIS_HOST', 'localhost'),
            redis_port=int(os.getenv('REDIS_PORT', '6379')),
            redis_db=int(os.getenv('REDIS_DB', '0')),
            redis_password=os.getenv('REDIS_PASSWORD'),
            redis_ssl=os.getenv('REDIS_SSL', 'false').lower() == 'true',
            default_ttl=int(os.getenv('CACHE_DEFAULT_TTL', '3600')),
            max_memory=os.getenv('CACHE_MAX_MEMORY', '256mb'),
            enable_compression=os.getenv('CACHE_ENABLE_COMPRESSION', 'true').lower() == 'true',
            connection_pool_size=int(os.getenv('CACHE_POOL_SIZE', '10')),
            connection_timeout=int(os.getenv('CACHE_CONNECTION_TIMEOUT', '5')),
            retry_on_timeout=os.getenv('CACHE_RETRY_ON_TIMEOUT', 'true').lower() == 'true',
            max_retries=int(os.getenv('CACHE_MAX_RETRIES', '3'))
        )

    def get_redis_url(self) -> str:
        """Get Redis connection URL."""
        auth = f":{self.redis_password}@" if self.redis_password else ""
        ssl = "?ssl=true" if self.redis_ssl else ""
        return f"redis://{auth}{self.redis_host}:{self.redis_port}/{self.redis_db}{ssl}"

    def get_cache_key(self, prefix: str, identifier: str) -> str:
        """Generate cache key."""
        return f"{prefix}{identifier}"

    def get_document_cache_key(self, document_id: str) -> str:
        """Generate document cache key."""
        return self.get_cache_key(self.document_cache_prefix, document_id)

    def get_analysis_cache_key(self, analysis_id: str) -> str:
        """Generate analysis cache key."""
        return self.get_cache_key(self.analysis_cache_prefix, analysis_id)

    def get_finding_cache_key(self, finding_id: str) -> str:
        """Generate finding cache key."""
        return self.get_cache_key(self.finding_cache_prefix, finding_id)

    def get_connection_config(self) -> dict:
        """Get Redis connection configuration."""
        config = {
            'host': self.redis_host,
            'port': self.redis_port,
            'db': self.redis_db,
            'password': self.redis_password,
            'ssl': self.redis_ssl,
            'socket_connect_timeout': self.connection_timeout,
            'socket_timeout': self.connection_timeout,
            'retry_on_timeout': self.retry_on_timeout,
            'max_connections': self.connection_pool_size
        }

        # Remove None values
        return {k: v for k, v in config.items() if v is not None}

    def get_cache_config(self) -> dict:
        """Get cache configuration."""
        return {
            'default_ttl': self.default_ttl,
            'max_memory': self.max_memory,
            'enable_compression': self.enable_compression,
            'max_retries': self.max_retries
        }

    def validate(self) -> list[str]:
        """Validate configuration."""
        errors = []

        if not self.redis_host:
            errors.append("Redis host must be specified")

        if self.redis_port < 1 or self.redis_port > 65535:
            errors.append("Redis port must be between 1 and 65535")

        if self.redis_db < 0:
            errors.append("Redis database must be >= 0")

        if self.default_ttl < 0:
            errors.append("Default TTL must be >= 0")

        if self.connection_timeout < 1:
            errors.append("Connection timeout must be >= 1 second")

        if self.connection_pool_size < 1:
            errors.append("Connection pool size must be >= 1")

        if self.max_retries < 0:
            errors.append("Max retries must be >= 0")

        return errors

    def is_enabled(self) -> bool:
        """Check if caching is enabled."""
        return self.redis_host is not None and self.redis_port > 0
