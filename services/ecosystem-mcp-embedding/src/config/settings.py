"""
Configuration settings for embedding service.
"""

import os
import tempfile
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Embedding service settings."""
    
    # Service
    service_name: str = "embedding-service"
    host: str = "0.0.0.0"
    port: int = 8000
    
    # FastEmbed Model
    model_name: str = "BAAI/bge-base-en-v1.5"  # 768 dims (matches nomic-embed-text)
    model_cache_dir: str = os.getenv("MODEL_CACHE_DIR", os.path.join(tempfile.gettempdir(), "fastembed_cache"))
    max_text_length: int = 8000
    
    # Redis Cache
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    cache_ttl: int = 2592000  # 30 days
    cache_enabled: bool = True
    
    # Performance
    batch_size: int = 32
    max_workers: int = 4
    
    # Logging
    log_level: str = "INFO"
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get settings instance."""
    return settings

