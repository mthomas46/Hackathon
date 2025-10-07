---
llm_metadata:
  document_type: guide
  content_focus: operational
  platform:
    primary: mcp
    secondary: []
  status: active
  created_date: '2024-09-01'
  last_modified: '2025-10-07'
  topics:
  - python
  - docker
  - llm_orchestration
  - testing
  - deployment
  - monitoring
  concepts: []
  technologies: []
  services_mentioned: []
  semantic_summary: Guide document about operational aspects of the mcp platform
  archive_reason: n/a
  historical_value: current
  reference_value: high
semantic_embedding:
  model: text-embedding-ada-002
  embedding_date: '2025-10-07'
  embedding_checksum: pending
rag_metadata:
  chunk_strategy: semantic
  optimal_chunk_size: 512
  retrieval_priority: high
---

# 🔗 **Service Integration Guide**

## **Complete Guide to Integrating with Performance Store and MCP Store**

---

## **Table of Contents**

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [Performance Store Integration](#performance-store-integration)
4. [MCP Store Integration](#mcp-store-integration)
5. [Best Practices](#best-practices)
6. [Error Handling](#error-handling)
7. [Testing](#testing)
8. [Troubleshooting](#troubleshooting)

---

## **Overview**

This guide explains how to integrate your service with:

- **Performance Store** - For tracking execution metrics, performance trends, and anomaly detection
- **MCP Store** - For managing MCP packages, versions, and marketplace features

### **Architecture**

```
┌─────────────────┐
│  Your Service   │
└────────┬────────┘
         │
         ├────────────────────┐
         │                    │
         ▼                    ▼
┌────────────────┐  ┌─────────────────┐
│ Performance    │  │   MCP Store     │
│   Store        │  │                 │
│ (Port 5649)    │  │  (Port 5648)    │
└────────────────┘  └─────────────────┘
```

### **Key Features**

✅ **Circuit Breaker** - Prevents cascade failures  
✅ **Automatic Retry** - Exponential backoff (max 3 attempts)  
✅ **Timeout Handling** - Configurable timeouts  
✅ **Health Checks** - Service availability monitoring  
✅ **Request Logging** - Debug & performance tracking  
✅ **Non-blocking** - Performance recording doesn't block main workflow  

---

## **Quick Start**

### **1. Install Dependencies**

The HTTP clients are already available in the `common` package:

```python
from common.clients import PerformanceStoreClient, MCPStoreClient
```

### **2. Initialize Clients**

```python
# Performance Store client
perf_client = PerformanceStoreClient(base_url="http://localhost:5649")

# MCP Store client
store_client = MCPStoreClient(base_url="http://localhost:5648")
```

### **3. Use Clients**

```python
# Record performance
await perf_client.record_execution(
    orchestration_id="exec-123",
    mcp_id="mcp-prod",
    pattern_name="chain-of-thought",
    status="success",
    duration_ms=1500
)

# Get package
package = await store_client.get_package_by_name("my-mcp")
```

### **4. Clean Up**

```python
# Close clients when done
await perf_client.close()
await store_client.close()
```

---

## **Performance Store Integration**

### **Use Cases**

- **Orchestrator** - Record query execution metrics
- **Composer** - Track composition performance
- **Gateway** - Monitor API performance
- **Interpreter** - Track parsing performance

### **Basic Integration**

```python
from common.clients import PerformanceStoreClient
import logging

logger = logging.getLogger(__name__)

class MyService:
    def __init__(self):
        self.perf_client = PerformanceStoreClient()
    
    async def execute_task(self, task_id: str):
        """Execute task and record performance."""
        start_time = time.time()
        
        try:
            # Your business logic here
            result = await self._do_work()
            
            # Calculate duration
            duration_ms = (time.time() - start_time) * 1000
            
            # Record success
            await self.perf_client.record_execution(
                orchestration_id=task_id,
                mcp_id="my-mcp",
                pattern_name="my-pattern",
                status="success",
                duration_ms=duration_ms,
            )
            
            return result
        
        except Exception as e:
            # Calculate duration even on failure
            duration_ms = (time.time() - start_time) * 1000
            
            # Record failure
            await self.perf_client.record_execution(
                orchestration_id=task_id,
                mcp_id="my-mcp",
                pattern_name="my-pattern",
                status="failed",
                duration_ms=duration_ms,
                error_message=str(e),
            )
            
            raise
    
    async def close(self):
        await self.perf_client.close()
```

### **Advanced: Monitoring & Analytics**

```python
async def monitor_performance(self):
    """Monitor service performance and detect issues."""
    
    # Get performance summary
    summary = await self.perf_client.get_performance_summary(
        time_window_hours=24
    )
    
    logger.info(f"24h Summary:")
    logger.info(f"  Total executions: {summary.get('total_executions')}")
    logger.info(f"  Success rate: {summary.get('success_rate')}%")
    logger.info(f"  Avg duration: {summary.get('avg_duration_ms')}ms")
    
    # Check for anomalies
    anomalies = await self.perf_client.detect_orchestration_anomalies(
        time_window_days=7
    )
    
    if anomalies:
        logger.warning(f"⚠️ Detected {len(anomalies)} anomalies!")
        for anomaly in anomalies:
            logger.warning(
                f"  - {anomaly['type']}: {anomaly['description']}"
            )
    
    # Get degrading patterns
    degrading = await self.perf_client.get_degrading_patterns()
    
    if degrading:
        logger.warning(f"⚠️ Degrading patterns: {degrading}")
```

### **Performance Store API Reference**

#### **Execution Recording**
```python
await perf_client.record_execution(
    orchestration_id: str,      # Unique execution ID
    mcp_id: str,                # MCP identifier
    pattern_name: str,          # Pattern name
    status: str,                # success/failed/timeout/cancelled
    duration_ms: float,         # Duration in milliseconds
    query: str = None,          # Original query (optional)
    confidence: float = None,   # Result confidence 0-1
    num_sources: int = None,    # Number of sources used
    response_length: int = None,# Response length
    error_message: str = None,  # Error message if failed
    metadata: dict = None,      # Additional metadata
)
```

#### **Querying**
```python
# Get specific execution
execution = await perf_client.get_execution(execution_id)

# Get recent executions
recent = await perf_client.get_recent_executions(
    limit=10,
    pattern_name="chain-of-thought",  # optional filter
    mcp_id="mcp-prod",                # optional filter
)

# Get performance summary
summary = await perf_client.get_performance_summary(
    time_window_hours=24,
    pattern_name="chain-of-thought",  # optional filter
)

# List all patterns
patterns = await perf_client.list_patterns()
```

#### **Analytics**
```python
# Get trends
trends = await perf_client.get_orchestration_trends(time_window_days=7)
pattern_trends = await perf_client.get_pattern_trends("chain-of-thought", 7)

# Compare patterns
comparison = await perf_client.compare_patterns("pattern1", "pattern2", 7)

# Get degrading patterns
degrading = await perf_client.get_degrading_patterns()
```

#### **Anomaly Detection**
```python
# Detect orchestration anomalies
anomalies = await perf_client.detect_orchestration_anomalies(
    time_window_days=7
)

# Detect pattern-specific anomalies
pattern_anomalies = await perf_client.detect_pattern_anomalies(
    "chain-of-thought",
    time_window_days=7
)
```

---

## **MCP Store Integration**

### **Use Cases**

- **Registry** - Manage package catalog
- **Training Coordinator** - Fetch/store training packages
- **Provisioner** - Deploy packages to MCPs
- **Dashboard** - Display marketplace

### **Basic Integration**

```python
from common.clients import MCPStoreClient

class MyService:
    def __init__(self):
        self.store_client = MCPStoreClient()
    
    async def use_package(self, package_name: str):
        """Fetch and use an MCP package."""
        
        # Search for package
        package = await self.store_client.get_package_by_name(package_name)
        
        if not package:
            raise ValueError(f"Package {package_name} not found")
        
        # Get latest version
        versions = await self.store_client.list_versions(
            package["package_id"]
        )
        
        if not versions:
            raise ValueError(f"No versions for package {package_name}")
        
        latest = versions[0]
        
        # Download version
        file_data = await self.store_client.download_version(
            package["package_id"],
            latest["version"]
        )
        
        # Use file_data...
        return file_data
    
    async def close(self):
        await self.store_client.close()
```

### **Advanced: Package Management**

```python
async def create_and_publish_package(self, name: str, file_data: bytes):
    """Create package and upload first version."""
    
    # Create package
    package = await self.store_client.create_package(
        name=name,
        description="My knowledge base",
        owner_id="user-123",
        tags=["production", "knowledge"],
        categories=["knowledge-base"],
        metadata={
            "author": "John Doe",
            "license": "MIT",
        }
    )
    
    logger.info(f"Created package: {package['package_id']}")
    
    # Upload version
    version = await self.store_client.upload_version(
        package_id=package["package_id"],
        version="1.0.0",
        file_data=file_data,
        changelog="Initial release",
        metadata={
            "size_bytes": len(file_data),
            "created_at": datetime.now().isoformat(),
        }
    )
    
    logger.info(f"Uploaded version: {version['version_id']}")
    
    return package, version
```

### **Advanced: Marketplace Features**

```python
async def discover_packages(self):
    """Discover trending and popular packages."""
    
    # Get trending packages
    trending = await self.store_client.get_trending_packages(
        time_window_days=7,
        limit=10
    )
    
    logger.info(f"📈 Trending packages:")
    for pkg in trending:
        logger.info(f"  - {pkg['name']}: {pkg['download_count']} downloads")
    
    # Get popular tags
    tags = await self.store_client.get_popular_tags(limit=20)
    
    logger.info(f"🏷️ Popular tags:")
    for tag in tags:
        logger.info(f"  - {tag['tag']}: {tag['count']} packages")
    
    # Get marketplace stats
    stats = await self.store_client.get_marketplace_stats()
    
    logger.info(f"📊 Marketplace stats:")
    logger.info(f"  Total packages: {stats.get('total_packages')}")
    logger.info(f"  Total downloads: {stats.get('total_downloads')}")
```

### **MCP Store API Reference**

#### **Package Management**
```python
# Create package
package = await store_client.create_package(
    name: str,
    description: str,
    owner_id: str,
    tags: List[str] = None,
    categories: List[str] = None,
    metadata: dict = None,
)

# Get package
package = await store_client.get_package(package_id)
package = await store_client.get_package_by_name(name)

# List packages
packages = await store_client.list_packages(
    limit=50,
    offset=0,
    status="published",  # draft/published/deprecated/archived
)

# Update package
updated = await store_client.update_package(package_id, **updates)

# Delete package
deleted = await store_client.delete_package(package_id)
```

#### **Version Management**
```python
# Upload version
version = await store_client.upload_version(
    package_id,
    version,
    file_data,
    changelog=None,
    metadata=None,
)

# Get version
version = await store_client.get_version(package_id, version)

# List versions
versions = await store_client.list_versions(package_id)

# Download version
file_data = await store_client.download_version(package_id, version)
```

#### **Search & Discovery**
```python
# Search packages
results = await store_client.search_packages(
    query,
    limit=20,
    tags=["tag1", "tag2"],
    categories=["category1"],
)
```

#### **Marketplace**
```python
# Star/unstar package
await store_client.star_package(package_id, user_id)
await store_client.unstar_package(package_id, user_id)

# Get trending
trending = await store_client.get_trending_packages(
    time_window_days=7,
    limit=10
)

# Get popular tags
tags = await store_client.get_popular_tags(limit=20)

# Get stats
stats = await store_client.get_marketplace_stats()
```

#### **Export/Import**
```python
# Export package
file_data = await store_client.export_package(
    package_id,
    version="1.0.0",        # optional
    include_all_versions=False
)

# Import package
package = await store_client.import_package(file_data)
```

---

## **Best Practices**

### **1. Always Close Clients**

```python
# ✅ Good: Use try/finally
perf_client = PerformanceStoreClient()
try:
    await perf_client.record_execution(...)
finally:
    await perf_client.close()

# ✅ Better: Use async context manager (if available)
# async with PerformanceStoreClient() as client:
#     await client.record_execution(...)
```

### **2. Non-blocking Performance Recording**

```python
# ✅ Good: Don't let performance recording block main workflow
try:
    await perf_client.record_execution(...)
except Exception as e:
    logger.warning(f"Failed to record performance: {e}")
    # Continue with main workflow - don't raise!
```

### **3. Use Health Checks**

```python
# Check service health before critical operations
if not await store_client.health_check():
    logger.warning("MCP Store is unavailable")
    # Fall back to cached data or fail gracefully
```

### **4. Provide Rich Metadata**

```python
# ✅ Good: Provide rich context for debugging
await perf_client.record_execution(
    orchestration_id=exec_id,
    mcp_id=mcp_id,
    pattern_name=pattern_name,
    status="success",
    duration_ms=duration_ms,
    query=query,                    # Original query
    confidence=confidence,          # Result confidence
    num_sources=num_sources,        # Sources used
    response_length=len(response),  # Response size
    metadata={                      # Additional context
        "user_id": user_id,
        "session_id": session_id,
        "environment": "production",
    }
)
```

### **5. Handle Errors Gracefully**

```python
# ✅ Good: Handle errors without disrupting service
try:
    package = await store_client.get_package(package_id)
except Exception as e:
    logger.error(f"Failed to get package: {e}")
    # Provide sensible default or cached data
    package = get_cached_package(package_id)
```

### **6. Use Timeouts**

```python
# ✅ Good: Set appropriate timeouts
perf_client = PerformanceStoreClient()
perf_client.client.timeout = 10  # 10 second timeout

# For long operations (uploads/downloads)
store_client = MCPStoreClient()
store_client.client.timeout = 60  # 60 second timeout
```

### **7. Monitor Performance**

```python
# ✅ Good: Regularly check for anomalies
async def periodic_health_check():
    """Run periodically (e.g., every 5 minutes)."""
    anomalies = await perf_client.detect_orchestration_anomalies(
        time_window_days=1
    )
    
    if anomalies:
        send_alert(f"Detected {len(anomalies)} anomalies!")
```

---

## **Error Handling**

### **Circuit Breaker Behavior**

The circuit breaker protects against cascade failures:

```
CLOSED (normal) → OPEN (failing) → HALF_OPEN (testing) → CLOSED
```

**States:**
- **CLOSED**: Normal operation, requests go through
- **OPEN**: Too many failures, requests fail immediately
- **HALF_OPEN**: Testing if service recovered

**Configuration:**
```python
from common.http_client import ServiceHTTPClient

client = ServiceHTTPClient(
    base_url="http://localhost:5649",
    service_name="my-service",
    timeout=30,
    max_retries=3,
    circuit_breaker_threshold=5,    # Open after 5 failures
    circuit_breaker_timeout=30,     # Try recovery after 30s
)
```

### **Retry Logic**

Failed requests are automatically retried with exponential backoff:

```
Attempt 1: immediate
Attempt 2: wait 1 second
Attempt 3: wait 2 seconds
Attempt 4: fail
```

### **Common Error Scenarios**

#### **Service Unavailable**
```python
if not await client.health_check():
    # Service is down - use fallback
    return get_cached_data()
```

#### **Request Timeout**
```python
try:
    result = await client.some_operation()
except asyncio.TimeoutError:
    logger.error("Request timed out")
    # Retry or use fallback
```

#### **Circuit Breaker Open**
```python
try:
    result = await client.some_operation()
except Exception as e:
    if "circuit breaker is OPEN" in str(e):
        logger.error("Circuit breaker is open - service degraded")
        # Use fallback or cached data
```

---

## **Testing**

### **Unit Tests**

Mock the HTTP clients in unit tests:

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_my_service():
    with patch('common.clients.PerformanceStoreClient') as mock_client:
        # Setup mock
        mock_instance = AsyncMock()
        mock_instance.record_execution.return_value = {"status": "ok"}
        mock_client.return_value = mock_instance
        
        # Test your service
        service = MyService()
        await service.execute_task("task-123")
        
        # Verify recording was called
        mock_instance.record_execution.assert_called_once()
```

### **Integration Tests**

Run integration tests against live services:

```python
@pytest.mark.asyncio
async def test_integration():
    client = PerformanceStoreClient()
    
    try:
        # Check if service is running
        if not await client.health_check():
            pytest.skip("Service not running")
        
        # Test integration
        result = await client.record_execution(...)
        assert result is not None
    
    finally:
        await client.close()
```

### **Running Tests**

```bash
# Unit tests (fast, no services needed)
pytest tests/unit/ -v

# Integration tests (requires services)
pytest tests/integration/ -v

# All tests
pytest -v
```

---

## **Troubleshooting**

### **Connection Refused**

**Problem:** `Connection refused to http://localhost:5649`

**Solution:**
```bash
# Start the service
cd services/mcp-performance-store
docker-compose up -d

# Check it's running
curl http://localhost:5649/health
```

### **Circuit Breaker Open**

**Problem:** `Circuit breaker is OPEN - failing fast`

**Solution:**
```python
# Wait for circuit breaker to recover (30 seconds default)
await asyncio.sleep(30)

# Or reset manually (not recommended in production)
client.client.circuit_breaker._state = CircuitBreakerState.CLOSED
```

### **Timeout Errors**

**Problem:** `Request timed out after 30 seconds`

**Solution:**
```python
# Increase timeout for long operations
client = MCPStoreClient()
client.client.timeout = 120  # 2 minute timeout
```

### **Performance Recording Failures**

**Problem:** Performance recording fails but main workflow should continue

**Solution:**
```python
# ✅ Always catch recording exceptions
try:
    await perf_client.record_execution(...)
except Exception as e:
    logger.warning(f"Failed to record performance: {e}")
    # Don't raise - continue with main workflow
```

### **Debugging**

Enable debug logging:

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("common.http_client")
logger.setLevel(logging.DEBUG)
```

---

## **Examples**

See complete examples in:
- `examples/service_integration_example.py` - Full workflow examples
- `tests/integration/test_http_clients.py` - Integration tests

Run the example:
```bash
python examples/service_integration_example.py
```

---

## **Support**

For issues or questions:
1. Check logs: `docker-compose logs service-name`
2. Verify health: `curl http://localhost:PORT/health`
3. Review this guide
4. Check integration tests for examples

---

**Happy Integrating! 🚀**

