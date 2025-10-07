# Common Utilities for MCP Services

Shared utilities and infrastructure for all MCP services.

## 📦 Modules

### 1. Logging (`common.logging`)

Provides structured logging with integration to mcp-logs service.

#### MCPLogClient

Async client for sending logs to mcp-logs service.

```python
from common.logging import MCPLogClient

# Initialize client
log_client = MCPLogClient(
    service_name="my-service",
    mcp_logs_url="http://mcp-logs:8016"
)

# Start background flush task
await log_client.start()

# Send logs
await log_client.info(
    "Operation completed",
    correlation_id="abc-123",
    fields={"duration_ms": 150}
)

# Convenience methods
await log_client.debug("Debug message")
await log_client.warning("Warning message")
await log_client.error("Error message", exc_info=exception)

# Clean shutdown
await log_client.stop()
```

#### Configuration

Configure structured logging for your service.

```python
from common.logging import configure_logging, get_logger

# Configure logging
configure_logging(
    service_name="my-service",
    log_level="INFO",
    structured=True
)

# Get logger
logger = get_logger(__name__)

# Use logger
logger.info("Service started")
logger.error("Error occurred", extra={"fields": {"user_id": "123"}})
```

### 2. Middleware (`common.middleware`)

Provides request correlation and tracking middleware.

#### Correlation Middleware

Tracks requests across services using correlation IDs.

```python
from fastapi import FastAPI
from common.middleware import CorrelationMiddleware, get_correlation_id

app = FastAPI()

# Add middleware
app.add_middleware(CorrelationMiddleware)

# Use in endpoints
@app.get("/api/data")
async def get_data():
    correlation_id = get_correlation_id()
    # Use correlation_id for logging
    return {"correlation_id": correlation_id}
```

Or use as a function-based middleware:

```python
from common.middleware import correlation_middleware

app.middleware("http")(correlation_middleware)
```

## 🔧 Installation

Add to your service's requirements.txt:

```txt
httpx>=0.25.0  # For MCPLogClient
```

## 📚 Features

### Logging Features
- ✅ Async HTTP transport to mcp-logs
- ✅ Automatic batching (configurable batch size)
- ✅ Periodic flushing (configurable interval)
- ✅ Graceful degradation (local logging if remote fails)
- ✅ Correlation ID tracking
- ✅ Structured log entries
- ✅ Custom fields and tags
- ✅ Exception tracking

### Middleware Features
- ✅ Automatic correlation ID generation
- ✅ Correlation ID extraction from headers
- ✅ Correlation ID propagation to responses
- ✅ Context variable storage for easy access
- ✅ Request state integration

## 🎯 Usage Examples

### Complete Service Integration

```python
from fastapi import FastAPI
from common.logging import MCPLogClient, configure_logging, get_logger
from common.middleware import CorrelationMiddleware, get_correlation_id

# Configure logging
configure_logging(
    service_name="my-service",
    log_level="INFO"
)

logger = get_logger(__name__)

# Create app
app = FastAPI()

# Add middleware
app.add_middleware(CorrelationMiddleware)

# Initialize log client
log_client = MCPLogClient(
    service_name="my-service",
    mcp_logs_url="http://mcp-logs:8016"
)

@app.on_event("startup")
async def startup():
    await log_client.start()
    logger.info("Service started")

@app.on_event("shutdown")
async def shutdown():
    logger.info("Service shutting down")
    await log_client.stop()

@app.get("/api/process")
async def process_data(data_id: str):
    correlation_id = get_correlation_id()
    
    # Log to mcp-logs
    await log_client.info(
        "Processing data",
        correlation_id=correlation_id,
        fields={"data_id": data_id}
    )
    
    # Process data...
    
    await log_client.info(
        "Processing complete",
        correlation_id=correlation_id,
        fields={"data_id": data_id, "duration_ms": 100}
    )
    
    return {"status": "success"}
```

## 🔍 Log Entry Structure

```python
{
    "entry_id": "uuid",
    "message": "Operation completed",
    "level": "INFO",
    "service": "my-service",
    "source": "module.function",
    "timestamp": "2025-10-07T12:00:00Z",
    
    # Context
    "correlation_id": "abc-123",
    "request_id": "req-456",
    "user_id": "user-789",
    
    # Custom fields
    "fields": {
        "duration_ms": 150,
        "records_processed": 100
    },
    
    # Tags
    "tags": ["processing", "batch"]
}
```

## 📊 Best Practices

1. **Always use correlation IDs** for request tracking
2. **Log at appropriate levels** (DEBUG for internals, INFO for operations)
3. **Include relevant context** in fields (IDs, durations, counts)
4. **Use structured logging** for better parsing and analysis
5. **Flush logs on shutdown** to ensure all logs are sent
6. **Handle exceptions** with exc_info for full stack traces
7. **Use tags** for categorization and filtering

## 🚀 Performance

- **Batching**: Reduces HTTP overhead by batching logs
- **Async**: Non-blocking HTTP requests
- **Background flushing**: Automatic periodic flush
- **Graceful degradation**: Falls back to local logging

## 📝 Notes

- Requires mcp-logs service running on port 8016
- Falls back to local logging if mcp-logs unavailable
- Correlation IDs automatically propagated in FastAPI middleware
- Context variables used for correlation ID access throughout request lifecycle

