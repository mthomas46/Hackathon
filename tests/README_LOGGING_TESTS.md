# DataStore Operation Logging - Test Documentation

Comprehensive test suite for verifying that all datastore services properly log operations to the log-collector service.

## Overview

This test suite validates:
- **Unit Tests**: Middleware functionality in isolation
- **Integration Tests**: End-to-end logging flow with real services
- **Cross-Service Tests**: Distributed tracing across multiple datastores

## Test Structure

```
tests/
├── run_logging_tests.sh                    # Main test runner script
├── README_LOGGING_TESTS.md                 # This file
└── integration/
    └── test_datastore_logging_integration.py   # Integration tests

services/shared/
└── tests/
    └── test_datastore_operation_logger.py      # Unit tests
```

## Running Tests

### Quick Start

```bash
# Run all tests (unit + integration)
cd /Users/mykalthomas/Documents/work/Hackathon
./tests/run_logging_tests.sh
```

### Run Specific Test Types

```bash
# Unit tests only (no services required)
cd services/shared
python3 -m pytest tests/test_datastore_operation_logger.py -v

# Integration tests only (requires services running)
cd tests
python3 -m pytest integration/test_datastore_logging_integration.py -v
```

### Requirements

**For Unit Tests:**
- Python 3.8+
- pytest
- pytest-asyncio
- httpx

**For Integration Tests:**
- All unit test requirements
- log-collector service running (port 8104)
- At least one datastore service running:
  - doc-store (5020)
  - prompt-store (5030)
  - external-service-store (5140)
  - memory-agent (5090)
  - user-store (5150)
  - project-planning-service (5160)

### Installing Dependencies

```bash
pip3 install pytest pytest-asyncio httpx fastapi
```

## Test Coverage

### Unit Tests (`test_datastore_operation_logger.py`)

#### TestDataStoreOperationMiddleware
- ✅ Middleware initialization with configuration
- ✅ Operation type detection (CREATE, READ, UPDATE, DELETE, LIST, SEARCH)
- ✅ Bulk operation detection
- ✅ Log sending with proper format
- ✅ Graceful failure handling
- ✅ Health check endpoint skipping
- ✅ Document operation logging

#### TestAddDatastoreLogging
- ✅ Basic middleware addition to FastAPI app
- ✅ Custom configuration support

#### TestWorkflowIdTracking
- ✅ X-Workflow-ID header capture
- ✅ Default workflow ID when header absent

#### TestErrorLogging
- ✅ Exception logging with error details
- ✅ Error type capture

#### TestPerformanceTracking
- ✅ Duration tracking in milliseconds
- ✅ Performance metrics accuracy

### Integration Tests (`test_datastore_logging_integration.py`)

#### TestLogCollectorIntegration
- ✅ Log-collector health check
- ✅ Log acceptance endpoint
- ✅ Log query endpoint

#### TestDatastoreLoggingEndToEnd
- ✅ Service operation logging (all 6 datastores)
- ✅ Log structure validation
- ✅ Operation phases (start, complete)
- ✅ Duration tracking
- ✅ Error logging

#### TestCrossServiceTracking
- ✅ Distributed tracing with workflow IDs
- ✅ Multi-service correlation

#### TestLogCollectorStatistics
- ✅ Statistics endpoint availability

## Test Scenarios

### 1. Basic Logging Flow

```
Client Request → Datastore Service → Middleware Intercept → Log Collector
                                    ↓
                            Log Entry Created
                                    ↓
                            POST /logs to collector
```

**Validated:**
- Request is intercepted
- Log entry is formatted correctly
- Log is sent to collector
- Log can be queried back

### 2. Workflow Tracking

```
Request 1 (workflow-abc) → Service A → Log Collector
Request 2 (workflow-abc) → Service B → Log Collector
                                       ↓
                        Query: GET /logs?workflow_id=workflow-abc
                                       ↓
                            Returns logs from both services
```

**Validated:**
- X-Workflow-ID header is captured
- Same workflow ID tracked across services
- Distributed tracing works

### 3. Performance Monitoring

```
Request Start (t0) → Process → Response (t1)
                     ↓
            duration_ms = (t1 - t0) * 1000
                     ↓
            Logged with duration
```

