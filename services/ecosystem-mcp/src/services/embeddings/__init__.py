"""
Embedding services for document vectorization.

This package contains services for generating embeddings from text
using various models (primarily Ollama).
"""

from .embedding_service import EmbeddingService, get_embedding_service

__all__ = [
    "EmbeddingService",
    "get_embedding_service",
]

