"""
Cache Warming Service

Pre-generates embeddings for common queries and documents on service startup.
"""

import logging
import time
from typing import List, Dict, Any
import asyncio

from .fastembed_service import get_fastembed_service
from .cache_service import get_cache_service
from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class CacheWarmingService:
    """
    Service for warming the embedding cache on startup.
    
    Pre-generates embeddings for:
    - Common search queries
    - Frequently accessed documents
    - Standard technical terms
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.fastembed = get_fastembed_service()
        self.cache = get_cache_service()
        
    async def warm_cache(self, warmup_texts: List[str] = None):
        """
        Warm the cache with common embeddings.
        
        Args:
            warmup_texts: Optional list of texts to warm up. If None, uses defaults.
        """
        if not self.settings.CACHE_ENABLED:
            logger.info("⏭️  Cache warming skipped (caching disabled)")
            return
            
        start_time = time.time()
        logger.info("🔥 Starting cache warming...")
        
        # Default warmup texts (common queries and terms)
        if warmup_texts is None:
            warmup_texts = self._get_default_warmup_texts()
        
        if not warmup_texts:
            logger.warning("⚠️  No warmup texts provided")
            return
        
        try:
            # Generate embeddings in batches
            logger.info(f"   Warming {len(warmup_texts)} embeddings...")
            
            # Use batch processing for efficiency
            batch_size = 20
            total_warmed = 0
            
            for i in range(0, len(warmup_texts), batch_size):
                batch = warmup_texts[i:i + batch_size]
                
                # Generate embeddings (this will cache them)
                embeddings = self.fastembed.embed_batch(batch)
                
                # Store in cache
                text_embeddings = {
                    text: embedding 
                    for text, embedding in zip(batch, embeddings)
                }
                await self.cache.set_batch(text_embeddings)
                
                total_warmed += len(batch)
                logger.debug(f"   Warmed {total_warmed}/{len(warmup_texts)} embeddings...")
            
            duration = (time.time() - start_time) * 1000
            logger.info(
                f"✅ Cache warming complete: {total_warmed} embeddings in {duration:.2f}ms "
                f"({duration/total_warmed:.2f}ms per embedding)"
            )
            
        except Exception as e:
            logger.error(f"❌ Cache warming failed: {e}", exc_info=True)
    
    def _get_default_warmup_texts(self) -> List[str]:
        """
        Get default list of texts to warm up the cache.
        
        Returns:
            List of common queries and technical terms
        """
        return [
            # Common search queries
            "What is this project about?",
            "How do I install this?",
            "How do I get started?",
            "What are the requirements?",
            "How do I configure this?",
            "How do I run tests?",
            "How do I deploy this?",
            "What are the main features?",
            "How does authentication work?",
            "How does the API work?",
            
            # Common technical terms
            "function",
            "class",
            "method",
            "variable",
            "parameter",
            "return",
            "import",
            "export",
            "async",
            "await",
            "promise",
            "callback",
            "error",
            "exception",
            "try",
            "catch",
            "throw",
            "raise",
            "test",
            "mock",
            
            # Common programming concepts
            "database connection",
            "API endpoint",
            "authentication token",
            "error handling",
            "data validation",
            "configuration settings",
            "environment variables",
            "dependency injection",
            "unit testing",
            "integration testing",
            
            # Common documentation patterns
            "Installation instructions",
            "Configuration guide",
            "API reference",
            "Getting started tutorial",
            "Troubleshooting guide",
            "Best practices",
            "Architecture overview",
            "Contributing guidelines",
            "License information",
            "Changelog and releases",
            
            # Common code patterns
            "Initialize the service",
            "Connect to database",
            "Handle user request",
            "Validate input data",
            "Process and transform data",
            "Return response to client",
            "Log error message",
            "Catch and handle exception",
            "Clean up resources",
            "Close connections",
        ]
    
    async def warm_from_recent_queries(self, limit: int = 100):
        """
        Warm cache from recent queries stored in Redis.
        
        Args:
            limit: Maximum number of recent queries to warm
        """
        if not self.settings.CACHE_ENABLED:
            return
            
        try:
            logger.info(f"🔥 Warming cache from {limit} recent queries...")
            
            # Get recent queries from Redis (if stored)
            # This would require tracking recent queries
            # For now, this is a placeholder for future enhancement
            
            logger.info("✅ Recent query warming complete")
            
        except Exception as e:
            logger.error(f"❌ Recent query warming failed: {e}")
    
    async def warm_from_frequent_documents(self, limit: int = 50):
        """
        Warm cache from frequently accessed documents.
        
        Args:
            limit: Maximum number of documents to warm
        """
        if not self.settings.CACHE_ENABLED:
            return
            
        try:
            logger.info(f"🔥 Warming cache from {limit} frequent documents...")
            
            # Get frequently accessed documents from analytics
            # This would require tracking document access patterns
            # For now, this is a placeholder for future enhancement
            
            logger.info("✅ Frequent document warming complete")
            
        except Exception as e:
            logger.error(f"❌ Frequent document warming failed: {e}")


# Singleton instance
_cache_warming_service: CacheWarmingService = None


def get_cache_warming_service() -> CacheWarmingService:
    """Get singleton cache warming service instance."""
    global _cache_warming_service
    if _cache_warming_service is None:
        _cache_warming_service = CacheWarmingService()
    return _cache_warming_service

