"""Vector search service for managing embeddings in memory."""

import asyncio
import logging
import math
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class DocumentVector:
    """Represents a document with its embedding vector."""
    document_id: str
    embedding: List[float]
    title: str
    confluence_page_id: str


@dataclass
class SearchMatch:
    """Represents a search result match."""
    document_id: str
    score: float
    title: str
    confluence_page_id: str


class VectorSearchService:
    """Service for managing document embeddings and performing vector similarity search."""
    
    def __init__(self):
        """Initialize the vector search service."""
        self.vector_cache: Dict[str, DocumentVector] = {}
        self.initialized = False
        
    async def initialize(self, mongodb_client) -> None:
        """Initialize the vector search service by loading embeddings from MongoDB.
        
        Args:
            mongodb_client: MongoDB client instance
        """
        logger.info("Initializing vector search service...")
        
        try:
            # Clear existing cache
            self.vector_cache.clear()
            
            # Load all documents with embeddings from MongoDB
            documents = await mongodb_client.get_pages_with_embeddings()
            
            # Populate cache
            for doc in documents:
                if doc.get('embedding') and len(doc['embedding']) > 0:
                    # Validate embedding dimension (should be 1536 for text-embedding-3-small)
                    if len(doc['embedding']) == 1536:
                        self.vector_cache[str(doc['_id'])] = DocumentVector(
                            document_id=str(doc['_id']),
                            embedding=doc['embedding'],
                            title=doc['title'],
                            confluence_page_id=doc['confluence_page_id']
                        )
                    else:
                        logger.warning(f"Document {doc['_id']} has invalid embedding dimension: {len(doc['embedding'])}")
            
            self.initialized = True
            logger.info(f"Vector search initialized with {len(self.vector_cache)} document embeddings")
            
        except Exception as e:
            logger.error(f"Error initializing vector search: {str(e)}")
            raise Exception(f"Failed to initialize vector search: {str(e)}")
    
    def cosine_similarity(self, a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors.
        
        Args:
            a: First vector
            b: Second vector
            
        Returns:
            Cosine similarity score between -1 and 1
        """
        if len(a) != len(b):
            raise ValueError("Vectors must have the same length")
        
        dot_product = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        
        # Avoid division by zero
        if norm_a == 0 or norm_b == 0:
            return 0.0
        
        return dot_product / (norm_a * norm_b)
    
    async def search_similar(
        self, 
        query_embedding: List[float], 
        limit: int = 5, 
        min_score: float = 0.15
    ) -> List[SearchMatch]:
        """Search for documents similar to the query embedding.
        
        Args:
            query_embedding: Query embedding vector
            limit: Maximum number of results to return
            min_score: Minimum similarity score threshold
            
        Returns:
            List of search matches sorted by similarity score
        """
        if not self.initialized:
            raise ValueError("Vector search service not initialized. Call initialize() first.")
        
        if len(query_embedding) != 1536:
            raise ValueError("Query embedding must have exactly 1536 dimensions")
        
        results: List[SearchMatch] = []
        
        # Calculate similarity for all cached documents
        for doc_id, doc_vector in self.vector_cache.items():
            try:
                score = self.cosine_similarity(query_embedding, doc_vector.embedding)
                
                if score >= min_score:
                    results.append(SearchMatch(
                        document_id=doc_id,
                        score=score,
                        title=doc_vector.title,
                        confluence_page_id=doc_vector.confluence_page_id
                    ))
                    
            except Exception as e:
                logger.error(f"Error calculating similarity for document {doc_id}: {str(e)}")
                continue
        
        # Sort by score in descending order and limit results
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]
    
    async def update_vector(
        self, 
        document_id: str, 
        embedding: List[float], 
        title: str, 
        confluence_page_id: str
    ) -> None:
        """Update or add a vector to the cache.
        
        Args:
            document_id: Document ID
            embedding: Embedding vector
            title: Document title
            confluence_page_id: Confluence page ID
        """
        if len(embedding) != 1536:
            raise ValueError("Embedding must have exactly 1536 dimensions")
        
        self.vector_cache[document_id] = DocumentVector(
            document_id=document_id,
            embedding=embedding,
            title=title,
            confluence_page_id=confluence_page_id
        )
        
        logger.info(f"Updated vector cache for document: {title}")
    
    def remove_vector(self, document_id: str) -> None:
        """Remove a vector from the cache.
        
        Args:
            document_id: Document ID to remove
        """
        if document_id in self.vector_cache:
            del self.vector_cache[document_id]
            logger.info(f"Removed vector for document: {document_id}")
    
    def get_cache_size(self) -> int:
        """Get the number of vectors in cache.
        
        Returns:
            Number of cached vectors
        """
        return len(self.vector_cache)
    
    def is_initialized(self) -> bool:
        """Check if the service is initialized.
        
        Returns:
            True if initialized, False otherwise
        """
        return self.initialized
    
    def get_memory_usage(self) -> str:
        """Estimate memory usage of the vector cache.
        
        Returns:
            Estimated memory usage as a string
        """
        # Estimate memory usage (each embedding is ~6KB: 1536 floats * 4 bytes)
        estimated_bytes = len(self.vector_cache) * 1536 * 4
        estimated_mb = estimated_bytes / (1024 * 1024)
        return f"{estimated_mb:.2f} MB"
    
    async def refresh(self, mongodb_client) -> None:
        """Refresh the vector cache by reloading from MongoDB.
        
        Args:
            mongodb_client: MongoDB client instance
        """
        logger.info("Refreshing vector cache...")
        self.initialized = False
        await self.initialize(mongodb_client)
    
    def get_stats(self) -> Dict[str, any]:
        """Get statistics about the vector cache.
        
        Returns:
            Dictionary with cache statistics
        """
        return {
            "cache_size": self.get_cache_size(),
            "memory_usage": self.get_memory_usage(),
            "initialized": self.is_initialized(),
            "embedding_dimension": 1536
        }