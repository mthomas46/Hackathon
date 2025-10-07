"""Application Settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Service
    service_name: str = "mcp-package-manager"
    service_version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8020
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    
    # Storage
    storage_dir: str = "./packages"
    max_package_size_mb: int = 1000
    
    # Export/Import
    default_compression: str = "gzip"
    export_format: str = "mcp_v1"
    
    class Config:
        env_file = ".env"
        env_prefix = "PKG_"

