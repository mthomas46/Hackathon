"""Settings for MCP Interpreter Service."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings for the MCP Interpreter Service.
    Settings are loaded from environment variables or a .env file.
    """
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    # Service Configuration
    service_name: str = "mcp-interpreter"
    service_api_port: int = 5100
    environment: str = "development"  # development, staging, production
    
    # Redis Configuration (for caching)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 3  # Separate DB from other MCP services
    redis_key_prefix: str = "mcp:interpreter:"
    redis_socket_connect_timeout: int = 5
    redis_socket_timeout: int = 5
    
    # Query Caching
    cache_enabled: bool = True
    cache_ttl_seconds: int = 3600  # 1 hour default
    cache_max_queries: int = 10000
    
    # NLP Configuration
    spacy_model: str = "en_core_web_sm"  # spaCy model to use
    nlp_enabled: bool = True
    entity_confidence_threshold: float = 0.5
    
    # Intent Classification
    intent_classification_enabled: bool = True
    use_llm_for_intent: bool = True  # Use LLM Gateway vs simple classification
    intent_confidence_threshold: float = 0.6
    
    # LLM Gateway Integration
    llm_gateway_url: str = "http://llm-gateway:5055"
    llm_gateway_enabled: bool = True
    llm_model: str = "llama3.2:3b"
    llm_temperature: float = 0.3  # Lower for classification
    llm_max_tokens: int = 200
    llm_timeout_seconds: int = 10
    
    # Query Processing
    max_query_length: int = 500  # Maximum query length in characters
    max_keywords: int = 10
    default_complexity: int = 5
    
    # Integration with ecosystem services
    mcp_infrastructure_url: str = "http://mcp-infrastructure:5500"
    mcp_infrastructure_enabled: bool = False  # Optional integration
    log_collector_url: str = "http://log-collector:5080"
    log_collector_enabled: bool = True
    
    # Logging
    log_level: str = "INFO"  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    log_format: str = "json"  # json or basic
    
    # API Configuration
    api_prefix: str = "/api/v1"
    docs_url: str = "/docs"
    openapi_url: str = "/openapi.json"
    redoc_url: str = "/redoc"
    
    # CORS Configuration
    cors_origins: List[str] = ["*"]
    cors_allow_credentials: bool = True
    cors_allow_methods: List[str] = ["*"]
    cors_allow_headers: List[str] = ["*"]
    
    # Monitoring & Observability
    enable_metrics: bool = True
    metrics_port: int = 9090
    
    # DDD Architecture
    ddd_architecture: bool = True
    
    # Debug
    debug_mode: bool = False


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached instance of the Settings.
    """
    return Settings()

