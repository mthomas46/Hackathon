"""Module initialization for confluence-hub modules."""

from .confluence_client import ConfluenceClient
from .mongodb_client import MongoDBClient
from .content_converter import confluence_to_markdown, process_confluence_page
from .openai_service import OpenAIService
from .vector_search_service import VectorSearchService, DocumentVector, SearchMatch
from .embeddings_manager import EmbeddingsManager

__all__ = [
    'ConfluenceClient',
    'MongoDBClient', 
    'confluence_to_markdown',
    'process_confluence_page',
    'OpenAIService',
    'VectorSearchService',
    'DocumentVector',
    'SearchMatch',
    'EmbeddingsManager',
]