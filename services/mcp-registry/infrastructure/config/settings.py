"""Settings for MCP Registry Service."""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """MCP Registry Service Settings."""
    
    # Service configuration
    service_name: str = Field(default="mcp-registry", env="SERVICE_NAME")
    service_api_port: int = Field(default=5550, env="SERVICE_API_PORT")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Redis configuration (for registry metadata)
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=6, env="REDIS_DB")
    redis_key_prefix: str = Field(default="mcp:registry:", env="REDIS_KEY_PREFIX")
    redis_socket_connect_timeout: int = Field(default=5, env="REDIS_SOCKET_CONNECT_TIMEOUT")
    redis_socket_timeout: int = Field(default=5, env="REDIS_SOCKET_TIMEOUT")
    redis_max_connections: int = Field(default=50, env="REDIS_MAX_CONNECTIONS")
    
    # Storage configuration
    default_storage_backend: str = Field(default="local_filesystem", env="DEFAULT_STORAGE_BACKEND")
    local_storage_path: str = Field(default="./data/mcp-packages", env="LOCAL_STORAGE_PATH")
    s3_bucket_name: str = Field(default="mcp-packages", env="S3_BUCKET_NAME")
    s3_endpoint_url: str = Field(default="", env="S3_ENDPOINT_URL")  # For MinIO
    s3_access_key: str = Field(default="", env="S3_ACCESS_KEY")
    s3_secret_key: str = Field(default="", env="S3_SECRET_KEY")
    s3_region: str = Field(default="us-east-1", env="S3_REGION")
    
    # Export/Import configuration
    default_export_format: str = Field(default="msgpack", env="DEFAULT_EXPORT_FORMAT")
    enable_compression: bool = Field(default=True, env="ENABLE_COMPRESSION")
    default_compression_level: int = Field(default=6, env="DEFAULT_COMPRESSION_LEVEL")
    max_package_size_mb: int = Field(default=1024, env="MAX_PACKAGE_SIZE_MB")  # 1GB
    
    # Security configuration
    enable_security_scan: bool = Field(default=True, env="ENABLE_SECURITY_SCAN")
    enable_integrity_check: bool = Field(default=True, env="ENABLE_INTEGRITY_CHECK")
    quarantine_on_security_failure: bool = Field(default=True, env="QUARANTINE_ON_SECURITY_FAILURE")
    
    # Versioning configuration
    enable_auto_versioning: bool = Field(default=True, env="ENABLE_AUTO_VERSIONING")
    max_versions_per_mcp: int = Field(default=10, env="MAX_VERSIONS_PER_MCP")
    auto_deprecate_old_versions: bool = Field(default=False, env="AUTO_DEPRECATE_OLD_VERSIONS")
    
    # Registry configuration
    enable_public_registry: bool = Field(default=True, env="ENABLE_PUBLIC_REGISTRY")
    default_mcp_visibility: str = Field(default="private", env="DEFAULT_MCP_VISIBILITY")
    max_search_results: int = Field(default=100, env="MAX_SEARCH_RESULTS")
    
    # Integration with ecosystem services
    mcp_provisioner_url: str = Field(default="http://mcp-provisioner:5400", env="MCP_PROVISIONER_URL")
    mcp_provisioner_enabled: bool = Field(default=True, env="MCP_PROVISIONER_ENABLED")
    mcp_gateway_url: str = Field(default="http://mcp-gateway:5300", env="MCP_GATEWAY_URL")
    mcp_gateway_enabled: bool = Field(default=True, env="MCP_GATEWAY_ENABLED")
    log_collector_url: str = Field(default="http://log-collector:5080", env="LOG_COLLECTOR_URL")
    log_collector_enabled: bool = Field(default=True, env="LOG_COLLECTOR_ENABLED")
    
    # Background tasks
    enable_background_tasks: bool = Field(default=True, env="ENABLE_BACKGROUND_TASKS")
    cleanup_interval_seconds: int = Field(default=3600, env="CLEANUP_INTERVAL_SECONDS")
    integrity_check_interval_seconds: int = Field(default=86400, env="INTEGRITY_CHECK_INTERVAL_SECONDS")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(default="json", env="LOG_FORMAT")
    
    # API configuration
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    docs_url: str = Field(default="/docs", env="DOCS_URL")
    openapi_url: str = Field(default="/openapi.json", env="OPENAPI_URL")
    redoc_url: str = Field(default="/redoc", env="REDOC_URL")
    
    # CORS
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: List[str] = Field(default=["*"], env="CORS_ALLOW_METHODS")
    cors_allow_headers: List[str] = Field(default=["*"], env="CORS_ALLOW_HEADERS")
    
    # Monitoring
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=9090, env="METRICS_PORT")
    enable_tracing: bool = Field(default=False, env="ENABLE_TRACING")
    
    # Debug
    debug_mode: bool = Field(default=False, env="DEBUG_MODE")
    verbose_logging: bool = Field(default=False, env="VERBOSE_LOGGING")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

