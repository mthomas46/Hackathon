# 🧪 Testing Guide - kafka-ingestion-service

This document explains the testing strategy and provides examples for writing tests for the kafka-ingestion-service.

---

## 📁 Test Structure

```
tests/
├── __init__.py
├── conftest.py                       # Shared fixtures
├── unit/                             # Unit tests (70%)
│   ├── domain/
│   │   ├── test_document_event.py    # ✅ Example provided
│   │   ├── test_ingestion_job.py
│   │   ├── test_event_status.py
│   │   └── test_source_metadata.py
│   ├── application/
│   │   ├── test_ingest_command.py
│   │   ├── test_create_job_command.py
│   │   └── test_event_processor.py
│   └── infrastructure/
│       ├── test_kafka_clients.py     # Mocked
│       └── test_repositories.py      # Mocked
├── integration/                      # Integration tests (20%)
│   ├── test_kafka_integration.py     # Real Kafka
│   ├── test_redis_integration.py     # Real Redis
│   └── test_doc_store_integration.py
├── functional/                       # Functional/E2E tests (10%)
│   ├── test_api_endpoints.py
│   └── test_complete_workflows.py
└── fixtures/
    ├── sample_documents.py
    └── sample_events.py
```

---

## 🚀 Running Tests

### Quick Commands

```bash
# Run all tests
pytest

# Run unit tests only (fast)
pytest tests/unit -v

# Run with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/domain/test_document_event.py -v

# Run tests matching pattern
pytest -k "test_event" -v

# Run tests by marker
pytest -m unit -v
pytest -m integration -v
pytest -m functional -v

# Show test durations
pytest --durations=10
```

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=. --cov-report=html

# View in browser
open htmlcov/index.html

# Terminal report with missing lines
pytest --cov=. --cov-report=term-missing
```

---

## 📝 Writing Tests

### Test Template

```python
"""Test module for [Component Name]."""

import pytest
from unittest.mock import Mock, patch


@pytest.mark.unit  # or @pytest.mark.integration, @pytest.mark.functional
class Test[ComponentName]:
    """Test suite for [ComponentName]."""
    
    def test_[scenario]_[expected_behavior](self):
        """
        Test that [component] [expected behavior] when [scenario].
        
        Given: [preconditions]
        When: [action]
        Then: [expected outcome]
        """
        # Arrange - Set up test data
        # ... setup code
        
        # Act - Execute the code under test
        # ... execution code
        
        # Assert - Verify the results
        # ... assertions
```

### Example: Unit Test

See `/tests/unit/domain/test_document_event.py` for a complete example with 15 test cases covering:
- Entity creation
- Validation
- Lifecycle transitions
- Serialization/deserialization
- Business logic

### Example: Integration Test

```python
"""Integration tests for Kafka."""

import pytest
from testcontainers.kafka import KafkaContainer

from infrastructure.kafka.kafka_producer import KafkaProducerClient
from infrastructure.kafka.kafka_consumer import KafkaConsumerClient
from domain.entities.document_event import DocumentEvent


@pytest.mark.integration
@pytest.mark.kafka
class TestKafkaIntegration:
    """Test Kafka producer/consumer integration."""
    
    @pytest.fixture(scope="class")
    def kafka_container(self):
        """Start Kafka test container."""
        with KafkaContainer() as kafka:
            yield kafka
    
    async def test_produce_and_consume_event(
        self,
        kafka_container,
        sample_document_event
    ):
        """
        Test that event can be produced and consumed from Kafka.
        
        Given: Running Kafka instance
        When: Publishing event via producer and consuming via consumer
        Then: Event is received correctly
        """
        # Arrange
        bootstrap_servers = kafka_container.get_bootstrap_server()
        producer = KafkaProducerClient(bootstrap_servers=bootstrap_servers)
        consumer = KafkaConsumerClient(bootstrap_servers=bootstrap_servers)
        
        await producer.start()
        await consumer.start()
        await consumer.subscribe(["document-events"])
        
        try:
            # Act
            await producer.publish_event(sample_document_event)
            
            # Consume
            messages = await consumer.poll(timeout_ms=5000)
            
            # Assert
            assert len(messages) > 0
            record = list(messages.values())[0][0]
            consumed_event = DocumentEvent.from_dict(json.loads(record.value))
            assert consumed_event.document_id == sample_document_event.document_id
            
        finally:
            await producer.stop()
            await consumer.stop()
```

### Example: Functional Test

```python
"""Functional tests for API endpoints."""

import pytest
from httpx import AsyncClient

