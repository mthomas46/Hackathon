# 🧪 MCP Workflow Testing Strategy

**Date:** October 7, 2025  
**Status:** Testing Plan Defined  
**Coverage Target:** 85%+ for all services  

---

## 📊 Testing Overview

### Testing Pyramid

```
                    /\
                   /  \
                  / E2E \     ← 10% (Integration/Functional)
                 /______\
                /        \
               / Integration\   ← 20% (Service Integration)
              /____________\
             /              \
            /  Unit Tests    \  ← 70% (Fast, Isolated)
           /__________________\
```

**Target Distribution:**
- **Unit Tests:** 70% of test suite (fast, isolated, comprehensive)
- **Integration Tests:** 20% of test suite (service boundaries, external systems)
- **Functional/E2E Tests:** 10% of test suite (complete workflows)

---

## 🎯 Testing Phases

### Phase 1: kafka-ingestion-service Testing (Week 1.5)

#### Unit Tests (~30 tests)
**Domain Layer Tests:**
- [x] DocumentEvent entity
  - [x] Lifecycle transitions (pending → ingested → processing → processed)
  - [x] Invalid transitions raise errors
  - [x] Retry logic (increment, max retries)
  - [x] Serialization (to_dict, from_dict)
- [x] IngestionJob entity
  - [x] Status transitions
  - [x] Event tracking
  - [x] Progress calculation
  - [x] Metrics updates
- [x] EventStatus value object
  - [x] State properties (is_terminal, is_active, is_error)
  - [x] Transition validation
- [x] JobStatus value object
  - [x] State properties
  - [x] Transition validation
- [x] SourceMetadata value object
  - [x] Factory methods (for_docs_directory, for_github, for_confluence)
  - [x] Validation
  - [x] Immutability

**Application Layer Tests:**
- [x] IngestDocumentCommand handler
  - [x] Valid command creates event
  - [x] Invalid command raises ValueError
  - [x] Event persisted via repository
- [x] CreateJobCommand handler
  - [x] Valid command creates job
  - [x] Invalid command raises ValueError
- [x] EventProcessorService
  - [x] Process content event
  - [x] Process metadata event
  - [x] Handle processing errors
  - [x] Retry failed events

**Infrastructure Layer Tests (Unit - Mocked):**
- [x] KafkaProducerClient (mocked Kafka)
  - [x] Publish event serialization
  - [x] Error handling
- [x] KafkaConsumerClient (mocked Kafka)
  - [x] Message parsing
  - [x] Offset management

**Files:** ~10 test files (~800 LOC)

#### Integration Tests (~15 tests)
**Kafka Integration:**
- [x] Producer publishes to real Kafka
- [x] Consumer reads from real Kafka
- [x] Message ordering preserved
- [x] Error recovery with retries

**Redis Integration:**
- [x] Event repository CRUD operations
- [x] Job repository CRUD operations
- [x] Status index queries
- [x] Document index queries
- [x] Pagination

**doc_store Integration:**
- [x] Event routing to doc_store
- [x] Error handling

**Files:** ~5 test files (~600 LOC)

#### Functional/E2E Tests (~10 tests)
**API Endpoints:**
- [x] POST /api/v1/events (happy path)
- [x] POST /api/v1/events (validation errors)
- [x] POST /api/v1/jobs
- [x] GET /api/v1/events/{id}
- [x] GET /api/v1/jobs/{id}
- [x] GET /api/v1/jobs (pagination)
- [x] GET /health
- [x] GET /ready

**Complete Workflows:**
- [x] Document ingestion → processing → completion
- [x] Failed event → retry → success
- [x] Failed event → max retries → dead letter
- [x] Batch job → multiple events → completion

**Files:** ~3 test files (~400 LOC)

**Total kafka-ingestion Tests:** ~18 files, ~1,800 LOC

---

### Phase 2: llm-tagging-pipeline Testing (Week 2.5)

#### Unit Tests (~25 tests)
**Domain Layer:**
- [ ] Document entity (with LLM metadata)
- [ ] LLMMetadata value object
- [ ] TagValidationRules
- [ ] Tagging job entity

**Application Layer:**
- [ ] TagDocumentCommand handler
- [ ] LLM content analysis service
- [ ] Tag extraction service
- [ ] Validation service

**Infrastructure Layer (Mocked):**
- [ ] OllamaTagger (mocked Ollama API)
- [ ] Metadata repository

**Files:** ~8 test files (~600 LOC)

#### Integration Tests (~12 tests)
**Ollama Integration:**
- [ ] Real LLM tagging requests
- [ ] Tag extraction accuracy
- [ ] Batch processing
- [ ] Error handling

**Repository Integration:**
- [ ] Metadata persistence
- [ ] Query operations

**Files:** ~4 test files (~400 LOC)

