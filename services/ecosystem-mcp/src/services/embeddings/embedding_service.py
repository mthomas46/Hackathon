"""
Embedding Service

Service for generating embeddings from text using Ollama.
Handles batching, retry logic, and cost tracking.
"""

import logging
from typing import List, Dict, Any
import time

from ..models.ollama_client import get_ollama_client

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Service for generating text embeddings.
    
    Features:
    - Single and batch embedding generation
    - Automatic retry with exponential backoff
    - Cost tracking
    - Performance optimization
    - Circuit breaker integration (via OllamaClient)
    """
    
    def __init__(self):
        """Initialize the embedding service."""
        self.ollama_client = get_ollama_client()
        logger.info("EmbeddingService initialized")
    
    async def generate_embedding(self, text: str) -> Dict[str, Any]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to generate embedding for
        
        Returns:
            Dict with:
            {
                "embedding": List[float],
                "tokens": int,
                "cost": float,
                "model": str
            }
        """
        start_time = time.time()
        
        try:
            # Truncate very long text (Ollama has limits)
            max_chars = 8000  # ~2000 tokens
            if len(text) > max_chars:
                logger.warning(f"Text too long ({len(text)} chars), truncating to {max_chars}")
                text = text[:max_chars]
            
            # Generate embedding via Ollama
            embedding = await self.ollama_client.embed(text)
            
            if not embedding:
                raise ValueError("Ollama returned empty embedding")
            
            # Estimate tokens (rough approximation)
            tokens = self._estimate_tokens(text)
            
            # Calculate cost (Ollama is free, but track for metrics)
            cost = 0.0  # Ollama is local and free
            
            duration = time.time() - start_time
            logger.debug(f"Generated embedding: {len(embedding)} dimensions, {tokens} tokens, {duration:.2f}s")
            
            return {
                "embedding": embedding,
                "tokens": tokens,
                "cost": cost,
                "model": "nomic-embed-text",
                "duration": duration
            }
        
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}", exc_info=True)
            raise
    
    async def generate_batch(
        self,
        texts: List[str],
        batch_size: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of texts to generate embeddings for
            batch_size: Number of texts to process at once
        
        Returns:
            List of embedding results
        """
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.info(f"Processing embedding batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1}")
            
            # Process batch
            for text in batch:
                try:
                    result = await self.generate_embedding(text)
                    results.append(result)
                except Exception as e:
                    logger.error(f"Failed to process text in batch: {e}")
                    # Add placeholder for failed embedding
                    results.append({
                        "embedding": None,
                        "tokens": 0,
                        "cost": 0.0,
                        "model": "nomic-embed-text",
                        "error": str(e)
                    })
        
        total_tokens = sum(r.get("tokens", 0) for r in results)
        total_cost = sum(r.get("cost", 0.0) for r in results)
        
        logger.info(
            f"Batch complete: {len(results)} embeddings, "
            f"{total_tokens} tokens, ${total_cost:.4f} cost"
        )
        
        return results
    
    def _estimate_tokens(self, text: str) -> int:
        """
        Estimate token count for text.
        
        Uses simple heuristic: ~4 characters per token.
        
        Args:
            text: Text to estimate tokens for
        
        Returns:
            Estimated token count
        """
        return len(text) // 4

