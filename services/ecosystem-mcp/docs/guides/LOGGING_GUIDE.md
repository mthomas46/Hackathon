---
title: "📝 ECOSYSTEM MCP - LOGGING & TERMINAL FEEDBACK GUIDE"
service: "ecosystem-mcp"
category: "guides"
tags: ['config', 'configuration', 'database', 'deployment', 'docker', 'guide', 'health', 'howto', 'ingestion', 'llm']
related: ['INDEX.md', 'architecture/OVERVIEW.md', 'CODE_REFERENCE.md', 'API_ENDPOINTS_COMPLETE.md']
status: "current"
last_updated: "2025-10-28"
audience: "user"
difficulty: "beginner"
semantic_keywords: ['config', 'configuration', 'database', 'deployment', 'docker']
llm_search_hints: ['what is 📝 ecosystem mcp - logging & terminal feedback guide', 'how does 📝 ecosystem mcp - logging & terminal feedback guide work', 'guide to 📝 ecosystem mcp - logging & terminal feedback guide']
---

# 📝 ECOSYSTEM MCP - LOGGING & TERMINAL FEEDBACK GUIDE

**Purpose**: Comprehensive logging and beautiful terminal feedback for all operations  
**Status**: ✅ Production-Ready  
**Coverage**: All crucial features tracked

---

## 🎯 OVERVIEW

Ecosystem MCP Service includes comprehensive logging and rich terminal feedback to track all crucial features and operations.

### **Features**

1. **Structured Logging** - JSON format for machine processing
2. **Rich Terminal Output** - Beautiful, readable terminal feedback
3. **Progress Tracking** - Progress bars for long operations
4. **Operation Logging** - Automatic start/complete/failure tracking
5. **Metrics Logging** - Performance and statistics tracking
6. **Checkpoint Logging** - Track progress through complex operations
7. **Multiple Outputs** - Console (rich) + File (JSON)

---

## 🚀 QUICK START

### **Basic Logging**

```python
import logging

logger = logging.getLogger(__name__)

# Standard logging
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

### **Rich Terminal Output**

```python
from src.utils.terminal_feedback import (
    print_success,
    print_error,
    print_warning,
    print_info
)

print_success("Operation completed successfully")
print_error("Something went wrong")
print_warning("This might be an issue")
print_info("Just so you know...")
```

### **Operation Logging**

```python
from src.utils.logging_config import OperationLogger

# Automatic success/failure tracking
with OperationLogger("Ingesting documents") as op:
    # Do work
    op.checkpoint("Scanned files")
    op.metric("files_found", 100)
    
    # Process files
    op.checkpoint("Parsing documents")
    op.metric("documents_parsed", 95)
    
    # Automatically logs success/failure on exit
```

---

## 📊 LOGGING FEATURES

### **1. Structured Logging**

All logs are structured for easy parsing and analysis:

```json
{
  "timestamp": "2025-10-10T12:00:00",
  "level": "INFO",
  "logger": "src.ingestion.pipeline",
  "message": "Document ingested successfully",
  "document_id": "abc123",
  "service_name": "code-analyzer"
}
```

### **2. Rich Terminal Output**

Beautiful, readable terminal output with:
- ✅ Color-coded messages
- ✅ Icons and symbols
- ✅ Progress bars
- ✅ Tables and trees
- ✅ Syntax highlighting
- ✅ Panels and boxes

### **3. Operation Tracking**

Automatic tracking of major operations:

```
================================================================================
Starting: Document Ingestion
================================================================================
Operation: Document Ingestion
  mode: quick
  target_files: 150

🔹 Checkpoint: Files scanned
  files_found: 150

📊 files_processed: 150.00

🔹 Checkpoint: Documents normalized
  normalized: 148
  failed: 2

================================================================================
✅ Completed: Document Ingestion (45.23s)
================================================================================
Operation completed: Document Ingestion
  duration_seconds: 45.23
  files_processed: 150
```

### **4. Progress Bars**

Visual progress tracking for long operations:

```python
from src.utils.logging_config import create_progress

with create_progress() as progress:
    task = progress.add_task("Processing files", total=100)
    
    for i in range(100):
        # Do work
        progress.update(task, advance=1)
