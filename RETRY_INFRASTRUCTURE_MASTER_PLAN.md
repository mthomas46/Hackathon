**Date:** October 26, 2025  
**Status:** 🔧 Master Implementation Plan  
**Version:** 1.0 - Comprehensive Audit + Phased Execution  
**Critical Issue:** 68% failure rate (Job: 19374bb8-3957-454d-a5e0-74e0fad46bcf)  

---

# Retry Infrastructure - Master Implementation Plan

## 📊 **EXECUTIVE SUMMARY**

**Problem:** 68.72% document failure rate with no retry mechanism  
**Root Cause:** Missing comprehensive retry infrastructure  
**Solution:** Phased implementation leveraging 80% existing infrastructure  
**Timeline:** 3 phases, ~12 hours total  
**Risk Level:** Medium (requires service restart, but backward compatible)  

---

## 🔍 **PHASE 0: INFRASTRUCTURE AUDIT**

### **✅ EXISTING INFRASTRUCTURE (Leverage)**

#### **1. Redis Streams Infrastructure** ✅ **EXCELLENT**
**Location:** `services/ecosystem-mcp/src/utils/redis_client.py`

**What Exists:**
```python
class RedisClient:
    INGESTION_STREAM = "ingestion_queue"      ✅ Active
    EMBEDDING_STREAM = "embedding_queue"       ✅ Active  
    FAILED_STREAM = "failed_queue"             ✅ EXISTS BUT UNUSED!
    CONSUMER_GROUP = "workers"                  ✅ Active
    MAX_RETRIES = 3                             ❌ Not enforced
```

**Critical Finding:** 
- ✅ `FAILED_STREAM` already exists as dead letter queue
- ❌ **BUT IT'S NEVER WRITTEN TO!**
- ✅ Consumer group infrastructure ready
- ✅ Stream operations (`xadd`, `xread`, `xack`) implemented

**What's Missing:**
- ❌ No method to enqueue failed documents to `FAILED_STREAM`
- ❌ No separate retry queue (using FAILED_STREAM for both)
- ❌ No retry count tracking in stream messages
- ❌ No exponential backoff calculation

**Leverage Opportunity:** 95% - Just need to add enqueue methods

---

#### **2. Worker Infrastructure** ✅ **GOOD**
**Location:** `services/ecosystem-mcp/src/services/ingestion/ingestion_worker.py`

**What Exists:**
```python
class IngestionWorker:
    - Async worker loop ✅
    - Redis stream polling ✅
    - Job processing ✅
    - Graceful shutdown ✅
    - Health checking ✅
    - Error handling (basic) ⚠️
```

**Critical Finding:**
- ✅ Worker pattern is solid
- ✅ Can easily clone for RetryWorker
- ⚠️ Error handling doesn't classify transient vs permanent
- ❌ No circuit breaker

**What's Missing:**
- ❌ Dedicated retry worker class
- ❌ Circuit breaker logic
- ❌ Exponential backoff

**Leverage Opportunity:** 80% - Clone and modify IngestionWorker

---

#### **3. Job Processor Infrastructure** ✅ **EXCELLENT**
**Location:** `services/ecosystem-mcp/src/services/ingestion/job_processor.py`

**What Exists:**
```python
class JobProcessor:
    - Document processing pipeline ✅
    - Error handling ✅
    - Progress tracking ✅
    - Database operations ✅
    - ChromaDB operations with retry (3x) ⚠️
```

**Critical Finding:**
- ✅ Mature processing pipeline
- ✅ Has `add_embeddings_with_retry` with 3 retries
- ❌ **BUT: Failed documents are logged and forgotten!**
- ❌ No classification of error types
- ❌ No enqueuing of failures

**What's Missing:**
- ❌ Error classification function
- ❌ Failed document enqueuing
- ❌ Retry metadata tracking

**Leverage Opportunity:** 90% - Just add error classification and enqueue

---

#### **4. Multiple Processor Types** ✅ **COMPLEX**
**Files:**
- `batched_commit_processor.py` ✅
- `recoverable_job_processor.py` ✅
- `snapshot_processor.py` ✅
- `enhanced_job_processor.py` ✅

**Critical Finding:**
- ✅ Checkpointing exists (batch-level and commit-level)
- ✅ Recovery mechanisms exist
- ❌ **BUT: All operate at batch/commit level, not document level!**
- ❌ No processor uses FAILED_STREAM

**Integration Challenge:** Must inject retry logic into ALL processors

**Leverage Opportunity:** 70% - Add retry enqueuing to base error paths

---

#### **5. Monitoring Infrastructure** ✅ **EXCELLENT**
**Files:**
- `services/orchestration/execution_monitor.py` ✅
- `services/monitoring/performance_monitor.py` ✅
- `utils/redis_queue_health_checker.py` ✅
- `utils/worker_health.py` ✅

**What Exists:**
```python
ExecutionMonitor:
    - Real-time metrics ✅
    - Anomaly detection ✅
    - Resource tracking ✅
    
PerformanceMonitor:
    - Bottleneck detection ✅
    - Throughput monitoring ✅
    
RedisQueueHealthChecker:
    - Queue depth monitoring ✅
    - Orphaned message cleanup ✅
```

**Critical Finding:**
- ✅ Comprehensive monitoring already exists
- ✅ Can easily extend for retry queue monitoring
- ✅ Anomaly detection can trigger circuit breaker

