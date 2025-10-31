---
title: "Fallback Strategies Guide (Phase 10 - Day 3 - Task 3.2)"
service: "ecosystem-mcp"
category: "architecture"
tags: ['architecture', 'cache', 'caching', 'config', 'configuration', 'database', 'design', 'health', 'monitoring', 'postgresql']
related: ['INDEX.md', 'architecture/OVERVIEW.md', 'CODE_REFERENCE.md', 'API_ENDPOINTS_COMPLETE.md']
status: "current"
last_updated: "2025-10-28"
audience: "developer"
difficulty: "beginner"
semantic_keywords: ['architecture', 'cache', 'caching', 'config', 'configuration']
llm_search_hints: ['what is fallback strategies guide (phase 10 - day 3 - task 3.2)', 'how does fallback strategies guide (phase 10 - day 3 - task 3.2) work', 'guide to fallback strategies guide (phase 10 - day 3 - task 3.2)']
---

# Fallback Strategies Guide (Phase 10 - Day 3 - Task 3.2)

## Overview

Fallback strategies ensure the system continues operating with degraded functionality when services fail, rather than failing completely. This guide documents all implemented fallback strategies.

---

## 🎯 Fallback Philosophy

**Core Principle:** Fail gracefully, not catastrophically.

- **Critical Operations:** Re-raise errors (must succeed)
- **Important Operations:** Use sensible defaults
- **Non-Critical Operations:** Skip with logging
- **Cache Operations:** Fall back to direct computation

---

## 📚 Pre-Built Fallback Strategies

### Location
`src/utils/resilience.py` → `FallbackStrategies` class

### Available Strategies

#### 1. **Empty Collections**

```python
from src.utils.resilience import FallbackStrategies

# Empty list
result = await FallbackStrategies.empty_list()
# Returns: []

# Empty dict
result = await FallbackStrategies.empty_dict()
# Returns: {}
```

**Use Cases:**
- Search/query results when service is down
- List operations that can be empty
- Optional data collections

---

#### 2. **None Value**

```python
result = await FallbackStrategies.none_value()
# Returns: None
```

**Use Cases:**
- Optional metadata lookups
- Non-critical configuration values
- Optional enhancement features

---

#### 3. **Default Embedding**

```python
embedding = await FallbackStrategies.default_embedding()
# Returns: [0.0] * 768  # Zero vector
```

**Use Cases:**
- Embedding service temporarily unavailable
- Non-critical documents
- Allows document storage even without embedding

**Note:** Zero vectors won't match in similarity search but allow the pipeline to continue.

---

#### 4. **Skip Operation**

```python
result = await FallbackStrategies.skip_operation()
# Returns: {
#     "success": True,
#     "skipped": True,
#     "reason": "Service unavailable"
# }
```

**Use Cases:**
- Non-critical operations
- Optional enrichment steps
- Background processing

---

#### 5. **Custom Default Value**

```python
fallback = FallbackStrategies.create_default_value({"status": "degraded"})
result = await fallback()
# Returns: {"status": "degraded"}
```

**Use Cases:**
- Service-specific defaults
- Custom error responses
- Configurable fallbacks

---

## 🛠️ Applying Fallback Strategies

### Method 1: @resilient Decorator (Recommended)

```python
from src.utils.resilience import resilient, FallbackStrategies

@resilient(
    circuit_breaker_name="service_name",
    timeout_seconds=30.0,
    fallback=FallbackStrategies.empty_list
)
async def get_optional_data():
    # May fail
    return await external_service.fetch_data()

# Usage
result = await get_optional_data()
# Returns: [] if service fails, actual data if succeeds
```

---

### Method 2: Manual with_fallback

```python
from src.utils.resilience import with_fallback

async def primary_operation():
    return await expensive_operation()

async def fallback_operation():
    return {"cached": True, "data": get_from_cache()}

result = await with_fallback(
    primary_operation,
    fallback_operation
)
```

---

### Method 3: Inline Try-Except