```

Output:
```
⠋ Processing files ━━━━━━━━━━━━━━━━━━━━━━━━━━ 45/100 45%
```

### **5. Metrics Logging**

Track performance and statistics:

```python
from src.utils.logging_config import log_metric

log_metric("documents_processed", 150)
log_metric("processing_time", 45.23, "seconds")
log_metric("throughput", 3.32, "docs/sec")
```

Output:
```
📊 documents_processed: 150
📊 processing_time: 45.23 seconds
📊 throughput: 3.32 docs/sec
```

---

## 🎨 TERMINAL FEEDBACK

### **Banners**

```python
from src.utils.terminal_feedback import print_banner

print_banner(
    "ECOSYSTEM MCP SERVER",
    "Intelligent Refactoring Knowledge Base"
)
```

Output:
```
╔════════════════════════════════════════════════════════════╗
║  ECOSYSTEM MCP SERVER                                      ║
║  Intelligent Refactoring Knowledge Base                    ║
╚════════════════════════════════════════════════════════════╝
```

### **Tables**

```python
from src.utils.terminal_feedback import print_table

print_table(
    "Service Status",
    columns=["Service", "Status", "Uptime"],
    rows=[
        ["PostgreSQL", "✅ Healthy", "2h 15m"],
        ["Redis", "✅ Healthy", "2h 15m"],
        ["Ollama", "✅ Healthy", "2h 10m"],
    ]
)
```

Output:
```
                    Service Status                     
┌─────────────┬────────────┬─────────┐
│ Service     │ Status     │ Uptime  │
├─────────────┼────────────┼─────────┤
│ PostgreSQL  │ ✅ Healthy │ 2h 15m  │
│ Redis       │ ✅ Healthy │ 2h 15m  │
│ Ollama      │ ✅ Healthy │ 2h 10m  │
└─────────────┴────────────┴─────────┘
```

### **Statistics**

```python
from src.utils.terminal_feedback import print_statistics

print_statistics({
    "documents_ingested": 150,
    "documents_failed": 2,
    "success_rate": 98.67,
    "duration_seconds": 45.23,
    "throughput": 3.32
}, "Ingestion Statistics")
```

Output:
```
╭─────────────────── Ingestion Statistics ────────────────────╮
│ Documents Ingested: 150                                     │
│ Documents Failed: 2                                         │
│ Success Rate: 98.67                                         │
│ Duration Seconds: 45.23                                     │
│ Throughput: 3.32                                            │
╰─────────────────────────────────────────────────────────────╯
```

### **Health Status**

```python
from src.utils.terminal_feedback import print_health_status

print_health_status(
    "PostgreSQL",
    healthy=True,
    details={
        "version": "16.0",
        "connections": 5,
        "uptime": "2h 15m"
    }
)
```

Output:
```
PostgreSQL: ✅ Healthy
  version: 16.0
  connections: 5
  uptime: 2h 15m
```

---

## 📁 LOGGING CONFIGURATION

### **Setup Logging**

```python
from src.utils.logging_config import setup_logging

# Setup with defaults
setup_logging()

# Setup with custom level
setup_logging(log_level="DEBUG")

# Setup with custom file
setup_logging(log_file="custom.log")

# Disable rich output (for CI/CD)
setup_logging(enable_rich=False)
```

### **Log Files**

Logs are written to `./logs/` directory:

```
logs/
├── ecosystem-mcp-20251010.log    # Daily log file
├── ecosystem-mcp-20251009.log
└── ecosystem-mcp-20251008.log
```

### **Log Format**

**Console** (Human-readable):
```
2025-10-10 12:00:00 - src.ingestion.pipeline - INFO - Starting ingestion
```

**File** (JSON for processing):
```json
{"timestamp": "2025-10-10T12:00:00", "level": "INFO", "logger": "src.ingestion.pipeline", "message": "Starting ingestion"}
```

---

## 🎯 LOGGING BEST PRACTICES

### **1. Use Appropriate Log Levels**

```python
# DEBUG: Detailed diagnostic information
logger.debug(f"Processing file: {file_path}")

# INFO: General informational messages
logger.info(f"Ingested {count} documents")

# WARNING: Warning messages for potential issues
logger.warning(f"Document {doc_id} missing metadata")

# ERROR: Error messages for failures
logger.error(f"Failed to parse {file_path}: {error}")

