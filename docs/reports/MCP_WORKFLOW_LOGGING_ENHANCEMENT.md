# 🔍 MCP Workflow - Logging & Observability Enhancement Plan

**Date:** October 7, 2025  
**Enhancement Focus:** Comprehensive logging integration with mcp-logs service  
**Status:** Planning → Implementation  
**Impact:** Full workflow observability & debugging

---

## 📊 Overview

### Logging Architecture
```
[All Workflow Services]
         ↓
   [Log Entries]
         ↓
   [mcp-logs Service] (Port 8016)
         ↓
   [Elasticsearch] ← Indexed logs
         ↓
   [Anomaly Detection] ← Pattern analysis
         ↓
   [Alerts & Dashboards]
```

### Services Requiring Logging Integration (9)
1. ✅ **mcp-logs** - Centralized logging service (IMPLEMENTED)
2. ❌ **kafka-ingestion-service** - Document ingestion events
3. ❌ **llm-tagging-pipeline** - Tagging operations
4. ❌ **mcp-training-coordinator** - Training pipeline stages
5. ❌ **mcp-store** - Storage operations
6. ❌ **mcp-registry** - Registration events
7. ❌ **mcp-gateway** - Gateway requests
8. ❌ **mcp-package-manager** - Export/import operations
9. ❌ **mcp-evergreen-docs** - Documentation sync events

---

## 🎯 Logging Integration Requirements

### For Each Service

#### 1. Log Entry Structure
```python
{
    "entry_id": "uuid",
    "message": "Document ingestion started",
    "level": "INFO",  # DEBUG, INFO, WARNING, ERROR, CRITICAL
    "service": "kafka-ingestion-service",
    "source": "IngestDocumentCommand",
    "host": "container-id",
    "environment": "production",
    "timestamp": "2025-10-07T12:00:00Z",
    
    # Context
    "correlation_id": "workflow-123",
    "request_id": "req-456",
    "user_id": "user-789",
    "session_id": "session-abc",
    
    # Custom fields
    "fields": {
        "document_id": "doc-001",
        "event_type": "document_created",
        "processing_time_ms": 123
    },
    
    # Tags
    "tags": ["ingestion", "document", "kafka"]
}
```

#### 2. Log Levels by Operation
- **DEBUG**: Internal state changes, variable values
- **INFO**: Normal operation flow, successful completions
- **WARNING**: Potential issues, degraded performance
- **ERROR**: Operation failures, exceptions
- **CRITICAL**: Service failures, data loss

#### 3. Required Logging Points

**All Services Must Log:**
- Service startup/shutdown
- Request received/completed
- External service calls (start/end)
- Errors and exceptions with stack traces
- Performance metrics (latency, throughput)
- Resource usage (memory, CPU)

---

## 🔄 Workflow-Specific Logging

### 1. Document Ingestion Flow

#### kafka-ingestion-service
```python
# Log Points:
logger.info("Document ingestion started", extra={
    "document_id": doc_id,
    "source": source_type,
    "correlation_id": correlation_id
})

logger.info("Document validated", extra={
    "document_id": doc_id,
    "validation_time_ms": time_ms
})

logger.info("Event published to Kafka", extra={
    "document_id": doc_id,
    "topic": topic_name,
    "partition": partition
})

logger.error("Document ingestion failed", extra={
    "document_id": doc_id,
    "error": str(e),
    "retry_count": retry_count
}, exc_info=True)
```

**Metrics to Track:**
- Documents ingested per minute
- Average processing time
- Error rate
- Kafka lag

---

### 2. LLM Tagging Flow

#### llm-tagging-pipeline
```python
# Log Points:
logger.info("LLM tagging started", extra={
    "document_id": doc_id,
    "model": "llama2",
    "correlation_id": correlation_id
})

logger.info("Tags extracted", extra={
    "document_id": doc_id,
    "tags": extracted_tags,
    "confidence": confidence_score,
    "llm_time_ms": time_ms
})

logger.warning("Low confidence tagging", extra={
    "document_id": doc_id,
    "confidence": confidence_score,
    "threshold": min_confidence
})

logger.error("LLM request failed", extra={
    "document_id": doc_id,
    "model": "llama2",
    "error": str(e)
}, exc_info=True)
```

**Metrics to Track:**
- Tags generated per document
- Average confidence scores
- LLM response time
- Token usage

---

### 3. Training Pipeline Flow

