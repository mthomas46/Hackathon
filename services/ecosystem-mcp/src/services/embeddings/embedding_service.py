"""
Embedding Service

Service for generating embeddings from text.
Supports both Ollama (legacy) and FastEmbed service (10-50× faster).
"""

import logging
from typing import List, Dict, Any, Optional
import time
import os
import httpx

from ..models.ollama_client import get_ollama_client
from ...utils.circuit_breaker import CircuitBreakerOpenError
from ...utils.cache_decorator import cache

logger = logging.getLogger(__name__)

# Singleton instance
_embedding_service: Optional["EmbeddingService"] = None


def chunk_text(text: str, max_chars: int = 7000, overlap: int = 500) -> List[str]:
    """
    Split text into overlapping chunks for embedding generation.
    
    Args:
        text: Text to chunk
        max_chars: Maximum characters per chunk (default 7000, leaves buffer for 8000 limit)
        overlap: Number of overlapping characters between chunks (default 500)
    
    Returns:
        List of text chunks
    """
    if len(text) <= max_chars:
        return [text]
    
    chunks = []
    start = 0
    
    while start < len(text):
        end = start + max_chars
        
        # If this is not the last chunk, try to break at a sentence or word boundary
        if end < len(text):
            # Look for sentence boundary (. ! ?)
            sentence_break = max(
                text.rfind('. ', start, end),
                text.rfind('! ', start, end),
                text.rfind('? ', start, end)
            )
            
            if sentence_break > start + max_chars // 2:  # Found a reasonable break point
                end = sentence_break + 1
            else:
                # Fall back to word boundary
                word_break = text.rfind(' ', start, end)
                if word_break > start + max_chars // 2:
                    end = word_break
        
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        
        # Move start forward, with overlap
        start = end - overlap if end < len(text) else end
    
    logger.debug(f"📄 Split text into {len(chunks)} chunks (total: {len(text)} chars)")
    return chunks


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
        self.embedding_client = None
        
        # ALWAYS initialize Ollama client as fallback (even when using FastEmbed)
        try:
            self.ollama_client = get_ollama_client()
            logger.debug("✅ Ollama client initialized as fallback")
        except Exception as e:
            logger.warning(f"⚠️  Failed to initialize Ollama client: {e}")
            self.ollama_client = None
        
        if self.backend == "service":
            try:
                from .embedding_client import get_embedding_client
                self.embedding_client = get_embedding_client()
                logger.info("✅ EmbeddingService initialized with FastEmbed backend (10-50× faster)")
            except Exception as e:
                logger.warning(f"⚠️  Failed to initialize FastEmbed client, falling back to Ollama: {e}")
                self.backend = "ollama"
        else:
            logger.info("ℹ️  EmbeddingService initialized with Ollama backend (legacy)")
    
    @cache(ttl=3600, key_prefix="embedding")  # ⚡ Cache for 1 hour
    async def generate_embedding(self, text: str) -> Dict[str, Any]:
        """
        Generate embedding for a single text with smart retry and chunking (CACHED).
        
        Routes to appropriate backend (FastEmbed service or Ollama).
        Includes smart retry logic with health checks to auto-recover from transient failures.
        Automatically chunks large texts (>7000 chars) and averages embeddings.
        
        Args:
            text: Text to generate embedding for
        
        Returns:
            Dict with:
            {
                "embedding": List[float],
                "tokens": int,
                "cost": float,
                "model": str,
                "dimensions": int,
                "backend": str,
                "chunks": int  # Number of chunks processed
            }
        """
        logger.debug(f"🔄 Generating embedding: text_len={len(text)}, backend={self.backend}")
        start_time = time.time()
        
        # Chunk text if needed (prevents FastEmbed 422 errors)
        max_chars = 7000  # Safe limit for both FastEmbed and Ollama
        chunks = chunk_text(text, max_chars=max_chars)
        
        if len(chunks) > 1:
            logger.info(f"📄 Chunking large text: {len(chunks)} chunks for {len(text)} chars")
        
        # Route to appropriate backend
        if self.backend == "service" and self.embedding_client:
            try:
                # Process each chunk
                chunk_embeddings = []
                total_tokens = 0
                
                for i, chunk in enumerate(chunks, 1):
                    result = await self.embedding_client.generate_embedding(chunk)
                    chunk_embeddings.append(result["embedding"])
                    total_tokens += result["tokens"]
                    
                    if len(chunks) > 1:
                        logger.debug(f"  ✅ FastEmbed chunk {i}/{len(chunks)}: {len(chunk)} chars")
                
                # Average embeddings if multiple chunks
                if len(chunk_embeddings) > 1:
                    import numpy as np
                    embedding = np.mean(chunk_embeddings, axis=0).tolist()
                    logger.info(f"✅ Averaged {len(chunk_embeddings)} FastEmbed chunk embeddings")
                else:
                    embedding = chunk_embeddings[0]
                
                model = result["model"]
                dimensions = len(embedding)
                duration = time.time() - start_time
                
                logger.info(
                    f"✅ FastEmbed embedding generated: "
                    f"model={model}, dims={dimensions}, chunks={len(chunks)}, duration={duration:.3f}s"
                )
                
                return {
                    "embedding": embedding,
                    "tokens": total_tokens,
                    "cost": 0.0,  # Local and free
                    "model": model,
                    "dimensions": dimensions,
                    "backend": "fastembed",
                    "duration": duration,
                    "chunks": len(chunks)
                }
            except CircuitBreakerOpenError as e:
                # Smart retry: Check if service is actually healthy
                logger.warning(f"⚠️  Circuit breaker OPEN for FastEmbed, checking health...")
                
                if await self._check_fastembed_health():
                    logger.info(f"✅ FastEmbed service is healthy, resetting circuit breaker...")
                    try:
                        # Reset circuit breaker and retry with first chunk
                        await self.embedding_client.circuit_breaker.reset()
                        result = await self.embedding_client.generate_embedding(chunks[0])
                        logger.info(f"✅ Smart retry successful!")
                        return {
                            "embedding": result["embedding"],
                            "tokens": result["tokens"],
                            "cost": 0.0,
                            "model": result["model"],
                            "duration": result["duration_ms"] / 1000,
                            "chunks": 1
                        }
                    except Exception as retry_error:
                        logger.error(f"❌ Smart retry failed: {retry_error}")
                        # Fall through to Ollama fallback
                else:
                    logger.warning(f"⚠️  FastEmbed service is unhealthy, falling back to Ollama")
                    # Fall through to Ollama fallback
                    
            except Exception as e:
                logger.error(f"❌ FastEmbed service failed, falling back to Ollama: {e}")
                # Fall through to Ollama fallback
        
        # Ollama fallback with smart retry
        try:
            return await self._generate_with_ollama(text)
        except CircuitBreakerOpenError:
            logger.warning(f"⚠️  Circuit breaker OPEN for Ollama, checking health...")
            
            if await self._check_ollama_health():
                logger.info(f"✅ Ollama is healthy, resetting circuit breaker...")
                try:
                    await self.ollama_client.circuit_breaker.reset()
                    return await self._generate_with_ollama(text)
                except Exception as retry_error:
                    logger.error(f"❌ Ollama smart retry failed: {retry_error}")
                    raise
            else:
                logger.error(f"❌ Ollama is unhealthy and circuit breaker is OPEN")
                raise
    
    async def _generate_with_ollama(self, text: str) -> Dict[str, Any]:
        """Generate embedding using Ollama (legacy) with chunking support."""
        # Check if Ollama client is available
        if self.ollama_client is None:
            error_msg = "Ollama client not initialized and FastEmbed unavailable"
            logger.error(f"❌ {error_msg}")
            raise RuntimeError(error_msg)
        
        start_time = time.time()
        
        try:
            # Use chunking for long text instead of truncation
            max_chars = 7000  # Safe limit leaving buffer for 8000
            chunks = chunk_text(text, max_chars=max_chars)
            
            if len(chunks) > 1:
                logger.info(f"📄 Processing {len(chunks)} chunks for long text ({len(text)} chars)")
            
            # Generate embeddings for all chunks
            chunk_embeddings = []
            total_tokens = 0
            
            for i, chunk in enumerate(chunks, 1):
                chunk_embedding = await self.ollama_client.embed(chunk)
                
                if not chunk_embedding:
                    raise ValueError(f"Ollama returned empty embedding for chunk {i}")
                
                chunk_embeddings.append(chunk_embedding)
                total_tokens += self._estimate_tokens(chunk)
                
                if len(chunks) > 1:
                    logger.debug(f"  ✅ Chunk {i}/{len(chunks)}: {len(chunk)} chars")
            
            # Average embeddings if multiple chunks
            if len(chunk_embeddings) > 1:
                import numpy as np
                embedding = np.mean(chunk_embeddings, axis=0).tolist()
                logger.info(f"✅ Averaged {len(chunk_embeddings)} chunk embeddings")
            else:
                embedding = chunk_embeddings[0]
            
            # Calculate cost (Ollama is free, but track for metrics)
            cost = 0.0  # Ollama is local and free
            
            duration = time.time() - start_time
            dimensions = len(embedding)
            
            logger.info(
                f"✅ Ollama embedding generated: "
                f"model=nomic-embed-text, dims={dimensions}, tokens={total_tokens}, "
                f"chunks={len(chunks)}, duration={duration:.3f}s"
            )
            
            return {
                "embedding": embedding,
                "tokens": total_tokens,
                "cost": cost,
                "model": "nomic-embed-text",
                "dimensions": dimensions,
                "backend": "ollama",
                "duration": duration,
                "chunks": len(chunks)  # Track chunking
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
    
    async def _check_fastembed_health(self) -> bool:
        """
        Check if FastEmbed service is healthy.
        
        Returns:
            True if service is reachable and healthy, False otherwise
        """
        if not self.embedding_client:
            return False
        
        try:
            # Get service URL from embedding client
            service_url = os.getenv("EMBEDDING_SERVICE_URL", "http://ecosystem-mcp-embedding:8001")
            
            async with httpx.AsyncClient(timeout=2.0) as client:
                response = await client.get(f"{service_url}/health")
                
                if response.status_code == 200:
                    logger.info(f"✅ FastEmbed service health check: OK")
                    return True
                else:
                    logger.warning(f"⚠️  FastEmbed service health check: HTTP {response.status_code}")
                    return False
                    
        except Exception as e:
            logger.warning(f"⚠️  FastEmbed service health check failed: {e}")
            return False
    
    async def _check_ollama_health(self) -> bool:
        """
        Check if Ollama is healthy and accessible.
        
        Returns:
            True if Ollama is reachable and healthy, False otherwise
        """
        if not self.ollama_client:
            return False
        
        try:
            # Check if Ollama is available
            is_available = await self.ollama_client.is_available()
            
            if is_available:
                logger.info(f"✅ Ollama health check: OK")
                return True
            else:
                logger.warning(f"⚠️  Ollama health check: Not available")
                return False
                
        except Exception as e:
            logger.warning(f"⚠️  Ollama health check failed: {e}")
            return False


# Module-level convenience function for backward compatibility and testing
async def generate_embedding(text: str) -> List[float]:
    """
    Generate embedding for text (convenience function).
    
    Args:
        text: Text to embed
    
    Returns:
        Embedding vector
    """
    service = get_embedding_service()
    result = await service.generate_embedding(text)
    return result["embedding"]

