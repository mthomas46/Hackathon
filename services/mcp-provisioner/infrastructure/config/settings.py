"""Application Settings - Infrastructure Layer.

Centralized configuration using environment variables.
"""

import os
from functools import lru_cache
from typing import Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Service Configuration
    service_name: str = "mcp-provisioner"
    service_api_port: int = 5400
    environment: str = "development"
    
    # Redis Configuration
    redis_host: str = "redis"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_key_prefix: str = "mcp:provisioner:"
    
    # Docker Configuration
    docker_socket: str = "unix:///var/run/docker.sock"
    docker_network: str = "hackathon_default"
    docker_mcp_image_prefix: str = "client-mcp"
    
    # Port Allocation
    mcp_port_range_start: int = 9000
    mcp_port_range_end: int = 9100
    
    # LLM Gateway Integration
    llm_gateway_url: str = "http://llm-gateway:5055"
    llm_gateway_enabled: bool = True
    
    # Log Collector Integration
    log_collector_url: str = "http://log-collector:5080"
    log_collector_enabled: bool = True
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    # API Configuration
    api_prefix: str = "/api/v1"
    docs_url: str = "/docs"
    openapi_url: str = "/openapi.json"
    
    # CORS
    cors_origins: list[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]
    
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
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

