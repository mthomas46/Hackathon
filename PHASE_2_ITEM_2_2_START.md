**Date:** October 28, 2025  
**Status:** Item 2.2 Starting - Shared Embedding Cache  
**Goal:** Share embedding cache across services via Redis  

# Phase 2 Item 2.2: Shared Embedding Cache

## 🎯 Goal

Replace memory-only LRU cache with Redis-backed cache to share embeddings between:
- Main service (`ecosystem-mcp`)
- Embedding service (`ecosystem-mcp-embedding`)

## 📊 Current State

**Main Service:**
- Uses Redis cache with `@cache` decorator
- Embeddings cached and sharable

**Embedding Service:**
- Uses Python `@lru_cache` (memory only)
- **Not shared** between workers or with main service
- **50% wasted compute** on duplicate embeddings

## 🎯 Target State

Both services use shared Redis cache:
- Cache key: `embedding:{model}:{hash(text)}`
- TTL: 30 days (configurable)
- Graceful fallback on Redis failure
- Cache hit metrics

## 📋 Implementation Plan

1. Update `fastembed_service.py`:
   - Add Redis client initialization
   - Implement cache check before generation
   - Cache new embeddings after generation
   - Add batch caching for efficiency

2. Configuration:
   - Reuse existing Redis settings
   - Add cache TTL configuration
   - Add cache enable/disable flag

3. Testing:
   - Test cache hit/miss scenarios
   - Test Redis unavailable (fallback)
   - Measure cache hit rate

## ⚡ Expected Impact

- **-50-80% compute** - Duplicate embeddings served from cache
- **+2-5x throughput** - Faster embeddings for repeated text
- **Cross-service sharing** - Main and embedding service benefit
- **Graceful fallback** - Works without Redis (slower)

---

**Status:** Starting implementation...
