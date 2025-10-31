**Date:** October 29, 2025  
**Status:** 🎯 ROOT CAUSE IDENTIFIED!  

# Root Cause: Dead Consumers Holding Messages

## 🔍 Discovery

Redis shows:
- **59 messages** in stream
- **61 dead consumers** 
- **0 pending messages** (all were delivered but never ACK'd)
- **entries-read: 59** (all delivered to dead consumers)

## 💡 The Problem

Every time we restart the service, a NEW consumer is created but the OLD ones remain registered. The 59 messages were delivered to consumers that no longer exist, and they're stuck there.

## 🔧 The Fix

We need to:
1. Delete all dead consumers from the group
2. Reset the consumer group to start fresh
3. OR use XAUTOCLAIM to reclaim stuck messages

### Option 1: Reset Consumer Group (Nuclear)
```bash
# Delete the group
redis-cli XGROUP DESTROY ingestion_queue workers

# Recreate it
redis-cli XGROUP CREATE ingestion_queue workers 0 MKSTREAM

# Worker will now read all 59 messages
```

### Option 2: Auto-claim Stuck Messages (Surgical)
```python
# In worker, use XAUTOCLAIM instead of XREADGROUP
await redis.xautoclaim(
    name="ingestion_queue",
    groupname="workers",
    consumername=f"worker-{self.worker_id}",
    min_idle_time=5000,  # 5 seconds
    start_id="0-0",
    count=10
)
```

## ✅ Implementing Fix...

