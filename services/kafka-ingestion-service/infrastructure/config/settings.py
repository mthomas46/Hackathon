"""Service Settings."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings.
    
    Loads configuration from environment variables.
    """
    
    # Service
    service_name: str = "kafka-ingestion-service"
    service_version: str = "1.0.0"
    service_port: int = 5700
    
    # Kafka
    kafka_bootstrap_servers: str = "localhost:9092"
    kafka_topic: str = "document-events"
    kafka_consumer_group: str = "kafka-ingestion-service"
    kafka_auto_offset_reset: str = "earliest"
    
    # Redis
    redis_url: str = "redis://localhost:6379"
    
    # doc_store
    doc_store_url: str = "http://localhost:5087"
    doc_store_enabled: bool = False
    
    # Logging
    log_level: str = "INFO"
    
    # Performance
    max_concurrent_events: int = 100
    event_batch_size: int = 10
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

