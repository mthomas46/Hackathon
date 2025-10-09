<!-- AI_READ_PRIORITY: 3 -->
<!-- AI_TAGS: logging, observability, structured-logging, log-collector -->
<!-- AI_KEY_SECTIONS: Logging Standards, Log Levels, Structured Logging, Log-Collector Integration -->

---
ai_metadata:
  purpose: logging_guidance
  read_priority: 3
  context_level: tactical
  tags:
  - logging
  - observability
  - structured-logging
  - log-collector
  when_to_read: During Phase 3 (TDD Implementation)
  key_sections:
  - Logging Standards
  - Log Levels
  - Structured Logging
  - Log-Collector Integration
  execution_relevance: phase-specific
  relevant_phases:
  - Phase 3
---

# 📊 Standardized Logging Strategy - Log-Collector Integration

**Version**: 1.0.0  
**Created**: October 8, 2025  
**Status**: Active

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Logging Standards](#logging-standards)
3. [Log Levels](#log-levels)
4. [Structured Logging](#structured-logging)
5. [Log-Collector Integration](#log-collector-integration)
6. [Implementation Guide](#implementation-guide)
7. [Log Analysis Preparation](#log-analysis-preparation)
8. [Examples](#examples)

---

## 🎯 Overview

### Purpose

Every service must implement **standardized, comprehensive logging** that:

- **Covers all core features** with appropriate detail
- **Uses consistent structure** across all services
- **Integrates with log-collector** for centralized logging
- **Enables future log analysis** with structured data
- **Supports debugging** with rich context
- **Facilitates monitoring** with metrics and alerts

### Logging Philosophy

1. **Log Meaningfully**: Every log provides value
2. **Log Consistently**: Same format across all services
3. **Log Contextually**: Include relevant context
4. **Log Securely**: Never log sensitive data
5. **Log Efficiently**: Balance detail with performance

### Key Requirements

| Requirement | Description |
|-------------|-------------|
| **Structured Format** | JSON format for all logs |
| **Standard Fields** | Consistent fields across services |
| **Log-Collector Integration** | All logs sent to centralized service |
| **Core Feature Coverage** | Every core feature logged |
| **Correlation IDs** | Track requests across services |
| **Performance Metrics** | Duration, latency, throughput |

---

## 📏 Logging Standards

### Standard Log Format

All services must use this JSON structure:

```json
{
  "timestamp": "2025-10-08T10:30:45.123Z",
  "level": "INFO",
  "service": "doc-store",
  "version": "2.0.0",
  "environment": "production",
  "correlation_id": "req-123abc",
  "user_id": "user-456",
  "operation": "create_document",
  "message": "Document created successfully",
  "duration_ms": 45,
  "metadata": {
    "document_id": "doc-789",
    "document_type": "markdown",
    "size_bytes": 1024
  },
  "error": null
}
```

### Required Fields

Every log entry MUST include:

```python
{
    # Core identification
    "timestamp": str,          # ISO 8601 format
    "level": str,              # DEBUG, INFO, WARNING, ERROR, CRITICAL
    "service": str,            # Service name
    "version": str,            # Service version
    "environment": str,        # dev, staging, production
    
    # Request context
    "correlation_id": str,     # Request tracking ID
    "operation": str,          # Operation being performed
    "message": str,            # Human-readable message
    
    # Performance
    "duration_ms": int,        # Operation duration (if applicable)
    
    # Additional data
    "metadata": dict,          # Operation-specific data
    "error": dict | null       # Error details (if error occurred)
}
```

### Optional Fields (When Applicable)

```python
{
    "user_id": str,           # User performing operation
    "session_id": str,        # User session ID
    "ip_address": str,        # Client IP (hashed for privacy)
    "request_id": str,        # HTTP request ID
    "parent_id": str,         # Parent operation ID
    "trace_id": str,          # Distributed tracing ID
    "resource_id": str,       # Resource being operated on
    "resource_type": str,     # Type of resource
    "http_method": str,       # HTTP method (GET, POST, etc.)
    "http_status": int,       # HTTP status code
    "http_path": str,         # Request path
    "query_params": dict,     # Query parameters (sanitized)
    "tags": list              # Custom tags for categorization
}
```

### Error Format

When logging errors:

```json
{
  "level": "ERROR",
  "message": "Failed to create document",
  "error": {
    "type": "ValidationError",
    "message": "Title cannot be empty",
    "code": "VALIDATION_ERROR",
    "stack_trace": "...",
    "context": {
      "field": "title",
      "value": "",
      "constraint": "non_empty"
    }
  }
}
```

---

## 📊 Log Levels

### Level Definitions

| Level | When to Use | Examples |
|-------|-------------|----------|
| **DEBUG** | Detailed diagnostic info for development | Variable values, flow control, detailed state |
| **INFO** | Significant business events | User actions, service starts/stops, feature usage |
| **WARNING** | Unexpected but handled situations | Deprecated API usage, slow operations, retry attempts |
| **ERROR** | Error events that impact functionality | Failed operations, exceptions, data inconsistencies |
| **CRITICAL** | Severe errors requiring immediate action | Service crashes, data loss, security breaches |

### Level Usage Guidelines

```python
# DEBUG - Development/troubleshooting only
logger.debug(
    "Processing document",
    extra={
        "document_id": doc_id,
        "content_length": len(content),
        "metadata_keys": list(metadata.keys())
    }
)

# INFO - Normal business operations
logger.info(
    "Document created successfully",
    extra={
        "operation": "create_document",
        "document_id": doc_id,
        "user_id": user_id,
        "duration_ms": duration
    }
)

# WARNING - Unexpected but handled
logger.warning(
    "Document creation slower than expected",
    extra={
        "operation": "create_document",
        "duration_ms": duration,
        "threshold_ms": 1000,
        "document_size": size
    }
)

# ERROR - Operation failed
logger.error(
    "Failed to create document",
    extra={
        "operation": "create_document",
        "error_type": "ValidationError",
        "error_message": str(error),
        "user_id": user_id
    },
    exc_info=True
)

# CRITICAL - System-level failure
logger.critical(
    "Database connection lost",
    extra={
        "operation": "database_connection",
        "error_type": "ConnectionError",
        "retry_attempts": attempts,
        "last_error": str(error)
    },
    exc_info=True
)
```

---

## 🏗️ Structured Logging

### Python Implementation

```python
# common/logging/structured_logger.py

import logging
import json
import time
from typing import Any, Dict, Optional
from datetime import datetime
from contextvars import ContextVar

# Context variables for request tracking
correlation_id_var: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)
user_id_var: ContextVar[Optional[str]] = ContextVar('user_id', default=None)

class StructuredLogger:
    """
    Standardized structured logger for all services
    
    Provides consistent JSON logging with required fields and
    automatic integration with log-collector service.
    """
    
    def __init__(
        self,
        service_name: str,
        service_version: str,
        environment: str,
        log_collector_enabled: bool = True
    ):
        self.service_name = service_name
        self.service_version = service_version
        self.environment = environment
        self.log_collector_enabled = log_collector_enabled
        
        # Set up Python logger
        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(logging.DEBUG)
        
        # Add JSON formatter
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        self.logger.addHandler(handler)
        
        # Set up log collector client
        if log_collector_enabled:
            from common.clients.log_collector_client import LogCollectorClient
            self.log_collector = LogCollectorClient()
    
    def _build_log_entry(
        self,
        level: str,
        message: str,
        operation: str,
        duration_ms: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
        error: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Build standardized log entry"""
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": level,
            "service": self.service_name,
            "version": self.service_version,
            "environment": self.environment,
            "correlation_id": correlation_id_var.get(),
            "user_id": user_id_var.get(),
            "operation": operation,
            "message": message,
            "duration_ms": duration_ms,
            "metadata": metadata or {},
            "error": error
        }
    
    def debug(self, message: str, **kwargs):
        """Log debug message"""
        entry = self._build_log_entry("DEBUG", message, **kwargs)
        self.logger.debug(json.dumps(entry))
    
    def info(self, message: str, **kwargs):
        """Log info message"""
        entry = self._build_log_entry("INFO", message, **kwargs)
        self.logger.info(json.dumps(entry))
        
        # Send to log collector
        if self.log_collector_enabled:
            self.log_collector.send_async(entry)
    
    def warning(self, message: str, **kwargs):
        """Log warning message"""
        entry = self._build_log_entry("WARNING", message, **kwargs)
        self.logger.warning(json.dumps(entry))
        
        if self.log_collector_enabled:
            self.log_collector.send_async(entry)
    
    def error(self, message: str, **kwargs):
        """Log error message"""
        entry = self._build_log_entry("ERROR", message, **kwargs)
        self.logger.error(json.dumps(entry))
        
        if self.log_collector_enabled:
            self.log_collector.send_async(entry, priority="high")
    
    def critical(self, message: str, **kwargs):
        """Log critical message"""
        entry = self._build_log_entry("CRITICAL", message, **kwargs)
        self.logger.critical(json.dumps(entry))
        
        if self.log_collector_enabled:
            self.log_collector.send_async(entry, priority="critical")


class JSONFormatter(logging.Formatter):
    """JSON formatter for Python logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        # If message is already JSON, return as-is
        try:
            json.loads(record.getMessage())
            return record.getMessage()
        except (ValueError, TypeError):
            # Otherwise, wrap in JSON
            return json.dumps({
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "level": record.levelname,
                "message": record.getMessage(),
                "logger": record.name
            })
```

### Operation Logging Context Manager

```python
# common/logging/operation_context.py

import time
from contextlib import contextmanager
from typing import Dict, Any, Optional

@contextmanager
def log_operation(
    logger: StructuredLogger,
    operation: str,
    metadata: Optional[Dict[str, Any]] = None
):
    """
    Context manager for logging operations with automatic duration tracking
    
    Usage:
        with log_operation(logger, "create_document", {"doc_id": doc_id}):
            # Perform operation
            result = create_document(...)
    """
    start_time = time.time()
    
    # Log operation start
    logger.info(
        f"Starting {operation}",
        operation=operation,
        metadata=metadata or {}
    )
    
    try:
        yield
        
        # Log success
        duration_ms = int((time.time() - start_time) * 1000)
        logger.info(
            f"Completed {operation}",
            operation=operation,
            duration_ms=duration_ms,
            metadata=metadata or {}
        )
        
    except Exception as e:
        # Log failure
        duration_ms = int((time.time() - start_time) * 1000)
        logger.error(
            f"Failed {operation}",
            operation=operation,
            duration_ms=duration_ms,
            metadata=metadata or {},
            error={
                "type": type(e).__name__,
                "message": str(e),
                "code": getattr(e, 'code', None)
            }
        )
        raise
```

---

## 🔗 Log-Collector Integration

### Log-Collector Client

```python
# common/clients/log_collector_client.py

import httpx
import asyncio
import queue
import threading
from typing import Dict, Any, Optional
from datetime import datetime

class LogCollectorClient:
    """
    Client for sending logs to log-collector service
    
    Features:
    - Async/batch sending for performance
    - Automatic retry on failure
    - Local buffering for reliability
    - Priority queue for critical logs
    """
    
    def __init__(
        self,
        log_collector_url: str = "http://log-collector:5080",
        batch_size: int = 100,
        flush_interval: int = 5
    ):
        self.log_collector_url = log_collector_url
        self.batch_size = batch_size
        self.flush_interval = flush_interval
        
        # Buffering
        self.log_queue = queue.Queue(maxsize=10000)
        self.high_priority_queue = queue.Queue(maxsize=1000)
        
        # HTTP client
        self.client = httpx.AsyncClient(
            base_url=log_collector_url,
            timeout=5.0
        )
        
        # Start background sender
        self._start_background_sender()
    
    def send_async(
        self,
        log_entry: Dict[str, Any],
        priority: str = "normal"
    ):
        """
        Send log entry asynchronously
        
        Args:
            log_entry: Structured log entry
            priority: "normal", "high", or "critical"
        """
        try:
            if priority in ["high", "critical"]:
                self.high_priority_queue.put_nowait(log_entry)
            else:
                self.log_queue.put_nowait(log_entry)
        except queue.Full:
            # Queue full - drop lowest priority logs
            # In production, consider persisting to disk
            pass
    
    def _start_background_sender(self):
        """Start background thread for sending logs"""
        def sender_loop():
            while True:
                try:
                    # Collect batch of logs
                    logs_to_send = []
                    
                    # High priority first
                    while len(logs_to_send) < self.batch_size and not self.high_priority_queue.empty():
                        logs_to_send.append(self.high_priority_queue.get_nowait())
                    
                    # Then normal priority
                    while len(logs_to_send) < self.batch_size and not self.log_queue.empty():
                        logs_to_send.append(self.log_queue.get_nowait())
                    
                    # Send batch if we have logs
                    if logs_to_send:
                        asyncio.run(self._send_batch(logs_to_send))
                    
                    # Wait before next batch
                    threading.Event().wait(self.flush_interval)
                    
                except Exception as e:
                    print(f"Error in log sender: {e}")
                    threading.Event().wait(1)
        
        thread = threading.Thread(target=sender_loop, daemon=True)
        thread.start()
    
    async def _send_batch(self, logs: list):
        """Send batch of logs to log-collector"""
        try:
            response = await self.client.post(
                "/api/v1/logs/batch",
                json={"logs": logs}
            )
            response.raise_for_status()
        except Exception as e:
            # On failure, could persist to local file
            print(f"Failed to send logs to collector: {e}")
    
    def flush(self):
        """Flush all pending logs immediately"""
        # Implementation for graceful shutdown
        pass
```

### Log-Collector API

```python
# services/log-collector/presentation/api/v1/routes.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter(prefix="/api/v1/logs", tags=["logs"])

class LogEntry(BaseModel):
    """Standard log entry"""
    timestamp: str
    level: str
    service: str
    version: str
    environment: str
    correlation_id: str | None
    operation: str
    message: str
    duration_ms: int | None
    metadata: Dict[str, Any]
    error: Dict[str, Any] | None

class LogBatch(BaseModel):
    """Batch of log entries"""
    logs: List[LogEntry]

@router.post("/batch")
async def receive_log_batch(batch: LogBatch):
    """
    Receive batch of logs from services
    
    Stores logs in database and forwards to
    analysis pipeline for real-time processing.
    """
    # Store logs
    await log_repository.save_batch(batch.logs)
    
    # Forward to analysis pipeline (async)
    await publish_to_analysis_queue(batch.logs)
    
    return {"status": "received", "count": len(batch.logs)}

@router.post("/")
async def receive_single_log(log_entry: LogEntry):
    """Receive single log entry"""
    await log_repository.save(log_entry)
    return {"status": "received"}
```

---

## 💻 Implementation Guide

### Step 1: Set Up Logging Infrastructure

```python
# services/<service>/infrastructure/logging/logger.py

import os
from common.logging.structured_logger import StructuredLogger

def create_logger() -> StructuredLogger:
    """Create standardized logger for this service"""
    return StructuredLogger(
        service_name=os.getenv("SERVICE_NAME", "unknown"),
        service_version=os.getenv("SERVICE_VERSION", "1.0.0"),
        environment=os.getenv("ENVIRONMENT", "development"),
        log_collector_enabled=os.getenv("LOG_COLLECTOR_ENABLED", "true") == "true"
    )

# Global logger instance
logger = create_logger()
```

### Step 2: Log All Core Features

```python
# services/doc_store/application/commands/create_document.py

from infrastructure.logging.logger import logger
from common.logging.operation_context import log_operation

class CreateDocumentCommand:
    """Command to create a document"""
    
    async def execute(
        self,
        title: str,
        content: str,
        user_id: str
    ) -> Document:
        """Create document with comprehensive logging"""
        
        with log_operation(
            logger,
            "create_document",
            metadata={
                "title_length": len(title),
                "content_length": len(content),
                "user_id": user_id
            }
        ):
            # Validate
            logger.debug(
                "Validating document data",
                operation="create_document",
                metadata={"title": title[:50]}  # Log first 50 chars only
            )
            
            self._validate(title, content)
            
            # Create entity
            logger.debug(
                "Creating document entity",
                operation="create_document"
            )
            
            document = Document(title=title, content=content)
            
            # Save
            logger.debug(
                "Saving document to repository",
                operation="create_document",
                metadata={"document_id": document.id}
            )
            
            await self.repository.save(document)
            
            # Log success metrics
            logger.info(
                "Document created successfully",
                operation="create_document",
                metadata={
                    "document_id": document.id,
                    "title_length": len(title),
                    "content_length": len(content),
                    "user_id": user_id,
                    "tags": ["document_created", "success"]
                }
            )
            
            return document
```

### Step 3: Log API Requests

```python
# services/doc_store/presentation/api/middleware/logging_middleware.py

import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from infrastructure.logging.logger import logger
from common.logging.structured_logger import correlation_id_var, user_id_var

class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all HTTP requests"""
    
    async def dispatch(self, request: Request, call_next):
        # Generate/extract correlation ID
        correlation_id = request.headers.get("X-Correlation-ID") or generate_id()
        correlation_id_var.set(correlation_id)
        
        # Extract user ID if authenticated
        user_id = self._extract_user_id(request)
        user_id_var.set(user_id)
        
        # Log request start
        start_time = time.time()
        
        logger.info(
            f"HTTP request started",
            operation="http_request",
            metadata={
                "method": request.method,
                "path": request.url.path,
                "query_params": dict(request.query_params),
                "correlation_id": correlation_id,
                "user_id": user_id,
                "user_agent": request.headers.get("user-agent"),
                "ip_address": hash_ip(request.client.host)  # Hash for privacy
            }
        )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Log response
            duration_ms = int((time.time() - start_time) * 1000)
            
            logger.info(
                f"HTTP request completed",
                operation="http_request",
                duration_ms=duration_ms,
                metadata={
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "correlation_id": correlation_id,
                    "duration_ms": duration_ms
                }
            )
            
            # Add correlation ID to response
            response.headers["X-Correlation-ID"] = correlation_id
            
            return response
            
        except Exception as e:
            # Log error
            duration_ms = int((time.time() - start_time) * 1000)
            
            logger.error(
                f"HTTP request failed",
                operation="http_request",
                duration_ms=duration_ms,
                metadata={
                    "method": request.method,
                    "path": request.url.path,
                    "correlation_id": correlation_id
                },
                error={
                    "type": type(e).__name__,
                    "message": str(e)
                }
            )
            
            raise
```

### Step 4: Log Background Tasks

```python
# services/doc_store/infrastructure/tasks/document_processor.py

from infrastructure.logging.logger import logger

async def process_documents_batch():
    """Background task to process documents"""
    
    logger.info(
        "Starting document batch processing",
        operation="batch_process_documents"
    )
    
    try:
        documents = await get_pending_documents()
        
        logger.info(
            "Retrieved documents for processing",
            operation="batch_process_documents",
            metadata={"count": len(documents)}
        )
        
        processed_count = 0
        error_count = 0
        
        for doc in documents:
            try:
                await process_document(doc)
                processed_count += 1
            except Exception as e:
                error_count += 1
                logger.error(
                    "Failed to process document",
                    operation="process_document",
                    metadata={"document_id": doc.id},
                    error={
                        "type": type(e).__name__,
                        "message": str(e)
                    }
                )
        
        logger.info(
            "Completed document batch processing",
            operation="batch_process_documents",
            metadata={
                "processed": processed_count,
                "errors": error_count,
                "total": len(documents)
            }
        )
        
    except Exception as e:
        logger.critical(
            "Document batch processing failed",
            operation="batch_process_documents",
            error={
                "type": type(e).__name__,
                "message": str(e)
            }
        )
```

---

## 📈 Log Analysis Preparation

### Structured for Future Analysis

All logs follow a consistent structure to enable:

**1. Performance Analysis**
```sql
-- Average response time by operation
SELECT 
    operation,
    AVG(duration_ms) as avg_duration,
    MAX(duration_ms) as max_duration,
    COUNT(*) as request_count
FROM logs
WHERE level = 'INFO'
AND duration_ms IS NOT NULL
GROUP BY operation
ORDER BY avg_duration DESC;
```

**2. Error Analysis**
```sql
-- Error rates by service
SELECT 
    service,
    COUNT(*) as error_count,
    COUNT(DISTINCT correlation_id) as affected_requests
FROM logs
WHERE level IN ('ERROR', 'CRITICAL')
AND timestamp > NOW() - INTERVAL '1 hour'
GROUP BY service;
```

**3. User Behavior Analysis**
```sql
-- Most common user operations
SELECT 
    operation,
    COUNT(*) as usage_count,
    COUNT(DISTINCT user_id) as unique_users
FROM logs
WHERE level = 'INFO'
AND user_id IS NOT NULL
GROUP BY operation
ORDER BY usage_count DESC;
```

**4. Correlation Tracking**
```sql
-- Full request trace by correlation ID
SELECT 
    timestamp,
    service,
    operation,
    duration_ms,
    message
FROM logs
WHERE correlation_id = 'req-123abc'
ORDER BY timestamp;
```

### Log Analysis Service Integration

The log data structure supports future log analysis features:

```python
# Future: services/log-analysis/queries/get_service_health.py

async def get_service_health(service_name: str, time_window: int = 3600):
    """Analyze service health from logs"""
    
    # Query logs from log-collector
    logs = await log_collector_client.query_logs(
        service=service_name,
        time_window=time_window
    )
    
    # Calculate metrics
    total_requests = count_by_level(logs, "INFO")
    error_count = count_by_level(logs, "ERROR")
    critical_count = count_by_level(logs, "CRITICAL")
    
    avg_duration = calculate_avg_duration(logs)
    p95_duration = calculate_p95_duration(logs)
    
    error_rate = error_count / total_requests if total_requests > 0 else 0
    
    # Determine health status
    health = "healthy"
    if error_rate > 0.05 or critical_count > 0:
        health = "degraded"
    if error_rate > 0.10 or critical_count > 5:
        health = "unhealthy"
    
    return {
        "service": service_name,
        "health": health,
        "metrics": {
            "total_requests": total_requests,
            "error_rate": error_rate,
            "avg_duration_ms": avg_duration,
            "p95_duration_ms": p95_duration
        }
    }
```

---

## ✅ Checklist

### Per-Service Logging Checklist

**Setup**:
- [ ] StructuredLogger configured
- [ ] Log-collector client initialized
- [ ] Correlation ID middleware added
- [ ] JSON formatter enabled
- [ ] Environment variables configured

**Core Feature Logging**:
- [ ] All core operations logged (INFO level)
- [ ] All errors logged (ERROR/CRITICAL level)
- [ ] Performance metrics included (duration_ms)
- [ ] User context included (user_id where applicable)
- [ ] Resource IDs included (document_id, etc.)

**API Logging**:
- [ ] All HTTP requests logged
- [ ] Correlation IDs tracked
- [ ] Response times measured
- [ ] Status codes logged
- [ ] Error responses detailed

**Quality**:
- [ ] No sensitive data in logs
- [ ] Logs are structured JSON
- [ ] All required fields present
- [ ] Logs sent to log-collector
- [ ] Log levels appropriate

---

**Document Control**  
**Version**: 1.0.0  
**Last Updated**: October 8, 2025  
**Next Review**: 2025-11-08  
**Owner**: Hackathon Team