#### mcp-training-coordinator
```python
# Log Points:
logger.info("Training job started", extra={
    "job_id": job_id,
    "source_docs": doc_count,
    "correlation_id": correlation_id
})

logger.info("Training stage completed", extra={
    "job_id": job_id,
    "stage": stage_name,
    "duration_seconds": duration
})

logger.info("MCP created", extra={
    "job_id": job_id,
    "mcp_id": mcp_id,
    "total_time_seconds": total_time
})

logger.error("Training failed", extra={
    "job_id": job_id,
    "stage": failed_stage,
    "error": str(e)
}, exc_info=True)
```

**Metrics to Track:**
- Training jobs per hour
- Success/failure rate
- Average training time per stage
- Resource utilization

---

### 4. Storage Operations Flow

#### mcp-store
```python
# Log Points:
logger.info("MCP storage started", extra={
    "mcp_id": mcp_id,
    "size_bytes": size,
    "correlation_id": correlation_id
})

logger.info("MCP stored successfully", extra={
    "mcp_id": mcp_id,
    "backend": storage_backend,
    "duration_ms": duration
})

logger.error("Storage failed", extra={
    "mcp_id": mcp_id,
    "backend": storage_backend,
    "error": str(e)
}, exc_info=True)
```

**Metrics to Track:**
- MCPs stored per hour
- Storage backend performance
- Average storage time
- Storage errors

---

### 5. Registration Flow

#### mcp-registry
```python
# Log Points:
logger.info("MCP registration started", extra={
    "mcp_id": mcp_id,
    "version": version,
    "correlation_id": correlation_id
})

logger.info("MCP registered", extra={
    "mcp_id": mcp_id,
    "version": version,
    "registry_id": registry_id
})

logger.warning("Duplicate registration attempted", extra={
    "mcp_id": mcp_id,
    "existing_version": existing_version
})

logger.error("Registration failed", extra={
    "mcp_id": mcp_id,
    "error": str(e)
}, exc_info=True)
```

**Metrics to Track:**
- Registrations per day
- Version conflicts
- Registration success rate

---

### 6. Export/Import Flow

#### mcp-package-manager
```python
# Log Points:
logger.info("Package export started", extra={
    "package_id": pkg_id,
    "format": export_format,
    "correlation_id": correlation_id
})

logger.info("Package exported", extra={
    "package_id": pkg_id,
    "file_size_mb": size_mb,
    "duration_seconds": duration
})

logger.info("Package import started", extra={
    "package_file": filename,
    "correlation_id": correlation_id
})

logger.error("Export failed", extra={
    "package_id": pkg_id,
    "error": str(e)
}, exc_info=True)
```

**Metrics to Track:**
- Exports per day
- Imports per day
- Average package size
- Export/import success rate

---

### 7. Evergreen Docs Flow

#### mcp-evergreen-docs
```python
# Log Points:
logger.info("Documentation sync started", extra={
    "sync_job_id": job_id,
    "source_type": source_type,
    "correlation_id": correlation_id
})

logger.info("Documents synced", extra={
    "sync_job_id": job_id,
    "docs_synced": count,
    "duration_seconds": duration
})

logger.warning("Outdated documentation detected", extra={
    "doc_ids": outdated_doc_ids,
    "last_sync": last_sync_time
})

logger.error("Sync failed", extra={
    "sync_job_id": job_id,
    "error": str(e)
}, exc_info=True)
```

**Metrics to Track:**
- Sync operations per day
- Documents synced
- Sync failures
- Documentation freshness

---

## 🛠️ Implementation Components

### 1. Log Client Library
**File:** `common/logging/mcp_log_client.py`

```python
import logging
import httpx
from typing import Dict, Any, Optional

class MCPLogClient:
    """Client for sending logs to mcp-logs service."""
    
    def __init__(self, mcp_logs_url: str, service_name: str):
        self.mcp_logs_url = mcp_logs_url
        self.service_name = service_name
        self.client = httpx.AsyncClient(timeout=5.0)
        
        # Configure local logger
        self.logger = logging.getLogger(service_name)
        self.logger.addHandler(MCPLogHandler(self))
    
    async def send_log(
        self,
        message: str,
        level: str,
        source: str,
        correlation_id: Optional[str] = None,
        fields: Dict[str, Any] = None,
        tags: list = None,
    ):
        """Send log entry to mcp-logs service."""
        log_entry = {
            "message": message,
            "level": level,
            "service": self.service_name,
            "source": source,
            "correlation_id": correlation_id,
            "fields": fields or {},
            "tags": tags or [],
        }
        
        try:
            await self.client.post(
                f"{self.mcp_logs_url}/api/v1/logs",
                json=log_entry
            )
        except Exception as e:
            # Fail gracefully - don't break service if logging fails
            self.logger.error(f"Failed to send log: {e}")
```

