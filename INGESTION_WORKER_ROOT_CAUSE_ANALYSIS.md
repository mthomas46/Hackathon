**Date:** October 29, 2025  
**Status:** 🎯 ROOT CAUSE IDENTIFIED!  

# Ingestion Worker - Root Cause Analysis

## 🔍 **Complete Codepath Trace**

### 1. Job Creation Flow ✅
\`\`\`
POST /api/v1/admin/ingest
  → Create job in database (status="queued")
  → Add to Redis stream: XADD ingestion_queue {job_id, mode, repo_path}
  → Return job_id to client
\`\`\`

### 2. Worker Initialization ✅
\`\`\`
App startup (app.py:184-186)
  → get_ingestion_worker() [singleton]
  → worker.start()
    → Test Redis connection
    → Set self.running = True
    → Create asyncio.Task(_worker_loop())
\`\`\`

### 3. Worker Loop ✅
\`\`\`python
while self.running:
    # Send heartbeat every 10s
    # Recover pending every 5 min
    
    result = await _get_next_job()
    
    if result:
        message_id, job_id = result
        await _process_job(job_id, message_id)
        await redis.xack(stream, group, message_id)
    else:
        await asyncio.sleep(5)
\`\`\`

### 4. Message Reading ✅
\`\`\`python
async def _get_next_job():
    messages = await redis.read_from_stream(
        stream="ingestion_queue",
        consumer_name=f"worker-{worker_id}",
        count=1,
        block=1000
    )
\`\`\`

### 5. Redis Stream Read Implementation ✅
\`\`\`python
async def read_from_stream():
    messages = await client.xreadgroup(
        groupname="workers",
        consumername=consumer_name,
        streams={stream: ">"},  # ❌ THIS IS THE PROBLEM!
        count=count,
        block=block
    )
\`\`\`

---

## 🎯 **THE ACTUAL PROBLEM**

### Redis Stream State:
\`\`\`
Stream: ingestion_queue
  - Length: 60 messages
  - Message IDs: 1761564096482-0 to 1761773570729-0

Consumer Group: workers
  - last-delivered-id: 1761773570729-0 (most recent)
  - entries-read: 60 (all delivered)
  - pending: 0 (no messages pending for active consumers)
  - consumers: 2 (current active)
\`\`\`

### What `streams={stream: ">"}` Means:
- `>` = Read messages AFTER `last-delivered-id`
- `last-delivered-id` is 1761773570729-0
- All messages are BEFORE this ID
- **Result: 0 messages returned**

### Why This Happened:
1. Service restarted multiple times (61 dead consumers)
2. Each restart created a new consumer
3. Messages were delivered to old consumers
4. `last-delivered-id` pointer moved forward
5. Old consumers died without ACKing
6. Messages are "delivered but not ACKed"
7. New consumer can't see them with `>`

---

## 💡 **The Solution**

We need to read **pending messages** (delivered but not ACKed), NOT new messages.

### Option 1: Use XAUTOCLAIM (Recommended)
\`\`\`python
# Instead of XREADGROUP with ">", use XAUTOCLAIM
messages = await redis.client.xautoclaim(
    name="ingestion_queue",
    groupname="workers",
    consumername=consumer_name,
    min_idle_time=5000,  # 5 seconds
    start_id="0-0",
    count=10
)
\`\`\`

**Why this works:**
- Claims messages from dead consumers
- Takes ownership of pending messages
- Automatically reassigns to current consumer
- Perfect for our scenario

### Option 2: Use XPENDING + XCLAIM
\`\`\`python
# 1. Find pending messages
pending = await redis.client.xpending_range(
    name="ingestion_queue",
    groupname="workers",
    min="-",
    max="+",
    count=10
)

# 2. Claim them
for msg in pending:
    claimed = await redis.client.xclaim(
        name="ingestion_queue",
        groupname="workers",
        consumername=consumer_name,
        min_idle_time=5000,
        message_ids=[msg['message_id']]
    )
\`\`\`

**More manual, but same result.**

### Option 3: Reset Group on Every Startup (Nuclear)
\`\`\`python
# On worker startup, reset the group
await redis.client.xgroup_setid(
    name="ingestion_queue",
    groupname="workers",
    id="0-0"  # Start from beginning
)
\`\`\`

**Why this works:**
- Resets `last-delivered-id` to 0
- Now `>` will read all messages
- Simple but loses delivery tracking

---

## 🎯 **Recommended Fix (Phased)**

### Phase 1: Immediate Fix (5 min)
Change worker to use BOTH `>` AND XAUTOCLAIM:

\`\`\`python
async def read_from_stream():
    # Try to read new messages first
    messages = await client.xreadgroup(
        groupname="workers",
        consumername=consumer_name,
        streams={stream: ">"},
        count=count,
        block=block
    )
    
    if not messages:
        # No new messages, try to claim pending ones
        claimed = await client.xautoclaim(
            name=stream,
            groupname="workers",
            consumername=consumer_name,
            min_idle_time=5000,  # 5 seconds idle
            start_id="0-0",
            count=count
        )
        if claimed and claimed[1]:  # claimed[1] is the messages list
            messages = [(stream, claimed[1])]
    
    return parse_messages(messages)
\`\`\`

**Benefits:**
- Reads new messages normally
- Falls back to claiming pending messages
- Handles both scenarios
- No data loss

### Phase 2: Startup Recovery (10 min)
Add startup recovery in worker.start():

\`\`\`python
async def start(self):
    # ... existing code ...
    
    # Recover pending messages on startup
    logger.info("�� Checking for pending messages...")
    pending_count = await self._claim_pending_messages()
    if pending_count > 0:
        logger.warning(f"⚠️  Claimed {pending_count} pending messages from dead consumers")
\`\`\`

### Phase 3: Consumer Cleanup (15 min)
Add dead consumer detection and removal:

\`\`\`python
async def cleanup_dead_consumers(self):
    # Get all consumers
    groups = await redis.client.xinfo_groups(stream)
    for group in groups:
        consumers = await redis.client.xinfo_consumers(stream, group['name'])
        
        # Find idle consumers (no activity for 1 hour)
        for consumer in consumers:
            if consumer['idle'] > 3600000:  # 1 hour in ms
                # Delete dead consumer
                await redis.client.xgroup_delconsumer(
                    stream,
                    group['name'],
                    consumer['name']
                )
\`\`\`

---

## ✅ **Summary**

**Problem:** Worker using `>` to read new messages, but all messages were already delivered to dead consumers.

**Root Cause:** Consumer group's `last-delivered-id` pointer is ahead of all messages in stream.

**Solution:** Use XAUTOCLAIM to reclaim pending messages from dead consumers.

**Implementation:** Phased approach starting with simple fallback, then adding recovery and cleanup.

**Status:** Ready to implement Phase 1 fix!


---

## 🔄 **Update After Initial Fix Attempt**

### What We Tried:
- Implemented XAUTOCLAIM fallback in `read_from_stream()`
- Restarted service

### Result:
- Still 0 messages being processed
- XAUTOCLAIM not finding any pending messages

### Why?
**XAUTOCLAIM only works for messages that are PENDING** (delivered but not ACKed).

Our messages are NOT pending - they're just sitting in the stream undelivered!

When we ran `XGROUP SETID ingestion_queue workers 0-0`, we reset the pointer, but the service has already restarted and the group pointer may have moved again.

### Real Fix Needed:
We need to **ensure the group pointer stays at 0-0** so that `>` reads from the beginning.

The issue is that the pointer gets reset, but then immediately moves forward when the worker starts and there are no messages (or if there's a race condition).

Let me check the actual group state now...