from main import app


@pytest.mark.functional
class TestAPIEndpoints:
    """Test API endpoints end-to-end."""
    
    @pytest.fixture
    async def client(self):
        """Create test client."""
        async with AsyncClient(app=app, base_url="http://test") as client:
            yield client
    
    async def test_ingest_document_success(self, client):
        """
        Test that document can be ingested via API.
        
        Given: Valid document data
        When: POST to /api/v1/events
        Then: Event is created and returned
        """
        # Arrange
        payload = {
            "document_id": "test-doc-1",
            "title": "Test Document",
            "content": "# Test Content",
            "event_type": "document_created",
            "source_metadata": {
                "source_type": "docs_directory",
                "source_id": "/docs/test.md",
                "source_name": "Test"
            }
        }
        
        # Act
        response = await client.post("/api/v1/events", json=payload)
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["document_id"] == "test-doc-1"
        assert data["status"] == "ingested"
```

---

## 🎯 Coverage Targets

| Layer | Target | Actual | Status |
|-------|--------|--------|--------|
| Domain | 90%+ | TBD | ⏳ Pending |
| Application | 85%+ | TBD | ⏳ Pending |
| Infrastructure | 80%+ | TBD | ⏳ Pending |
| Presentation | 85%+ | TBD | ⏳ Pending |
| **Overall** | **85%+** | **TBD** | **⏳ Pending** |

---

## ✅ Test Checklist

### Unit Tests (10 files)
- [ ] test_document_event.py (15 tests) ✅ Example provided
- [ ] test_ingestion_job.py (10 tests)
- [ ] test_event_status.py (8 tests)
- [ ] test_job_status.py (8 tests)
- [ ] test_source_metadata.py (10 tests)
- [ ] test_ingest_command.py (8 tests)
- [ ] test_create_job_command.py (6 tests)
- [ ] test_event_processor.py (12 tests)
- [ ] test_kafka_clients.py (10 tests, mocked)
- [ ] test_repositories.py (10 tests, mocked)

**Total:** ~97 unit tests

### Integration Tests (5 files)
- [ ] test_kafka_integration.py (8 tests)
- [ ] test_redis_integration.py (10 tests)
- [ ] test_doc_store_integration.py (5 tests)
- [ ] test_event_repository.py (8 tests, real Redis)
- [ ] test_job_repository.py (8 tests, real Redis)

**Total:** ~39 integration tests

### Functional Tests (3 files)
- [ ] test_api_endpoints.py (10 tests)
- [ ] test_health_endpoints.py (4 tests)
- [ ] test_complete_workflows.py (8 tests)

**Total:** ~22 functional tests

**Grand Total:** ~158 tests across 18 files

---

## 🔧 Test Dependencies

All testing dependencies are in `requirements-test.txt`:
- pytest (core framework)
- pytest-asyncio (async support)
- pytest-cov (coverage)
- pytest-mock (mocking)
- testcontainers (Docker containers for integration tests)
- factory-boy (test factories)
- faker (test data generation)
- httpx (HTTP client testing)

Install with:
```bash
pip install -r requirements-test.txt
```

---

## 📊 Test Markers

Use markers to categorize and run specific test groups:

```python
@pytest.mark.unit        # Fast, isolated unit tests
@pytest.mark.integration # Tests with external dependencies
@pytest.mark.functional  # End-to-end workflow tests
@pytest.mark.slow        # Slow-running tests
@pytest.mark.kafka       # Tests requiring Kafka
@pytest.mark.redis       # Tests requiring Redis
```

Run specific markers:
```bash
pytest -m "unit and not slow" -v
pytest -m "integration and kafka" -v
```

---

## 🚀 CI/CD Integration

Tests should run in CI/CD pipeline:

```yaml
# Example GitHub Actions
- name: Run unit tests
  run: pytest tests/unit -v --cov --cov-report=xml

- name: Run integration tests
  run: pytest tests/integration -v

- name: Run functional tests
  run: pytest tests/functional -v

- name: Upload coverage
  uses: codecov/codecov-action@v3
```

---

## 📝 Next Steps

1. [ ] Review example test in `test_document_event.py`
2. [ ] Implement remaining unit tests
3. [ ] Set up test containers for integration tests
4. [ ] Implement integration tests
5. [ ] Implement functional tests
6. [ ] Review coverage reports
7. [ ] Fix any gaps to reach 85%+ coverage

---

**Status:** Testing infrastructure ready, example tests provided  
**Coverage Target:** 85%+  
**Total Tests:** ~158 tests across 18 files
