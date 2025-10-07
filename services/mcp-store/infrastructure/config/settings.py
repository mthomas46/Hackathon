"""Application settings configuration."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Service info
    service_name: str = "mcp-store"
    service_version: str = "1.0.0"
    service_port: int = 5648
    
    # SQLite configuration (for metadata)
    database_url: str = "sqlite+aiosqlite:///./data/mcp_store.db"
    database_echo: bool = False
    
    # S3/MinIO configuration (for binary storage)
    storage_type: str = "minio"  # "s3" or "minio"
    storage_endpoint: str = "localhost:9000"
    storage_access_key: Optional[str] = None
    storage_secret_key: Optional[str] = None
    storage_bucket: str = "mcp-packages"
    storage_region: str = "us-east-1"
    storage_use_ssl: bool = False
    
    # Redis configuration (for caching)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 1
    redis_password: Optional[str] = None
    redis_key_prefix: str = "mcp-store:"
    
    # Package settings
    max_package_size_mb: int = 500  # Maximum .mcp file size
    max_versions_per_package: int = 100
    
    # Search settings
    enable_full_text_search: bool = True
    search_results_limit: int = 100
    
    # Security
    enable_auth: bool = False  # JWT authentication
    jwt_secret: Optional[str] = None
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # Data retention
    retention_yanked_versions_days: int = 90
    retention_download_stats_days: int = 365
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
