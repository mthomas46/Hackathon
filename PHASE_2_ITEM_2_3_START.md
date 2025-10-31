**Date:** October 28, 2025  
**Status:** Item 2.3 Starting - Event-Driven Architecture  
**Complexity:** High (4 hours estimated)  

# Phase 2 Item 2.3: Event-Driven Architecture

## 🎯 Goal

Replace wasteful polling loops with event-driven architecture using Redis pub/sub.

---

## 📊 Current State - Polling Everywhere

**Problem:** 450+ `sleep()` calls across the codebase
- Many are polling loops checking for status changes
- Wasteful CPU usage (constant checking)
- Poor responsiveness (bounded by sleep interval)
- Inefficient resource utilization

**Top Offenders:**
1. Job status polling (job_processor.py)
2. Worker health monitoring  
3. Dashboard status checks

---

## 🎯 Target Architecture

### Event-Driven Model
```
┌─────────────┐        ┌─────────────┐        ┌─────────────┐
│   Producer  │───────▶│ Redis PubSub│───────▶│  Consumer   │
│  (updates)  │ Publish│   Channel   │Subscribe│  (waiter)   │
└─────────────┘        └─────────────┘        └─────────────┘
```

### Hybrid Approach (Reliable)
```
Event-driven (fast path):
  ✅ Publish event on status change
  ✅ Subscribers wake immediately
  ✅ 0ms wait time

Fallback polling (safety net):
  ✅ Timeout after N seconds
  ✅ Poll once more as backup
  ✅ Handles missed events
```

---

## 📋 Implementation Plan

### Phase 1: Infrastructure (1 hour)
1. Create event system module
   - Redis pub/sub wrapper
   - Event registry
   - Typed event classes

2. Add event publisher utility
   - Publish to Redis channel
   - Graceful degradation if Redis unavailable

3. Add event subscriber utility
   - Subscribe to channels
   - Async event waiting with timeout

### Phase 2: Job Status Events (1.5 hours)
1. Identify polling in job_processor.py
2. Add job status change events
3. Replace polling with event waiting
4. Maintain fallback polling

### Phase 3: Worker Monitoring (1 hour)
1. Add worker heartbeat events
2. Replace polling with event-driven checks
3. Maintain fallback polling

### Phase 4: Testing & Validation (0.5 hours)
1. Test event-driven flow
2. Test fallback polling
3. Test Redis unavailable scenario
4. Measure CPU reduction

---

## 🔧 Technical Design

### Event Types
```python
class JobStatusChangedEvent:
    job_id: str
    old_status: str
    new_status: str
    timestamp: datetime

class WorkerHeartbeatEvent:
    worker_id: str
    job_id: str
    timestamp: datetime
```

### Event Channels
```
job_status:{job_id}      - Job-specific updates
worker_heartbeat:{job_id} - Worker health
global_events            - System-wide events
```

### Usage Pattern
```python
# Old: Polling
while True:
    job = await get_job_status(job_id)
    if job.status in ['completed', 'failed']:
        return job
    await asyncio.sleep(1.0)  # Wasteful!

# New: Event-driven with fallback
event = asyncio.Event()
subscribe_to_job_status(job_id, event.set)

try:
    await asyncio.wait_for(event.wait(), timeout=300)
    return await get_job_status(job_id)
except asyncio.TimeoutError:
    # Fallback: poll once more
    return await get_job_status(job_id)
```

---

## 📈 Expected Impact

### Performance
- **-30% CPU usage** - Eliminate constant polling
- **Faster response** - Immediate notification vs sleep interval
- **Better scalability** - Fewer wasted cycles

### Reliability
- **Fallback polling** - Handles missed events
- **Timeout protection** - Never hang forever
- **Graceful degradation** - Works without Redis

---

## ⚠️ Risks & Mitigation

### Risk 1: Missed Events
**Mitigation:** Fallback polling after timeout

### Risk 2: Redis Unavailable
**Mitigation:** Fall back to pure polling

### Risk 3: Race Conditions
**Mitigation:**
- Atomic event publishing
- Event sequence numbers
- Idempotent handlers

---

**Status:** Starting Phase 1 - Infrastructure Setup