**What's Missing:**
- ❌ Retry queue metrics
- ❌ Circuit breaker state tracking
- ❌ Failure classification metrics

**Leverage Opportunity:** 95% - Just add retry-specific metrics

---

#### **6. Embedding Service** ✅ **INDEPENDENT**
**Location:** `services/ecosystem-mcp-embedding/`

**What Exists:**
```python
FastEmbedService:
    - ONNX optimization ✅
    - Redis caching ✅
    - Batch processing ✅
    - Error handling ✅
    - Health checks ✅
```

**Critical Finding:**
- ✅ Embedding service is fault-isolated
- ✅ Has own caching layer
- ✅ Returns proper error responses
- ❌ **BUT: Ecosystem-mcp doesn't retry embedding failures!**

**Integration Point:** 
- Job processor should retry embedding failures
- Already has HTTP client, just need retry logic

**Leverage Opportunity:** 100% - No changes needed to embedding service

---

#### **7. Database & Models** ✅ **GOOD**
**Location:** `services/ecosystem-mcp/src/storage/`

**What Exists:**
```python
IngestionJobRepository:
    - Job CRUD ✅
    - Counter updates ✅
    - Status tracking ✅
    
IngestionJobModel:
    - processed_documents ✅
    - failed_documents ✅
    - error_message (single) ⚠️
```

**Critical Finding:**
- ✅ Job tracking is solid
- ⚠️ Only stores single error message (last error)
- ❌ **No failed_document_details table for tracking individual failures**

**What's Missing:**
- ❌ Failed document tracking table
- ❌ Retry count per document
- ❌ Error type classification storage

**Leverage Opportunity:** 60% - Need new table for failed documents

---

### **❌ MISSING INFRASTRUCTURE (Build)**

#### **1. Retry Queue (Separate from Dead Letter)** ❌
**Need:** Dedicated retry stream separate from permanent failures

**Rationale:**
- `FAILED_STREAM` should be dead letter (permanent failures)
- Need `RETRY_STREAM` for transient failures with retry logic

**Implementation:** Add new Redis stream

---

#### **2. Error Classification Engine** ❌
**Need:** Function to classify errors as transient vs permanent

**Types Needed:**
- `connectivity` - Network/timeout issues (retry)
- `rate_limit` - Rate limiting (retry with backoff)
- `timeout` - Processing timeouts (retry)
- `invalid_data` - Bad data (dead letter)
- `permission_denied` - Auth issues (dead letter)
- `unknown` - Treat as transient (retry once)

---

#### **3. Retry Worker** ❌
**Need:** Dedicated worker to process retry queue

**Features:**
- Read from RETRY_STREAM
- Exponential backoff
- Circuit breaker
- Max retries (5)
- Move to dead letter after max retries

---

#### **4. Circuit Breaker** ❌
**Need:** Protect services during outages

**Logic:**
- Track consecutive failures
- Open circuit after threshold (10 failures)
- Half-open after cooldown (5 minutes)
- Close on success

---

#### **5. Failed Document Tracking** ❌
**Need:** Database table for failed document metadata

**Schema:**
```sql
CREATE TABLE failed_documents (
    id UUID PRIMARY KEY,
    job_id UUID REFERENCES ingestion_jobs(id),
    file_path TEXT,
    error_type TEXT,
    error_message TEXT,
    retry_count INTEGER,
    last_retry_at TIMESTAMP,
    next_retry_at TIMESTAMP,
    created_at TIMESTAMP,
    moved_to_dlq_at TIMESTAMP
);
```

---

## 🎯 **CRITICAL FLAWS IN CURRENT IMPLEMENTATION**

### **FLAW #1: Silent Document Loss** 🔴 **CRITICAL**
**Location:** All processors

**Issue:**
```python
except Exception as e:
    logger.error(f"Failed to process {file_path}: {e}")
    result["failed"] += 1
    # ❌ DOCUMENT IS LOST HERE - NEVER RETRIED!
```

**Impact:**
- 68% of documents lost in current job
- Transient failures become permanent
- No recovery path

**Fix:** Enqueue to retry stream

---

### **FLAW #2: No Distinction Between Transient and Permanent** 🔴 **CRITICAL**
**Location:** All error handling

**Issue:**
- Network timeout treated same as corrupt data
- Both count as "failed" with no retry
- Wastes resources retrying permanent failures

**Fix:** Implement error classification

---

### **FLAW #3: ChromaDB Retry is Insufficient** 🟡 **MEDIUM**
**Location:** `src/storage/chromadb_client.py:add_embeddings_with_retry`

**Issue:**
```python
async def add_embeddings_with_retry(self, ..., max_retries=3):
    for attempt in range(max_retries):
        try:
            # ... attempt ...
        except Exception as e:
            if attempt < max_retries - 1:
                await asyncio.sleep(1)  # ❌ Fixed 1s delay
            else:
                return False  # ❌ Document lost after 3 tries
```

**Problems:**
- ❌ Only 3 retries
- ❌ Fixed 1s delay (no exponential backoff)
- ❌ Returns False but document not enqueued for later retry
- ❌ Doesn't distinguish connection failure from data corruption

**Fix:** Keep existing retry for immediate failures, but enqueue document on final failure

---

### **FLAW #4: Batch-Level Granularity Too Coarse** 🟡 **MEDIUM**
**Location:** `batched_commit_processor.py`

