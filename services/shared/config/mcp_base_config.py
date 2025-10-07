"""
Unified MCP Service Configuration using Pydantic.

This provides a base configuration class that all MCP services should extend.
It ensures consistency across the ecosystem and validates configuration at startup.
"""

from pydantic import BaseSettings, Field, validator
from typing import Optional, Dict, Any
import os


class MCPBaseConfig(BaseSettings):
    """Base configuration for all MCP services."""
    
    # Service Identity
    service_name: str = Field(..., description="Name of the service")
    service_version: str = Field(default="1.0.0", description="Service version")
    service_port: int = Field(..., description="Port the service runs on")
    
    # Environment
    environment: str = Field(default="development", description="Environment (development, staging, production)")
    debug: bool = Field(default=False, description="Debug mode")
    
    # Docker Network
    docker_network: str = Field(default="ams", description="Docker network name")
    
    # Logging
    log_level: str = Field(default="INFO", description="Logging level")
    log_format: str = Field(default="json", description="Log format (json, text)")
    
    # MCP Logs Integration
    mcp_logs_enabled: bool = Field(default=True, description="Enable MCP logs integration")
    mcp_logs_host: str = Field(default="mcp-logs", description="MCP logs service host")
    mcp_logs_port: int = Field(default=8016, description="MCP logs service port")
    
    # Health Check
    health_check_enabled: bool = Field(default=True, description="Enable health check endpoint")
    
    # CORS
    cors_enabled: bool = Field(default=True, description="Enable CORS")
    cors_origins: list = Field(default=["*"], description="Allowed CORS origins")
    
    @property
    def mcp_logs_url(self) -> str:
        """Get MCP logs URL."""
        return f"http://{self.mcp_logs_host}:{self.mcp_logs_port}"
    
    @validator("service_port")
    def validate_port(cls, v):
        """Validate port is in valid range."""
        if not (1024 <= v <= 65535):
            raise ValueError(f"Port must be between 1024 and 65535, got {v}")
        return v
    
    @validator("log_level")
    def validate_log_level(cls, v):
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}, got {v}")
        return v.upper()
    
    @validator("environment")
    def validate_environment(cls, v):
        """Validate environment."""
        valid_envs = ["development", "staging", "production"]
        if v.lower() not in valid_envs:
            raise ValueError(f"Environment must be one of {valid_envs}, got {v}")
        return v.lower()
    
    class Config:
        """Pydantic config."""
        env_prefix = ""  # No prefix for environment variables
        case_sensitive = False
        
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return self.dict()
    
    def validate_network_connectivity(self) -> Dict[str, bool]:
        """Validate connectivity to required services."""
        import socket
        
        results = {}
        
        # Check MCP logs if enabled
        if self.mcp_logs_enabled:
            try:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(2)
                result = sock.connect_ex((self.mcp_logs_host, self.mcp_logs_port))
                results["mcp_logs"] = result == 0
                sock.close()
            except Exception:
                results["mcp_logs"] = False
        
        return results
    
    def print_config(self):
        """Print configuration for debugging."""
        print(f"{'='*60}")
        print(f"Service Configuration: {self.service_name}")
        print(f"{'='*60}")
        print(f"Version: {self.service_version}")
        print(f"Port: {self.service_port}")
        print(f"Environment: {self.environment}")
        print(f"Debug: {self.debug}")
        print(f"Log Level: {self.log_level}")
        print(f"Docker Network: {self.docker_network}")
        if self.mcp_logs_enabled:
            print(f"MCP Logs: {self.mcp_logs_url}")
        print(f"{'='*60}")


class KafkaIngestionConfig(MCPBaseConfig):
    """Configuration for Kafka Ingestion Service."""
    
    service_name: str = "kafka-ingestion-service"
    service_port: int = 5700
    
    # Kafka settings
    kafka_bootstrap_servers: str = Field(default="kafka:29092", description="Kafka bootstrap servers")
    kafka_topic: str = Field(default="document-ingestion", description="Kafka topic")
    
    # Redis settings
    redis_url: str = Field(default="redis://redis:6379", description="Redis connection URL")
    
    # Doc Store
    doc_store_url: str = Field(default="http://doc_store:5087", description="Doc Store URL")


class LLMTaggingConfig(MCPBaseConfig):
    """Configuration for LLM Tagging Pipeline."""
    
    service_name: str = "llm-tagging-pipeline"
    service_port: int = 8021
    
    # Ollama settings
    ollama_host: str = Field(default="ollama", description="Ollama host")
    ollama_port: int = Field(default=11434, description="Ollama port")
    default_model: str = Field(default="llama2", description="Default LLM model")
    
    @property
    def ollama_url(self) -> str:
        """Get Ollama URL."""
        return f"http://{self.ollama_host}:{self.ollama_port}"


class MCPLocalLLMConfig(MCPBaseConfig):
    """Configuration for MCP Local LLM."""
    
    service_name: str = "mcp-local-llm"
    service_port: int = 8014
    
    # Ollama settings
    ollama_host: str = Field(default="ollama", description="Ollama host")
    ollama_port: int = Field(default=11434, description="Ollama port")
    default_model: str = Field(default="llama2", description="Default LLM model")
    
    @property
    def ollama_url(self) -> str:
        """Get Ollama URL."""
        return f"http://{self.ollama_host}:{self.ollama_port}"


class MCPPackageManagerConfig(MCPBaseConfig):
    """Configuration for MCP Package Manager."""
    
    service_name: str = "mcp-package-manager"
    service_port: int = 8103
    
    # Storage settings
    storage_dir: str = Field(default="/data/packages", description="Package storage directory")
    redis_url: str = Field(default="redis://redis:6379", description="Redis connection URL")


class MCPEvergreenDocsConfig(MCPBaseConfig):
    """Configuration for MCP Evergreen Docs."""
    
    service_name: str = "mcp-evergreen-docs"
    service_port: int = 8104
    
    # Redis settings
    redis_url: str = Field(default="redis://redis:6379", description="Redis connection URL")


class MCPLogsConfig(MCPBaseConfig):
    """Configuration for MCP Logs."""
    
    service_name: str = "mcp-logs"
    service_port: int = 8016
    
    # Elasticsearch settings
    elasticsearch_url: str = Field(default="http://elasticsearch:9200", description="Elasticsearch URL")
    elasticsearch_index: str = Field(default="mcp-logs", description="Elasticsearch index")
    
    # Disable self-logging to MCP logs (prevent circular dependency)
    mcp_logs_enabled: bool = False
