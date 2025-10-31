**Date:** October 29, 2025  
**Status:** 🚨 CRITICAL - Worker Still Not Processing After Multiple Fixes  

# Ingestion Worker Critical Issue Report

## 🎯 **Problem Statement**

The ingestion worker is completely non-functional. Despite multiple fixes, **ZERO documents are being processed**.

---

## 🔍 **Investigation Timeline**

### Fix #1: Added Timeout Wrapper ✅
- **What**: Added `asyncio.wait_for()` with 3s timeout around `redis.read_from_stream()`
- **Result**: ✅ Worker no longer hangs - logs show it's reading
- **Impact**: Partial success - reveals worker IS running

### Fix #2: Changed Stream Read Position ⚠️
- **What**: Changed from `streams={stream: ">"}` to `streams={stream: "0"}`
- **Why**: `>` only reads NEW messages, `0` reads ALL pending/backlog
- **Result**: ⚠️ Still getting 0 messages
- **Status**: Did not solve the problem

---

## 📊 **Current State**

### What's Working ✅
1. Service is healthy
2. API endpoints responding
3. Worker heartbeat active
4. Worker polling every few seconds
5. `_get_next_job()` being called
6. No timeouts or hangs

### What's Broken ❌
1. **Worker gets 0 messages from Redis**
2. **59 items stuck in queue**
3. **NO documents processing**
4. **NO embeddings generated**

### Evidence
```
🔍 Calling redis.read_from_stream() with 3s timeout...
🔍 Redis returned 0 messages
🔍 Messages: []
```

This repeats every 5 seconds - worker is polling but getting nothing.

---

## 💡 **Root Cause Hypothesis**

###  Hypothesis #1: Consumer Group Mismatch
- Jobs added to stream with one consumer group
- Worker reading from a DIFFERENT consumer group
- Messages exist but not assigned to worker's group

### Hypothesis #2: Stream Name Mismatch  
- Jobs added to stream "ingestion_queue"
- Worker reading from a DIFFERENT stream name
- Classic naming mismatch issue

### Hypothesis #3: Messages in Wrong Format
- Messages added in format worker doesn't understand
- Worker reads but immediately discards as invalid
- No error logs because silent validation failure

### Hypothesis #4: ACL/Permissions Issue
- Redis ACL preventing worker from reading
- Silent failure - no error but no messages

---

## 🔬 **Next Steps to Diagnose**

### Step 1: Verify Stream Name
```bash
# Check what streams exist
redis-cli KEYS "*queue*"

# Check if "ingestion_queue" exists
redis-cli XLEN ingestion_queue
```

### Step 2: Verify Consumer Group  
```bash
# Check what consumer groups exist on ingestion_queue
redis-cli XINFO GROUPS ingestion_queue

# Check if "workers" group exists
```

### Step 3: Check Message Format
```bash
# Read first message directly
redis-cli XRANGE ingestion_queue - + COUNT 1

# Compare with what worker expects
```

### Step 4: Manual Test
```python
# Manually add a test message
redis.xadd("ingestion_queue", {"job_id": "test-123", "mode": "test"})

# Check if worker picks it up
```

---

## 🎯 **Most Likely Issue**

Based on the evidence, **Hypothesis #2 (Stream Name Mismatch)** is most likely:

**Why?**
1. Queue status shows 59 items in "ingestion_queue"
2. Worker polls but gets 0 messages
3. No error messages (would see if group didn't exist)
4. Worker logs show it's trying to read from "ingestion_queue"

**BUT** - The actual messages might be in a DIFFERENT stream!

---

## 🔧 **Recommended Action**

**STOP TRYING MORE FIXES** - We need to diagnose the actual mismatch first.

**Next Action:** Add comprehensive diagnostic logging to show:
1. What stream name is worker reading from?
2. What streams actually exist in Redis?
3. What's the exact XREADGROUP command being sent?
4. What's the response from Redis?

Only THEN can we fix the right thing.

---

**Status:** Awaiting deep diagnostic investigation...