**Issue:**
```python
except Exception as e:
    logger.error(f"❌ Batch {batch_num} failed: {e}")
    result["batches_failed"] += 1
    continue  # ❌ Skip entire batch, lose track of individual docs
```

**Impact:**
- If 1 document in batch of 100 fails, we lose track
- Can't retry that 1 document specifically
- Either re-process entire batch (duplication) or skip it (data loss)

**Fix:** Track document-level failures within batch processing

---

### **FLAW #5: No Circuit Breaker** 🟡 **MEDIUM**
**Impact:** During ChromaDB outage, system hammers it with retries

**Scenario:**
```
ChromaDB goes down
→ 1000 documents try to embed
→ All fail after 3 retries each = 3000 failed attempts
→ Overwhelms ChromaDB when it comes back up
```

**Fix:** Circuit breaker pauses retries during outages

---

### **FLAW #6: Single Error Message Per Job** 🟢 **LOW**
**Location:** `IngestionJobModel.error_message`

**Issue:**
- Only stores last error
- Can't analyze error patterns
- Can't see if all failures are same error or different

**Fix:** Failed documents table stores all errors

---

### **FLAW #7: No Retry Visibility** 🟢 **LOW**
**Impact:** No way to see what's being retried or why

**Missing:**
- Retry queue dashboard
- Retry success rate metrics
- Dead letter queue browser

**Fix:** Admin API endpoints + dashboard integration

---

## 🏗️ **ARCHITECTURE OVERVIEW**

### **Existing Flow (Broken):**
```
Ingestion Job
    ↓
Job Processor
    ↓
Document Fails → Log Error → Count as Failed → LOST FOREVER ❌
```

### **New Flow (Fixed):**
```
Ingestion Job
    ↓
Job Processor
    ↓
Document Fails
    ↓
Error Classification
    ├─ Transient → RETRY_STREAM (exponential backoff)
    │               ↓
    │          Retry Worker
    │               ├─ Success → Done ✅
    │               ├─ Fail (< 5 retries) → Re-queue with backoff
    │               └─ Fail (≥ 5 retries) → FAILED_STREAM (dead letter)
    │
    └─ Permanent → FAILED_STREAM (immediate dead letter)
```

### **Service Topology:**
```
┌─────────────────────────────────────────────────────────────┐
│                   ECOSYSTEM-MCP                              │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │  Ingestion   │  │    Retry     │  │   Monitor    │     │
│  │   Worker     │  │   Worker     │  │   Worker     │     │
│  │  (existing)  │  │    (new)     │  │  (existing)  │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
│         ↓                 ↓                  ↓              │
│  ┌─────────────────────────────────────────────────┐       │
│  │              REDIS STREAMS                       │       │
│  │  - ingestion_queue (existing)                   │       │
│  │  - retry_queue (NEW)                            │       │
│  │  - failed_queue (existing, repurposed)          │       │
│  └─────────────────────────────────────────────────┘       │
│         ↓                                                    │
│  ┌─────────────────────────────────────────────────┐       │
│  │          PostgreSQL (Job Tracking)               │       │
│  │  - ingestion_jobs (existing)                    │       │
│  │  - failed_documents (NEW)                       │       │
│  └─────────────────────────────────────────────────┘       │
│         ↓                                                    │
│  ┌─────────────────────────────────────────────────┐       │
│  │              ChromaDB / Embedding                │       │
│  └─────────────────────────────────────────────────┘       │
└─────────────────────────────────────────────────────────────┘
         ↓                              ↓
┌──────────────────────┐   ┌──────────────────────┐
│  EMBEDDING SERVICE   │   │      DASHBOARD       │
│   (independent)      │   │  - Retry queue UI    │
│   - No changes       │   │  - Dead letter UI    │
│   needed ✅          │   │  - Metrics display   │
└──────────────────────┘   └──────────────────────┘
```

---

## 📋 **PHASED IMPLEMENTATION PLAN**

### **PHASE 1: Foundation (4 hours)** 🔴 **CRITICAL**

**Goal:** Stop the bleeding - prevent future data loss

#### **1.1 Add Retry Stream to Redis (30 min)**
**File:** `services/ecosystem-mcp/src/utils/redis_client.py`

