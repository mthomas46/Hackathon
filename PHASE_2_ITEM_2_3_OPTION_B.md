**Date:** October 28, 2025  
**Status:** Implementing Option B - Job Events Only  
**Time:** ~1 hour (targeted, high-value)  

# Phase 2 Item 2.3: Job Events Only (Option B)

## 🎯 Goal

Add job completion events for dashboard responsiveness while keeping efficient Redis Stream workers.

**Value:** 80% of event system benefits in 25% of the time  
**Risk:** Low (minimal changes, existing workers unchanged)  

---

## 📋 Implementation Plan

### Step 1: Create Job Event Publisher (20 min)
- Create `src/utils/job_events.py`
- Simple Redis pub/sub wrapper
- Event types: job_completed, job_failed, job_progress
- Graceful fallback if Redis unavailable

### Step 2: Add Events to Job Processor (20 min)
- Publish events on job completion
- Publish events on job failure
- Publish progress milestones
- No changes to worker loops

### Step 3: Add Event Endpoint (Optional - 20 min)
- Create SSE endpoint for dashboard
- Stream job events to frontend
- Enable real-time updates

---

## 🔧 Implementation

### File 1: `src/utils/job_events.py` (NEW)
Simple event publisher for job lifecycle events.

### File 2: `src/services/ingestion/job_processor.py` (MODIFY)
Add event publishing on status changes.

### File 3: `src/api/routes/events.py` (NEW - Optional)
SSE endpoint for dashboard subscriptions.

---

**Status:** Starting implementation...