**Validated:**
- Start time captured
- End time captured
- Duration calculated accurately
- Duration in milliseconds

### 4. Error Handling

```
Request → Service Error → Exception Caught → Error Logged
                                            ↓
                        Contains: error message, error type, stack trace
```

**Validated:**
- Exceptions are logged
- Error details captured
- Error phase marked
- Level set to ERROR

## Log Entry Structure

All logged operations contain:

```json
{
  "service": "doc-store",
  "level": "INFO",
  "message": "DataStore operation completed: POST /documents",
  "context": {
    "operation_id": "abc123",
    "workflow_id": "workflow-xyz",
    "method": "POST",
    "path": "/documents",
    "operation_type": "create",
    "status_code": 201,
    "duration_ms": 45.2,
    "success": true,
    "phase": "complete",
    "query_params": {}
  },
  "timestamp": "2025-10-04T01:00:00.123456Z"
}
```

## Running Services for Testing

### Start Log Collector

```bash
cd services/log-collector
python3 main.py
# Should start on port 8104
```

### Start Datastore Services

```bash
# Terminal 1: doc-store
cd services/doc_store
python3 main.py

# Terminal 2: prompt-store
cd services/prompt_store
python3 main.py

# Terminal 3: external-service-store
cd services/external-service-store
python3 main.py

# Terminal 4: memory-agent
cd services/memory-agent
python3 main.py

# Terminal 5: user-store
cd services/user-store
python3 main.py

# Terminal 6: project-planning-service
cd services/project-planning-service
python3 main.py
```

## Interpreting Test Results

### Successful Test Run

```
✓ All tests passed!
  Unit Tests:        ✓ PASSED
  Integration Tests: ✓ PASSED
  Services Running:  6 / 6
  Log Collector:     Running
```

### Partial Success

```
⚠ Some tests skipped
  Unit Tests:        ✓ PASSED
  Integration Tests: ⊘ SKIPPED (services not running)
  Services Running:  0 / 6
  Log Collector:     Not running
```

### Test Failure

```
✗ Some tests failed
  Unit Tests:        ✓ PASSED
  Integration Tests: ✗ FAILED
  Services Running:  3 / 6
```

## Troubleshooting

### "pytest not found"

```bash
pip3 install pytest pytest-asyncio
```

### "Connection refused" errors

1. Check if log-collector is running:
   ```bash
   curl http://localhost:8104/health
   ```

2. Check if datastore services are running:
   ```bash
   curl http://localhost:5020/health  # doc-store
   curl http://localhost:5030/health  # prompt-store
   # etc.
   ```

### Tests timing out

Increase timeout in test files:
```python
TIMEOUT = 10  # Increase from 5 to 10 seconds
```

### Import errors

Make sure you're running from the correct directory:
```bash
cd /Users/mykalthomas/Documents/work/Hackathon
./tests/run_logging_tests.sh
```

## Continuous Integration

To integrate with CI/CD:

```yaml
# Example GitHub Actions workflow
- name: Run Logging Tests
  run: |
    # Start services
    docker-compose up -d log-collector
    docker-compose up -d doc-store
    
    # Wait for services
    sleep 10
    
    # Run tests
    ./tests/run_logging_tests.sh
    
    # Cleanup
    docker-compose down
```

## Adding New Tests

### Unit Test Example

```python
def test_new_functionality(self, middleware):
    """Test description."""
    # Arrange
    # Act
    # Assert
```

### Integration Test Example

```python
def test_new_scenario(self):
    """Test description."""
    workflow_id = f"test-{uuid.uuid4().hex[:12]}"
    
    # Make request with workflow ID
    # Query logs
    # Verify results
```

## Metrics

The test suite verifies:
- **14+ unit test cases**
- **10+ integration test scenarios**
- **6 datastore services**
- **100% middleware coverage**

## Support

For issues or questions:
1. Check service logs
2. Verify all services are running
3. Review test output for specific errors
4. Check log-collector for received logs

---

**Last Updated:** October 4, 2025  
**Version:** 1.0.0  
**Maintainer:** LLM Documentation Ecosystem Team

