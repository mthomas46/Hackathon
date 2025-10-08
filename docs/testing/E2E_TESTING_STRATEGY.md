# End-to-End Testing Strategy for MCP Ecosystem

**Date:** October 7, 2025  
**Goal:** Comprehensive E2E testing covering both code-level and deployment-level testing  
**Approach:** Dual-mode testing (local code + live services)

---

## 🎯 Testing Philosophy

### Dual-Mode Testing
Tests must support two execution modes:

1. **Code Mode** (CI/CD): Tests against service code with mocked dependencies
2. **Live Mode** (Staging/Production): Tests against running Docker containers

### Test Pyramid for E2E

```
        /\
       /  \
      / E2E \ ← End-to-end workflow tests (this document)
     /______\
    /        \
   / Integr.  \ ← Integration tests (service + dependencies)
  /____________\
 /              \
/  Unit Tests    \ ← Unit tests (isolated components)
/__________________\
```

---

## 📋 Test Categories

### 1. Infrastructure E2E Tests
**File:** `tests/e2e/test_infrastructure.py`

Tests infrastructure readiness:
- ✅ Kafka broker connectivity
- ✅ Redis availability
- ✅ Ollama model loading
- ✅ Elasticsearch cluster health
- ✅ Network connectivity (AMS network)

**Modes:**
- Code: Mock responses
- Live: Actual health checks

---

### 2. Service Health E2E Tests
**File:** `tests/e2e/test_service_health.py`

Tests all services are operational:
- ✅ Health endpoint responds 200
- ✅ Service metadata correct
- ✅ Dependencies reported as healthy
- ✅ Response time < 1s

**Modes:**
- Code: Unit test service health endpoint
- Live: HTTP requests to running containers

---

### 3. Document Ingestion E2E Tests
**File:** `tests/e2e/test_document_ingestion.py`

Tests complete ingestion workflow:
- ✅ Document submission to kafka-ingestion
- ✅ Event published to Kafka topic
- ✅ Event persisted in Redis
- ✅ Job status tracking
- ✅ Error handling and retries

**Modes:**
- Code: Test ingestion service with mock Kafka/Redis
- Live: Full workflow with real Kafka/Redis

**Test Scenarios:**
1. Single document ingestion
2. Batch document ingestion (10 documents)
3. Large document (> 1MB)
4. Invalid document (should fail gracefully)
5. Duplicate document (idempotency)

---

### 4. LLM Tagging E2E Tests
**File:** `tests/e2e/test_llm_tagging.py`

Tests LLM tagging workflow:
- ✅ Document submitted for tagging
- ✅ Ollama called with correct parameters
- ✅ Tags extracted and validated
- ✅ Metadata persisted
- ✅ Confidence scores calculated

**Modes:**
- Code: Mock Ollama responses
- Live: Real Ollama inference

**Test Scenarios:**
1. Simple document tagging
2. Technical document with code
3. Multi-language document
4. Empty document (edge case)
5. Very long document (chunking)

---

### 5. Logging & Observability E2E Tests
**File:** `tests/e2e/test_logging_observability.py`

Tests logging integration:
- ✅ Logs sent to mcp-logs service
- ✅ Correlation IDs propagated
- ✅ Logs queryable by correlation ID
- ✅ Log levels respected
- ✅ Structured format preserved

**Modes:**
- Code: Test log client and middleware
- Live: Query actual Elasticsearch

**Test Scenarios:**
1. Single service logs
2. Multi-service correlation tracking
3. Error log aggregation
4. Performance metric logging
5. Anomaly detection triggers

---

### 6. Complete Workflow E2E Tests
**File:** `tests/e2e/test_complete_workflow.py`

Tests end-to-end MCP creation:
- ✅ Document ingestion → LLM tagging → Training → Storage → Registry → Package → Export
- ✅ All services involved
- ✅ Full correlation tracking
- ✅ Data integrity throughout

