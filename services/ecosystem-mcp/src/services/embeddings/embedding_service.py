"""
Embedding Service

Service for generating embeddings from text.
Supports both Ollama (legacy) and FastEmbed service (10-50× faster).
"""

import logging
from typing import List, Dict, Any, Optional
import time
import os

from ..models.ollama_client import get_ollama_client

logger = logging.getLogger(__name__)

# Singleton instance
_embedding_service: Optional["EmbeddingService"] = None


def get_embedding_service() -> "EmbeddingService":
    """
    Get singleton embedding service instance.
    
    Returns:
        Embedding service instance
    """
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service


class EmbeddingService:
    """
    Service for generating text embeddings.
    
    Supports two backends:
    - FastEmbed service (default, 10-50× faster)
    - Ollama (legacy fallback)
    
    Features:
    - Single and batch embedding generation
    - Automatic backend selection
    - Fallback on failure
    - Cost tracking
    - Performance optimization
    """
    
    def __init__(self, backend: str = None):
        """
        Initialize the embedding service.
        
        Args:
            backend: "service" (FastEmbed) or "ollama" (legacy)
                     If None, uses EMBEDDING_BACKEND env var (defaults to "service")
        """
        # Determine backend
        if backend is None:
            backend = os.getenv("EMBEDDING_BACKEND", "service")
        
        self.backend = backend
        self.ollama_client = None
        self.embedding_client = None
        
        if self.backend == "service":
            try:
                from .embedding_client import get_embedding_client
                self.embedding_client = get_embedding_client()
                logger.info("✅ EmbeddingService initialized with FastEmbed backend (10-50× faster)")
            except Exception as e:
                logger.warning(f"⚠️  Failed to initialize FastEmbed client, falling back to Ollama: {e}")
                self.backend = "ollama"
                self.ollama_client = get_ollama_client()
        else:
            self.ollama_client = get_ollama_client()
            logger.info("ℹ️  EmbeddingService initialized with Ollama backend (legacy)")
    
    async def generate_embedding(self, text: str) -> Dict[str, Any]:
        """
        Generate embedding for a single text.
        
        Routes to appropriate backend (FastEmbed service or Ollama).
        
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
        # Route to appropriate backend
        if self.backend == "service" and self.embedding_client:
            try:
                result = await self.embedding_client.generate_embedding(text)
                return {
                    "embedding": result["embedding"],
                    "tokens": result["tokens"],
                    "cost": 0.0,  # Local and free
                    "model": result["model"],
                    "duration": result["duration_ms"] / 1000
                }
            except Exception as e:
                logger.error(f"❌ FastEmbed service failed, falling back to Ollama: {e}")
                # Fall through to Ollama fallback
        
        # Ollama fallback
        return await self._generate_with_ollama(text)
    
    async def _generate_with_ollama(self, text: str) -> Dict[str, Any]:
        """Generate embedding using Ollama (legacy)."""
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
        batch_size: int = 32
    ) -> List[Dict[str, Any]]:
        """
        Generate embeddings for multiple texts in batches.
        
        Routes to appropriate backend:
        - FastEmbed service: TRUE batch processing (ONNX-optimized, 10-50× faster)
        - Ollama: Parallel async processing (10× faster than sequential)
        
        Args:
            texts: List of texts to generate embeddings for
            batch_size: Number of texts to process at once
        
        Returns:
            List of embedding results
        """
        if not texts:
            return []
        
        # Route to FastEmbed service for TRUE batch processing
        if self.backend == "service" and self.embedding_client:
            try:
                results = await self.embedding_client.generate_batch(texts)
                # Convert to expected format
                return [{
                    "embedding": r["embedding"],
                    "tokens": r["tokens"],
                    "cost": 0.0,
                    "model": r["model"],
                    "duration": r["duration_ms"] / 1000
                } for r in results]
            except Exception as e:
                logger.error(f"❌ FastEmbed batch failed, falling back to Ollama: {e}")
                # Fall through to Ollama fallback
        
        # Ollama fallback: parallel processing
        import asyncio
        
        results = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            logger.info(f"Processing embedding batch {i//batch_size + 1}/{(len(texts)-1)//batch_size + 1} (PARALLEL)")
            
            # ⚡ OPTIMIZED: Process entire batch in parallel instead of sequentially
            batch_tasks = [self._generate_with_ollama(text) for text in batch]
            batch_results = await asyncio.gather(*batch_tasks, return_exceptions=True)
            
            # Handle results and errors
            for idx, result in enumerate(batch_results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to process text {idx} in batch: {result}")
                    # Add placeholder for failed embedding
                    results.append({
                        "embedding": None,
                        "tokens": 0,
                        "cost": 0.0,
                        "model": "nomic-embed-text",
                        "error": str(result)
                    })
                else:
                    results.append(result)
        
        total_tokens = sum(r.get("tokens", 0) for r in results)
        total_cost = sum(r.get("cost", 0.0) for r in results)
        
        logger.info(
            f"Batch complete (PARALLEL): {len(results)} embeddings, "
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

