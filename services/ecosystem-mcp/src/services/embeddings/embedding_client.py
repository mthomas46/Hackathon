"""
HTTP client for embedding service.

Provides a clean interface to the FastEmbed embedding service.
PHASE 10 (Day 2): Enhanced with circuit breaker and timeout protection.
"""

import logging
from typing import List, Dict, Any, Optional
import httpx

from ...config import settings
from ...utils.resilience import (  # PHASE 10 (Day 2)
    get_embedding_circuit_breaker,
    resilient,
    with_timeout,
    FallbackStrategies
)

logger = logging.getLogger(__name__)


class EmbeddingClient:
    """
    HTTP client for embedding service.
    
    Connects to the FastEmbed embedding service for 10-50× faster embeddings.
    """
    
    def __init__(self, base_url: str = None):
        """
        Initialize embedding client.
        
        Args:
            base_url: Base URL of embedding service (uses settings if None)
        """
        self.base_url = base_url or getattr(settings, 'embedding_service_url', 'http://embedding-service:8000')
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=30.0,
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20)
        )
        
        logger.info(f"✅ Embedding client initialized: {self.base_url}")
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    @resilient(
        circuit_breaker_name="embedding_service",
        timeout_seconds=30.0,
        fallback=None,  # Re-raise on failure (embeddings are critical)
        failure_threshold=10,
        breaker_timeout=30.0
    )
    async def generate_embedding(self, text: str, model: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate embedding for a single text.
        
        PHASE 10 (Day 2): Protected by circuit breaker and timeout.
        
        Args:
            text: Text to embed
            model: Optional model override
        
        Returns:
            Dict with embedding, dimensions, tokens, cached, duration_ms
        
        Raises:
            Exception: If embedding generation fails
            TimeoutError: If operation exceeds 30s
            CircuitBreakerOpenError: If circuit breaker is open
        """
        try:
            payload = {"text": text}
            if model:
                payload["model"] = model
            
            response = await self.client.post("/embed/single", json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # Log cache hit/miss
            if result.get("cached"):
                logger.debug(f"✅ Embedding cache HIT ({result['duration_ms']:.1f}ms)")
            else:
                logger.debug(f"⚡ Embedding generated ({result['duration_ms']:.1f}ms)")
            
            return result
        
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Embedding service error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"❌ Failed to connect to embedding service: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error in embedding client: {e}")
            raise
    
    @resilient(
        circuit_breaker_name="embedding_service",
        timeout_seconds=60.0,  # Longer timeout for batch
        fallback=None,
        failure_threshold=10,
        breaker_timeout=30.0
    )
    async def generate_batch(
        self,
        texts: List[str],
        model: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Generate embeddings for multiple texts (TRUE batch processing).
        
        PHASE 10 (Day 2): Protected by circuit breaker and timeout.
        
        Args:
            texts: List of texts to embed
            model: Optional model override
        
        Returns:
            List of embedding dicts
        
        Raises:
            TimeoutError: If batch exceeds 60s
            CircuitBreakerOpenError: If circuit breaker is open
            Exception: If batch embedding fails
        """
        if not texts:
            return []
        
        try:
            payload = {"texts": texts}
            if model:
                payload["model"] = model
            
            response = await self.client.post("/embed/batch", json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # Log batch statistics
            logger.info(
                f"📊 Batch embedding: {len(texts)} texts, "
                f"{result['cache_hits']} hits, {result['cache_misses']} misses "
                f"({result['duration_ms']:.1f}ms total)"
            )
            
            # Convert response format to match expected format
            embeddings = []
            for i, embedding in enumerate(result["embeddings"]):
                embeddings.append({
                    "embedding": embedding,
                    "dimensions": result["dimensions"],
                    "tokens": result["tokens"][i],
                    "model": result["model"],
                    "duration_ms": result["duration_ms"] / len(texts)  # Avg per text
                })
            
            return embeddings
        
        except httpx.HTTPStatusError as e:
            logger.error(f"❌ Embedding service error: {e.response.status_code} - {e.response.text}")
            raise
        except httpx.RequestError as e:
            logger.error(f"❌ Failed to connect to embedding service: {e}")
            raise
        except Exception as e:
            logger.error(f"❌ Unexpected error in batch embedding: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check health of embedding service.
        
        Returns:
            Health status dict
        """
        try:
            response = await self.client.get("/health")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ Embedding service health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}
    
    async def get_info(self) -> Dict[str, Any]:
        """
        Get embedding service information.
        
        Returns:
            Service info dict
        """
        try:
            response = await self.client.get("/embed/info")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"❌ Failed to get embedding service info: {e}")
            return {"error": str(e)}


# Global client instance
_embedding_client: Optional[EmbeddingClient] = None


def get_embedding_client() -> EmbeddingClient:
    """Get global embedding client instance."""
    global _embedding_client
    if _embedding_client is None:
        _embedding_client = EmbeddingClient()
    return _embedding_client