**Modes:**
- Code: Integration tests with test doubles
- Live: Full system test with real services

**Test Scenarios:**
1. Happy path: Complete workflow success
2. Service failure: Graceful degradation
3. Network partition: Retry logic
4. Concurrent workflows: No interference
5. Long-running workflow: Progress tracking

---

### 7. Package Management E2E Tests
**File:** `tests/e2e/test_package_management.py`

Tests package operations:
- ✅ Package creation
- ✅ Versioning
- ✅ Export to .mcp file
- ✅ Import from .mcp file
- ✅ Package validation

**Modes:**
- Code: Test package manager logic
- Live: Full export/import cycle

---

### 8. Evergreen Docs E2E Tests
**File:** `tests/e2e/test_evergreen_docs.py`

Tests documentation sync:
- ✅ Multi-source synchronization
- ✅ Validation rules applied
- ✅ Documentation freshness
- ✅ Conflict resolution

**Modes:**
- Code: Mock external sources
- Live: Real GitHub/Confluence sync

---

## 🛠️ Test Infrastructure

### Base Test Class
```python
# tests/e2e/base.py

class E2ETestBase:
    """Base class for E2E tests supporting dual modes."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment based on mode."""
        cls.mode = os.getenv("TEST_MODE", "code")  # code or live
        cls.correlation_id = str(uuid.uuid4())
        
        if cls.mode == "live":
            cls.setup_live_environment()
        else:
            cls.setup_code_environment()
    
    @classmethod
    def setup_live_environment(cls):
        """Connect to live services."""
        cls.services = {
            "kafka-ingestion": "http://localhost:5700",
            "llm-tagging": "http://localhost:8021",
            # ... all services
        }
        cls.client = httpx.AsyncClient(timeout=30.0)
    
    @classmethod
    def setup_code_environment(cls):
        """Set up mocks for code testing."""
        cls.kafka_mock = MagicMock()
        cls.redis_mock = MagicMock()
        cls.ollama_mock = MagicMock()
```

### Test Fixtures
```python
# tests/e2e/fixtures.py

@pytest.fixture
def sample_document():
    """Sample document for testing."""
    return {
        "document_id": f"doc_{uuid.uuid4().hex[:8]}",
        "content": "Test document content",
        "metadata": {"title": "Test", "author": "Tester"}
    }

@pytest.fixture
def correlation_context():
    """Correlation ID context for request tracking."""
    return {
        "correlation_id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat()
    }
```

### Test Helpers
```python
# tests/e2e/helpers.py

async def wait_for_service(url: str, timeout: int = 30) -> bool:
    """Wait for service to become available."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{url}/health")
                if response.status_code == 200:
                    return True
        except:
            pass
        await asyncio.sleep(1)
    return False

async def wait_for_log_entry(
    mcp_logs_url: str,
    correlation_id: str,
    timeout: int = 10
) -> Optional[Dict]:
    """Wait for log entry with correlation ID to appear."""
    start = time.time()
    while time.time() - start < timeout:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{mcp_logs_url}/api/v1/logs",
                params={"correlation_id": correlation_id}
            )
            if response.status_code == 200:
                logs = response.json()
                if len(logs.get("entries", [])) > 0:
                    return logs["entries"][0]
        await asyncio.sleep(0.5)
    return None
```

---

## 📊 Test Execution

### Running Tests

**Code Mode (CI/CD):**
```bash
# Run all E2E tests against code
pytest tests/e2e/ --mode=code

# Run specific test file
pytest tests/e2e/test_document_ingestion.py --mode=code

# With coverage
pytest tests/e2e/ --mode=code --cov=services --cov-report=html
```

**Live Mode (Staging/Production):**
```bash
# Ensure services are running
docker-compose -f docker-compose-mcp-ecosystem.yml up -d

# Run E2E tests against live services
pytest tests/e2e/ --mode=live

# Run with verbose output
pytest tests/e2e/ --mode=live -v

# Run specific workflow test
pytest tests/e2e/test_complete_workflow.py --mode=live -s
```

