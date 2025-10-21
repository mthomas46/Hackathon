# Timeout Protection Summary (Phase 10 - Day 2 - Task 2.2)

## Overview

All long-running operations in the Ecosystem MCP service now have timeout protection to prevent hung operations and ensure responsive behavior.

---

## Protected Operations

### 1. **Embedding Generation** ✅

**Location:** `src/services/embeddings/embedding_client.py`

**Timeout Configuration:**
- **Single Embedding:** 30 seconds
- **Batch Embedding:** 60 seconds

**Protection Method:**
```python
@resilient(
    circuit_breaker_name="embedding_service",
    timeout_seconds=30.0,  # or 60.0 for batch
    fallback=None
)
async def generate_embedding(...)
```

**Behavior:**
- Fails fast after timeout
- Circuit breaker tracks failures
- No fallback (embeddings are critical)
- Proper error logging

---

### 2. **File Processing (Commits)** ✅

**Location:** `src/services/ingestion/job_processor.py`

**Timeout Configuration:**
- **Per Commit:** Configurable (default based on mode)
- **With Semaphore:** Controls concurrency

**Protection Method:**
```python
result = await asyncio.wait_for(
    process_task,
    timeout=self.commit_timeout_seconds
)
```

**Behavior:**
- Returns partial results on timeout
- Continues with next commit
- Tracks timeout in statistics
- Detailed logging

---

### 3. **Document Normalization** ⚠️ (Ready for Future)

**Location:** `src/ingestion/normalizer.py`

**Timeout Configuration:**
- **Constant Defined:** `NORMALIZE_TIMEOUT_SECONDS = 30.0`
- **Currently Sync:** No timeout needed yet

**Note:**
- Normalization is currently synchronous and fast (<1s)
- Timeout constant added for future async normalizers
- Ready to apply when needed

---

### 4. **LLM Calls (RAG Queries)** ✅

**Location:** `src/services/documentation/recoverable_doc_generator.py`

**Timeout Configuration:**
- **Initial Timeout:** 120 seconds (LLMs can be slow)
- **Retry with Increase:** 180s, 270s (1.5× increase)

**Protection Method:**
```python
result = await asyncio.wait_for(
    query_service.query(...),
    timeout=timeout_seconds
)
```

**Behavior:**
- 120s timeout for LLM calls
- Retries with longer timeout (1.5×)
- Exponential backoff between retries
- Detailed timeout logging

---

### 5. **Database Operations** ✅ (Pre-existing)

**Location:** `src/storage/database.py`

**Protection:**
- Circuit breaker already in place
- Connection pool with pre-ping
- Pool recycle after 1 hour

**Configuration:**
```python
_db_breaker = get_circuit_breaker(
    name="database",
    failure_threshold=5,
    timeout=30.0
)
```

---

## Timeout Matrix

| Operation | Initial Timeout | Retry Timeout | Max Retries | Fallback |
|-----------|----------------|---------------|-------------|----------|
| **Single Embedding** | 30s | N/A | 0 (via circuit breaker) | None |
| **Batch Embedding** | 60s | N/A | 0 (via circuit breaker) | None |
| **Commit Processing** | Variable | N/A | 0 | Partial results |
| **LLM RAG Query** | 120s | 180s, 270s | 3 | Raise |
| **Normalization** | 30s (future) | N/A | 0 | N/A |
| **Database** | N/A (breaker) | N/A | 0 (breaker handles) | Raise |

---

## Implementation Patterns

### Pattern 1: Resilient Decorator (Recommended)

**Best for:** External service calls (embedding, LLM)

```python
from src.utils.resilience import resilient

@resilient(
    circuit_breaker_name="service_name",
    timeout_seconds=30.0,
    fallback=my_fallback_function
)
async def call_external_service():
    ...
```

**Benefits:**
- ✅ Circuit breaker + timeout + fallback
- ✅ Automatic state management
- ✅ Health monitoring
- ✅ Graceful degradation

---

### Pattern 2: Manual asyncio.wait_for

**Best for:** Internal operations with custom error handling

```python
try:
    result = await asyncio.wait_for(
        long_running_operation(),
        timeout=60.0
    )
except asyncio.TimeoutError:
    logger.error("Operation timed out")
    return {"error": "Timeout"}
```

