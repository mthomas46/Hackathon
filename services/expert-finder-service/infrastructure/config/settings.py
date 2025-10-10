"""
Service configuration with type-safe settings.

Uses pydantic-settings for automatic environment variable loading
and type validation. This replaces 30+ lines of manual os.getenv() calls
throughout the codebase (MANDATORY from Phase 2.7).

Benefits:
- Type safety (validates types on startup)
- Automatic .env file loading
- Clear defaults
- Self-documenting
- Validation on startup (fails fast)
"""

from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

from utils.constants import (
    SERVICE_NAME,
    SERVICE_VERSION,
    DEFAULT_SERVICE_PORT,
    DEFAULT_ROLE_WEIGHT,
    DEFAULT_TOPIC_WEIGHT,
    DEFAULT_SERVICE_WEIGHT,
    DEFAULT_DOCUMENT_WEIGHT,
    DEFAULT_USER_STORE_URL,
    DEFAULT_DOC_STORE_URL,
    DEFAULT_SERVICE_STORE_URL,
    DEFAULT_TIMEOUT_SECONDS,
    DEFAULT_RETRY_ATTEMPTS,
    SME_MIN_DOCUMENTS,
    SME_MIN_SCORE,
    DEFAULT_RESULTS,
    MAX_RESULTS,
    DEFAULT_CACHE_TTL_SECONDS,
    DEFAULT_CACHE_MAX_SIZE,
)


class Settings(BaseSettings):
    """
    Service configuration with type-safe settings.
    
    Automatically loads from environment variables and .env files.
    All settings are validated on startup.
    
    Environment Variable Naming:
    - Fields are converted to UPPERCASE
    - Example: service_name → SERVICE_NAME env var
    - Example: user_store_url → USER_STORE_URL env var
    """
    
    # ========================================================================
    # Service Configuration
    # ========================================================================
    
    service_name: str = SERVICE_NAME
    service_version: str = SERVICE_VERSION
    service_port: int = DEFAULT_SERVICE_PORT
    
    # Environment (dev, test, staging, prod)
    environment: str = "dev"
    
    # Debug mode
    debug: bool = False
    
    # ========================================================================
    # External Service URLs
    # ========================================================================
    
    user_store_url: str = DEFAULT_USER_STORE_URL
    doc_store_url: str = DEFAULT_DOC_STORE_URL
    service_store_url: str = DEFAULT_SERVICE_STORE_URL
    
    # Optional: LLM Gateway for advanced query understanding
    llm_gateway_url: Optional[str] = None
    
    # ========================================================================
    # Scoring Weights
    # ========================================================================
    
    role_weight: float = DEFAULT_ROLE_WEIGHT
    topic_weight: float = DEFAULT_TOPIC_WEIGHT
    service_weight: float = DEFAULT_SERVICE_WEIGHT
    document_weight: float = DEFAULT_DOCUMENT_WEIGHT
    
    # ========================================================================
    # HTTP Configuration
    # ========================================================================
    
    http_timeout: float = DEFAULT_TIMEOUT_SECONDS
    http_retry_attempts: int = DEFAULT_RETRY_ATTEMPTS
    http_retry_min_wait: float = 1.0  # Minimum wait between retries (seconds)
    http_retry_max_wait: float = 10.0  # Maximum wait between retries (seconds)
    
    # Connection pooling
    http_pool_connections: int = 10
    http_pool_maxsize: int = 10
    
    # ========================================================================
    # SME Thresholds
    # ========================================================================
    
    sme_min_documents: int = SME_MIN_DOCUMENTS
    sme_min_score: float = SME_MIN_SCORE
    
    # ========================================================================
    # Results Configuration
    # ========================================================================
    
    default_results: int = DEFAULT_RESULTS
    max_results: int = MAX_RESULTS
    
    # ========================================================================
    # Cache Configuration
    # ========================================================================
    
    cache_enabled: bool = True
    cache_ttl_seconds: int = DEFAULT_CACHE_TTL_SECONDS
    cache_max_size: int = DEFAULT_CACHE_MAX_SIZE
    
    # ========================================================================
    # Logging Configuration
    # ========================================================================
    
    log_level: str = "INFO"
    log_format: str = "json"  # json or text
    log_collector_url: Optional[str] = None
    
    # ========================================================================
    # CORS Configuration
    # ========================================================================
    
    cors_origins: list[str] = ["*"]  # In production, set specific origins
    cors_allow_credentials: bool = True
    cors_allow_methods: list[str] = ["*"]
    cors_allow_headers: list[str] = ["*"]
    
    # ========================================================================
    # Pydantic Settings Configuration
    # ========================================================================
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # Allow lowercase env vars
        extra="ignore"  # Ignore extra env vars not defined here
    )
    
    # ========================================================================
    # Validation Methods
    # ========================================================================
    
    def validate_weights(self) -> None:
        """
        Validate that scoring weights sum to approximately 1.0.
        
        Raises:
            ValueError: If weights don't sum to ~1.0
        """
        total = (
            self.role_weight +
            self.topic_weight +
            self.service_weight +
            self.document_weight
        )
        
        if not 0.95 <= total <= 1.05:  # Allow 5% tolerance
            raise ValueError(
                f"Scoring weights must sum to ~1.0, got {total:.2f}. "
                f"(role={self.role_weight}, topic={self.topic_weight}, "
                f"service={self.service_weight}, document={self.document_weight})"
            )
    
    def validate_thresholds(self) -> None:
        """
        Validate that score thresholds are in valid range.
        
        Raises:
            ValueError: If thresholds are invalid
        """
        if not 0.0 <= self.sme_min_score <= 1.0:
            raise ValueError(
                f"SME minimum score must be between 0.0 and 1.0, got {self.sme_min_score}"
            )
        
        if self.sme_min_documents < 0:
            raise ValueError(
                f"SME minimum documents must be non-negative, got {self.sme_min_documents}"
            )
    
    def model_post_init(self, __context) -> None:
        """
        Run validation after model initialization.
        
        This is called automatically by Pydantic after the settings
        are loaded and validated.
        """
        self.validate_weights()
        self.validate_thresholds()


@lru_cache
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses lru_cache to ensure we only create one Settings instance
    and reuse it throughout the application.
    
    Returns:
        Settings: Singleton settings instance
        
    Examples:
        >>> settings = get_settings()
        >>> settings.service_name
        'expert-finder-service'
        >>> settings.service_port
        5160
    """
    return Settings()


# Convenience: Create a module-level settings instance
settings = get_settings()