**Continuous Integration:**
```bash
# .github/workflows/e2e-tests.yml
- name: Run E2E Tests (Code Mode)
  run: pytest tests/e2e/ --mode=code --junitxml=results.xml

- name: Start Services
  run: docker-compose up -d

- name: Run E2E Tests (Live Mode)
  run: pytest tests/e2e/ --mode=live --junitxml=results-live.xml
```

---

## 📈 Success Criteria

### Test Coverage Targets
- **Infrastructure**: 100% of services health-checked
- **Document Ingestion**: 95% code coverage
- **LLM Tagging**: 90% code coverage (Ollama mocked)
- **Logging**: 100% correlation tracking validated
- **Complete Workflow**: 85% happy path + error scenarios

### Performance Benchmarks
- **Service Health Check**: < 1s per service
- **Document Ingestion**: < 2s per document
- **LLM Tagging**: < 5s per document (with mock)
- **Complete Workflow**: < 30s end-to-end
- **Correlation Query**: < 1s for log retrieval

### Reliability Targets
- **Test Stability**: 99% pass rate
- **False Positives**: < 1%
- **Flaky Tests**: 0 (must be fixed immediately)

---

## 🔄 Test Maintenance

### When to Update Tests
1. **New Service Added**: Add health check, add to workflow
2. **API Changed**: Update request/response validation
3. **New Feature**: Add feature-specific E2E test
4. **Bug Found**: Add regression test

### Test Review Process
1. All E2E tests reviewed in PR
2. Tests must pass in both modes
3. Performance benchmarks must be met
4. Documentation updated

---

## 📝 Test Documentation

Each test file must include:
1. **Module docstring**: What workflow is being tested
2. **Test docstrings**: What specific scenario
3. **Assertions**: Clear failure messages
4. **Cleanup**: Proper teardown

Example:
```python
async def test_document_ingestion_happy_path(self):
    """
    Test successful document ingestion workflow.
    
    Steps:
    1. Submit document to kafka-ingestion
    2. Verify event published to Kafka
    3. Check job status is COMPLETED
    4. Verify logs contain correlation ID
    
    Expected: 200 response, job completed, logs tracked
    """
    # Test implementation...
```

---

## 🎯 Integration with CI/CD

### Pre-commit Hooks
```bash
# Run quick E2E tests before commit
pytest tests/e2e/test_service_health.py --mode=code
```

### PR Validation
```bash
# Run all code-mode E2E tests
pytest tests/e2e/ --mode=code
```

### Staging Deployment
```bash
# Run full live-mode E2E tests
pytest tests/e2e/ --mode=live
```

### Production Smoke Tests
```bash
# Run critical path tests only
pytest tests/e2e/ --mode=live -m smoke
```

---

## 📊 Test Reporting

### Metrics to Track
1. **Test Execution Time**: By file, by mode
2. **Pass Rate**: Overall and per test
3. **Coverage**: Code coverage from E2E tests
4. **Flakiness**: Tests that fail intermittently
5. **Performance**: Benchmark trends over time

### Report Format
```json
{
  "test_run_id": "uuid",
  "timestamp": "2025-10-07T12:00:00Z",
  "mode": "live",
  "correlation_id": "uuid",
  "summary": {
    "total": 50,
    "passed": 48,
    "failed": 2,
    "skipped": 0,
    "duration_seconds": 120.5
  },
  "failures": [
    {
      "test": "test_llm_tagging_timeout",
      "reason": "Ollama took > 5s to respond",
      "traceback": "..."
    }
  ]
}
```

---

**Status**: Ready for implementation  
**Priority**: High - Critical for production confidence  
**Estimated Effort**: 2 weeks (8 test files, ~2,000 LOC)  
