"""Application settings configuration."""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Service info
    service_name: str = "mcp-composer"
    service_version: str = "1.0.0"
    service_port: int = 5646
    
    # Redis configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: Optional[str] = None
    redis_key_prefix: str = "mcp-composer"
    redis_socket_timeout: int = 5
    redis_socket_connect_timeout: int = 5
    
    # MCP Gateway configuration
    mcp_gateway_url: str = "http://localhost:5601"
    
    # Logging
    log_level: str = "INFO"
    log_format: str = "json"
    
    class Config:
        """Pydantic config."""
        env_file = ".env"
        case_sensitive = False


def get_settings() -> Settings:
    """Get application settings."""
    return Settings()
