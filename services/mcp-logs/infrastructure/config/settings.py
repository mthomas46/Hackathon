"""Application Settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # Service
    service_name: str = "mcp-logs"
    service_version: str = "1.0.0"
    host: str = "0.0.0.0"
    port: int = 8016
    
    # Elasticsearch
    elasticsearch_host: str = "localhost"
    elasticsearch_port: int = 9200
    elasticsearch_index: str = "mcp-logs"
    elasticsearch_user: str = ""
    elasticsearch_password: str = ""
    
    # Redis
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_password: str = ""
    
    # Log retention
    log_retention_days: int = 90
    max_log_size_mb: int = 100
    
    # Anomaly detection
    anomaly_detection_enabled: bool = True
    anomaly_threshold: float = 2.0
    
    # Alerting
    alerting_enabled: bool = True
    alert_channels: str = "email,slack"
    
    class Config:
        env_file = ".env"
        env_prefix = "LOGS_"

