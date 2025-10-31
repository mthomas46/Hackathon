---
title: "Response Caching Documentation"
service: "ecosystem-mcp"
category: "architecture"
tags: ['architecture', 'cache', 'caching', 'config', 'configuration', 'design', 'health', 'ingestion', 'llm', 'monitoring']
related: ['INDEX.md', 'architecture/OVERVIEW.md', 'CODE_REFERENCE.md', 'API_ENDPOINTS_COMPLETE.md']
status: "current"
last_updated: "2025-10-28"
audience: "developer"
difficulty: "advanced"
semantic_keywords: ['architecture', 'cache', 'caching', 'config', 'configuration']
llm_search_hints: ['what is response caching documentation', 'how does response caching documentation work', 'guide to response caching documentation']
---

# Response Caching Documentation

**Date**: 2025-10-12  
**Service**: ecosystem-mcp v0.1.0  
**Status**: Implemented ✅

---

## Overview

The ecosystem-mcp service implements Redis-based response caching to improve performance and reduce load on expensive operations.

---

## Cached Operations

### 1. Ollama Embeddings (TTL: 1 hour)
**Location**: `src/services/models/ollama_client.py::embed()`  
**TTL**: 3600 seconds (1 hour)  
**Key Prefix**: `embedding:`

**Why Cached**:
- Most expensive operation (~200-500ms per embedding)
- Deterministic (same text = same embedding)
- Safe to cache aggressively

**Example**:
```python
embedding = await ollama_client.embed("Hello world")
# First call: 300ms (cache miss)
# Subsequent calls: 5ms (cache hit)
```

**Cache Key Format**:
```
embedding:embed:a3b2c1d4e5f6
```

### 2. Search Results (TTL: 5 minutes)
**Location**: `src/api/routes/search.py::search_documents()`  
**TTL**: 300 seconds (5 minutes)  
**Key Prefix**: `search:`

**Why Cached**:
- Moderate expense (embedding + vector search + DB lookup)
- Results relatively stable in short time windows
- Balances freshness vs performance

**Example**:
```python
results = await search_documents(query="architecture patterns")
# First call: 500ms (cache miss)
# Subsequent calls: 10ms (cache hit)
```

**Cache Key Format**:
```
search:search_documents:b4c5d6e7f8g9
```

---

## Cache Architecture

### Components

```
┌─────────────────┐
│   FastAPI App   │
│   (Endpoints)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ Cache Decorator │
│  (@cache(...))  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Redis Client   │
│   (get/set)     │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Redis Server   │
│  (Port: 6379)   │
└─────────────────┘
```

### Cache Decorator

**File**: `src/utils/cache_decorator.py`

**Features**:
- Automatic JSON serialization/deserialization
- MD5 hashing of arguments for cache keys
- TTL-based expiration
- Graceful degradation (compute if cache fails)
- Prometheus metrics integration
- Non-serializable argument filtering

**Usage**:
```python
from src.utils.cache_decorator import cache

@cache(ttl=3600, key_prefix="myfunction")
async def expensive_operation(arg1: str, arg2: int):
    # ... expensive computation ...
    return result
```

---

## Monitoring

### Admin Endpoints

#### Get Cache Statistics
```bash
GET /api/v1/admin/cache-stats

Response:
{
  "cache_hits": 1234,
  "cache_misses": 456,
  "total_requests": 1690,
  "hit_rate_percent": 73.02,
  "message": "Cache is performing well"
}
```

#### Clear Cache by Prefix
```bash
POST /api/v1/admin/clear-cache?prefix=embedding

Response:
{
  "status": "success",
  "message": "Cleared 42 cache keys with prefix 'embedding'"
}
```

#### Clear All Cache
```bash
POST /api/v1/admin/clear-all-cache

Response:
{
  "status": "success",
  "message": "Cleared ALL cache: 156 keys deleted"
}
```

### Prometheus Metrics

**Metrics Exposed**:
- `ecosystem_mcp_cache_hits_total{prefix}` - Total cache hits by prefix
- `ecosystem_mcp_cache_misses_total{prefix}` - Total cache misses by prefix