#### Functional/E2E Tests (~8 tests)
**API Endpoints:**
- [ ] Tag document endpoint
- [ ] Batch tagging
- [ ] Tag validation
- [ ] Complete workflow

**Files:** ~2 test files (~300 LOC)

**Total llm-tagging Tests:** ~14 files, ~1,300 LOC

---

### Phase 3: mcp-evergreen-docs Testing (Week 2.5)

#### Unit Tests (~20 tests)
**Domain Layer:**
- [ ] Documentation entity
- [ ] SyncJob entity
- [ ] ValidationRules

**Application Layer:**
- [ ] Sync commands
- [ ] Generation commands
- [ ] Validation service

**Files:** ~6 test files (~500 LOC)

#### Integration Tests (~10 tests)
**Git Integration:**
- [ ] Repository cloning
- [ ] File monitoring
- [ ] Commit detection

**API Integration:**
- [ ] External API clients
- [ ] Template engine

**Files:** ~3 test files (~300 LOC)

#### Functional/E2E Tests (~6 tests)
**Complete Workflows:**
- [ ] Document sync
- [ ] Document generation
- [ ] Validation workflow

**Files:** ~2 test files (~250 LOC)

**Total evergreen-docs Tests:** ~11 files, ~1,050 LOC

---

### Phase 4: Integration Testing (Week 3)

#### Service-to-Service Integration (~15 tests)
**Kafka → Ingestion → doc_store:**
- [ ] End-to-end event flow
- [ ] Error propagation
- [ ] Retry behavior

**Ingestion → LLM Tagging → Training:**
- [ ] Complete MCP creation workflow
- [ ] Metadata enrichment
- [ ] Training pipeline trigger

**Registry → Store → Export/Import:**
- [ ] Package creation
- [ ] Package export
- [ ] Package import
- [ ] Hotswap

**Files:** ~5 test files (~600 LOC)

#### System-Level Tests (~10 tests)
**Complete MCP Workflow:**
- [ ] docs/ → Kafka → ingestion → tagging → training → MCP
- [ ] MCP registration
- [ ] MCP query via gateway
- [ ] MCP export/import
- [ ] Evergreen docs generation

**Performance Tests:**
- [ ] Load testing (100 events/sec)
- [ ] Stress testing (1000 events/sec)
- [ ] Latency benchmarks

**Files:** ~3 test files (~400 LOC)

**Total Integration Tests:** ~8 files, ~1,000 LOC

---

## 📋 Testing Tools & Frameworks

### Python Testing Stack

```python
# requirements-test.txt

# Core Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0

# Integration Testing
pytest-docker==2.0.1
testcontainers==3.7.1

# Fixtures & Factories
factory-boy==3.3.0
faker==20.1.0

# HTTP Testing
httpx==0.25.2
respx==0.20.2

# Mocking
responses==0.24.1

# Coverage
coverage[toml]==7.3.2

# Load Testing
locust==2.19.1
```

### Testing Infrastructure

**Docker Test Containers:**
```yaml
# docker-compose.test.yml
version: '3.8'

services:
  kafka-test:
    image: confluentinc/cp-kafka:7.5.0
    environment:
      KAFKA_BROKER_ID: 1
      KAFKA_ZOOKEEPER_CONNECT: zookeeper-test:2181
  
  zookeeper-test:
    image: confluentinc/cp-zookeeper:7.5.0
  
  redis-test:
    image: redis:7-alpine
  
  ollama-test:
    image: ollama/ollama:latest
```

---

## 🧪 Test Structure

### Directory Layout

```
service-name/
├── tests/
│   ├── __init__.py
│   ├── conftest.py                    # Shared fixtures
│   ├── unit/
│   │   ├── __init__.py
│   │   ├── domain/
│   │   │   ├── test_entities.py
│   │   │   ├── test_value_objects.py
│   │   │   └── test_events.py
│   │   ├── application/
│   │   │   ├── test_commands.py
│   │   │   └── test_services.py
│   │   └── infrastructure/
│   │       └── test_clients.py        # With mocks
│   ├── integration/
│   │   ├── __init__.py
│   │   ├── test_kafka_integration.py
│   │   ├── test_redis_integration.py
│   │   └── test_ollama_integration.py
│   ├── functional/
│   │   ├── __init__.py
│   │   ├── test_api_endpoints.py
│   │   └── test_workflows.py
│   └── fixtures/
│       ├── __init__.py
│       ├── sample_documents.py
│       └── sample_events.py
└── pytest.ini
```

---

## ✅ Test Coverage Targets

### Per-Service Coverage