```python
class RedisClient:
    # Stream names
    INGESTION_STREAM = "ingestion_queue"
    EMBEDDING_STREAM = "embedding_queue"
    RETRY_STREAM = "retry_queue"  # NEW - Transient failures
    FAILED_STREAM = "failed_queue"  # Repurpose as dead letter only
    
    # Retry configuration
    MAX_RETRIES = 5  # Up from 3
    RETRY_BACKOFF_BASE = 2  # Exponential base (2^n minutes)
    
    async def enqueue_failed_document(
        self,
        job_id: str,
        document_info: Dict[str, Any],
        error_type: str,
        error_message: str,
        retry_count: int = 0
    ) -> str:
        """
        Enqueue failed document for retry.
        
        Args:
            job_id: Parent job ID
            document_info: Document details (file_path, mode, etc.)
            error_type: Classified error type
            error_message: Full error message
            retry_count: Current retry count
        
        Returns:
            Message ID
        """
        next_retry_minutes = self.RETRY_BACKOFF_BASE ** retry_count
        next_retry_at = datetime.utcnow() + timedelta(minutes=next_retry_minutes)
        
        data = {
            "job_id": job_id,
            "document_info": json.dumps(document_info),
            "error_type": error_type,
            "error_message": error_message,
            "retry_count": retry_count,
            "failed_at": datetime.utcnow().isoformat(),
            "next_retry_at": next_retry_at.isoformat()
        }
        
        message_id = await self.add_to_stream(
            self.RETRY_STREAM,
            data,
            max_len=50000  # Higher limit for retry queue
        )
        
        logger.info(
            f"📝 Enqueued document for retry: {document_info.get('file_path', 'unknown')} "
            f"(retry {retry_count + 1}/{self.MAX_RETRIES}, "
            f"next attempt in {next_retry_minutes}min)"
        )
        
        return message_id
    
    async def move_to_dead_letter(
        self,
        job_id: str,
        document_info: Dict[str, Any],
        error_type: str,
        error_message: str,
        retry_count: int
    ) -> str:
        """
        Move document to dead letter queue (permanent failure).
        
        Args:
            job_id: Parent job ID
            document_info: Document details
            error_type: Classified error type
            error_message: Full error message
            retry_count: Number of retries attempted
        
        Returns:
            Message ID
        """
        data = {
            "job_id": job_id,
            "document_info": json.dumps(document_info),
            "error_type": error_type,
            "error_message": error_message,
            "retry_count": retry_count,
            "failed_at": datetime.utcnow().isoformat(),
            "moved_to_dlq_at": datetime.utcnow().isoformat()
        }
        
        message_id = await self.add_to_stream(
            self.FAILED_STREAM,
            data,
            max_len=100000  # Keep dead letters longer
        )
        
        logger.warning(
            f"💀 Moved to dead letter queue: {document_info.get('file_path', 'unknown')} "
            f"after {retry_count} retries (error: {error_type})"
        )
        
        return message_id
```

**Testing:**
```python
# Test enqueue
redis = get_redis_client()
await redis.enqueue_failed_document(
    job_id="test-job",
    document_info={"file_path": "test.py"},
    error_type="connectivity",
    error_message="Connection timeout",
    retry_count=0
)

# Verify in stream
messages = await redis.client.xrange(redis.RETRY_STREAM, count=10)
assert len(messages) > 0
```

---

#### **1.2 Create Error Classification Engine (1 hour)**
**File:** `services/ecosystem-mcp/src/services/ingestion/error_classifier.py` (NEW)

```python
"""
Error Classification Engine

Classifies exceptions into categories for intelligent retry logic.
"""

import logging
from enum import Enum
from typing import Optional
import re

logger = logging.getLogger(__name__)


class ErrorType(Enum):
    """Classification of error types."""
    # Transient errors (should retry)
    CONNECTIVITY = "connectivity"  # Network/connection issues
    TIMEOUT = "timeout"  # Processing timeouts
    RATE_LIMIT = "rate_limit"  # Rate limiting
    RESOURCE_EXHAUSTION = "resource_exhaustion"  # Out of memory, connections, etc.
    SERVICE_UNAVAILABLE = "service_unavailable"  # 503, service down
    
    # Permanent errors (should NOT retry)
    INVALID_DATA = "invalid_data"  # Malformed, corrupt data
    PARSE_ERROR = "parse_error"  # Cannot parse file
    UNSUPPORTED_FORMAT = "unsupported_format"  # File type not supported
    PERMISSION_DENIED = "permission_denied"  # 403, auth issues
    NOT_FOUND = "not_found"  # 404, file missing
    
    # Unknown (retry once)
    UNKNOWN = "unknown"


class ErrorClassifier:
    """
    Classify exceptions for intelligent retry logic.
    
    Features:
    - Pattern matching on error messages
    - Exception type analysis
    - HTTP status code detection
    - Transient vs permanent classification
    """
    
    # Transient error patterns
    TRANSIENT_PATTERNS = {
        ErrorType.CONNECTIVITY: [
            r"connection.*(?:refused|reset|closed|timeout|lost)",
            r"network.*(?:unreachable|error|timeout)",
            r"socket.*(?:timeout|error)",
            r"broken pipe",
            r"connection pool exhausted",
            r"too many open files",
            r"temporarily unavailable"
        ],
        ErrorType.TIMEOUT: [
            r"timeout",
            r"timed out",
            r"deadline exceeded",
            r"operation timed out"
        ],
        ErrorType.RATE_LIMIT: [
            r"rate limit",
            r"too many requests",
            r"429",
            r"quota exceeded",
            r"throttled"
        ],
        ErrorType.RESOURCE_EXHAUSTION: [
            r"out of memory",
            r"memory error",
            r"resource exhausted",
            r"no space left",
            r"disk full"
        ],
        ErrorType.SERVICE_UNAVAILABLE: [
            r"service unavailable",
            r"503",
            r"server error",
            r"5\d{2}",  # 5xx errors
            r"upstream.*(?:timeout|error)"
        ]
    }
    
    # Permanent error patterns
    PERMANENT_PATTERNS = {
        ErrorType.INVALID_DATA: [
            r"invalid.*(?:data|format|syntax)",
            r"malformed",
            r"corrupt",
            r"cannot decode",
            r"decode error"
        ],
        ErrorType.PARSE_ERROR: [
            r"parse error",
            r"parsing failed",
            r"syntax error",
            r"unexpected.*(?:token|character)",
            r"invalid syntax"
        ],
        ErrorType.UNSUPPORTED_FORMAT: [
            r"unsupported.*(?:format|type|extension)",
            r"unknown format",
            r"not supported"
        ],
        ErrorType.PERMISSION_DENIED: [
            r"permission denied",
            r"403",
            r"forbidden",
            r"unauthorized",
            r"401",
            r"access denied"
        ],
        ErrorType.NOT_FOUND: [
            r"not found",
            r"404",
            r"no such file",
            r"does not exist"
        ]
    }
    
    @classmethod
    def classify(cls, error: Exception) -> ErrorType:
        """
        Classify an exception.
        
        Args:
            error: Exception to classify
        
        Returns:
            ErrorType enum value
        """
        error_str = str(error).lower()
        error_type_name = type(error).__name__.lower()
        
        # Compile full error context
        full_context = f"{error_type_name} {error_str}"
        
        # Check transient patterns first
        for error_type, patterns in cls.TRANSIENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, full_context, re.IGNORECASE):
                    logger.debug(
                        f"Classified as {error_type.value}: matched pattern '{pattern}'"
                    )
                    return error_type
        
        # Check permanent patterns
        for error_type, patterns in cls.PERMANENT_PATTERNS.items():
            for pattern in patterns:
                if re.search(pattern, full_context, re.IGNORECASE):
                    logger.debug(
                        f"Classified as {error_type.value}: matched pattern '{pattern}'"
                    )
                    return error_type
        
        # Unknown - treat as transient (better to retry once than lose data)
        logger.warning(
            f"Could not classify error: {error_type_name}: {error_str[:100]}"
        )
        return ErrorType.UNKNOWN
    
    @classmethod
    def is_transient(cls, error_type: ErrorType) -> bool:
        """Check if error type is transient (should retry)."""
        return error_type in [
            ErrorType.CONNECTIVITY,
            ErrorType.TIMEOUT,
            ErrorType.RATE_LIMIT,
            ErrorType.RESOURCE_EXHAUSTION,
            ErrorType.SERVICE_UNAVAILABLE,
            ErrorType.UNKNOWN  # Retry unknown once
        ]
    
    @classmethod
    def is_permanent(cls, error_type: ErrorType) -> bool:
        """Check if error type is permanent (should not retry)."""
        return not cls.is_transient(error_type)
    
    @classmethod
    def get_suggested_backoff(cls, error_type: ErrorType, retry_count: int) -> int:
        """
        Get suggested backoff time in minutes.
        
        Args:
            error_type: Type of error
            retry_count: Current retry count
        
        Returns:
            Backoff time in minutes
        """
        # Rate limits need longer backoff
        if error_type == ErrorType.RATE_LIMIT:
            return 2 ** (retry_count + 2)  # 4, 8, 16, 32, 64 minutes
        
        # Service unavailable needs moderate backoff
        elif error_type == ErrorType.SERVICE_UNAVAILABLE:
            return 2 ** (retry_count + 1)  # 2, 4, 8, 16, 32 minutes
        
        # Others use standard exponential backoff
        else:
            return 2 ** retry_count  # 1, 2, 4, 8, 16 minutes
```

