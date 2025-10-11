"""
Configuration management for Ecosystem MCP Service.

Loads configuration from environment variables with sensible defaults.
"""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    # Model Strategy
    model_strategy: str = Field(
        default="auto",
        description="Model selection strategy: 'auto' (intelligent), 'ollama-only' (local only), 'cloud-first' (prefer cloud)"
    )

    # Database
    database_url: str = Field(
        default="postgresql://ecosystem:ecosystem_password@localhost:5432/ecosystem_mcp",
        description="PostgreSQL connection string"
    )
    database_pool_size: int = Field(default=20, ge=1, le=100)
    database_max_overflow: int = Field(default=10, ge=0, le=50)

    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis connection string"
    )
    redis_max_connections: int = Field(default=50, ge=1, le=200)

    # ChromaDB
    chroma_path: Path = Field(
        default=Path("./data/chroma_db"),
        description="Path to ChromaDB persistent storage"
    )
    chroma_collection_name: str = Field(default="ecosystem_docs")

    # Ollama
    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama API base URL"
    )
    ollama_model_small: str = Field(default="llama3.1:8b-instruct-q8_0")
    ollama_model_medium: str = Field(default="mistral:7b-instruct-q8_0")
    ollama_embedding_model: str = Field(default="nomic-embed-text:latest")
    ollama_timeout: int = Field(default=300, ge=10, le=600)

    # OpenAI
    openai_api_key: Optional[str] = Field(default=None)
    openai_embedding_model: str = Field(default="text-embedding-3-small")

    # Anthropic
    anthropic_api_key: Optional[str] = Field(default=None)

    # Git
    git_repo_path: Path = Field(
        default=Path("/Users/mykalthomas/Documents/work/Hackathon"),
        description="Path to git repository"
    )

    # Ingestion
    max_workers: int = Field(default=8, ge=1, le=16)
    batch_size: int = Field(default=100, ge=10, le=1000)
    embedding_batch_size: int = Field(default=50, ge=10, le=100)

    # Cost Controls
    embedding_daily_budget_usd: float = Field(default=10.0, ge=0.0)
    embedding_cost_per_1m_tokens: float = Field(default=0.13, ge=0.0)

    # Performance
    search_max_results: int = Field(default=50, ge=1, le=200)
    search_timeout_seconds: int = Field(default=5, ge=1, le=30)
    cache_ttl_seconds: int = Field(default=3600, ge=60, le=86400)

    # Monitoring
    environment: str = Field(default="development", description="Deployment environment")
    log_level: str = Field(default="INFO")
    sentry_dsn: Optional[str] = Field(default=None)
    metrics_port: int = Field(default=9090, ge=1024, le=65535)
    
    @model_validator(mode='after')
    def validate_environment(self):
        """Validate environment is one of the allowed values."""
        # Import here to avoid circular import
        # (utils.__init__ imports redis_client which imports settings)
        import sys
        from pathlib import Path
        
        # Add utils directly to avoid __init__ import
        utils_path = Path(__file__).parent / "utils"
        sys.path.insert(0, str(utils_path.parent))
        
        # Import just the environment module, not the package
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "environment", 
            utils_path / "environment.py"
        )
        env_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(env_module)
        
        # Validate environment
        try:
            env_module.validate_environment(self.environment)
        except Exception as e:
            # Wrap any validation error as a configuration error
            # Can't import ConfigurationError directly due to circular imports
            raise ValueError(f"Configuration error: {e}") from e
        
        return self

    # MCP Server
    mcp_host: str = Field(default="127.0.0.1")
    mcp_port: int = Field(default=8000, ge=1024, le=65535)
    mcp_debug: bool = Field(default=False)

    def ensure_directories(self) -> None:
        """Ensure required directories exist."""
        self.chroma_path.mkdir(parents=True, exist_ok=True)
        
        data_dir = Path("./data")
        (data_dir / "postgresql").mkdir(parents=True, exist_ok=True)
        (data_dir / "redis").mkdir(parents=True, exist_ok=True)
        (data_dir / "backups").mkdir(parents=True, exist_ok=True)

    @property
    def ollama_available(self) -> bool:
        """Check if Ollama is configured and potentially available."""
        return bool(self.ollama_base_url)

    @property
    def openai_available(self) -> bool:
        """Check if OpenAI is configured."""
        return bool(self.openai_api_key)

    @property
    def anthropic_available(self) -> bool:
        """Check if Anthropic is configured."""
        return bool(self.anthropic_api_key)

    @property
    def is_ollama_only(self) -> bool:
        """Check if running in ollama-only mode."""
        return self.model_strategy == "ollama-only"


# Global settings instance
settings = Settings()

# Ensure directories exist on import
settings.ensure_directories()