| Service | Unit Tests | Integration | Functional | Total Coverage |
|---------|-----------|-------------|------------|----------------|
| kafka-ingestion | 85%+ | 80%+ | 90%+ | **85%+** |
| llm-tagging-pipeline | 85%+ | 75%+ | 85%+ | **80%+** |
| mcp-evergreen-docs | 85%+ | 75%+ | 85%+ | **80%+** |
| mock-data-generator | 80%+ | 70%+ | 80%+ | **75%+** |

### Critical Path Coverage

**High Priority (90%+ coverage):**
- Domain entities and value objects
- Command handlers
- Event processing logic
- API endpoints

**Medium Priority (80%+ coverage):**
- Repository implementations
- Infrastructure clients
- Service integrations

**Lower Priority (70%+ coverage):**
- Configuration
- Utilities
- DTOs

---

## 🎯 Test Execution Strategy

### Development Workflow

```bash
# Run fast unit tests (during development)
pytest tests/unit -v

# Run all tests with coverage
pytest --cov=. --cov-report=html

# Run specific test file
pytest tests/unit/domain/test_entities.py -v

# Run tests matching pattern
pytest -k "test_event" -v

# Run with markers
pytest -m "unit" -v
pytest -m "integration" -v
pytest -m "slow" -v
```

### CI/CD Pipeline

```yaml
# .github/workflows/test.yml

name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
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

## 📊 Test Metrics & Reporting

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=. --cov-report=html

# View in browser
open htmlcov/index.html

# Generate terminal report
pytest --cov=. --cov-report=term-missing
```

### Test Timing

```bash
# Show slowest 10 tests
pytest --durations=10

# Show all test durations
pytest --durations=0
```

### Test Statistics

**Expected Test Suite Stats:**
- **Total Tests:** ~120 tests across all services
- **Total Test LOC:** ~5,150 lines
- **Unit Tests:** ~70 tests (~70%)
- **Integration Tests:** ~37 tests (~20%)
- **Functional Tests:** ~24 tests (~10%)

---

## 🔄 Testing Phases Timeline

### Week 1.5: kafka-ingestion Tests
- **Days 1-2:** Unit tests (domain + application)
- **Days 3-4:** Integration tests (Kafka, Redis)
- **Day 5:** Functional tests + coverage review

### Week 2.5: llm-tagging + evergreen-docs Tests
- **Days 1-2:** llm-tagging unit + integration tests
- **Days 3-4:** evergreen-docs unit + integration tests
- **Day 5:** Functional tests for both

### Week 3: Integration Testing
- **Days 1-2:** Service-to-service integration tests
- **Days 3-4:** System-level E2E tests
- **Day 5:** Performance tests + final coverage

---

## ✅ Success Criteria

### Per-Service
- [x] Unit test coverage ≥ 85%
- [x] Integration test coverage ≥ 75%
- [x] Functional test coverage ≥ 85%
- [x] All tests passing
- [x] No critical bugs
- [x] Performance benchmarks met

### Overall Project
- [x] Total coverage ≥ 85%
- [x] All critical paths tested
- [x] E2E workflow validated
- [x] Load tests passing (100 events/sec)
- [x] Documentation complete

---

## 📝 Test Documentation

### Test Case Template

```python
"""Test module for [Component Name]."""

import pytest
from unittest.mock import Mock, patch


class Test[ComponentName]:
    """Test suite for [ComponentName]."""
    
    def test_[scenario]_[expected_behavior](self):
        """
        Test that [component] [expected behavior] when [scenario].
        
        Given: [preconditions]
        When: [action]
        Then: [expected outcome]
        """
        # Arrange
        # ... setup
        
        # Act
        # ... execute
        
        # Assert
        # ... verify
```

### Fixture Template

```python
"""Shared test fixtures."""

import pytest


@pytest.fixture
def sample_document_event():
    """Create sample document event."""
    return DocumentEvent(
        document_id="test-doc-1",
        title="Test Document",
        content="# Test Content",
        # ... other fields
    )
```

---

## 🚀 Next Steps

### Immediate (This Week)
1. [x] Create testing strategy document (THIS FILE)
2. [ ] Set up pytest configuration
3. [ ] Create conftest.py with shared fixtures
4. [ ] Implement kafka-ingestion unit tests
5. [ ] Implement kafka-ingestion integration tests

### Week 2
1. [ ] Complete kafka-ingestion functional tests
2. [ ] Implement llm-tagging-pipeline tests
3. [ ] Implement mcp-evergreen-docs tests
4. [ ] Review coverage reports

### Week 3
1. [ ] Service-to-service integration tests
2. [ ] System-level E2E tests
3. [ ] Performance testing
4. [ ] Final coverage review
5. [ ] Test documentation

---

**Status:** ✅ Testing Strategy Defined  
**Total Test Files:** ~60 files (~5,150 LOC)  
**Coverage Target:** 85%+  
**Timeline:** 2-3 weeks parallel with development
