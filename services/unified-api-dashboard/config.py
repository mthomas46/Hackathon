"""
Configuration for the Unified API Dashboard service.
"""

import os
from typing import List, Optional
from pydantic import BaseModel, Field


class ServiceConfig(BaseModel):
    """Service configuration."""
    name: str = Field(default="unified-api-dashboard", description="Service name")
    version: str = Field(default="1.0.0", description="Service version")
    debug: bool = Field(default=True, description="Debug mode")
    port: int = Field(default=8501, description="Streamlit dashboard port")
    api_port: int = Field(default=8000, description="FastAPI server port")


class DiscoveryConfig(BaseModel):
    """Discovery Agent configuration."""
    base_url: str = Field(default="http://localhost:5010", description="Discovery Agent base URL")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")


class EcosystemServicesConfig(BaseModel):
    """Ecosystem services configuration."""
    orchestrator: dict = Field(default_factory=lambda: {"base_url": "http://localhost:5006", "enabled": True})
    interpreter: dict = Field(default_factory=lambda: {"base_url": "http://localhost:5120", "enabled": True})
    doc_store: dict = Field(default_factory=lambda: {"base_url": "http://localhost:5087", "enabled": True})
    prompt_store: dict = Field(default_factory=lambda: {"base_url": "http://localhost:5110", "enabled": True})
    frontend: dict = Field(default_factory=lambda: {"base_url": "http://localhost:3000", "enabled": True})
    cli: dict = Field(default_factory=lambda: {"base_url": "http://localhost:5005", "enabled": True})
    discovery_agent: dict = Field(default_factory=lambda: {"base_url": "http://localhost:5010", "enabled": True})
    project_simulation: dict = Field(default_factory=lambda: {"base_url": "http://localhost:5001", "enabled": True})


class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO", description="Logging level")
    format: str = Field(default="%(asctime)s - %(name)s - %(levelname)s - %(message)s", description="Log format")
    file: Optional[str] = Field(default="logs/dashboard.log", description="Log file path")


class CachingConfig(BaseModel):
    """Caching configuration."""
    enabled: bool = Field(default=True, description="Enable caching")
    ttl_seconds: int = Field(default=300, description="Cache TTL in seconds")
    max_size: int = Field(default=1000, description="Maximum cache size")


class UIConfig(BaseModel):
    """UI configuration."""
    theme: str = Field(default="light", description="UI theme")
    auto_refresh_interval: int = Field(default=30, description="Auto refresh interval in seconds")
    max_display_rows: int = Field(default=100, description="Maximum rows to display")


class APIConfig(BaseModel):
    """API configuration."""
    enable_cors: bool = Field(default=True, description="Enable CORS")
    cors_origins: List[str] = Field(default_factory=lambda: ["*"], description="CORS allowed origins")
    enable_swagger: bool = Field(default=True, description="Enable Swagger UI")
    enable_redoc: bool = Field(default=True, description="Enable ReDoc")


class Config(BaseModel):
    """Main configuration class."""
    service: ServiceConfig = Field(default_factory=ServiceConfig)
    discovery_agent: DiscoveryConfig = Field(default_factory=DiscoveryConfig)
    ecosystem_services: EcosystemServicesConfig = Field(default_factory=EcosystemServicesConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    caching: CachingConfig = Field(default_factory=CachingConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    api: APIConfig = Field(default_factory=APIConfig)

    # Derived properties
    @property
    def discovery_agent_url(self) -> str:
        """Get the full Discovery Agent URL."""
        return self.discovery_agent.base_url

    @property
    def api_polling_interval(self) -> int:
        """Get the API polling interval in seconds."""
        return 30  # Fixed for now, could be configurable

    @property
    def streamlit_port(self) -> int:
        """Get the Streamlit port."""
        return self.service.port

    @classmethod
    def from_env(cls) -> "Config":
        """Create configuration from environment variables."""
        return cls(
            service=ServiceConfig(
                name=os.getenv("SERVICE_NAME", "unified-api-dashboard"),
                version=os.getenv("SERVICE_VERSION", "1.0.0"),
                debug=os.getenv("DEBUG", "true").lower() == "true",
                port=int(os.getenv("STREAMLIT_PORT", "8501")),
                api_port=int(os.getenv("API_PORT", "8000"))
            ),
            discovery_agent=DiscoveryConfig(
                base_url=os.getenv("DISCOVERY_AGENT_URL", "http://localhost:5010"),
                timeout=int(os.getenv("DISCOVERY_TIMEOUT", "30")),
                retry_attempts=int(os.getenv("DISCOVERY_RETRIES", "3"))
            ),
            caching=CachingConfig(
                enabled=os.getenv("CACHE_ENABLED", "true").lower() == "true",
                ttl_seconds=int(os.getenv("CACHE_TTL", "300")),
                max_size=int(os.getenv("CACHE_MAX_SIZE", "1000"))
            ),
            ui=UIConfig(
                theme=os.getenv("UI_THEME", "light"),
                auto_refresh_interval=int(os.getenv("UI_REFRESH_INTERVAL", "30")),
                max_display_rows=int(os.getenv("UI_MAX_ROWS", "100"))
            )
        )

    @classmethod
    def from_yaml(cls, yaml_file: str) -> "Config":
        """Create configuration from YAML file."""
        try:
            import yaml
            with open(yaml_file, 'r') as f:
                data = yaml.safe_load(f)
            return cls(**data)
        except ImportError:
            # YAML not available, fall back to env
            return cls.from_env()
        except Exception as e:
            print(f"Error loading config from {yaml_file}: {e}")
            return cls.from_env()


# Global configuration instance
config = Config.from_env()

# Try to load from config.yaml if it exists
try:
    config = Config.from_yaml("config.yaml")
except:
    pass
