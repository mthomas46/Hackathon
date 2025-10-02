"""Configuration settings for the Meta-Orchestration Service"""

import os
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class DockerSettings:
    """Docker-related configuration"""
    host: str = "unix:///var/run/docker.sock"
    tls_verify: bool = False
    cert_path: Optional[str] = None
    timeout: int = 60

    def __post_init__(self):
        """Load settings from environment variables"""
        self.host = os.getenv("DOCKER_HOST", self.host)
        self.tls_verify = os.getenv("DOCKER_TLS_VERIFY", "false").lower() == "true"
        self.cert_path = os.getenv("DOCKER_CERT_PATH", self.cert_path)
        self.timeout = int(os.getenv("DOCKER_TIMEOUT", self.timeout))


@dataclass
class ServiceSettings:
    """Service configuration"""
    name: str = "meta-orchestrator"
    version: str = "1.0.0"
    debug: bool = False
    log_level: str = "INFO"

    def __post_init__(self):
        """Load settings from environment variables"""
        self.debug = os.getenv("DEBUG", "false").lower() == "true"
        self.log_level = os.getenv("LOG_LEVEL", self.log_level)


@dataclass
class SecuritySettings:
    """Security-related configuration"""
    allowed_networks: List[str] = None
    enable_auth: bool = False
    api_key: Optional[str] = None

    def __post_init__(self):
        """Load settings from environment variables"""
        if self.allowed_networks is None:
            self.allowed_networks = ["172.0.0.0/8", "10.0.0.0/8"]

        self.enable_auth = os.getenv("ENABLE_AUTH", "false").lower() == "true"
        self.api_key = os.getenv("API_KEY", self.api_key)


@dataclass
class Settings:
    """Main settings class"""

    # Service settings
    service: ServiceSettings = None

    # Docker settings
    docker: DockerSettings = None

    # Security settings
    security: SecuritySettings = None

    # Paths
    workspace_path: str = "/app"
    compose_file: str = "docker-compose.dev.yml"

    # Feature flags
    enable_auto_scaling: bool = False
    enable_config_sync: bool = True
    enable_health_monitoring: bool = True

    def __post_init__(self):
        """Initialize settings and load from environment"""
        # Initialize nested objects if not provided
        if self.service is None:
            self.service = ServiceSettings()
        if self.docker is None:
            self.docker = DockerSettings()
        if self.security is None:
            self.security = SecuritySettings()

        # Load main settings from environment
        self.workspace_path = os.getenv("WORKSPACE_PATH", self.workspace_path)
        self.compose_file = os.getenv("COMPOSE_FILE", self.compose_file)
        self.enable_auto_scaling = os.getenv("ENABLE_AUTO_SCALING", "false").lower() == "true"
        self.enable_config_sync = os.getenv("ENABLE_CONFIG_SYNC", "true").lower() == "true"
        self.enable_health_monitoring = os.getenv("ENABLE_HEALTH_MONITORING", "true").lower() == "true"


# Global settings instance
settings = Settings()
