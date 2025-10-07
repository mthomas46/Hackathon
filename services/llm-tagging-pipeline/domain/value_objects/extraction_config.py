"""Extraction Configuration Value Object."""

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ExtractionConfig:
    """
    LLM extraction configuration value object.
    
    Configures how LLM should extract metadata from documents.
    """
    
    # Model configuration
    model_name: str = "llama2"
    temperature: float = 0.7
    max_tokens: int = 500
    
    # Extraction features
    extract_summary: bool = True
    extract_keywords: bool = True
    extract_tags: bool = True
    extract_categories: bool = True
    extract_entities: bool = True
    extract_topics: bool = True
    extract_sentiment: bool = True
    extract_complexity: bool = True
    
    # Processing options
    chunk_large_documents: bool = True
    max_chunk_size: int = 4000  # characters
    chunk_overlap: int = 200  # characters
    
    # Quality thresholds
    min_confidence: float = 0.6
    
    # Retry configuration
    max_retries: int = 3
    retry_delay_seconds: float = 1.0
    
    # Timeout
    timeout_seconds: int = 30
    
    def __post_init__(self):
        """Validate configuration."""
        if not 0.0 <= self.temperature <= 2.0:
            raise ValueError(f"Temperature must be between 0.0 and 2.0, got {self.temperature}")
        
        if not 0.0 <= self.min_confidence <= 1.0:
            raise ValueError(f"Min confidence must be between 0.0 and 1.0, got {self.min_confidence}")
        
        if self.max_tokens < 100:
            raise ValueError(f"Max tokens must be at least 100, got {self.max_tokens}")
    
    @classmethod
    def for_production(cls) -> "ExtractionConfig":
        """
        Create production configuration.
        
        Returns:
            Production-optimized extraction config
        """
        return cls(
            model_name="llama2",
            temperature=0.5,  # Lower temperature for consistency
            max_tokens=500,
            min_confidence=0.7,  # Higher confidence threshold
            max_retries=5,
        )
    
    @classmethod
    def for_development(cls) -> "ExtractionConfig":
        """
        Create development configuration.
        
        Returns:
            Development-optimized extraction config
        """
        return cls(
            model_name="llama2",
            temperature=0.7,
            max_tokens=300,
            min_confidence=0.5,  # Lower threshold for testing
            max_retries=2,
            timeout_seconds=15,  # Shorter timeout
        )
    
    @classmethod
    def for_fast_processing(cls) -> "ExtractionConfig":
        """
        Create fast processing configuration.
        
        Returns:
            Fast-processing extraction config
        """
        return cls(
            model_name="llama2",
            temperature=0.8,
            max_tokens=200,
            extract_entities=False,  # Skip expensive operations
            extract_complexity=False,
            chunk_large_documents=False,
            min_confidence=0.5,
            max_retries=1,
            timeout_seconds=10,
        )

