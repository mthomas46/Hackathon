"""Repository interfaces for summarizer-hub service."""

from .document_repository import IDocumentRepository
from .summary_repository import ISummaryRepository
from .category_repository import ICategoryRepository
from .recommendation_repository import IRecommendationRepository

__all__ = [
    "IDocumentRepository",
    "ISummaryRepository",
    "ICategoryRepository",
    "IRecommendationRepository",
]
