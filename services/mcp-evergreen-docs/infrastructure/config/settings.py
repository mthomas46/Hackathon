"""Application Settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Service
    service_name: str = "mcp-evergreen-docs"
    service_version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8019
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    
    # Sync
    sync_interval_minutes: int = 60
    max_concurrent_syncs: int = 5
    
    # Validation
    validation_enabled: bool = True
    auto_validate: bool = True
    
    # Git
    git_clone_timeout: int = 300
    git_pull_timeout: int = 120
    
    class Config:
        env_file = ".env"
        env_prefix = "EVERGREEN_"