### 2. Correlation ID Middleware
**File:** `common/middleware/correlation_middleware.py`

```python
from fastapi import Request
import uuid

async def correlation_middleware(request: Request, call_next):
    """Add correlation ID to all requests."""
    correlation_id = request.headers.get(
        "X-Correlation-ID",
        str(uuid.uuid4())
    )
    
    request.state.correlation_id = correlation_id
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    
    return response
```

### 3. Structured Logging Configuration
**File:** `common/logging/config.py`

```python
import logging
import sys

def configure_logging(service_name: str, log_level: str = "INFO"):
    """Configure structured logging."""
    
    # Create formatter
    formatter = logging.Formatter(
        '{"timestamp":"%(asctime)s", "service":"' + service_name + '", '
        '"level":"%(levelname)s", "source":"%(name)s", '
        '"message":"%(message)s", "fields":%(fields)s}'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
```

---

## 📋 Implementation Tasks (TODOs)

### Common Logging Infrastructure (3 files)
- [ ] Create `common/logging/mcp_log_client.py` - Log client library
- [ ] Create `common/middleware/correlation_middleware.py` - Correlation tracking
- [ ] Create `common/logging/config.py` - Structured logging config

### Service Integrations (9 services)
- [ ] kafka-ingestion-service - Add logging (5 log points)
- [ ] llm-tagging-pipeline - Add logging (6 log points)
- [ ] mcp-training-coordinator - Add logging (8 log points)
- [ ] mcp-store - Add logging (4 log points)
- [ ] mcp-registry - Add logging (5 log points)
- [ ] mcp-gateway - Add logging (6 log points)
- [ ] mcp-package-manager - Add logging (6 log points)
- [ ] mcp-evergreen-docs - Add logging (5 log points)
- [ ] mcp-local-llm - Add logging (4 log points)

### Log Streams Configuration
- [ ] Create log stream for each service in mcp-logs
- [ ] Configure anomaly detection thresholds
- [ ] Set up critical error alerts
- [ ] Create monitoring dashboards

### Testing & Validation
- [ ] Test log ingestion from all services
- [ ] Validate correlation ID propagation
- [ ] Test anomaly detection
- [ ] Verify alert triggering

---

## 🔍 Observability Dashboard

### Key Metrics to Display
1. **Workflow Health**
   - End-to-end success rate
   - Average processing time per document
   - Current workflow backlog

2. **Service Health**
   - Error rate per service
   - Average response time
   - Request throughput

3. **Resource Utilization**
   - CPU usage per service
   - Memory usage per service
   - Disk I/O

4. **Anomalies Detected**
   - Active anomalies count
   - Anomalies by severity
   - Recent anomaly trends

---

## 📊 Success Metrics

### Implementation Complete When:
- ✅ All 9 services sending logs to mcp-logs
- ✅ Correlation IDs tracked across entire workflow
- ✅ Anomaly detection operational
- ✅ Critical alerts configured
- ✅ Monitoring dashboard operational
- ✅ Log retention policy configured
- ✅ Performance impact < 5% per service

### Estimated Effort
- **Common Infrastructure**: 1 day
- **Service Integrations**: 2 days (9 services × 2-3 hours)
- **Stream Configuration**: 0.5 day
- **Testing & Validation**: 0.5 day
- **Total**: 4 days

---

## 🎯 Priority Integration Order

1. **Week 1 Critical Services** (High Priority)
   - kafka-ingestion-service
   - llm-tagging-pipeline
   - mcp-training-coordinator

2. **Week 2 Core Services** (Medium Priority)
   - mcp-store
   - mcp-registry
   - mcp-package-manager

3. **Week 3 Supporting Services** (Lower Priority)
   - mcp-gateway
   - mcp-evergreen-docs
   - mcp-local-llm

---

**Status**: Ready for Implementation  
**Next Step**: Create common logging infrastructure → Integrate services  
**Impact**: Complete workflow observability and debugging capability  

