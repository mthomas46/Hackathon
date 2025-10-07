"""Settings for Training Coordinator Service."""

from functools import lru_cache
from typing import List

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Training Coordinator Service Settings."""
    
    # Service configuration
    service_name: str = Field(default="training-coordinator", env="SERVICE_NAME")
    service_api_port: int = Field(default=5600, env="SERVICE_API_PORT")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Redis configuration (job queue)
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=7, env="REDIS_DB")
    redis_key_prefix: str = Field(default="training:", env="REDIS_KEY_PREFIX")
    
    # PostgreSQL configuration (job persistence)
    postgres_host: str = Field(default="localhost", env="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, env="POSTGRES_PORT")
    postgres_db: str = Field(default="training_coordinator", env="POSTGRES_DB")
    postgres_user: str = Field(default="training", env="POSTGRES_USER")
    postgres_password: str = Field(default="training", env="POSTGRES_PASSWORD")
    
    # Celery configuration
    celery_broker_url: str = Field(default="redis://localhost:6379/8", env="CELERY_BROKER_URL")
    celery_result_backend: str = Field(default="redis://localhost:6379/8", env="CELERY_RESULT_BACKEND")
    
    # Worker pool configuration
    max_extraction_workers: int = Field(default=5, env="MAX_EXTRACTION_WORKERS")
    max_normalization_workers: int = Field(default=3, env="MAX_NORMALIZATION_WORKERS")
    max_embedding_workers: int = Field(default=3, env="MAX_EMBEDDING_WORKERS")
    max_storage_workers: int = Field(default=2, env="MAX_STORAGE_WORKERS")
    
    # Job configuration
    max_concurrent_jobs: int = Field(default=10, env="MAX_CONCURRENT_JOBS")
    default_job_timeout_seconds: int = Field(default=3600, env="DEFAULT_JOB_TIMEOUT_SECONDS")
    job_cleanup_interval_seconds: int = Field(default=86400, env="JOB_CLEANUP_INTERVAL_SECONDS")
    
    # Ecosystem integration
    mcp_provisioner_url: str = Field(default="http://mcp-provisioner:5400", env="MCP_PROVISIONER_URL")
    mcp_infrastructure_url: str = Field(default="http://mcp-infrastructure:5500", env="MCP_INFRASTRUCTURE_URL")
    
    # API configuration
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")
    docs_url: str = Field(default="/docs", env="DOCS_URL")
    cors_origins: List[str] = Field(default=["*"], env="CORS_ORIGINS")
    
    # Logging
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()

