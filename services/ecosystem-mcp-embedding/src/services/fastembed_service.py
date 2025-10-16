"""
FastEmbed service for ONNX-optimized embedding generation.

10-50× faster than Ollama for embeddings!
"""

import logging
import time
from typing import List, Dict, Any
import numpy as np
from fastembed import TextEmbedding

from ..config.settings import settings

logger = logging.getLogger(__name__)


class FastEmbedService:
    """
    FastEmbed service using ONNX Runtime.
    
    Features:
    - ONNX Runtime optimization (SIMD, threading)
    - TRUE batch processing (parallel tensor operations)
    - Lightweight (embeddings-only, no LLM overhead)
    - 10-50× faster than Ollama
    """
    
    def __init__(self, model_name: str = None):
        """
        Initialize FastEmbed service.
        
        Args:
            model_name: Embedding model to use
                Options:
                - "BAAI/bge-base-en-v1.5" (768 dims, recommended - matches nomic)
                - "BAAI/bge-small-en-v1.5" (384 dims, faster)
                - "BAAI/bge-large-en-v1.5" (1024 dims, best quality)
                - "sentence-transformers/all-MiniLM-L6-v2" (384 dims, fast)
        """
        self.model_name = model_name or settings.model_name
        self.max_text_length = settings.max_text_length
        self.model = None
        self._dimensions = None
        
        logger.info(f"🚀 Initializing FastEmbed with model: {self.model_name}")
    
    def load_model(self):
        """Load the embedding model (called on startup)."""
        try:
            start_time = time.time()
            
            self.model = TextEmbedding(
                model_name=self.model_name,
                cache_dir=settings.model_cache_dir
            )
            
            # Test generation to get dimensions
            test_embedding = list(self.model.embed(["test"]))[0]
            self._dimensions = len(test_embedding)
            
            load_time = time.time() - start_time
            
            logger.info(
                f"✅ FastEmbed model loaded successfully "
                f"(dimensions: {self._dimensions}, load time: {load_time:.2f}s)"
            )
        
        except Exception as e:
            logger.error(f"❌ Failed to load FastEmbed model: {e}", exc_info=True)
            raise
    
    @property
    def dimensions(self) -> int:
        """Get embedding dimensions."""
        return self._dimensions
    
    def _truncate_text(self, text: str) -> str:
        """Truncate text if too long."""
        if len(text) > self.max_text_length:
            logger.warning(
                f"⚠️  Text too long ({len(text)} chars), "
                f"truncating to {self.max_text_length}"
            )
            return text[:self.max_text_length]
        return text
    
    def _estimate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)."""
        # Rough estimate: ~4 chars per token
        return len(text) // 4
    
    async def generate_embedding(self, text: str) -> Dict[str, Any]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to embed
        
        Returns:
            Dict with embedding, dimensions, tokens, model, duration
        """
        if not self.model:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        start_time = time.time()
        
        # Truncate if needed
        text = self._truncate_text(text)
        
        # Generate embedding
        # FastEmbed returns a generator, we get the first result
        embeddings = list(self.model.embed([text]))
        
        if not embeddings:
            raise ValueError("FastEmbed returned empty result")
        
        embedding = embeddings[0]
        
        duration_ms = (time.time() - start_time) * 1000
        
        return {
            "embedding": embedding.tolist(),
            "dimensions": len(embedding),
            "tokens": self._estimate_tokens(text),
            "model": self.model_name,
            "duration_ms": duration_ms
        }
    
    async def generate_batch(self, texts: List[str]) -> List[Dict[str, Any]]:
        """
        Generate embeddings for multiple texts (TRUE batch processing!).
        
        This is where FastEmbed shines:
        - ONNX Runtime processes all texts in parallel
        - Optimized tensor operations (SIMD)
        - 10-50× faster than Ollama's sequential processing
        
        Args:
            texts: List of texts to embed
        
        Returns:
            List of embedding dicts
        """
        if not self.model:
            raise RuntimeError("Model not loaded. Call load_model() first.")
        
        if not texts:
            return []
        
        start_time = time.time()
        
        # Truncate texts if needed
        truncated_texts = [self._truncate_text(text) for text in texts]
        
        # Generate embeddings in TRUE parallel batch
        # This is the magic - ONNX Runtime optimizes this heavily
        embeddings = list(self.model.embed(truncated_texts))
        
        duration_ms = (time.time() - start_time) * 1000
        
        # Format results
        results = []
        for text, embedding in zip(texts, embeddings):
            results.append({
                "embedding": embedding.tolist(),
                "dimensions": len(embedding),
                "tokens": self._estimate_tokens(text),
                "model": self.model_name,
                "duration_ms": duration_ms / len(texts)  # Average per text
            })
        
        logger.info(
            f"⚡ Generated {len(results)} embeddings in batch "
            f"({duration_ms:.1f}ms total, {duration_ms/len(texts):.1f}ms avg)"
        )
        
        return results
    
    def get_info(self) -> Dict[str, Any]:
        """Get model information."""
        return {
            "model": self.model_name,
            "dimensions": self._dimensions,
            "max_text_length": self.max_text_length,
            "backend": "ONNX Runtime",
            "loaded": self.model is not None
        }


# Global FastEmbed instance
_fastembed_service: FastEmbedService | None = None


def get_fastembed_service() -> FastEmbedService:
    """Get global FastEmbed service instance."""
    global _fastembed_service
    if _fastembed_service is None:
        _fastembed_service = FastEmbedService()
    return _fastembed_service