**Testing:**
```python
# Test transient classification
error = ConnectionError("Connection refused")
error_type = ErrorClassifier.classify(error)
assert error_type == ErrorType.CONNECTIVITY
assert ErrorClassifier.is_transient(error_type)

# Test permanent classification
error = ValueError("Invalid data format")
error_type = ErrorClassifier.classify(error)
assert error_type == ErrorType.INVALID_DATA
assert ErrorClassifier.is_permanent(error_type)
```

---

#### **1.3 Integrate Error Classification into Job Processor (1.5 hours)**
**File:** `services/ecosystem-mcp/src/services/ingestion/job_processor.py`

**Changes:**

1. Import error classifier:
```python
from .error_classifier import ErrorClassifier, ErrorType
from ...utils.redis_client import get_redis_client
```

2. Modify `_process_snapshot_document` error handling:
```python
async def _process_snapshot_document(self, file_path, ...):
    try:
        # ... existing processing logic ...
        
    except Exception as e:
        logger.error(f"❌ Failed to process {file_path}: {e}")
        
        # 🆕 PHASE 1: Classify error
        error_type = ErrorClassifier.classify(e)
        logger.info(f"🔍 Error classified as: {error_type.value}")
        
        # 🆕 PHASE 1: Handle based on classification
        redis = get_redis_client()
        
        if ErrorClassifier.is_transient(error_type):
            # Transient error - enqueue for retry
            await redis.enqueue_failed_document(
                job_id=str(job.id),
                document_info={
                    "file_path": file_path,
                    "mode": job.mode,
                    "repo_path": job.repo_path,
                    "service_name": job.service_name
                },
                error_type=error_type.value,
                error_message=str(e),
                retry_count=0
            )
            logger.info(f"📝 Enqueued {file_path} for retry (transient {error_type.value})")
        
        else:
            # Permanent error - move to dead letter immediately
            await redis.move_to_dead_letter(
                job_id=str(job.id),
                document_info={
                    "file_path": file_path,
                    "mode": job.mode,
                    "repo_path": job.repo_path,
                    "service_name": job.service_name
                },
                error_type=error_type.value,
                error_message=str(e),
                retry_count=0
            )
            logger.warning(f"💀 Moved {file_path} to dead letter (permanent {error_type.value})")
        
        # Still count as failed for job statistics
        result["failed"] = True
        result["error"] = str(e)
        result["error_type"] = error_type.value
        
        return result
```

3. Add same logic to other processing methods:
- `_process_file_optimized`
- `_process_file` (if exists)
- Any batch processing error handlers

