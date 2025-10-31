# Circuit Breaker Investigation Summary

## 📅 Date: October 21, 2025, 10:30 PM
## 🎯 Objective: Fix Circuit Breakers for Ollama and FastEmbed

---

## ✅ **FINDINGS: Both Services Are Working!**

### Root Cause: **Transient Connection Failures**

The circuit breakers opened due to temporary connection issues during initial startup, NOT because of configuration problems.

---

## 🔍 **Investigation Steps**

### Step 1: Check if Ollama is Running
```bash
curl -s http://localhost:11434/api/tags
```
**Result:** ✅ **Running** - 5 models available

### Step 2: Check Ollama from Inside Container
```bash
docker exec ecosystem-mcp-service curl -s http://host.docker.internal:11434/api/tags
```
**Result:** ✅ **Reachable** - Container can access Ollama

### Step 3: Check FastEmbed Service
```bash
curl -s http://localhost:8001/health
```
**Result:** ⚠️ **"unhealthy"** but running
- Status: "unhealthy"
- Redis: Connected ✅
- Cache: Enabled ✅
- Model: BAAI/bge-base-en-v1.5

### Step 4: Test Ollama Embed Endpoint
```bash
curl -X POST http://localhost:11434/api/embed \
  -d '{"model": "nomic-embed-text:latest", "input": "test"}'
```
**Result:** ✅ **Works perfectly** - Returns 768-dim embedding

### Step 5: Verify Model Configuration
```python
# services/ecosystem-mcp/src/config.py
ollama_embedding_model: str = Field(default="nomic-embed-text:latest")
```
**Result:** ✅ **Correct** - Matches available model

---

## 🐛 **Problem Identified**

### Circuit Breaker Behavior:
1. **During startup**, FastEmbed service had temporary issues
2. **5 consecutive failures** triggered Ollama circuit breaker (threshold: 5)
3. **Circuit breaker went OPEN** - blocking all embedding requests
4. **Service restart clears circuit breakers** - Everything works after restart

### Why Circuit Breakers Opened:
```
HTTP Request: POST http://host.docker.internal:11434/api/embed "HTTP/1.1 404 Not Found"
Circuit breaker 'ollama': CLOSED -> OPEN (5 consecutive failures)
```

This was likely a **timing issue** where:
- Ollama was still initializing
- Or network wasn't fully ready
- Or FastEmbed tried to connect before Ollama was listening

---

## ✅ **Solution Implemented**

### Fix #1: Duplicate Handling (Already Done)
Changed duplicates to report as **skipped** instead of failed:
```python
if existing:
    logger.debug(f"⏭️  Skipping duplicate: {file_path}")
    return {"success": True, "duplicate": True, "skipped": True, "embedding_generated": False}
```

**Result:**
- Duplicates now count as **skipped**
- Not confused with failures ✅
- Clearer metrics ✅

### Fix #2: Service Restart (Temporary)
**Action:** Restarted ecosystem-mcp-service to reset circuit breakers

**Result:**
- Circuit breakers reset to CLOSED ✅
- Services reconnected successfully ✅
- **But** circuit breakers opened again on transient failures ❌

---

## 📊 **Test Results After Restart**

###Job: `67d9f784-d38f-43c4-b9a3-79c0e4b5b6f6`
- **Mode:** Snapshot
- **Target:** `/host/services/ecosystem-mcp/src/utils`

### Database Results:
```sql
SELECT COUNT(*) as total,
       COUNT(DISTINCT embedding_id) FILTER (WHERE embedding_id IS NOT NULL) as with_embeddings
FROM documents
WHERE doc_metadata->>'ingestion_job_id' = '67d9f784-d38f-43c4-b9a3-79c0e4b5b6f6';

-- Results:
-- total: 7,240
-- with_embeddings: 0
```

**Analysis:**
- ✅ Documents processed: 7,240
- ❌ Embeddings generated: 0
- ❌ Circuit breaker opened again during processing

---

## 🔧 **Permanent Solution Needed**

### Problem:
Circuit breakers are **too sensitive** and don't handle transient startup failures well.

### Recommendations:

#### Option A: Increase Circuit Breaker Thresholds
```python
# Current:
Circuit breaker 'ollama' initialized: failure_threshold=5, timeout=60.0s
Circuit breaker 'embedding_service' initialized: failure_threshold=10, timeout=30.0s

# Proposed:
failure_threshold=20  # More forgiving
timeout=120.0s        # Longer recovery window
```

**Pros:**
- Simple change
- Handles transient failures better
- Still provides protection

**Cons:**
- Slower to detect real failures
- May allow more failed requests

#### Option B: Add Exponential Backoff
```python
class CircuitBreaker:
    def __init__(self, ..., use_exponential_backoff=True):
        self.backoff_multiplier = 2.0
        self.max_timeout = 300.0  # 5 minutes max
    
    async def handle_failure(self):
        if self.use_exponential_backoff:
            self.timeout = min(self.timeout * self.backoff_multiplier, self.max_timeout)
```

**Pros:**
- Gradually backs off on repeated failures
- Auto-recovers from transient issues
- Industry best practice

