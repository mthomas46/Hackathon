"""Settings for MCP Orchestrator Service."""

from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings for the MCP Orchestrator Service.
    Settings are loaded from environment variables or a .env file.
    """
    
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    
    # Service Configuration
    service_name: str = "mcp-orchestrator"
    service_api_port: int = 5200
    environment: str = "development"  # development, staging, production
    
    # Redis Configuration (for workflow state)
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 4  # Separate DB from other MCP services
    redis_key_prefix: str = "mcp:orchestrator:"
    redis_socket_connect_timeout: int = 5
    redis_socket_timeout: int = 5
    
    # Workflow Management
    max_concurrent_workflows: int = 100
    default_workflow_timeout_seconds: int = 300  # 5 minutes
    workflow_cleanup_interval_seconds: int = 3600  # 1 hour
    max_workflow_retries: int = 3
    
    # Execution Configuration
    default_execution_strategy: str = "scatter_gather"
    enable_async_execution: bool = True
    enable_parallel_step_execution: bool = True
    max_parallel_steps: int = 5
    step_timeout_seconds: int = 60
    
    # LLM Pattern Configuration
    enable_chain_of_thought: bool = True
    enable_self_critique: bool = True
    enable_ensemble: bool = True
    pattern_confidence_threshold: float = 0.7
    
    # MCP Selection
    max_mcps_per_workflow: int = 10
    prefer_hot_instances: bool = True
    mcp_query_timeout_seconds: int = 30
    enable_mcp_fallbacks: bool = True
    
    # Integration with ecosystem services
    mcp_gateway_url: str = "http://mcp-gateway:5300"
    mcp_gateway_enabled: bool = True
    mcp_gateway_timeout_seconds: int = 30
    
    mcp_interpreter_url: str = "http://mcp-interpreter:5100"
    mcp_interpreter_enabled: bool = True
    
    mcp_infrastructure_url: str = "http://mcp-infrastructure:5500"
    mcp_infrastructure_enabled: bool = True
    
    llm_gateway_url: str = "http://llm-gateway:5055"
    llm_gateway_enabled: bool = True
    llm_model: str = "llama3.2:3b"
    llm_temperature: float = 0.3
    llm_max_tokens: int = 500
    llm_timeout_seconds: int = 30
    
    log_collector_url: str = "http://log-collector:5080"
    log_collector_enabled: bool = True
    
    # Background Tasks (Celery)
    celery_broker_url: str = "redis://localhost:6379/5"
    celery_result_backend: str = "redis://localhost:6379/5"
    celery_task_soft_time_limit: int = 300  # 5 minutes
    celery_task_time_limit: int = 360  # 6 minutes
    
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
    
    # WebSocket Configuration
    websocket_enabled: bool = True
    websocket_ping_interval: int = 30
    websocket_ping_timeout: int = 10
    enable_progress_streaming: bool = True
    
    # Monitoring & Observability
    enable_metrics: bool = True
    metrics_port: int = 9090
    enable_tracing: bool = False
    
    # DDD Architecture
    ddd_architecture: bool = True
    
    # Approval Workflow
    enable_approval_workflow: bool = True
    approval_timeout_seconds: int = 86400  # 24 hours
    
    # Result Caching
    enable_result_caching: bool = True
    result_cache_ttl_seconds: int = 3600  # 1 hour
    
    # Performance Optimization
    enable_query_optimization: bool = True
    enable_prompt_caching: bool = True
    enable_connection_pooling: bool = True
    connection_pool_size: int = 10
    
    # Debug
    debug_mode: bool = False
    verbose_logging: bool = False


@lru_cache()
def get_settings() -> Settings:
    """
    Returns a cached instance of the Settings.
    """
    return Settings()

