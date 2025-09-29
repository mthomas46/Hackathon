"""Category domain entity.

This module contains the Category entity for document categorization
in the summarizer-hub domain.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass(frozen=True)
class CategoryId:
    """Value object for Category ID."""
    value: str

    def __post_init__(self):
        if not self.value:
            raise ValueError("Category ID cannot be empty")

    @classmethod
    def generate(cls) -> 'CategoryId':
        """Generate a new CategoryId."""
        return cls(str(uuid4()))

    def __str__(self) -> str:
        return self.value


@dataclass
class Category:
    """Category entity.

    Represents a document category with confidence scoring and metadata.
    """

    id: CategoryId
    document_id: str
    name: str
    confidence_score: float
    parent_category: Optional[str] = None
    subcategories: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        if not self.name or not self.name.strip():
            raise ValueError("Category name cannot be empty")

        if not (0.0 <= self.confidence_score <= 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")

        if not self.document_id:
            raise ValueError("Document ID is required")

    def update_confidence(self, new_score: float) -> None:
        """Update the confidence score."""
        if not (0.0 <= new_score <= 1.0):
            raise ValueError("Confidence score must be between 0.0 and 1.0")
        self.confidence_score = new_score

    def add_subcategory(self, subcategory: str) -> None:
        """Add a subcategory."""
        if subcategory not in self.subcategories:
            self.subcategories.append(subcategory)

    def remove_subcategory(self, subcategory: str) -> None:
        """Remove a subcategory."""
        if subcategory in self.subcategories:
            self.subcategories.remove(subcategory)

    def is_high_confidence(self, threshold: float = 0.8) -> bool:
        """Check if category has high confidence."""
        return self.confidence_score >= threshold

    def get_category_path(self) -> str:
        """Get the full category path including parent."""
        if self.parent_category:
            return f"{self.parent_category}/{self.name}"
        return self.name

    @classmethod
    def create(
        cls,
        document_id: str,
        name: str,
        confidence_score: float,
        parent_category: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> 'Category':
        """Factory method to create a new category."""
        category_id = CategoryId.generate()

        return cls(
            id=category_id,
            document_id=document_id,
            name=name.strip(),
            confidence_score=confidence_score,
            parent_category=parent_category,
            metadata=metadata or {},
        )