**Integration Points:**
- `batched_commit_processor.py` - Add to batch error handler
- `recoverable_job_processor.py` - Add to checkpoint error handler
- `snapshot_processor.py` - Add to snapshot error handler

---

#### **1.4 Create Database Migration for Failed Documents (1 hour)**
**File:** `services/ecosystem-mcp/src/storage/migrations/012_add_failed_documents_table.py` (NEW)

```python
"""
Migration 012: Add failed_documents tracking table

Tracks individual document failures with retry metadata.
"""

import logging
import asyncpg

logger = logging.getLogger(__name__)


async def upgrade(connection: asyncpg.Connection) -> None:
    """Add failed_documents table."""
    logger.info("🚀 Starting migration 012: Add failed_documents table")
    
    # Create table
    logger.info("  📝 Creating failed_documents table...")
    await connection.execute("""
        CREATE TABLE IF NOT EXISTS failed_documents (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            job_id UUID NOT NULL REFERENCES ingestion_jobs(id) ON DELETE CASCADE,
            file_path TEXT NOT NULL,
            service_name TEXT,
            error_type TEXT NOT NULL,
            error_message TEXT NOT NULL,
            retry_count INTEGER DEFAULT 0,
            max_retries INTEGER DEFAULT 5,
            last_retry_at TIMESTAMP,
            next_retry_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT NOW(),
            moved_to_dlq_at TIMESTAMP,
            dlq_reason TEXT,
            metadata JSONB DEFAULT '{}'::jsonb
        );
    """)
    
    # Create indexes
    logger.info("  📝 Creating indexes...")
    await connection.execute("""
        CREATE INDEX IF NOT EXISTS idx_failed_documents_job_id 
            ON failed_documents(job_id);
        
        CREATE INDEX IF NOT EXISTS idx_failed_documents_error_type 
            ON failed_documents(error_type);
        
        CREATE INDEX IF NOT EXISTS idx_failed_documents_retry_count 
            ON failed_documents(retry_count);
        
        CREATE INDEX IF NOT EXISTS idx_failed_documents_next_retry 
            ON failed_documents(next_retry_at) 
            WHERE moved_to_dlq_at IS NULL;
        
        CREATE INDEX IF NOT EXISTS idx_failed_documents_dlq 
            ON failed_documents(moved_to_dlq_at) 
            WHERE moved_to_dlq_at IS NOT NULL;
    """)
    
    logger.info("✅ Migration 012 complete: failed_documents table created")


async def downgrade(connection: asyncpg.Connection) -> None:
    """Remove failed_documents table."""
    logger.info("🔙 Starting downgrade 012: Remove failed_documents table")
    
    await connection.execute("DROP TABLE IF EXISTS failed_documents CASCADE;")
    
    logger.info("✅ Downgrade 012 complete: failed_documents table removed")
```

**Run Migration:**
```bash
# In ecosystem-mcp container
python -m src.storage.migrations.runner upgrade
```

---

**PHASE 1 DELIVERABLES:**
- ✅ Retry stream added to Redis
- ✅ Error classification engine
- ✅ Failed document enqueuing integrated
- ✅ Database table for tracking failures
- ✅ All future failures will be retried (stops data loss)

**PHASE 1 VALIDATION:**
1. Run new ingestion job
2. Check retry queue has entries: `redis-cli XLEN retry_queue`
3. Check failed_documents table has entries
4. Verify error types are classified correctly

---

### **PHASE 2: Retry Worker (4 hours)** 🟡 **HIGH PRIORITY**

**Goal:** Automatically retry failed documents

#### **2.1 Create Retry Worker (2.5 hours)**
**File:** `services/ecosystem-mcp/src/services/ingestion/retry_worker.py` (NEW)