```python
try:
    result = await critical_operation()
except Exception as e:
    logger.warning(f"Operation failed, using fallback: {e}")
    result = await FallbackStrategies.empty_dict()
```

---

## 📊 Service-Specific Fallback Strategies

### Embedding Service

**Strategy:** Skip embedding, store document

```python
@resilient(
    circuit_breaker_name="embedding_service",
    timeout_seconds=30.0,
    fallback=None  # Don't use fallback - embeddings are critical
)
async def generate_embedding(text: str):
    # If this fails, we want to know
    return await embedding_client.generate(text)
```

**Rationale:** Embeddings are critical for search functionality. Better to fail and retry later than store zero vectors.

---

### LLM Service (Documentation)

**Strategy:** Use cached results or skip

```python
@resilient(
    circuit_breaker_name="llm_service",
    timeout_seconds=120.0,
    fallback=FallbackStrategies.create_default_value({
        "answer": "LLM service temporarily unavailable",
        "cached": True
    })
)
async def query_llm(question: str):
    return await llm_client.query(question)
```

**Rationale:** Documentation generation can use cached results or be retried later.

---

### ChromaDB (Vector Store)

**Strategy:** Fall back to keyword search

```python
@resilient(
    circuit_breaker_name="chromadb",
    timeout_seconds=45.0,
    fallback=lambda: perform_keyword_search(query)
)
async def vector_search(query: str):
    return await chromadb.similarity_search(query)
```

**Rationale:** Keyword search is less effective but better than no results.

---

### Redis (Cache)

**Strategy:** Direct computation

```python
@resilient(
    circuit_breaker_name="redis",
    timeout_seconds=20.0,
    fallback=lambda: compute_expensive_value()
)
async def get_cached_value(key: str):
    return await redis.get(key)
```

**Rationale:** Cache misses are acceptable; compute on demand.

---

### Database (Critical)

**Strategy:** No fallback - must succeed

```python
@resilient(
    circuit_breaker_name="database",
    timeout_seconds=30.0,
    fallback=None  # Re-raise errors
)
async def save_document(doc: Document):
    return await db.insert(doc)
```

**Rationale:** Database operations are critical. Better to fail fast and alert than continue with data loss.

---

## 🎭 Fallback Decision Matrix

| Service | Criticality | Fallback Strategy | Reason |
|---------|-------------|-------------------|---------|
| **Database** | 🔴 Critical | None (re-raise) | Data integrity required |
| **Embedding** | 🟡 Important | None (re-raise) | Search quality required |
| **LLM** | 🟡 Important | Cached/Skip | Can retry later |
| **ChromaDB** | 🟡 Important | Keyword search | Some results better than none |
| **Redis** | 🟢 Non-Critical | Direct compute | Cache optimization only |
| **File Read** | 🔴 Critical | None (re-raise) | Can't process without content |
| **Normalization** | 🟡 Important | Raw content | Some format better than none |
| **Parsing** | 🟡 Important | Text extraction | Basic content better than none |

---

## 🔄 Fallback with Retry

### Pattern: Exponential Backoff with Fallback

```python
from src.utils.resilience import resilient

@resilient(
    circuit_breaker_name="flaky_service",
    timeout_seconds=30.0,
    fallback=FallbackStrategies.empty_list,
    failure_threshold=3  # Open circuit after 3 failures
)
async def get_data_with_retry():
    # Will retry up to 3 times before using fallback
    return await flaky_service.fetch()
```

### Pattern: Multi-Tier Fallback

```python
async def get_data():
    try:
        # Tier 1: Primary service
        return await primary_service.fetch()
    except Exception as e1:
        logger.warning(f"Primary failed: {e1}")
        try:
            # Tier 2: Secondary service
            return await secondary_service.fetch()
        except Exception as e2:
            logger.warning(f"Secondary failed: {e2}")
            # Tier 3: Cache
            try:
                return await cache.get("last_known_good")
            except Exception as e3:
                logger.error(f"All tiers failed: {e3}")
                # Tier 4: Static fallback
                return FallbackStrategies.empty_list()
```

---

## 📈 Monitoring Fallback Usage