**Calculated Metrics**:
- Hit Rate: `cache_hits / (cache_hits + cache_misses) * 100`
- Miss Rate: `cache_misses / (cache_hits + cache_misses) * 100`

**Query Examples**:
```promql
# Cache hit rate by prefix
rate(ecosystem_mcp_cache_hits_total[5m]) 
/ 
(rate(ecosystem_mcp_cache_hits_total[5m]) + rate(ecosystem_mcp_cache_misses_total[5m]))

# Total cache operations per second
rate(ecosystem_mcp_cache_hits_total[5m]) + rate(ecosystem_mcp_cache_misses_total[5m])
```

---

## Performance Impact

### Expected Improvements

| Operation | Without Cache | With Cache (Hit) | Improvement |
|-----------|---------------|------------------|-------------|
| Embedding generation | 200-500ms | 5-10ms | **95-98%** |
| Search query | 300-700ms | 10-20ms | **95-97%** |
| Overall API latency | Varies | 50-90% lower | **50-90%** |

### Cache Hit Rate Targets

- **Cold start**: 0-20% (first few minutes)
- **Warm cache**: 50-70% (normal operation)
- **Hot cache**: 70-90% (peak usage, repeated queries)

---

## Configuration

### Environment Variables

```bash
# Redis connection
REDIS_URL=redis://localhost:6379/0

# Redis connection pool
REDIS_MAX_CONNECTIONS=20
```

### TTL Configuration

**Current TTLs**:
- Embeddings: 3600s (1 hour)
- Search results: 300s (5 minutes)

**To Adjust**:
```python
# In the decorator
@cache(ttl=7200, key_prefix="embedding")  # Change to 2 hours
```

---

## Cache Invalidation

### Automatic Invalidation
- **TTL expiration**: Redis automatically removes expired keys
- **Memory pressure**: Redis uses LRU eviction if memory is full

### Manual Invalidation

#### By Prefix
```bash
curl -X POST http://localhost:8000/api/v1/admin/clear-cache?prefix=search
```

**Use cases**:
- After data ingestion (clear search cache)
- After model update (clear embedding cache)
- Testing cache behavior

#### All Cache
```bash
curl -X POST http://localhost:8000/api/v1/admin/clear-all-cache
```

**Use cases**:
- Major system update
- Cache corruption
- Reset for testing

### Programmatic Invalidation

```python
from src.utils.cache_decorator import clear_cache_prefix, clear_all_cache

# Clear specific prefix
deleted = await clear_cache_prefix("embedding")

# Clear all cache
deleted = await clear_all_cache()
```

---

## Best Practices

### When to Cache

✅ **Good candidates**:
- Expensive computations (>100ms)
- Deterministic operations (same input = same output)
- Read-heavy operations (>10:1 read:write ratio)
- Stable data (infrequent updates)

❌ **Bad candidates**:
- Real-time data (stock prices, live feeds)
- User-specific data (privacy concerns)
- Write operations (creates stale data)
- Non-deterministic operations (random values)

### TTL Selection

- **Long TTL (hours)**: Deterministic, expensive operations
- **Medium TTL (minutes)**: Semi-stable data
- **Short TTL (seconds)**: Frequently changing data

**Rule of thumb**: TTL should be **longer than average computation time** but **shorter than data freshness requirement**.

### Cache Key Design

**Good**:
```python
# Includes all parameters
cache_key = f"search:{query}:{service_name}:{limit}"
```

**Bad**:
```python
# Missing parameters (can return wrong results)
cache_key = f"search:{query}"
```

### Error Handling

The cache decorator implements graceful degradation:
1. Try to read from cache
2. If cache fails → compute result
3. Try to write to cache
4. If cache write fails → log warning, continue

**Never let cache failures break the API**.

---

## Troubleshooting

### Issue: Low cache hit rate

**Possible causes**:
- Cache is cold (just started)
- TTL too short
- Too many unique queries
- Redis not running