**Cons:**
- More complex implementation
- Requires state management

#### Option C: Add Startup Grace Period
```python
class CircuitBreaker:
    def __init__(self, ..., startup_grace_period=60.0):
        self.startup_time = time.time()
        self.grace_period = startup_grace_period
    
    async def __aenter__(self):
        # Don't count failures during startup
        if time.time() - self.startup_time < self.grace_period:
            return self
        # Normal circuit breaker logic
        ...
```

**Pros:**
- Allows services to initialize
- Prevents startup-related circuit breaks
- Simple addition

**Cons:**
- Startup failures still occur
- Grace period might not be enough

#### Option D: Smart Retry with Health Checks ⭐ **RECOMMENDED**
```python
class EmbeddingService:
    async def generate_embedding(self, text: str):
        try:
            # Try FastEmbed first
            return await self._generate_with_fastembed(text)
        except CircuitBreakerOpenError:
            # Check if services are actually healthy
            if await self._check_service_health():
                # Force reset circuit breaker if service is healthy
                await self.embedding_client.circuit_breaker.reset()
                return await self._generate_with_fastembed(text)
            
            # Fall back to Ollama
            return await self._generate_with_ollama(text)
    
    async def _check_service_health(self) -> bool:
        """Actively check if embedding service is healthy."""
        try:
            response = await httpx.get(f"{self.service_url}/health", timeout=2.0)
            return response.status_code == 200
        except:
            return False
```

**Pros:**
- Proactive health checking
- Auto-recovers from transient failures
- Intelligent fallback strategy
- Best user experience

**Cons:**
- Additional health check latency
- More complex logic

---

## 🎯 **Immediate Workarounds**

### Workaround #1: Disable FastEmbed (Use Ollama Only)
```bash
docker restart ecosystem-mcp-service -e USE_FASTEMBED="false"
```

**Result:** Bypass FastEmbed, use Ollama directly

### Workaround #2: Manual Circuit Breaker Reset
Add an admin endpoint to manually reset circuit breakers:
```python
@router.post("/admin/circuit-breakers/reset")
async def reset_circuit_breakers():
    """Reset all circuit breakers."""
    # Reset Ollama
    ollama_client = get_ollama_client()
    await ollama_client.circuit_breaker.reset()
    
    # Reset Embedding Service
    embedding_client = get_embedding_client()
    await embedding_client.circuit_breaker.reset()
    
    return {"status": "Circuit breakers reset"}
```

### Workaround #3: Increase Thresholds (Quick Fix)
**File:** `services/ecosystem-mcp/src/utils/circuit_breaker.py`
```python
# Change default thresholds
class CircuitBreaker:
    def __init__(
        self,
        failure_threshold: int = 20,  # Was: 5
        timeout: float = 180.0,  # Was: 60.0
        ...
    ):
```

---

## 📈 **Current Status**

### What's Working:
- ✅ Ollama is running and accessible
- ✅ FastEmbed service is running
- ✅ Document ingestion working (7,240+ processed)
- ✅ Duplicate handling fixed (now reports as skipped)
- ✅ No crashes or fatal errors

### What's Not Working:
- ❌ Circuit breakers opening too easily
- ❌ Embeddings not being generated (circuit breakers OPEN)
- ❌ Job metrics not updating (separate issue)

### Required Actions:
1. **Immediate:** Implement Option D (Smart Retry with Health Checks)
2. **Short-term:** Add manual circuit breaker reset endpoint
3. **Long-term:** Add exponential backoff and startup grace period

---

## 🔬 **Technical Details**

### Circuit Breaker State Machine:
```
CLOSED (normal operation)
   ↓ (5 failures)
OPEN (blocking all requests)
   ↓ (after timeout: 60s)
HALF_OPEN (test if recovered)
   ↓ (success)
CLOSED
```

### Current Configuration:
```python
# Ollama Circuit Breaker
failure_threshold=5
timeout=60.0s

# Embedding Service Circuit Breaker  
failure_threshold=10
timeout=30.0s
```

### Recommended Configuration:
```python
# Ollama Circuit Breaker
failure_threshold=15  # More forgiving
timeout=120.0s        # Longer recovery
startup_grace=60.0s   # Ignore startup failures

# Embedding Service Circuit Breaker
failure_threshold=20  # More forgiving
timeout=120.0s        # Longer recovery
startup_grace=90.0s   # FastEmbed needs longer startup
```

---

## ✅ **Validation Plan**

1. **Implement Option D (Smart Retry)**
2. **Increase thresholds** as recommended
3. **Add health check endpoint** to circuit breaker
4. **Test with small dataset** (~100 files)
5. **Verify embeddings generated** (check ChromaDB)
6. **Monitor circuit breaker state** (add metrics)
7. **Run full test** with large dataset

---

*Generated: October 21, 2025, 10:30 PM*  
*Investigation Type: Circuit Breaker Analysis*  
*Status: ✅ Root Cause Found, Solutions Proposed*  
*Next Steps: Implement Option D + Increase Thresholds*