### Health Check Integration

```python
from src.utils.resilience import get_all_service_health

# Check which services are using fallbacks
health = await get_all_service_health()

for service_name, status in health.items():
    if status["healthy"] == False:
        logger.warning(f"⚠️  {service_name} unhealthy - using fallbacks")
```

### Metrics to Track

1. **Fallback Frequency:** How often each fallback is used
2. **Service Availability:** Uptime percentage per service
3. **Circuit Breaker State:** Current state of each breaker
4. **Degraded Mode Duration:** Time spent in fallback mode

---

## 🎯 Best Practices

### DO:
- ✅ Use fallbacks for non-critical operations
- ✅ Log when fallbacks are used
- ✅ Monitor fallback frequency
- ✅ Test fallback paths regularly
- ✅ Document what each fallback returns
- ✅ Make fallbacks fast (no expensive operations)

### DON'T:
- ❌ Use fallbacks for critical data operations
- ❌ Hide errors with fallbacks (log them!)
- ❌ Use fallbacks that could cause data corruption
- ❌ Make fallback logic complex (keep it simple)
- ❌ Forget to test fallback code paths

---

## 🧪 Testing Fallback Strategies

### Unit Test Example

```python
import pytest
from src.utils.resilience import resilient, FallbackStrategies

@pytest.mark.asyncio
async def test_fallback_on_failure():
    """Test fallback is used when operation fails."""
    
    @resilient(
        circuit_breaker_name="test_service",
        timeout_seconds=1.0,
        fallback=FallbackStrategies.empty_list
    )
    async def failing_operation():
        raise Exception("Simulated failure")
    
    # Should return fallback instead of raising
    result = await failing_operation()
    assert result == []
```

### Integration Test Example

```python
@pytest.mark.integration
async def test_system_continues_with_service_down():
    """Test system continues operating with service down."""
    
    # Simulate service failure
    with mock_service_down("embedding_service"):
        # System should continue with fallback
        result = await process_document(doc)
        
        # Document processed (without embedding)
        assert result["success"] == True
        assert result.get("embedding_skipped") == True
```

---

## 📊 Current Implementation Status

### Implemented ✅

1. **FallbackStrategies class** (resilience.py)
   - Empty collections
   - None value
   - Default embedding
   - Skip operation
   - Custom defaults

2. **@resilient decorator** (resilience.py)
   - Circuit breaker integration
   - Timeout protection
   - Fallback support
   - Error logging

3. **Health monitoring** (resilience.py)
   - Service health checks
   - Circuit breaker states
   - Failure rate tracking

### Applied To ✅

- ✅ Embedding service (embedding_client.py)
- ✅ Database operations (database.py - circuit breaker)
- ✅ LLM queries (recoverable_doc_generator.py - timeout)
- ⏳ File processing (has error handling, could add fallbacks)
- ⏳ Normalization (has error handling, could add fallbacks)

---

## 🚀 Future Enhancements

1. **Adaptive Fallbacks:**
   - Learn which fallbacks work best
   - Adjust strategy based on success rate

2. **Graceful Degradation Levels:**
   - Level 1: Full functionality
   - Level 2: Reduced functionality
   - Level 3: Core functionality only
   - Level 4: Read-only mode

3. **Automatic Fallback Selection:**
   - AI-powered fallback choice
   - Based on error type and context

4. **Fallback Metrics Dashboard:**
   - Visualize fallback usage
   - Alert on excessive fallbacks
   - Track recovery time

---

## 📝 Summary

**Status:** ✅ **COMPLETE**

**Coverage:**
- ✅ 5 pre-built fallback strategies
- ✅ 3 integration patterns
- ✅ Service-specific strategies documented
- ✅ Decision matrix provided
- ✅ Best practices defined
- ✅ Testing examples included

**Benefits:**
- 🛡️ Graceful degradation
- 📊 Better user experience
- 🔄 System resilience
- 📈 Improved availability

---

*Generated: October 21, 2025*  
*Phase 10 - Day 3 - Task 3.2*