**Solution**:
```bash
# Check Redis
redis-cli ping

# Check cache stats
curl http://localhost:8000/api/v1/admin/cache-stats

# Increase TTL if appropriate
```

### Issue: Stale data in cache

**Possible causes**:
- TTL too long
- Data updated but cache not invalidated

**Solution**:
```bash
# Clear affected cache
curl -X POST http://localhost:8000/api/v1/admin/clear-cache?prefix=search

# Or adjust TTL in code
@cache(ttl=60)  # Reduce to 1 minute
```

### Issue: Cache memory growing too large

**Possible causes**:
- No TTL set
- Too many unique keys
- Redis max memory not configured

**Solution**:
```bash
# Configure Redis max memory
redis-cli CONFIG SET maxmemory 2gb
redis-cli CONFIG SET maxmemory-policy allkeys-lru

# Clear old cache
curl -X POST http://localhost:8000/api/v1/admin/clear-all-cache
```

---

## Future Enhancements

### Planned Improvements

1. **Cache warming** (High Priority)
   - Pre-populate cache on startup
   - Background cache refresh before expiration

2. **Smarter invalidation** (Medium Priority)
   - Invalidate on document ingestion
   - Cascade invalidation (clear dependent caches)

3. **Multi-tier caching** (Low Priority)
   - L1: In-memory (fastest)
   - L2: Redis (distributed)
   - L3: Disk (largest capacity)

4. **Cache analytics** (Medium Priority)
   - Hit rate by endpoint
   - Cache size by prefix
   - TTL effectiveness analysis

5. **Compression** (Low Priority)
   - Compress large cache values
   - Trade CPU for memory

---

## Testing

### Manual Testing

```bash
# 1. Make a search request (cache miss)
time curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "limit": 10}'

# 2. Make the same request again (cache hit)
time curl -X POST http://localhost:8000/api/v1/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test query", "limit": 10}'

# 3. Check cache stats
curl http://localhost:8000/api/v1/admin/cache-stats

# 4. Clear cache
curl -X POST http://localhost:8000/api/v1/admin/clear-cache?prefix=search

# 5. Verify cache cleared
curl http://localhost:8000/api/v1/admin/cache-stats
```

### Automated Testing

```python
# tests/test_cache.py
import pytest
from src.utils.cache_decorator import cache

@pytest.mark.asyncio
async def test_cache_hit():
    call_count = 0
    
    @cache(ttl=60, key_prefix="test")
    async def expensive_function(x):
        nonlocal call_count
        call_count += 1
        return x * 2
    
    # First call - cache miss
    result1 = await expensive_function(5)
    assert result1 == 10
    assert call_count == 1
    
    # Second call - cache hit
    result2 = await expensive_function(5)
    assert result2 == 10
    assert call_count == 1  # Function not called again
```

---

## Metrics Dashboard (Grafana)

### Recommended Panels

1. **Cache Hit Rate**
   ```promql
   rate(ecosystem_mcp_cache_hits_total[5m]) 
   / 
   (rate(ecosystem_mcp_cache_hits_total[5m]) + rate(ecosystem_mcp_cache_misses_total[5m])) 
   * 100
   ```

2. **Cache Operations per Second**
   ```promql
   rate(ecosystem_mcp_cache_hits_total[1m]) + rate(ecosystem_mcp_cache_misses_total[1m])
   ```

3. **Cache Hit Rate by Prefix**
   ```promql
   rate(ecosystem_mcp_cache_hits_total[5m]) by (prefix)
   ```

---

## Conclusion

**Status**: ✅ **CACHING FULLY OPERATIONAL**

The ecosystem-mcp service now has comprehensive response caching:
- Redis-based distributed caching
- Prometheus metrics for monitoring
- Admin endpoints for management
- Automatic TTL-based expiration
- Graceful degradation on failures

**Expected Impact**:
- 50-90% response time reduction
- Improved scalability
- Reduced load on backend services
- Better user experience

---

**Phase 3 Task 2**: ✅ **100% COMPLETE**

