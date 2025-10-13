# RAG Query Endpoint - Fixed

## Issue

RAG Query Interface was showing a 500 error when trying to ask questions.

## Root Causes (Fixed in Order)

### 1. Undefined `get_settings()` Function
**Error:** `NameError: name 'get_settings' is not defined`

**Location:** `src/api/routes/ask.py:152`

**Fix:** Removed the redundant `settings = get_settings()` call since `settings` is already imported at the module level.

### 2. Missing Settings Attributes
**Error:** `AttributeError: 'Settings' object has no attribute 'rate_limit_enabled'`

**Location:** `src/api/routes/ask.py:153`

**Fix:** Removed the rate limiting code that referenced non-existent settings attributes (`rate_limit_enabled` and `rag_rate_limit`). These attributes don't exist in the `Settings` class.

### 3. Missing Async Context Manager Support
**Error:** `'CircuitBreaker' object does not support the asynchronous context manager protocol`

**Location:** `src/storage/chromadb_client.py` and `src/services/models/ollama_client.py`

**Fix:** Added `__aenter__` and `__aexit__` methods to the `CircuitBreaker` class to support `async with` syntax.

## Files Modified

### 1. `src/api/routes/ask.py`
**Changes:**
- Line 152: Removed `settings = get_settings()` call
- Lines 151-154: Commented out rate limiting code that referenced non-existent settings

**Before:**
```python
# Apply rate limiting if enabled
settings = get_settings()
if settings.rate_limit_enabled:
    await limiter.limit(settings.rag_rate_limit)(lambda: None)()
```

**After:**
```python
# Rate limiting would go here if configured in settings
# Currently not enabled - would need to add rate_limit_enabled and rag_rate_limit to Settings
```

### 2. `src/utils/circuit_breaker.py`
**Changes:**
- Lines 324-348: Added async context manager support

**Added Methods:**
```python
async def __aenter__(self):
    """Async context manager entry - check if circuit is open."""
    if self.stats.state == CircuitState.OPEN:
        if not self._should_attempt_reset():
            raise CircuitBreakerOpenError(
                f"Circuit breaker '{self.name}' is OPEN"
            )
        # Try to transition to HALF_OPEN
        async with self._lock:
            if self.stats.state == CircuitState.OPEN:
                logger.info(f"Circuit breaker '{self.name}': OPEN -> HALF_OPEN (testing recovery)")
                self.stats.state = CircuitState.HALF_OPEN
                self.stats.success_count = 0
                self.stats.failure_count = 0
    return self

async def __aexit__(self, exc_type, exc_val, exc_tb):
    """Async context manager exit - record success or failure."""
    if exc_type is None:
        # Success
        await self._record_success()
    else:
        # Failure
        await self._record_failure()
    return False  # Don't suppress exceptions
```

## How Circuit Breaker Context Manager Works

The circuit breaker can now be used with `async with`:

```python
async with self.circuit_breaker:
    # Protected code here
    result = await some_operation()
    return result
```

**Behavior:**
1. **On Entry (`__aenter__`):**
   - If circuit is CLOSED: Continue normally
   - If circuit is OPEN and timeout not elapsed: Raise `CircuitBreakerOpenError`
   - If circuit is OPEN and timeout elapsed: Transition to HALF_OPEN (testing)

2. **On Exit (`__aexit__`):**
   - If no exception: Record success
   - If exception occurred: Record failure
   - Exception is not suppressed (propagates normally)

3. **State Transitions:**
   - CLOSED → OPEN: After failure threshold reached
   - OPEN → HALF_OPEN: After timeout elapsed
   - HALF_OPEN → CLOSED: After success threshold reached
   - HALF_OPEN → OPEN: If any test fails

## Testing

### Test RAG Query Endpoint

```bash
curl -X POST "http://localhost:8000/api/v1/ask" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "What is ecosystem-mcp?",
    "n_results": 5
  }'
```

**Expected Response:**
```json
{
  "answer": "Based on the provided context, ecosystem-mcp refers to the Ecosystem MCP Service...",
  "sources": [
    {
      "id": 1,
      "file_path": "services/ecosystem-mcp/src/api/__init__.py",
      "relevance_score": 0.332,
      "adjusted_score": 0.482,
      "recency_days": 1,
      "updated_at": "2025-10-12T20:08:18.142905"
    }
  ],
  "confidence": 0.85,
  "metadata": {...}
}
```

### Test via Dashboard

1. Open: http://localhost:8501/
2. Navigate to: **🤖 RAG Query Interface**
3. Enter a question: "What is ecosystem-mcp?"
4. Click "🔍 Ask Question"
5. ✅ Should display answer with sources

## Status

✅ **Fixed**: RAG endpoint working correctly  
✅ **Fixed**: Circuit breakers support async context manager  
✅ **Fixed**: Removed undefined settings references  
✅ **Tested**: Successfully answering questions  
✅ **Zero Lint Errors**: Clean code  

## Related Issues Fixed

As part of this session, we also fixed:
- Container logs displaying correctly (list to string conversion)
- Circuit breaker status display (added `get_state()` method)
- Database diagnostics error (removed `get_settings()` call)

## What's Working Now

The RAG (Retrieval Augmented Generation) system is fully operational:

1. **Semantic Search**: Finds relevant documents using ChromaDB
2. **Recency Scoring**: Boosts recent documents
3. **LLM Answer Generation**: Uses Ollama to synthesize answers
4. **Source Citation**: Provides references with relevance scores
5. **Circuit Breaker Protection**: Automatic failure handling for Ollama and ChromaDB
6. **Confidence Scoring**: Estimates answer quality

## Next Steps (Optional)

If you want to add rate limiting in the future:

1. Add to `src/config.py` Settings class:
```python
rate_limit_enabled: bool = Field(default=False)
rag_rate_limit: str = Field(default="10/minute")
```

2. Uncomment and update the rate limiting code in `src/api/routes/ask.py`

But for now, the endpoint works perfectly without rate limiting!

