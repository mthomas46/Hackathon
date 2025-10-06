"""Application Settings - Infrastructure Layer.

Centralized configuration using environment variables.
"""

import os
from functools import lru_cache
from typing import Optional, List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Service Configuration
    service_name: str = "mcp-infrastructure"
    service_api_port: int = 5500
    environment: str = "development"
    
    # Redis Configuration
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 1  # Separate DB from other services
    redis_password: Optional[str] = None
    redis_key_prefix: str = "mcp:infra:"
    redis_socket_connect_timeout: int = 5
    redis_socket_timeout: int = 5
    
    # Memory Management
    max_context_items: int = 10000
    default_ttl: int = 3600  # 1 hour
    ring_buffer_size: int = 5000
    cleanup_interval: int = 300  # 5 minutes
    
    # Event Processing
    subscribe_to_mcp_events: bool = True
    event_topics: List[str] = [
        "mcp.provisioned",
        "mcp.started",
        "mcp.stopped",
        "mcp.deleted",
        "mcp.training.*",
        "mcp.query.*",
        "mcp.knowledge.updated",
    ]
    
    # Integration with Ecosystem Services
    log_collector_url: str = "http://log-collector:5080"
    log_collector_enabled: bool = True
    llm_gateway_url: str = "http://llm-gateway:5055"
    llm_gateway_enabled: bool = True
    memory_agent_url: str = "http://memory-agent:5040"
    memory_agent_sync_enabled: bool = False  # Sync critical context to memory-agent
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # API Configuration
    api_prefix: str = "/api/v1"
    docs_url: str = "/docs"
    openapi_url: str = "/openapi.json"
    
    # CORS
    cors_origins: List[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # Circuit Breaker
    circuit_breaker_failure_threshold: int = 3
    circuit_breaker_recovery_timeout: int = 45
    
    # Retry Configuration
    retry_max_attempts: int = 2
    retry_backoff_factor: float = 2.0
    
    # Health Check
    health_check_interval: int = 30
    health_check_timeout: int = 10
    
    # DDD Configuration
    ddd_architecture: bool = True
    ddd_config_file: Optional[str] = "config/ddd_config.yaml"
    
    # WebSocket Configuration
    websocket_enabled: bool = True
    websocket_ping_interval: int = 30
    websocket_ping_timeout: int = 10
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

