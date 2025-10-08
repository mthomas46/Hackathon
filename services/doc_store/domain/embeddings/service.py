"""Embedding generation service for semantic search."""

import logging
from typing import List, Dict, Any, Optional
import asyncio

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating and managing document embeddings."""
    
    def __init__(self):
        """Initialize embedding service."""
        self.model_name = "sentence-transformers/all-MiniLM-L6-v2"
        self._generator = None
    
    def _get_generator(self):
        """Lazy load the embedding generator."""
        if self._generator is None:
            try:
                # Use sentence-transformers directly
                from sentence_transformers import SentenceTransformer
                self._generator = SentenceTransformer(self.model_name)
                logger.info(f"✅ Loaded embedding model: {self.model_name}")
            except ImportError as e:
                logger.error(f"❌ Failed to import sentence-transformers: {e}")
                raise RuntimeError(
                    "Embedding generation requires sentence-transformers. "
                    "Install with: pip install sentence-transformers"
                )
            except Exception as e:
                logger.error(f"❌ Failed to load embedding model: {e}")
                raise RuntimeError(f"Failed to initialize embedding model: {str(e)}")
        return self._generator
    
    async def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Input text
        
        Returns:
            Embedding vector
        """
        generator = self._get_generator()
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            generator.encode,
            text
        )
        
        return embedding.tolist()
    
    async def generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 32
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.
        
        Args:
            texts: List of input texts
            batch_size: Batch size for processing
        
        Returns:
            List of embedding vectors
        """
        generator = self._get_generator()
        
        # Run in thread pool (sentence-transformers handles batching internally)
        loop = asyncio.get_event_loop()
        # Use functools.partial to pass batch_size as keyword argument
        from functools import partial
        encode_func = partial(generator.encode, batch_size=batch_size, convert_to_numpy=True)
        embeddings = await loop.run_in_executor(
            None,
            encode_func,
            texts
        )
        
        # Convert numpy arrays to lists
        return [emb.tolist() for emb in embeddings]
    
    async def embed_document(
        self,
        document_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate and store embedding for a document.
        
        Args:
            document_id: Document ID
            content: Document content
            metadata: Optional metadata
        
        Returns:
            Embedding metadata
        """
        from ...db.queries import insert_document_vector
        
        # Generate embedding
        embedding = await self.generate_embedding(content)
        
        # Store in database
        vector_id = insert_document_vector(
            document_id=document_id,
            embedding=embedding,
            vector_model=self.model_name,
            metadata=metadata
        )
        
        logger.info(f"Generated embedding for document {document_id}")
        
        return {
            "vector_id": vector_id,
            "document_id": document_id,
            "vector_model": self.model_name,
            "embedding_dimension": len(embedding),
        }
    
    async def embed_documents_batch(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 32
    ) -> List[Dict[str, Any]]:
        """
        Generate and store embeddings for multiple documents.
        
        Args:
            documents: List of documents with 'id' and 'content'
            batch_size: Batch size for processing
        
        Returns:
            List of embedding metadata
        """
        from ...db.queries import insert_document_vector
        
        # Extract texts
        texts = [doc.get("content", "") for doc in documents]
        
        # Generate embeddings in batch
        embeddings = await self.generate_embeddings_batch(texts, batch_size)
        
        # Store embeddings
        results = []
        for doc, embedding in zip(documents, embeddings):
            try:
                vector_id = insert_document_vector(
                    document_id=doc["id"],
                    embedding=embedding,
                    vector_model=self.model_name,
                    metadata=doc.get("metadata")
                )
                
                results.append({
                    "vector_id": vector_id,
                    "document_id": doc["id"],
                    "vector_model": self.model_name,
                    "embedding_dimension": len(embedding),
                    "success": True
                })
            except Exception as e:
                logger.error(f"Failed to store embedding for {doc['id']}: {e}")
                results.append({
                    "document_id": doc["id"],
                    "success": False,
                    "error": str(e)
                })
        
        logger.info(f"Generated embeddings for {len(results)} documents")
        
        return results
    
    async def semantic_search(
        self,
        query: str,
        limit: int = 50,
        min_similarity: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using query text.
        
        Args:
            query: Search query
            limit: Maximum results
            min_similarity: Minimum similarity threshold
        
        Returns:
            List of documents with similarity scores
        """
        from ...db.queries import semantic_search_documents
        
        # Generate query embedding
        query_embedding = await self.generate_embedding(query)
        
        # Search
        results = semantic_search_documents(
            query_embedding=query_embedding,
            limit=limit,
            vector_model=self.model_name,
            min_similarity=min_similarity
        )
        
        return results
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the embedding model.
        
        Returns:
            Model information
        """
        generator = self._get_generator()
        model_info = generator.get_model_info()
        
        return {
            "name": model_info.name,
            "dimensions": model_info.dimensions,
            "max_sequence_length": model_info.max_sequence_length,
            "model_size_mb": round(model_info.model_size_mb, 2),
            "language": model_info.language
        }


# Singleton instance
_embedding_service = None


def get_embedding_service() -> EmbeddingService:
    """Get or create embedding service singleton."""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service

