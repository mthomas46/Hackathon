"""MCP Dashboard Configuration."""

from pydantic_settings import BaseSettings
from typing import Optional


class DashboardConfig(BaseSettings):
    """Dashboard configuration from environment variables."""
    
    # Dashboard Settings
    dashboard_host: str = "0.0.0.0"
    dashboard_port: int = 8015
    refresh_interval_seconds: int = 5
    max_concurrent_requests: int = 10
    enable_websockets: bool = True
    
    # Service Endpoints - PRIMARY INTEGRATIONS
    training_coordinator_url: str = "http://mcp-training-coordinator:5600"
    provisioner_url: str = "http://mcp-provisioner:8003"
    interpreter_url: str = "http://mcp-interpreter:8002"
    retrieval_url: str = "http://mcp-retrieval:8014"
    
    # Service Endpoints - SECONDARY INTEGRATIONS
    orchestrator_url: str = "http://mcp-orchestrator:8004"
    mcp_store_url: str = "http://mcp-store:8008"
    tier_manager_url: str = "http://mcp-tier-manager:8013"
    package_manager_url: str = "http://mcp-package-manager:8012"
    logs_url: str = "http://mcp-logs:8011"
    performance_store_url: str = "http://mcp-performance-store:8009"
    infrastructure_url: str = "http://mcp-infrastructure:8007"
    registry_url: str = "http://mcp-registry:8006"
    composer_url: str = "http://mcp-composer:8005"
    gateway_url: str = "http://mcp-gateway:8001"
    logging_url: str = "http://mcp-logging:8010"
    
    # Authentication (future)
    enable_auth: bool = False
    auth_provider: Optional[str] = None
    
    # Monitoring
    enable_metrics: bool = True
    metrics_export_interval: int = 60
    
    class Config:
        env_file = ".env"
        case_sensitive = False


# Global config instance
config = DashboardConfig()

