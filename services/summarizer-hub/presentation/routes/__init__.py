"""Presentation layer routes."""

from .document_routes import router as document_router
from .summarization_routes import router as summarization_router

__all__ = [
    "document_router",
    "summarization_router",
]
