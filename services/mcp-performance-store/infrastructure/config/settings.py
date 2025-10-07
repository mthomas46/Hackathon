"""
Configuration settings for MCP Performance Store Service.
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # Service Configuration
    service_name: str = Field(default="mcp-performance-store", env="SERVICE_NAME")
    service_version: str = Field(default="1.0.0", env="SERVICE_VERSION")
    host: str = Field(default="0.0.0.0", env="HOST")
    port: int = Field(default=5647, env="PORT")
    environment: str = Field(default="development", env="ENVIRONMENT")
    
    # Redis Configuration
    redis_host: str = Field(default="localhost", env="REDIS_HOST")
    redis_port: int = Field(default=6379, env="REDIS_PORT")
    redis_db: int = Field(default=8, env="REDIS_DB")  # Dedicated DB for performance store
    redis_password: Optional[str] = Field(default=None, env="REDIS_PASSWORD")
    redis_pool_size: int = Field(default=10, env="REDIS_POOL_SIZE")
    
    # TimescaleDB/PostgreSQL Configuration
    timescale_host: str = Field(default="localhost", env="TIMESCALE_HOST")
    timescale_port: int = Field(default=5432, env="TIMESCALE_PORT")
    timescale_database: str = Field(default="mcp_performance", env="TIMESCALE_DATABASE")
    timescale_user: str = Field(default="mcp_user", env="TIMESCALE_USER")
    timescale_password: str = Field(default="mcp_password", env="TIMESCALE_PASSWORD")
    timescale_pool_size: int = Field(default=20, env="TIMESCALE_POOL_SIZE")
    
    # Cache Configuration
    cache_ttl_seconds: int = Field(default=300, env="CACHE_TTL_SECONDS")  # 5 minutes
    cache_enabled: bool = Field(default=True, env="CACHE_ENABLED")
    
    # Analytics Configuration
    anomaly_detection_enabled: bool = Field(default=True, env="ANOMALY_DETECTION_ENABLED")
    anomaly_threshold_factor: float = Field(default=2.0, env="ANOMALY_THRESHOLD_FACTOR")
    trend_detection_enabled: bool = Field(default=True, env="TREND_DETECTION_ENABLED")
    
    # Data Retention
    execution_retention_days: int = Field(default=90, env="EXECUTION_RETENTION_DAYS")
    aggregation_retention_days: int = Field(default=365, env="AGGREGATION_RETENTION_DAYS")
    
    # API Configuration
    api_timeout: int = Field(default=30, env="API_TIMEOUT")
    max_page_size: int = Field(default=1000, env="MAX_PAGE_SIZE")
    default_page_size: int = Field(default=100, env="DEFAULT_PAGE_SIZE")
    
    # Integration URLs
    mcp_orchestrator_url: str = Field(
        default="http://localhost:5200",
        env="MCP_ORCHESTRATOR_URL"
    )
    mcp_composer_url: str = Field(
        default="http://localhost:5625",
        env="MCP_COMPOSER_URL"
    )
    mcp_gateway_url: str = Field(
        default="http://localhost:5300",
        env="MCP_GATEWAY_URL"
    )
    mcp_interpreter_url: str = Field(
        default="http://localhost:5100",
        env="MCP_INTERPRETER_URL"
    )
    mcp_infrastructure_url: str = Field(
        default="http://localhost:5500",
        env="MCP_INFRASTRUCTURE_URL"
    )
    mcp_store_url: str = Field(
        default="http://localhost:5648",
        env="MCP_STORE_URL"
    )
    mcp_logging_url: str = Field(
        default="http://localhost:5650",
        env="MCP_LOGGING_URL"
    )
    
    # Logging Configuration
    log_level: str = Field(default="INFO", env="LOG_LEVEL")
    log_format: str = Field(
        default="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        env="LOG_FORMAT"
    )
    
    # CORS Configuration
    cors_origins: list = Field(
        default=["http://localhost:3000", "http://localhost:8080"],
        env="CORS_ORIGINS"
    )
    cors_allow_credentials: bool = Field(default=True, env="CORS_ALLOW_CREDENTIALS")
    cors_allow_methods: list = Field(default=["*"], env="CORS_ALLOW_METHODS")
    cors_allow_headers: list = Field(default=["*"], env="CORS_ALLOW_HEADERS")
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @property
    def redis_url(self) -> str:
        """Construct Redis URL."""
        if self.redis_password:
            return f"redis://:{self.redis_password}@{self.redis_host}:{self.redis_port}/{self.redis_db}"
        return f"redis://{self.redis_host}:{self.redis_port}/{self.redis_db}"
    
    @property
    def timescale_url(self) -> str:
        """Construct TimescaleDB connection URL."""
        return (
            f"postgresql://{self.timescale_user}:{self.timescale_password}"
            f"@{self.timescale_host}:{self.timescale_port}/{self.timescale_database}"
        )
