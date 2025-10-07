"""Document Entity with LLM Metadata."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from uuid import uuid4


@dataclass
class Document:
    """
    Document entity with LLM-extracted metadata.
    
    Represents a document that needs tagging or has been tagged with LLM metadata.
    Aggregate root for tagging operations.
    """
    
    # Identity
    document_id: str = field(default_factory=lambda: str(uuid4()))
    title: str = ""
    content: str = ""
    
    # Source information
    source_type: str = ""  # "docs_directory", "github", "confluence", etc.
    source_id: str = ""
    source_url: Optional[str] = None
    
    # LLM-extracted metadata
    summary: Optional[str] = None
    keywords: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    categories: List[str] = field(default_factory=list)
    entities: List[Dict[str, str]] = field(default_factory=list)  # Named entities
    topics: List[str] = field(default_factory=list)
    sentiment: Optional[str] = None  # "positive", "negative", "neutral"
    complexity_score: Optional[float] = None  # 0.0 - 1.0
    
    # Tagging metadata
    tagged: bool = False
    tagging_model: Optional[str] = None
    tagging_confidence: Optional[float] = None
    tagging_timestamp: Optional[datetime] = None
    
    # Validation
    validated: bool = False
    validation_errors: List[str] = field(default_factory=list)
    
    # Timestamps
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: Optional[datetime] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate document."""
        if not self.document_id:
            self.document_id = str(uuid4())
        if not self.title:
            raise ValueError("Document title is required")
        if not self.content:
            raise ValueError("Document content is required")
    
    def mark_as_tagged(
        self,
        model: str,
        confidence: float
    ) -> None:
        """
        Mark document as tagged.
        
        Args:
            model: LLM model used for tagging
            confidence: Tagging confidence score
        """
        self.tagged = True
        self.tagging_model = model
        self.tagging_confidence = confidence
        self.tagging_timestamp = datetime.now(timezone.utc)
        self.updated_at = datetime.now(timezone.utc)
    
    def add_keywords(self, keywords: List[str]) -> None:
        """
        Add keywords to document.
        
        Args:
            keywords: List of keywords to add
        """
        for keyword in keywords:
            if keyword not in self.keywords:
                self.keywords.append(keyword)
        self.updated_at = datetime.now(timezone.utc)
    
    def add_tags(self, tags: List[str]) -> None:
        """
        Add tags to document.
        
        Args:
            tags: List of tags to add
        """
        for tag in tags:
            if tag not in self.tags:
                self.tags.append(tag)
        self.updated_at = datetime.now(timezone.utc)
    
    def add_categories(self, categories: List[str]) -> None:
        """
        Add categories to document.
        
        Args:
            categories: List of categories to add
        """
        for category in categories:
            if category not in self.categories:
                self.categories.append(category)
        self.updated_at = datetime.now(timezone.utc)
    
    def add_entity(self, entity_type: str, entity_value: str) -> None:
        """
        Add named entity to document.
        
        Args:
            entity_type: Type of entity (person, organization, location, etc.)
            entity_value: Entity value
        """
        entity = {"type": entity_type, "value": entity_value}
        if entity not in self.entities:
            self.entities.append(entity)
        self.updated_at = datetime.now(timezone.utc)
    
    def set_summary(self, summary: str) -> None:
        """
        Set document summary.
        
        Args:
            summary: Document summary
        """
        self.summary = summary
        self.updated_at = datetime.now(timezone.utc)
    
    def set_sentiment(self, sentiment: str) -> None:
        """
        Set document sentiment.
        
        Args:
            sentiment: Sentiment (positive, negative, neutral)
        """
        if sentiment not in ("positive", "negative", "neutral"):
            raise ValueError(f"Invalid sentiment: {sentiment}")
        self.sentiment = sentiment
        self.updated_at = datetime.now(timezone.utc)
    
    def set_complexity_score(self, score: float) -> None:
        """
        Set complexity score.
        
        Args:
            score: Complexity score (0.0 - 1.0)
        """
        if not 0.0 <= score <= 1.0:
            raise ValueError(f"Complexity score must be between 0.0 and 1.0, got {score}")
        self.complexity_score = score
        self.updated_at = datetime.now(timezone.utc)
    
    def validate(self) -> bool:
        """
        Validate document metadata.
        
        Returns:
            True if valid, False otherwise
        """
        self.validation_errors = []
        
        # Check minimum metadata
        if not self.keywords and not self.tags:
            self.validation_errors.append("Document must have at least keywords or tags")
        
        if not self.summary:
            self.validation_errors.append("Document must have a summary")
        
        # Check tagging metadata
        if self.tagged and not self.tagging_model:
            self.validation_errors.append("Tagged document must have tagging_model")
        
        if self.tagged and self.tagging_confidence is None:
            self.validation_errors.append("Tagged document must have tagging_confidence")
        
        # Check confidence score range
        if self.tagging_confidence is not None:
            if not 0.0 <= self.tagging_confidence <= 1.0:
                self.validation_errors.append(
                    f"Tagging confidence must be between 0.0 and 1.0, got {self.tagging_confidence}"
                )
        
        self.validated = len(self.validation_errors) == 0
        return self.validated
    
    def get_all_tags(self) -> List[str]:
        """
        Get all tags (keywords + tags + categories + topics).
        
        Returns:
            Combined list of all tags
        """
        all_tags = set()
        all_tags.update(self.keywords)
        all_tags.update(self.tags)
        all_tags.update(self.categories)
        all_tags.update(self.topics)
        return sorted(list(all_tags))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "document_id": self.document_id,
            "title": self.title,
            "content": self.content,
            "source_type": self.source_type,
            "source_id": self.source_id,
            "source_url": self.source_url,
            "summary": self.summary,
            "keywords": self.keywords,
            "tags": self.tags,
            "categories": self.categories,
            "entities": self.entities,
            "topics": self.topics,
            "sentiment": self.sentiment,
            "complexity_score": self.complexity_score,
            "tagged": self.tagged,
            "tagging_model": self.tagging_model,
            "tagging_confidence": self.tagging_confidence,
            "tagging_timestamp": self.tagging_timestamp.isoformat() if self.tagging_timestamp else None,
            "validated": self.validated,
            "validation_errors": self.validation_errors,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata,
        }

