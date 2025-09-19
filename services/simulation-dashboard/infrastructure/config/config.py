"""Configuration management for the Simulation Dashboard Service.

This module provides centralized configuration management for the dashboard service,
following environment-aware patterns consistent with the ecosystem.
"""

import os
from typing import Optional, List
from pydantic import BaseModel, Field, validator
from pydantic_settings import BaseSettings


class SimulationServiceConfig(BaseModel):
    """Configuration for the project-simulation service connection."""

    host: str = Field(default="localhost", description="Simulation service host")
    port: int = Field(default=5075, description="Simulation service port")
    base_url: str = Field(default="", description="Full base URL (auto-generated if empty)")
    timeout: float = Field(default=30.0, description="Request timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    retry_delay: float = Field(default=1.0, description="Delay between retries")

    @validator("base_url", always=True)
    def generate_base_url(cls, v, values):
        """Generate base URL from host and port if not provided."""
        if not v and "host" in values and "port" in values:
            return f"http://{values['host']}:{values['port']}"
        return v


class WebSocketConfig(BaseModel):
    """Configuration for WebSocket connections."""

    enabled: bool = Field(default=True, description="Enable WebSocket connections")
    reconnect_attempts: int = Field(default=5, description="Number of reconnection attempts")
    reconnect_delay: float = Field(default=2.0, description="Delay between reconnection attempts")
    heartbeat_interval: float = Field(default=30.0, description="Heartbeat interval in seconds")
    message_timeout: float = Field(default=10.0, description="Message timeout in seconds")


class DashboardConfig(BaseModel):
    """Dashboard-specific configuration."""

    title: str = Field(default="Project Simulation Dashboard", description="Dashboard title")
    theme: str = Field(default="light", description="Dashboard theme (light/dark)")
    refresh_interval: int = Field(default=5000, description="Auto-refresh interval in milliseconds")
    max_simulations_display: int = Field(default=50, description="Maximum simulations to display")
    enable_caching: bool = Field(default=True, description="Enable response caching")
    cache_ttl: int = Field(default=300, description="Cache TTL in seconds")


class LoggingConfig(BaseModel):
    """Logging configuration."""

    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(default="json", description="Log format (json/text)")
    enable_structlog: bool = Field(default=True, description="Enable structured logging")
    log_requests: bool = Field(default=True, description="Log HTTP requests")
    log_websocket: bool = Field(default=True, description="Log WebSocket messages")


class PerformanceConfig(BaseModel):
    """Performance-related configuration."""

    enable_compression: bool = Field(default=True, description="Enable response compression")
    max_concurrent_requests: int = Field(default=10, description="Maximum concurrent HTTP requests")
    connection_pool_size: int = Field(default=20, description="HTTP connection pool size")
    cache_size: int = Field(default=1000, description="LRU cache size")


class DashboardSettings(BaseSettings):
    """Main configuration settings for the dashboard service."""

    # Environment
    environment: str = Field(default="development", description="Deployment environment")
    debug: bool = Field(default=False, description="Debug mode")

    # Service identification
    service_name: str = Field(default="simulation-dashboard", description="Service name")
    service_version: str = Field(default="1.0.0", description="Service version")

    # Server configuration
    host: str = Field(default="0.0.0.0", description="Server host")
    port: int = Field(default=8501, description="Server port")

    # Service configurations
    simulation_service: SimulationServiceConfig = Field(default_factory=SimulationServiceConfig)
    websocket: WebSocketConfig = Field(default_factory=WebSocketConfig)
    dashboard: DashboardConfig = Field(default_factory=DashboardConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    performance: PerformanceConfig = Field(default_factory=PerformanceConfig)

    # CORS settings
    cors_origins: List[str] = Field(default_factory=lambda: ["*"], description="CORS allowed origins")

    # Optional ecosystem services
    analysis_service_url: Optional[str] = Field(default=None, description="Analysis service URL")
    health_service_url: Optional[str] = Field(default=None, description="Health service URL")

    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        env_prefix = "DASHBOARD_"
        case_sensitive = False

    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.environment.lower() in ["development", "dev", "local"]

    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() in ["production", "prod"]

    def get_simulation_service_url(self, path: str = "") -> str:
        """Get full URL for simulation service endpoint."""
        base = self.simulation_service.base_url.rstrip("/")
        path = path.lstrip("/")
        return f"{base}/{path}" if path else base


# Global configuration instance
_config: Optional[DashboardSettings] = None


def get_config() -> DashboardSettings:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = DashboardSettings()
    return _config


def reload_config() -> DashboardSettings:
    """Reload configuration from environment."""
    global _config
    _config = DashboardSettings()
    return _config


def get_simulation_service_url(path: str = "") -> str:
    """Convenience function to get simulation service URL."""
    return get_config().get_simulation_service_url(path)
