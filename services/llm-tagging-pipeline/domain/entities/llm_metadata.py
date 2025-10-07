"""LLM Metadata Entity."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any


@dataclass
class LLMMetadata:
    """
    LLM-extracted metadata entity.
    
    Encapsulates all metadata extracted by LLM for a document.
    Value object that can be attached to documents.
    """
    
    # Core metadata
    summary: str = ""
    keywords: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    
    # Advanced metadata
    topics: List[str] = field(default_factory=list)
    entities: List[Dict[str, str]] = field(default_factory=list)
    sentiment: Optional[str] = None
    complexity_score: Optional[float] = None
    
    # Confidence scores
    summary_confidence: float = 0.0
    keywords_confidence: float = 0.0
    tags_confidence: float = 0.0
    categories_confidence: float = 0.0
    
    # Extraction metadata
    model_name: str = ""
    extraction_timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    tokens_used: int = 0
    processing_time_seconds: float = 0.0
    
    # Additional data
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate metadata."""
        if not self.summary:
            raise ValueError("Summary is required")
        if not self.model_name:
            raise ValueError("Model name is required")
    
    def get_overall_confidence(self) -> float:
        """
        Calculate overall confidence score.
        
        Returns:
            Average confidence across all metadata types
        """
        confidences = [
            self.summary_confidence,
            self.keywords_confidence,
            self.tags_confidence,
            self.categories_confidence,
        ]
        return sum(confidences) / len(confidences)
    
    def is_high_quality(self, threshold: float = 0.7) -> bool:
        """
        Check if metadata is high quality.
        
        Args:
            threshold: Confidence threshold (0.0 - 1.0)
            
        Returns:
            True if overall confidence >= threshold
        """
        return self.get_overall_confidence() >= threshold
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "summary": self.summary,
            "keywords": self.keywords,
            "tags": self.tags,
            "categories": self.categories,
            "topics": self.topics,
            "entities": self.entities,
            "sentiment": self.sentiment,
            "complexity_score": self.complexity_score,
            "summary_confidence": self.summary_confidence,
            "keywords_confidence": self.keywords_confidence,
            "tags_confidence": self.tags_confidence,
            "categories_confidence": self.categories_confidence,
            "model_name": self.model_name,
            "extraction_timestamp": self.extraction_timestamp.isoformat(),
            "tokens_used": self.tokens_used,
            "processing_time_seconds": self.processing_time_seconds,
            "metadata": self.metadata,
        }