# CRITICAL: Critical failures requiring immediate attention
logger.critical(f"Database connection lost")
```

### **2. Include Context**

```python
# Good: Include relevant context
logger.info(f"Document ingested", extra={
    "document_id": doc_id,
    "service_name": service_name,
    "duration_ms": duration
})

# Bad: Vague message
logger.info("Done")
```

### **3. Log Key Operations**

Always log:
- ✅ Service startup/shutdown
- ✅ Configuration changes
- ✅ External API calls
- ✅ Database operations
- ✅ File I/O operations
- ✅ Error conditions
- ✅ Security events

### **4. Use Operation Logger for Complex Operations**

```python
# Good: Automatic tracking
with OperationLogger("Complex operation") as op:
    op.checkpoint("Step 1")
    # Do step 1
    op.checkpoint("Step 2")
    # Do step 2
    op.metric("items_processed", 100)

# Bad: Manual tracking
logger.info("Starting complex operation")
try:
    # Do work
    logger.info("Completed")
except:
    logger.error("Failed")
```

---

## 📊 MONITORING & OBSERVABILITY

### **Log Analysis**

Search logs via API:
```bash
# Search for errors
curl "http://localhost:8000/api/v1/logs/search?query=error&level=ERROR"

# Tail recent logs
curl "http://localhost:8000/api/v1/logs/tail?lines=100"
```

### **Metrics Collection**

All metrics are logged and can be extracted:
```bash
# Extract metrics from logs
grep "📊" logs/ecosystem-mcp-*.log

# Parse JSON logs
jq 'select(.level == "INFO") | .message' logs/ecosystem-mcp-*.log
```

### **Health Monitoring**

Check service health:
```bash
curl http://localhost:8000/health
```

---

## 🔧 CONFIGURATION

### **Environment Variables**

```bash
# Log level
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL

# Enable/disable rich output
RICH_CONSOLE=true

# Log file path
LOG_FILE=ecosystem-mcp.log
```

### **Programmatic Configuration**

```python
from src.config import settings

# Access logging config
log_level = settings.log_level  # From environment
```

---

## 📝 EXAMPLES

### **Example 1: Ingestion with Logging**

```python
from src.utils.logging_config import OperationLogger, create_progress
import logging

logger = logging.getLogger(__name__)

async def ingest_documents():
    """Ingest documents with comprehensive logging."""
    with OperationLogger("Document Ingestion", {"mode": "quick"}) as op:
        # Scan files
        op.checkpoint("Scanning files")
        files = scan_files()
        op.metric("files_found", len(files))
        
        # Process with progress bar
        with create_progress() as progress:
            task = progress.add_task("Processing", total=len(files))
            
            for file in files:
                try:
                    process_file(file)
                    progress.update(task, advance=1)
                except Exception as e:
                    logger.error(f"Failed to process {file}: {e}")
        
        op.checkpoint("Processing complete")
        op.metric("success_rate", 98.5, "%")
```

### **Example 2: API Request Logging**

```python
import logging
from fastapi import Request

logger = logging.getLogger(__name__)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all API requests."""
    logger.info(
        f"API Request",
        extra={
            "method": request.method,
            "path": request.url.path,
            "client": request.client.host
        }
    )
    
    response = await call_next(request)
    
    logger.info(
        f"API Response",
        extra={
            "status_code": response.status_code,
            "path": request.url.path
        }
    )
    
    return response
```

---

## ✅ CHECKLIST

For production deployment:

- [x] Logging configured with appropriate level
- [x] Log rotation enabled (daily files)
- [x] All major operations logged
- [x] Error conditions logged with context
- [x] Performance metrics tracked
- [x] Health checks logged
- [x] Security events logged
- [x] Log files backed up
- [x] Log analysis tools configured
- [x] Monitoring alerts set up

---

## 📚 ADDITIONAL RESOURCES

- [structlog Documentation](https://www.structlog.org/)
- [Rich Documentation](https://rich.readthedocs.io/)
- [Python Logging Best Practices](https://docs.python.org/3/howto/logging.html)

---

**Status**: ✅ Comprehensive Logging Implemented  
**Coverage**: All Crucial Features Tracked  
**Terminal Feedback**: Rich & Beautiful  
**Production-Ready**: Yes

