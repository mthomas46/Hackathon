"""
Configuration management for data-services-dashboard.

Loads configuration from environment variables with sensible defaults.
Uses Pydantic Settings for type-safe configuration.
"""

import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings


class DashboardConfig(BaseSettings):
    """
    Dashboard configuration loaded from environment variables.
    
    Environment variables use DASHBOARD_ prefix.
    
    Example:
        DASHBOARD_LOG_COLLECTOR_URL=http://log-collector:8104
        DASHBOARD_CACHE_TTL=10
    """
    
    # Service information
    service_name: str = Field(
        default="data-services-dashboard",
        description="Service name"
    )
    
    service_version: str = Field(
        default="1.0.0",
        description="Service version"
    )
    
    # Ports
    ui_port: int = Field(
        default=8501,
        ge=1024,
        le=65535,
        description="Streamlit UI port"
    )
    
    api_port: int = Field(
        default=8080,
        ge=1024,
        le=65535,
        description="FastAPI REST API port"
    )
    
    # Log Collector
    log_collector_url: str = Field(
        default="http://localhost:8104",
        description="Log collector service URL"
    )
    
    # Services to monitor
    default_services: List[str] = Field(
        default_factory=lambda: [
            "All",
            "doc_store",
            "prompt_store",
            "external-service-store",
            "memory-agent"
        ],
        description="Default services to monitor"
    )
    
    # Time ranges
    time_ranges: List[str] = Field(
        default_factory=lambda: [
            "Last 100 operations",
            "Last 500 operations",
            "Last 1000 operations"
        ],
        description="Available time range options"
    )
    
    # Cache settings
    cache_ttl: int = Field(
        default=5,
        ge=0,
        le=300,
        description="Cache TTL in seconds (0 = no cache)"
    )
    
    # Retry settings
    max_retry_attempts: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum retry attempts for HTTP requests"
    )
    
    retry_delay: float = Field(
        default=1.0,
        ge=0.1,
        le=10.0,
        description="Initial retry delay in seconds"
    )
    
    retry_backoff: float = Field(
        default=2.0,
        ge=1.0,
        le=5.0,
        description="Retry backoff multiplier"
    )
    
    # Request timeouts
    http_timeout: float = Field(
        default=5.0,
        ge=1.0,
        le=30.0,
        description="HTTP request timeout in seconds"
    )
    
    # Environment
    environment: str = Field(
        default="development",
        description="Environment (development, staging, production)"
    )
    
    # Debug mode
    debug: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    
    class Config:
        """Pydantic Settings configuration."""
        env_prefix = "DASHBOARD_"
        case_sensitive = False
        env_file = ".env"
        env_file_encoding = "utf-8"


def load_config() -> DashboardConfig:
    """
    Load dashboard configuration.
    
    Loads from environment variables with DASHBOARD_ prefix.
    Falls back to defaults if not set.
    
    Returns:
        DashboardConfig instance
        
    Example:
        config = load_config()
        print(config.log_collector_url)  # http://localhost:8104
    """
    return DashboardConfig()


# Global configuration instance
config = load_config()


def get_limit_from_time_range(time_range: str) -> int:
    """
    Convert time range string to limit value.
    
    Args:
        time_range: Time range string (e.g., "Last 100 operations")
        
    Returns:
        Limit value (100, 500, or 1000)
        
    Example:
        >>> get_limit_from_time_range("Last 500 operations")
        500
    """
    limit_map = {
        "Last 100 operations": 100,
        "Last 500 operations": 500,
        "Last 1000 operations": 1000
    }
    return limit_map.get(time_range, 100)


def is_production() -> bool:
    """Check if running in production environment."""
    return config.environment.lower() == "production"


def is_development() -> bool:
    """Check if running in development environment."""
    return config.environment.lower() == "development"