**Benefits:**
- ✅ Fine-grained control
- ✅ Custom timeout handling
- ✅ No overhead

---

### Pattern 3: with_timeout Decorator

**Best for:** Simple timeout without circuit breaker

```python
from src.utils.resilience import with_timeout

@with_timeout(30.0)
async def simple_operation():
    ...
```

**Benefits:**
- ✅ Clean syntax
- ✅ Minimal overhead
- ✅ Preserves exceptions

---

## Configuration Guidelines

### Timeout Values by Operation Type

1. **Fast Operations (<1s expected):**
   - Timeout: 5-10 seconds
   - Examples: Cache lookups, simple queries

2. **Medium Operations (1-10s expected):**
   - Timeout: 30-60 seconds
   - Examples: Embeddings, normalization, API calls

3. **Slow Operations (10-60s expected):**
   - Timeout: 120-300 seconds
   - Examples: LLM calls, batch processing

4. **Very Slow Operations (1-5min expected):**
   - Timeout: 300-600 seconds
   - Examples: Full repository ingestion, complex analysis

### Circuit Breaker Thresholds

1. **Critical Services (Database):**
   - Failure Threshold: 3
   - Timeout: 120s (longer recovery)

2. **Standard Services (LLM, ChromaDB):**
   - Failure Threshold: 5-7
   - Timeout: 45-60s

3. **Non-Critical Services (Cache, Embeddings):**
   - Failure Threshold: 10-15
   - Timeout: 20-30s (quick recovery)

---

## Monitoring

### Health Check Endpoints

```python
from src.utils.resilience import check_service_health, get_all_service_health

# Check single service
health = await check_service_health("embedding_service")

# Check all services
all_health = await get_all_service_health()
```

### Circuit Breaker States

- **CLOSED:** Normal operation (green)
- **OPEN:** Failing fast (red)
- **HALF_OPEN:** Testing recovery (yellow)

---

## Testing

### Unit Tests

**Location:** `tests/unit/test_resilience.py`

**Coverage:**
- ✅ Timeout success cases
- ✅ Timeout exceeded cases
- ✅ Exception preservation
- ✅ Circuit breaker integration
- ✅ Fallback strategies

### Integration Tests

**Location:** `tests/integration/test_timeout_integration.py` (to be created)

**Should test:**
- End-to-end timeout behavior
- Service recovery after timeout
- Multiple timeout scenarios
- Circuit breaker state transitions

---

## Future Enhancements

### Recommended Additions:

1. **Adaptive Timeouts:**
   - Track average operation time
   - Adjust timeout dynamically
   - P95 + buffer approach

2. **Timeout Metrics:**
   - Track timeout frequency
   - Monitor timeout patterns
   - Alert on spike in timeouts

3. **Graceful Cancellation:**
   - Cancel long-running tasks
   - Clean up resources
   - Proper task lifecycle

4. **Request Budgets:**
   - Time budget for entire request
   - Sub-operations share budget
   - Prevent cascading delays

---

## Best Practices

### DO:
- ✅ Set realistic timeouts based on P95 latency
- ✅ Log timeout events with context
- ✅ Provide fallbacks for non-critical operations
- ✅ Monitor timeout rates
- ✅ Test timeout scenarios

### DON'T:
- ❌ Set timeouts too short (false positives)
- ❌ Set timeouts too long (hung operations)
- ❌ Ignore timeout errors
- ❌ Use same timeout for all operations
- ❌ Forget to clean up on timeout

---

## Summary

**Total Operations Protected:** 4 (+ 1 ready for future)

**Coverage:**
- ✅ External services (embeddings, LLM)
- ✅ Internal operations (file processing)
- ✅ Database operations (via circuit breaker)
- ⏳ Future-ready (normalization)

**Benefits:**
- 🛡️ Prevents hung operations
- ⚡ Fails fast when needed
- 📊 Enables monitoring
- 🔄 Supports retries
- 🎯 Production-ready

**Status:** ✅ **COMPLETE**

---

*Generated: October 21, 2025*  
*Phase 10 - Day 2 - Task 2.2*