```python
"""
Retry Worker

Dedicated worker for retrying failed documents with:
- Exponential backoff
- Circuit breaker
- Max retries
- Dead letter queue handling
"""

import asyncio
import logging
import threading
import json
from typing import Optional, Dict, Any
from uuid import UUID, uuid4
from datetime import datetime, timedelta

from ...config import settings
from ...utils.redis_client import get_redis_client
from ...storage import get_database
from ...storage.repositories import IngestionJobRepository
from .job_processor import JobProcessor
from .error_classifier import ErrorClassifier, ErrorType

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Circuit breaker to protect services during outages.
    
    States:
    - CLOSED: Normal operation
    - OPEN: Failures detected, stop retries
    - HALF_OPEN: Testing if service recovered
    """
    
    FAILURE_THRESHOLD = 10  # Open after 10 consecutive failures
    SUCCESS_THRESHOLD = 3  # Close after 3 consecutive successes
    RESET_TIMEOUT = 300  # 5 minutes
    
    def __init__(self):
        """Initialize circuit breaker."""
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.state = "CLOSED"
        self.opened_at: Optional[datetime] = None
        logger.info("🔌 Circuit breaker initialized")
    
    def record_success(self):
        """Record successful operation."""
        self.consecutive_failures = 0
        
        if self.state == "HALF_OPEN":
            self.consecutive_successes += 1
            if self.consecutive_successes >= self.SUCCESS_THRESHOLD:
                self._close()
    
    def record_failure(self):
        """Record failed operation."""
        self.consecutive_successes = 0
        
        if self.state in ["CLOSED", "HALF_OPEN"]:
            self.consecutive_failures += 1
            if self.consecutive_failures >= self.FAILURE_THRESHOLD:
                self._open()
    
    def _open(self):
        """Open circuit (stop retries)."""
        self.state = "OPEN"
        self.opened_at = datetime.utcnow()
        logger.warning(
            f"🚨 Circuit breaker OPENED "
            f"(failures: {self.consecutive_failures})"
        )
    
    def _close(self):
        """Close circuit (resume retries)."""
        self.state = "CLOSED"
        self.consecutive_failures = 0
        self.consecutive_successes = 0
        self.opened_at = None
        logger.info("🔓 Circuit breaker CLOSED (service recovered)")
    
    def _half_open(self):
        """Half-open circuit (test recovery)."""
        self.state = "HALF_OPEN"
        self.consecutive_successes = 0
        logger.info("🔌 Circuit breaker HALF_OPEN (testing recovery)")
    
    def is_open(self) -> bool:
        """Check if circuit is open."""
        if self.state != "OPEN":
            return False
        
        # Check if reset timeout passed
        if self.opened_at:
            elapsed = (datetime.utcnow() - self.opened_at).total_seconds()
            if elapsed >= self.RESET_TIMEOUT:
                self._half_open()
                return False
        
        return True
    
    def get_state(self) -> Dict[str, Any]:
        """Get circuit breaker state."""
        return {
            "state": self.state,
            "consecutive_failures": self.consecutive_failures,
            "consecutive_successes": self.consecutive_successes,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None
        }


class RetryWorker:
    """
    Background worker for retrying failed documents.
    
    Features:
    - Exponential backoff (2^n minutes)
    - Circuit breaker (pause on outages)
    - Max retries (5 attempts)
    - Dead letter queue for permanent failures
    - Health monitoring
    """
    
    MAX_RETRIES = 5
    POLL_INTERVAL = 10  # seconds
    BATCH_SIZE = 10  # Process 10 retries per batch
    
    def __init__(self):
        """Initialize retry worker."""
        self.worker_id = str(uuid4())[:8]
        self.running = False
        self._task: Optional[asyncio.Task] = None
        self.circuit_breaker = CircuitBreaker()
        self.job_processor = JobProcessor(worker_id=self.worker_id)
        
        # Statistics
        self.stats = {
            "retries_attempted": 0,
            "retries_successful": 0,
            "retries_failed": 0,
            "moved_to_dlq": 0,
            "start_time": None
        }
        
        logger.info(f"🔄 RetryWorker initialized (ID: {self.worker_id})")
    
    async def start(self):
        """Start retry worker."""
        if self.running:
            logger.warning("Retry worker already running")
            return
        
        self.running = True
        self.stats["start_time"] = datetime.utcnow()
        self._task = asyncio.create_task(self._worker_loop())
        
        logger.info(f"✅ Retry worker {self.worker_id} started")
    
    async def stop(self):
        """Stop retry worker."""
        if not self.running:
            return
        
        self.running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info(f"🛑 Retry worker {self.worker_id} stopped")
    
    async def _worker_loop(self):
        """Main worker loop."""
        logger.info(f"🔄 Retry worker loop starting...")
        
        while self.running:
            try:
                # Check circuit breaker
                if self.circuit_breaker.is_open():
                    logger.warning("⚠️  Circuit breaker open, waiting...")
                    await asyncio.sleep(60)
                    continue
                
                # Get next batch of retries
                retries = await self._get_next_retries(self.BATCH_SIZE)
                
                if not retries:
                    await asyncio.sleep(self.POLL_INTERVAL)
                    continue
                
                logger.info(f"📦 Processing batch of {len(retries)} retries")
                
                # Process batch
                for retry_item in retries:
                    if not self.running:
                        break
                    
                    success = await self._retry_document(retry_item)
                    
                    if success:
                        self.circuit_breaker.record_success()
                    else:
                        self.circuit_breaker.record_failure()
                    
                    # Small delay between retries
                    await asyncio.sleep(0.5)
            
            except Exception as e:
                logger.error(f"❌ Error in retry worker loop: {e}", exc_info=True)
                await asyncio.sleep(10)
        
        logger.info("✅ Retry worker loop stopped")
    
    async def _get_next_retries(self, count: int) -> List[Dict[str, Any]]:
        """
        Get next batch of documents ready for retry.
        
        Args:
            count: Number of retries to fetch
        
        Returns:
            List of retry items
        """
        redis = get_redis_client()
        
        # Read from retry stream
        messages = await redis.client.xread(
            {redis.RETRY_STREAM: "0"},  # Read from beginning
            count=count * 2,  # Fetch extra to filter
            block=5000  # 5s block
        )
        
        if not messages:
            return []
        
        stream, message_list = messages[0]
        
        ready_retries = []
        now = datetime.utcnow()
        
        for message_id, data in message_list:
            # Check if ready for retry
            next_retry_str = data.get(b"next_retry_at", b"").decode()
            if not next_retry_str:
                continue
            
            next_retry_at = datetime.fromisoformat(next_retry_str)
            
            if now >= next_retry_at:
                # Parse retry item
                retry_item = {
                    "message_id": message_id,
                    "job_id": data.get(b"job_id", b"").decode(),
                    "document_info": json.loads(
                        data.get(b"document_info", b"{}").decode()
                    ),
                    "error_type": data.get(b"error_type", b"").decode(),
                    "error_message": data.get(b"error_message", b"").decode(),
                    "retry_count": int(data.get(b"retry_count", b"0").decode()),
                    "failed_at": data.get(b"failed_at", b"").decode()
                }
                
                ready_retries.append(retry_item)
                
                if len(ready_retries) >= count:
                    break
        
        return ready_retries
    
    async def _retry_document(self, retry_item: Dict[str, Any]) -> bool:
        """
        Retry processing a failed document.
        
        Args:
            retry_item: Retry item from stream
        
        Returns:
            True if successful, False if failed
        """
        retry_count = retry_item["retry_count"]
        doc_info = retry_item["document_info"]
        file_path = doc_info.get("file_path", "unknown")
        
        self.stats["retries_attempted"] += 1
        
        logger.info(
            f"🔄 Retrying document: {file_path} "
            f"(attempt {retry_count + 1}/{self.MAX_RETRIES})"
        )
        
        try:
            # Re-process document
            # Note: This is simplified - in production, you'd need to
            # reconstruct full job context or store more metadata
            
            result = await self.job_processor._process_snapshot_document(
                file_path=file_path,
                git_metadata=None,  # Will fetch fresh metadata
                job=await self._get_job(retry_item["job_id"])
            )
            
            if result.get("success"):
                # Success! Remove from retry queue
                await self._ack_retry(retry_item["message_id"])
                self.stats["retries_successful"] += 1
                logger.info(f"✅ Retry successful: {file_path}")
                return True
            
            else:
                # Still failing - handle retry
                return await self._handle_retry_failure(retry_item)
        
        except Exception as e:
            logger.error(f"❌ Retry failed with exception: {e}", exc_info=True)
            return await self._handle_retry_failure(retry_item)
    
    async def _handle_retry_failure(self, retry_item: Dict[str, Any]) -> bool:
        """
        Handle a failed retry attempt.
        
        Args:
            retry_item: Retry item
        
        Returns:
            False (always, since retry failed)
        """
        retry_count = retry_item["retry_count"] + 1
        doc_info = retry_item["document_info"]
        file_path = doc_info.get("file_path", "unknown")
        
        if retry_count >= self.MAX_RETRIES:
            # Max retries exceeded - move to dead letter
            redis = get_redis_client()
            await redis.move_to_dead_letter(
                job_id=retry_item["job_id"],
                document_info=doc_info,
                error_type=retry_item["error_type"],
                error_message=retry_item["error_message"],
                retry_count=retry_count
            )
            
            # Remove from retry queue
            await self._ack_retry(retry_item["message_id"])
            
            self.stats["moved_to_dlq"] += 1
            self.stats["retries_failed"] += 1
            
            logger.warning(
                f"💀 Max retries ({self.MAX_RETRIES}) exceeded for {file_path}, "
                f"moved to dead letter queue"
            )
        
        else:
            # Re-enqueue with incremented retry count
            redis = get_redis_client()
            await redis.enqueue_failed_document(
                job_id=retry_item["job_id"],
                document_info=doc_info,
                error_type=retry_item["error_type"],
                error_message=retry_item["error_message"],
                retry_count=retry_count
            )
            
            # Remove old entry
            await self._ack_retry(retry_item["message_id"])
            
            self.stats["retries_failed"] += 1
            
            backoff_minutes = 2 ** retry_count
            logger.info(
                f"📝 Re-queued {file_path} for retry "
                f"(attempt {retry_count + 1}/{self.MAX_RETRIES}, "
                f"next retry in {backoff_minutes}min)"
            )
        
        return False
    
    async def _ack_retry(self, message_id: str):
        """Acknowledge and delete retry message."""
        redis = get_redis_client()
        await redis.client.xack(
            redis.RETRY_STREAM,
            redis.CONSUMER_GROUP,
            message_id
        )
        await redis.client.xdel(redis.RETRY_STREAM, message_id)
    
    async def _get_job(self, job_id: str):
        """Get job from database."""
        async with get_database().session() as session:
            repo = IngestionJobRepository(session)
            return await repo.get_by_id(UUID(job_id))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get retry worker statistics."""
        runtime = None
        if self.stats["start_time"]:
            runtime = (datetime.utcnow() - self.stats["start_time"]).total_seconds()
        
        success_rate = 0.0
        if self.stats["retries_attempted"] > 0:
            success_rate = (
                self.stats["retries_successful"] / 
                self.stats["retries_attempted"]
            ) * 100
        
        return {
            "worker_id": self.worker_id,
            "running": self.running,
            "runtime_seconds": runtime,
            "circuit_breaker": self.circuit_breaker.get_state(),
            **self.stats,
            "success_rate_percent": round(success_rate, 2)
        }


# Singleton instance
_retry_worker_instance: Optional[RetryWorker] = None
_retry_worker_lock = threading.Lock()


def get_retry_worker() -> RetryWorker:
    """Get the global retry worker instance."""
    global _retry_worker_instance
    
    with _retry_worker_lock:
        if _retry_worker_instance is None:
            logger.info("🏗️  Creating new RetryWorker instance")
            _retry_worker_instance = RetryWorker()
        else:
            logger.info("♻️  Reusing existing RetryWorker instance")
    
    return _retry_worker_instance
```

---

**CONTINUE IN NEXT RESPONSE DUE TO LENGTH...**

This is the first half of the comprehensive plan. The document is getting very long. Should I:
1. Continue with Phase 2.2-2.4, Phase 3, and execution tracking?
2. Commit what we have so far and continue in a new document?
3. Create multiple smaller documents (one per phase)?

What's your preference?

