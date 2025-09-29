"""External service configuration management."""

import os
from typing import Optional, Dict, Any
from dataclasses import dataclass


@dataclass
class ExternalServiceConfig:
    """Configuration for external services."""

    # OpenAI configuration
    openai_api_key: Optional[str] = None
    openai_model: str = "gpt-4"
    openai_max_tokens: int = 2000
    openai_temperature: float = 0.7

    # Semantic analysis configuration
    semantic_model_path: Optional[str] = None
    semantic_batch_size: int = 32
    semantic_similarity_threshold: float = 0.8

    # Sentiment analysis configuration
    sentiment_model: str = "cardiffnlp/twitter-roberta-base-sentiment-latest"
    sentiment_confidence_threshold: float = 0.6

    # General external service settings
    request_timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0

    @classmethod
    def from_env(cls) -> 'ExternalServiceConfig':
        """Create configuration from environment variables."""
        return cls(
            openai_api_key=os.getenv('OPENAI_API_KEY'),
            openai_model=os.getenv('OPENAI_MODEL', 'gpt-4'),
            openai_max_tokens=int(os.getenv('OPENAI_MAX_TOKENS', '2000')),
            openai_temperature=float(os.getenv('OPENAI_TEMPERATURE', '0.7')),
            semantic_model_path=os.getenv('SEMANTIC_MODEL_PATH'),
            semantic_batch_size=int(os.getenv('SEMANTIC_BATCH_SIZE', '32')),
            semantic_similarity_threshold=float(os.getenv('SEMANTIC_SIMILARITY_THRESHOLD', '0.8')),
            sentiment_model=os.getenv('SENTIMENT_MODEL', 'cardiffnlp/twitter-roberta-base-sentiment-latest'),
            sentiment_confidence_threshold=float(os.getenv('SENTIMENT_CONFIDENCE_THRESHOLD', '0.6')),
            request_timeout=int(os.getenv('EXTERNAL_REQUEST_TIMEOUT', '30')),
            max_retries=int(os.getenv('EXTERNAL_MAX_RETRIES', '3')),
            retry_delay=float(os.getenv('EXTERNAL_RETRY_DELAY', '1.0'))
        )

    def get_openai_config(self) -> Dict[str, Any]:
        """Get OpenAI configuration."""
        return {
            'api_key': self.openai_api_key,
            'model': self.openai_model,
            'max_tokens': self.openai_max_tokens,
            'temperature': self.openai_temperature
        }

    def get_semantic_config(self) -> Dict[str, Any]:
        """Get semantic analysis configuration."""
        return {
            'model_path': self.semantic_model_path,
            'batch_size': self.semantic_batch_size,
            'similarity_threshold': self.semantic_similarity_threshold
        }

    def get_sentiment_config(self) -> Dict[str, Any]:
        """Get sentiment analysis configuration."""
        return {
            'model': self.sentiment_model,
            'confidence_threshold': self.sentiment_confidence_threshold
        }

    def get_retry_config(self) -> Dict[str, Any]:
        """Get retry configuration."""
        return {
            'max_retries': self.max_retries,
            'retry_delay': self.retry_delay,
            'timeout': self.request_timeout
        }

    def validate(self) -> list[str]:
        """Validate configuration."""
        errors = []

        # Validate OpenAI config if API key is provided
        if self.openai_api_key:
            if not self.openai_model:
                errors.append("OpenAI model must be specified when API key is provided")
            if self.openai_max_tokens < 1:
                errors.append("OpenAI max tokens must be >= 1")
            if not 0.0 <= self.openai_temperature <= 2.0:
                errors.append("OpenAI temperature must be between 0.0 and 2.0")

        # Validate semantic config
        if self.semantic_batch_size < 1:
            errors.append("Semantic batch size must be >= 1")
        if not 0.0 <= self.semantic_similarity_threshold <= 1.0:
            errors.append("Semantic similarity threshold must be between 0.0 and 1.0")

        # Validate sentiment config
        if not self.sentiment_model:
            errors.append("Sentiment model must be specified")
        if not 0.0 <= self.sentiment_confidence_threshold <= 1.0:
            errors.append("Sentiment confidence threshold must be between 0.0 and 1.0")

        # Validate general settings
        if self.request_timeout < 1:
            errors.append("Request timeout must be >= 1 second")
        if self.max_retries < 0:
            errors.append("Max retries must be >= 0")
        if self.retry_delay < 0:
            errors.append("Retry delay must be >= 0")

        return errors

    def is_openai_enabled(self) -> bool:
        """Check if OpenAI is enabled."""
        return self.openai_api_key is not None

    def is_semantic_enabled(self) -> bool:
        """Check if semantic analysis is enabled."""
        return True  # Always enabled for basic functionality

    def is_sentiment_enabled(self) -> bool:
        """Check if sentiment analysis is enabled."""
        return True  # Always enabled for basic functionality
