**Date:** October 29, 2025  
**Status:** 🔧 Root Cause Identified - Fix Ready  

# Ingestion Worker Fix Plan

## 🎯 Root Cause Identified

**Problem**: `_get_next_job()` is hanging on `redis.read_from_stream()`

### Evidence
1. Worker heartbeat shows loop is running (Loop #178, #180, #182)
2. Calls to `_get_next_job()` made every 5 seconds
3. **NO logs from inside `_get_next_job()`** - not even the first log line
4. This means the function is hanging BEFORE the first `logger.info()`

### Why is it hanging?
`redis.read_from_stream()` with `block=1000` should only block for 1 second, but it appears to be blocking indefinitely. This could be due to:

1. **Redis connection issue** - Connection dead/stale
2. **Consumer group issue** - Group not properly initialized
3. **Stream name mismatch** - Wrong stream name
4. **Deadlock in Redis client** - Client library issue

## 🔧 Fixes to Implement

### Fix #1: Add timeout to read_from_stream()
```python
# Wrap with asyncio.wait_for() to enforce timeout
try:
    messages = await asyncio.wait_for(
        redis.read_from_stream(
            stream=redis.INGESTION_STREAM,
            consumer_name=f"worker-{self.worker_id}",
            count=1,
            block=1000
        ),
        timeout=3.0  # 3 second timeout
    )
except asyncio.TimeoutError:
    logger.warning("⏱️ read_from_stream() timed out after 3s")
    return None
```

### Fix #2: Verify consumer group before each read
```python
# Ensure consumer group exists before reading
try:
    await redis.client.xgroup_create(
        name=redis.INGESTION_STREAM,
        groupname=redis.CONSUMER_GROUP,
        id='0',
        mkstream=True
    )
except Exception:
    pass  # Group already exists
```

### Fix #3: Reset Redis connection on hang
```python
# Detect hangs and reconnect
if self._last_successful_read and time.time() - self._last_successful_read > 60:
    logger.warning("⚠️ No successful reads in 60s, reconnecting...")
    await redis.connect()
```

### Fix #4: Use XREAD instead of XREADGROUP (simpler, more reliable)
```python
# Fallback to simpler XREAD if XREADGROUP hangs
messages = await redis.client.xread(
    streams={redis.INGESTION_STREAM: '>'},
    count=1,
    block=1000
)
```

## 📋 Implementation Plan

1. ✅ Identify root cause
2. ⏳ Add timeout wrapper (Fix #1)
3. ⏳ Add consumer group verification (Fix #2)
4. ⏳ Test with simple ingestion
5. ⏳ Deploy and monitor

**Status:** Ready to implement fixes...

