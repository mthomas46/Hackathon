"""Settings for MCP Gateway Service."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings for the MCP Gateway Service.
    Settings are loaded from environment variables or a .env file.
    """
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    # Service Configuration
    service_name: str = "mcp-gateway"
    service_api_port: int = 5300
    environment: str = "development"  # development, staging, production
    
    # Redis Configuration (for registry and caching)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 2  # Separate DB from MCP Infrastructure
    redis_key_prefix: str = "mcp:gateway:"
    redis_socket_connect_timeout: int = 5
    redis_socket_timeout: int = 5
    
    # Routing Configuration
    default_routing_strategy: str = "least_loaded"  # round_robin, least_loaded, random, etc.
    max_concurrent_requests_per_instance: int = 100
    enable_sticky_sessions: bool = True
    session_ttl_seconds: int = 3600  # 1 hour
    
    # Health Check Configuration
    health_check_enabled: bool = True
    health_check_interval_seconds: int = 30
    health_check_timeout_seconds: int = 5
    max_consecutive_failures: int = 3
    unhealthy_instance_ttl_seconds: int = 300  # 5 minutes before retry
    
    # Circuit Breaker Configuration
    circuit_breaker_enabled: bool = True
    circuit_breaker_failure_threshold: int = 5
    circuit_breaker_timeout_seconds: int = 60
    circuit_breaker_expected_exception: str = "Exception"
    
    # Request Configuration
    default_request_timeout_seconds: int = 30
    max_retries: int = 2
    retry_backoff_factor: float = 1.5
    
    # Rate Limiting
    rate_limiting_enabled: bool = True
    rate_limit_requests_per_minute: int = 1000
    rate_limit_burst: int = 100
    
    # Caching
    cache_enabled: bool = True
    cache_ttl_seconds: int = 300  # 5 minutes
    cache_max_size: int = 10000
    
    # Integration with ecosystem services
    mcp_infrastructure_url: str = "http://mcp-infrastructure:5500"
    mcp_infrastructure_enabled: bool = True
    log_collector_url: str = "http://log-collector:5080"
    log_collector_enabled: bool = True
    
    # Logging
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_format: str = "json"  # json or basic
    
    # API Configuration
    api_prefix: str = "/api/v1"
    docs_url: str = "/docs"
    openapi_url: str = "/openapi.json"
    redoc_url: str = "/redoc"
    
    # CORS Configuration
    cors_origins: List[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # Monitoring & Observability
    enable_metrics: bool = True
    metrics_port: int = 9090
    enable_tracing: bool = False
    tracing_endpoint: str = ""
    
    # Cleanup
    stale_instance_cleanup_enabled: bool = True
    stale_instance_max_age_seconds: int = 3600  # 1 hour
    cleanup_interval_seconds: int = 300  # 5 minutes
    
    # DDD Architecture
    ddd_architecture: bool = True
    
    # Debug
    debug_mode: bool = False


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached instance of the Settings.
    """
    return Settings()

