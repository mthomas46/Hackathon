"""
Redis cache service for embeddings and normalized content.

Provides content-addressable caching with TTL support.
"""

import json
import logging
from hashlib import sha256
from typing import Optional, List, Dict, Any, Tuple
import redis.asyncio as redis

from ..config.settings import settings

logger = logging.getLogger(__name__)


class CacheService:
    """
    Redis-based cache service.
    
    Features:
    - Content-addressable caching (hash-based keys)
    - TTL support (30 days default)
    - Batch operations (mget, mset)
    - Separate namespaces for embeddings and normalization
    """
    
    def __init__(self):
        """Initialize cache service."""
        self.redis: Optional[redis.Redis] = None
        self.enabled = settings.cache_enabled
        self.ttl = settings.cache_ttl
        
        if not self.enabled:
            logger.warning("⚠️  Cache disabled in settings")
    
    async def connect(self):
        """Connect to Redis."""
        if not self.enabled:
            return
        
        try:
            self.redis = redis.Redis(
                host=settings.redis_host,
                port=settings.redis_port,
                db=settings.redis_db,
                password=settings.redis_password,
                decode_responses=False,  # We handle encoding
                socket_connect_timeout=5,
                socket_timeout=5
            )
            
            # Test connection
            await self.redis.ping()
            logger.info(f"✅ Connected to Redis at {settings.redis_host}:{settings.redis_port}")
        
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            self.enabled = False
    
    async def close(self):
        """Close Redis connection."""
        if self.redis:
            await self.redis.close()
            logger.info("Redis connection closed")
    
    def _compute_hash(self, content: str) -> str:
        """Compute SHA256 hash of content."""
        return sha256(content.encode('utf-8')).hexdigest()
    
    def _make_key(self, namespace: str, content_hash: str) -> str:
        """Create cache key with namespace."""
        return f"{namespace}:{content_hash}"
    
    # ========== Embedding Cache ==========
    
    async def get_embedding(self, text: str) -> Optional[Dict[str, Any]]:
        """
        Get cached embedding for text.
        
        Args:
            text: Text to lookup
        
        Returns:
            Cached embedding dict or None if not found
        """
        if not self.enabled or not self.redis:
            return None
        
        try:
            content_hash = self._compute_hash(text)
            key = self._make_key("embed", content_hash)
            
            cached = await self.redis.get(key)
            if cached:
                logger.debug(f"✅ Embedding cache HIT: {content_hash[:16]}...")
                return json.loads(cached)
            
            logger.debug(f"❌ Embedding cache MISS: {content_hash[:16]}...")
            return None
        
        except Exception as e:
            logger.error(f"Error getting cached embedding: {e}")
            return None
    
    async def set_embedding(self, text: str, embedding: Dict[str, Any]):
        """
        Cache embedding for text.
        
        Args:
            text: Text that was embedded
            embedding: Embedding result to cache
        """
        if not self.enabled or not self.redis:
            return
        
        try:
            content_hash = self._compute_hash(text)
            key = self._make_key("embed", content_hash)
            
            await self.redis.setex(
                key,
                self.ttl,
                json.dumps(embedding)
            )
            
            logger.debug(f"💾 Cached embedding: {content_hash[:16]}...")
        
        except Exception as e:
            logger.error(f"Error caching embedding: {e}")
    
    async def get_embeddings_batch(self, texts: List[str]) -> Tuple[List[Optional[Dict[str, Any]]], List[int]]:
        """
        Get multiple embeddings from cache.
        
        Args:
            texts: List of texts to lookup
        
        Returns:
            Tuple of (cached results list, miss indices list)
        """
        if not self.enabled or not self.redis:
            return [None] * len(texts), list(range(len(texts)))
        
        try:
            # Compute hashes and keys
            hashes = [self._compute_hash(text) for text in texts]
            keys = [self._make_key("embed", h) for h in hashes]
            
            # Batch lookup
            cached_results = await self.redis.mget(keys)
            
            # Parse results and track misses
            results = []
            miss_indices = []
            
            for i, cached in enumerate(cached_results):
                if cached:
                    results.append(json.loads(cached))
                    logger.debug(f"✅ Batch cache HIT {i+1}/{len(texts)}")
                else:
                    results.append(None)
                    miss_indices.append(i)
                    logger.debug(f"❌ Batch cache MISS {i+1}/{len(texts)}")
            
            logger.info(
                f"📊 Batch cache: {len(texts) - len(miss_indices)} hits, "
                f"{len(miss_indices)} misses"
            )
            
            return results, miss_indices
        
        except Exception as e:
            logger.error(f"Error getting batch embeddings: {e}")
            return [None] * len(texts), list(range(len(texts)))
    
    async def set_embeddings_batch(self, texts: List[str], embeddings: List[Dict[str, Any]]):
        """
        Cache multiple embeddings.
        
        Args:
            texts: Texts that were embedded
            embeddings: Embedding results to cache
        """
        if not self.enabled or not self.redis:
            return
        
        try:
            # Prepare pipeline
            pipe = self.redis.pipeline()
            
            for text, embedding in zip(texts, embeddings):
                content_hash = self._compute_hash(text)
                key = self._make_key("embed", content_hash)
                pipe.setex(key, self.ttl, json.dumps(embedding))
            
            # Execute batch
            await pipe.execute()
            
            logger.info(f"💾 Cached {len(embeddings)} embeddings in batch")
        
        except Exception as e:
            logger.error(f"Error caching batch embeddings: {e}")
    
    # ========== Normalization Cache ==========
    
    async def get_normalized(self, content: str, file_ext: str) -> Optional[Dict[str, Any]]:
        """
        Get cached normalized content.
        
        Args:
            content: Raw content
            file_ext: File extension (e.g., '.py', '.md')
        
        Returns:
            Cached normalization dict or None if not found
        """
        if not self.enabled or not self.redis:
            return None
        
        try:
            # Include file extension in hash for different normalizations
            content_hash = self._compute_hash(f"{file_ext}:{content}")
            key = self._make_key("norm", content_hash)
            
            cached = await self.redis.get(key)
            if cached:
                logger.debug(f"✅ Normalization cache HIT: {content_hash[:16]}...")
                return json.loads(cached)
            
            logger.debug(f"❌ Normalization cache MISS: {content_hash[:16]}...")
            return None
        
        except Exception as e:
            logger.error(f"Error getting cached normalization: {e}")
            return None
    
    async def set_normalized(self, content: str, file_ext: str, normalized: Dict[str, Any]):
        """
        Cache normalized content.
        
        Args:
            content: Raw content that was normalized
            file_ext: File extension
            normalized: Normalization result to cache
        """
        if not self.enabled or not self.redis:
            return
        
        try:
            content_hash = self._compute_hash(f"{file_ext}:{content}")
            key = self._make_key("norm", content_hash)
            
            await self.redis.setex(
                key,
                self.ttl,
                json.dumps(normalized)
            )
            
            logger.debug(f"💾 Cached normalization: {content_hash[:16]}...")
        
        except Exception as e:
            logger.error(f"Error caching normalization: {e}")
    
    # ========== Stats ==========
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.enabled or not self.redis:
            return {
                "enabled": False,
                "connected": False
            }
        
        try:
            info = await self.redis.info()
            
            # Count keys by namespace
            embed_keys = 0
            norm_keys = 0
            
            # Use SCAN for large keyspaces
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(cursor, match="embed:*", count=1000)
                embed_keys += len(keys)
                if cursor == 0:
                    break
            
            cursor = 0
            while True:
                cursor, keys = await self.redis.scan(cursor, match="norm:*", count=1000)
                norm_keys += len(keys)
                if cursor == 0:
                    break
            
            return {
                "enabled": True,
                "connected": True,
                "redis_version": info.get("redis_version"),
                "used_memory_human": info.get("used_memory_human"),
                "total_keys": embed_keys + norm_keys,
                "embedding_keys": embed_keys,
                "normalization_keys": norm_keys,
                "cache_ttl": self.ttl
            }
        
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {
                "enabled": True,
                "connected": False,
                "error": str(e)
            }


# Global cache instance
_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Get global cache service instance."""
    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service

