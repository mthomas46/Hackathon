<!-- AI_READ_PRIORITY: 3 -->
<!-- AI_TAGS: testing, coverage, tdd, quality -->
<!-- AI_KEY_SECTIONS: Testing Pyramid, Coverage Requirements, Test Types, Implementation Guide -->

---
ai_metadata:
  purpose: testing_guidance
  read_priority: 3
  context_level: tactical
  tags:
  - testing
  - coverage
  - tdd
  - quality
  when_to_read: During Phase 3 (TDD Implementation)
  key_sections:
  - Testing Pyramid
  - Coverage Requirements
  - Test Types
  - Implementation Guide
  execution_relevance: phase-specific
  relevant_phases:
  - Phase 3
---

# 🧪 Comprehensive Testing Strategy - 80% Coverage Standard

**Version**: 1.0.0  
**Created**: October 8, 2025  
**Status**: Active

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Testing Pyramid](#testing-pyramid)
3. [Coverage Requirements](#coverage-requirements)
4. [Test Types](#test-types)
5. [Testing Standards](#testing-standards)
6. [Implementation Guide](#implementation-guide)
7. [Tools and Frameworks](#tools-and-frameworks)
8. [Examples](#examples)

---

## 🎯 Overview

### Purpose

Every refactored service must have **comprehensive, standardized testing** that covers at least **80% of core features**. This ensures:

- **Quality**: High confidence in code correctness
- **Regression Prevention**: Changes don't break existing functionality
- **Documentation**: Tests serve as living documentation
- **Refactoring Safety**: Can refactor with confidence
- **Deployment Confidence**: Safe to deploy to production

### Testing Philosophy

1. **Test First**: Follow TDD (Red-Green-Refactor)
2. **Test Comprehensively**: Cover happy paths, edge cases, and error paths
3. **Test Realistically**: Use realistic data and scenarios
4. **Test Independently**: Tests should be isolated and repeatable
5. **Test Continuously**: Run tests on every commit

### Coverage Target

| Layer | Minimum Coverage | Target Coverage |
|-------|-----------------|-----------------|
| Domain | 90% | 95% |
| Application | 80% | 90% |
| Infrastructure | 70% | 80% |
| Presentation | 80% | 90% |
| **Overall** | **80%** | **85%** |

---

## 🔺 Testing Pyramid

### Standard Test Distribution

```
           /\
          /  \
         / E2E \         5-10% of tests
        /-------\
       /         \
      / Integration\    20-30% of tests
     /-------------\
    /               \
   /   Unit Tests    \  60-70% of tests
  /___________________\

Unit Tests (60-70%):
├── Fast execution (< 1ms per test)
├── Test single units in isolation
├── Mock external dependencies
└── High coverage of business logic

Integration Tests (20-30%):
├── Medium execution (< 100ms per test)
├── Test multiple units together
├── Real dependencies where possible
└── Test service boundaries

E2E Tests (5-10%):
├── Slow execution (< 5s per test)
├── Test complete workflows
├── All services running
└── Critical user journeys
```

---

## 📊 Coverage Requirements

### Core Features Definition

**Core features** are the primary responsibilities of a service. For example:

**doc-store core features**:
1. Create document (POST /api/v2/documents)
2. Retrieve document (GET /api/v2/documents/{id})
3. Update document (PUT /api/v2/documents/{id})
4. Delete document (DELETE /api/v2/documents/{id})
5. List documents (GET /api/v2/documents)
6. Search documents (GET /api/v2/documents?search=...)
7. Document versioning
8. Metadata management

**Required Coverage**:
- **Each core feature**: Minimum 80% line coverage
- **Critical paths**: 100% coverage (authentication, data persistence)
- **Error handling**: 100% coverage (all error paths tested)
- **Edge cases**: All known edge cases have tests

### Coverage Measurement

```bash
# Measure coverage
pytest --cov=services/<service> --cov-report=html --cov-report=term

# Coverage by layer
pytest --cov=services/<service>/domain --cov-report=term
pytest --cov=services/<service>/application --cov-report=term
pytest --cov=services/<service>/infrastructure --cov-report=term
pytest --cov=services/<service>/presentation --cov-report=term

# Coverage report
open htmlcov/index.html
```

### Coverage Enforcement

```ini
# pytest.ini
[pytest]
addopts = 
    --cov=.
    --cov-report=html
    --cov-report=term
    --cov-fail-under=80
    --strict-markers

# Fail build if coverage < 80%
```

---

## 🧪 Test Types

### 1. Unit Tests (60-70%)

**Purpose**: Test individual units (functions, classes, methods) in isolation

**Characteristics**:
- Fast (< 1ms per test)
- Isolated (no external dependencies)
- Focused (test one thing)
- Deterministic (always same result)

**Structure**:
```
tests/unit/
├── domain/
│   ├── entities/
│   │   ├── test_document.py
│   │   └── test_analysis.py
│   ├── value_objects/
│   │   ├── test_document_id.py
│   │   └── test_confidence.py
│   ├── services/
│   │   └── test_document_service.py
│   └── repositories/
│       └── test_document_repository.py
├── application/
│   ├── commands/
│   │   ├── test_create_document.py
│   │   └── test_update_document.py
│   ├── queries/
│   │   └── test_get_document.py
│   └── services/
│       └── test_document_application_service.py
├── infrastructure/
│   ├── repositories/
│   │   └── test_sqlite_document_repository.py
│   └── external_services/
│       └── test_analysis_client.py
└── presentation/
    ├── api/
    │   └── test_document_controller.py
    └── middleware/
        └── test_error_handler.py
```

**Example**:
```python
# tests/unit/domain/entities/test_document.py

import pytest
from domain.entities.document import Document
from domain.exceptions import ValidationError

class TestDocument:
    """Unit tests for Document entity"""
    
    def test_create_document_with_valid_data_returns_document(self):
        """Test creating document with valid data"""
        # Arrange
        title = "Test Document"
        content = "Test content"
        
        # Act
        doc = Document(title=title, content=content)
        
        # Assert
        assert doc.title == title
        assert doc.content == content
        assert doc.id is not None
        assert doc.created_at is not None
    
    def test_create_document_with_empty_title_raises_error(self):
        """Test creating document with empty title raises ValidationError"""
        # Arrange
        title = ""
        content = "Test content"
        
        # Act & Assert
        with pytest.raises(ValidationError, match="Title cannot be empty"):
            Document(title=title, content=content)
    
    def test_document_update_changes_updated_at(self):
        """Test updating document changes updated_at timestamp"""
        # Arrange
        doc = Document(title="Original", content="Original content")
        original_updated_at = doc.updated_at
        
        # Act
        doc.update_content("New content")
        
        # Assert
        assert doc.content == "New content"
        assert doc.updated_at > original_updated_at
    
    @pytest.mark.parametrize("title,content", [
        ("A" * 1000, "Content"),  # Long title
        ("Title", "C" * 100000),  # Long content
        ("Title with émojis 🎉", "Content"),  # Unicode
        ("Title\nWith\nNewlines", "Content"),  # Special chars
    ])
    def test_document_handles_edge_cases(self, title, content):
        """Test document handles various edge cases"""
        doc = Document(title=title, content=content)
        assert doc.title == title
        assert doc.content == content
```

### 2. Integration Tests (20-30%)

**Purpose**: Test multiple units working together, including databases and external services

**Characteristics**:
- Medium speed (< 100ms per test)
- Real dependencies (database, cache, etc.)
- Test boundaries between components
- May require setup/teardown

**Structure**:
```
tests/integration/
├── api/
│   ├── test_document_endpoints.py
│   └── test_analysis_endpoints.py
├── database/
│   ├── test_document_repository.py
│   └── test_analysis_repository.py
├── services/
│   ├── test_document_service_integration.py
│   └── test_external_api_integration.py
└── workflows/
    ├── test_document_analysis_flow.py
    └── test_notification_flow.py
```

**Example**:
```python
# tests/integration/database/test_document_repository.py

import pytest
from infrastructure.repositories.sqlite_document_repository import SQLiteDocumentRepository
from domain.entities.document import Document

@pytest.mark.integration
class TestDocumentRepository:
    """Integration tests for document repository"""
    
    @pytest.fixture
    async def repository(self, test_db):
        """Create repository with test database"""
        return SQLiteDocumentRepository(test_db)
    
    async def test_save_and_retrieve_document(self, repository):
        """Test saving and retrieving document from database"""
        # Arrange
        doc = Document(title="Test", content="Content")
        
        # Act - Save
        saved_id = await repository.save(doc)
        
        # Act - Retrieve
        retrieved = await repository.get_by_id(saved_id)
        
        # Assert
        assert retrieved is not None
        assert retrieved.id == saved_id
        assert retrieved.title == doc.title
        assert retrieved.content == doc.content
    
    async def test_update_document_persists_changes(self, repository):
        """Test updating document persists to database"""
        # Arrange
        doc = Document(title="Original", content="Original")
        doc_id = await repository.save(doc)
        
        # Act
        doc.update_content("Updated")
        await repository.update(doc)
        
        # Retrieve again
        updated = await repository.get_by_id(doc_id)
        
        # Assert
        assert updated.content == "Updated"
    
    async def test_delete_document_removes_from_database(self, repository):
        """Test deleting document removes it from database"""
        # Arrange
        doc = Document(title="To Delete", content="Content")
        doc_id = await repository.save(doc)
        
        # Act
        await repository.delete(doc_id)
        
        # Assert
        deleted = await repository.get_by_id(doc_id)
        assert deleted is None
    
    async def test_search_returns_matching_documents(self, repository):
        """Test search functionality"""
        # Arrange
        doc1 = Document(title="Python Guide", content="Python content")
        doc2 = Document(title="Java Guide", content="Java content")
        doc3 = Document(title="Python Advanced", content="More Python")
        
        await repository.save(doc1)
        await repository.save(doc2)
        await repository.save(doc3)
        
        # Act
        results = await repository.search("Python")
        
        # Assert
        assert len(results) == 2
        assert all("Python" in doc.title for doc in results)
```

### 3. Functional Tests (10-15%)

**Purpose**: Test complete features from user perspective

**Characteristics**:
- Test complete features
- Black-box testing approach
- Test through public APIs
- Realistic scenarios

**Structure**:
```
tests/functional/
├── features/
│   ├── test_document_management.py
│   ├── test_document_analysis.py
│   └── test_search_functionality.py
└── scenarios/
    ├── test_user_workflow.py
    └── test_admin_workflow.py
```

**Example**:
```python
# tests/functional/features/test_document_management.py

import pytest
from httpx import AsyncClient

@pytest.mark.functional
@pytest.mark.asyncio
class TestDocumentManagement:
    """Functional tests for document management feature"""
    
    async def test_complete_document_lifecycle(self, api_client: AsyncClient):
        """Test complete document lifecycle from user perspective"""
        # Create document
        create_response = await api_client.post(
            "/api/v2/documents",
            json={
                "title": "User Document",
                "content": "User content",
                "metadata": {"author": "test_user"}
            }
        )
        assert create_response.status_code == 201
        doc_id = create_response.json()["data"]["id"]
        
        # Retrieve document
        get_response = await api_client.get(f"/api/v2/documents/{doc_id}")
        assert get_response.status_code == 200
        assert get_response.json()["data"]["title"] == "User Document"
        
        # Update document
        update_response = await api_client.put(
            f"/api/v2/documents/{doc_id}",
            json={
                "title": "Updated Document",
                "content": "Updated content"
            }
        )
        assert update_response.status_code == 200
        
        # Verify update
        updated_doc = await api_client.get(f"/api/v2/documents/{doc_id}")
        assert updated_doc.json()["data"]["title"] == "Updated Document"
        
        # Search for document
        search_response = await api_client.get(
            "/api/v2/documents",
            params={"search": "Updated"}
        )
        assert search_response.status_code == 200
        results = search_response.json()["data"]
        assert any(doc["id"] == doc_id for doc in results)
        
        # Delete document
        delete_response = await api_client.delete(f"/api/v2/documents/{doc_id}")
        assert delete_response.status_code == 204
        
        # Verify deletion
        deleted_doc = await api_client.get(f"/api/v2/documents/{doc_id}")
        assert deleted_doc.status_code == 404
```

### 4. End-to-End Tests (5-10%)

**Purpose**: Test critical user journeys through entire system

**Characteristics**:
- Slow (< 5s per test)
- All services running
- Real infrastructure
- Critical paths only

**Structure**:
```
tests/e2e/
├── critical_paths/
│   ├── test_document_to_analysis_flow.py
│   └── test_user_registration_flow.py
└── user_journeys/
    ├── test_new_user_journey.py
    └── test_admin_journey.py
```

### 5. Performance Tests (As Needed)

**Purpose**: Verify performance requirements

**Structure**:
```
tests/performance/
├── load/
│   └── test_document_api_load.py
├── stress/
│   └── test_concurrent_requests.py
└── endurance/
    └── test_24hour_stability.py
```

---

## 📏 Testing Standards

### Test Naming Convention

```python
def test_<scenario>_<expected_behavior>():
    """Test description in plain English"""
    pass

# Examples:
def test_create_document_with_valid_data_returns_document():
def test_create_document_with_empty_title_raises_validation_error():
def test_get_document_with_nonexistent_id_returns_404():
def test_update_document_with_concurrent_requests_handles_conflict():
```

### Test Structure (AAA Pattern)

```python
def test_example():
    # Arrange - Set up test data and dependencies
    document = create_test_document()
    service = DocumentService()
    
    # Act - Execute the code being tested
    result = service.process(document)
    
    # Assert - Verify the expected outcome
    assert result.status == "completed"
    assert result.errors == []
```

### Test Fixtures

```python
# conftest.py
import pytest
from infrastructure.database import Database

@pytest.fixture
async def test_db():
    """Provide test database"""
    db = Database(":memory:")  # In-memory for tests
    await db.initialize()
    yield db
    await db.cleanup()

@pytest.fixture
def sample_document():
    """Provide sample document for tests"""
    return Document(
        title="Test Document",
        content="Test content",
        metadata={"author": "test"}
    )

@pytest.fixture
async def document_repository(test_db):
    """Provide document repository with test database"""
    return SQLiteDocumentRepository(test_db)
```

### Parametrized Tests

```python
@pytest.mark.parametrize("input,expected", [
    ("", ValidationError),
    ("a", ValidationError),  # Too short
    ("A" * 1001, ValidationError),  # Too long
    ("Valid Title", None),  # Valid
])
def test_document_title_validation(input, expected):
    """Test various title validation scenarios"""
    if expected is None:
        doc = Document(title=input, content="Content")
        assert doc.title == input
    else:
        with pytest.raises(expected):
            Document(title=input, content="Content")
```

### Mocking External Dependencies

```python
from unittest.mock import Mock, patch, AsyncMock

async def test_document_analysis_with_external_service():
    """Test document analysis with mocked external service"""
    # Arrange
    mock_analysis_client = AsyncMock()
    mock_analysis_client.analyze.return_value = {
        "quality_score": 0.95,
        "sentiment": "positive"
    }
    
    service = DocumentService(analysis_client=mock_analysis_client)
    doc = Document(title="Test", content="Content")
    
    # Act
    result = await service.analyze_document(doc)
    
    # Assert
    assert result.quality_score == 0.95
    mock_analysis_client.analyze.assert_called_once_with(doc)
```

---

## 💻 Implementation Guide

### Step 1: Set Up Testing Infrastructure

```bash
# Install testing dependencies
pip install pytest pytest-asyncio pytest-cov pytest-mock pytest-xdist

# Create pytest.ini
cat > pytest.ini << EOF
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = 
    -v
    --tb=short
    --strict-markers
    --cov=.
    --cov-report=html
    --cov-report=term
    --cov-fail-under=80
    -n auto
markers =
    unit: Unit tests
    integration: Integration tests
    functional: Functional tests
    e2e: End-to-end tests
    slow: Slow tests (> 1s)
    performance: Performance tests
EOF
```

### Step 2: Create Test Directory Structure

```bash
# Create standard test structure
mkdir -p tests/{unit/{domain,application,infrastructure,presentation},integration,functional,e2e,performance,fixtures}

# Create __init__.py files
find tests -type d -exec touch {}/__init__.py \;

# Create conftest.py
touch tests/conftest.py
```

### Step 3: Write Tests (TDD)

Follow Red-Green-Refactor for each feature:

```python
# 1. RED - Write failing test
def test_create_document_returns_document():
    service = DocumentService()
    result = service.create_document("Title", "Content")
    assert isinstance(result, Document)
# Run: pytest -> FAIL

# 2. GREEN - Minimal implementation
class DocumentService:
    def create_document(self, title, content):
        return Document(title=title, content=content)
# Run: pytest -> PASS

# 3. REFACTOR - Improve code
class DocumentService:
    def __init__(self, repository: DocumentRepository):
        self._repository = repository
        self._validator = DocumentValidator()
    
    def create_document(self, title: str, content: str) -> Document:
        # Validate
        self._validator.validate_title(title)
        self._validator.validate_content(content)
        
        # Create
        document = Document(title=title, content=content)
        
        # Save
        self._repository.save(document)
        
        return document
# Run: pytest -> PASS (refactor more tests as needed)
```

### Step 4: Measure Coverage

```bash
# Run tests with coverage
pytest --cov=services/<service> --cov-report=html

# View coverage report
open htmlcov/index.html

# Identify gaps
pytest --cov=services/<service> --cov-report=term-missing

# Focus on uncovered lines
```

### Step 5: Continuous Testing

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov pytest-asyncio
      
      - name: Run tests
        run: pytest --cov --cov-fail-under=80
      
      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

---

## 🛠️ Tools and Frameworks

### Core Testing Tools

```python
# pytest - Testing framework
pytest==7.4.0

# pytest-asyncio - Async test support
pytest-asyncio==0.21.0

# pytest-cov - Coverage measurement
pytest-cov==4.1.0

# pytest-mock - Mocking support
pytest-mock==3.11.1

# pytest-xdist - Parallel execution
pytest-xdist==3.3.1

# pytest-timeout - Timeout support
pytest-timeout==2.1.0

# faker - Generate test data
faker==19.2.0

# factory-boy - Test factories
factory-boy==3.2.1

# httpx - HTTP client for API tests
httpx==0.24.1
```

### Coverage Tools

```bash
# Generate HTML coverage report
pytest --cov --cov-report=html

# Generate XML for CI
pytest --cov --cov-report=xml

# Show missing lines
pytest --cov --cov-report=term-missing

# Focus on specific module
pytest --cov=services/doc_store/domain --cov-report=term
```

### Test Data Generation

```python
# Use Faker for realistic test data
from faker import Faker

fake = Faker()

def generate_test_document():
    return Document(
        title=fake.sentence(),
        content=fake.text(),
        metadata={
            "author": fake.name(),
            "created": fake.date_time()
        }
    )
```

---

## 📚 Examples

### Complete Test Suite Example

```python
# tests/unit/domain/test_document.py

import pytest
from datetime import datetime
from domain.entities.document import Document
from domain.exceptions import ValidationError

@pytest.mark.unit
class TestDocument:
    """Comprehensive unit tests for Document entity"""
    
    # Happy path tests
    def test_create_document_with_valid_data(self):
        """Test creating document with all valid fields"""
        doc = Document(
            title="Test Document",
            content="Test content",
            metadata={"author": "Test User"}
        )
        
        assert doc.id is not None
        assert doc.title == "Test Document"
        assert doc.content == "Test content"
        assert doc.metadata["author"] == "Test User"
        assert isinstance(doc.created_at, datetime)
    
    # Error path tests
    def test_create_document_with_empty_title_raises_error(self):
        """Test validation: empty title"""
        with pytest.raises(ValidationError, match="Title cannot be empty"):
            Document(title="", content="Content")
    
    def test_create_document_with_empty_content_raises_error(self):
        """Test validation: empty content"""
        with pytest.raises(ValidationError, match="Content cannot be empty"):
            Document(title="Title", content="")
    
    def test_create_document_with_invalid_metadata_raises_error(self):
        """Test validation: invalid metadata type"""
        with pytest.raises(ValidationError, match="Metadata must be a dictionary"):
            Document(title="Title", content="Content", metadata="invalid")
    
    # Edge case tests
    @pytest.mark.parametrize("title_length", [1, 10, 100, 255])
    def test_document_handles_various_title_lengths(self, title_length):
        """Test document handles titles of various lengths"""
        title = "A" * title_length
        doc = Document(title=title, content="Content")
        assert len(doc.title) == title_length
    
    def test_document_with_very_long_title_raises_error(self):
        """Test validation: title too long"""
        with pytest.raises(ValidationError, match="Title too long"):
            Document(title="A" * 256, content="Content")
    
    def test_document_with_unicode_characters(self):
        """Test document handles unicode characters"""
        doc = Document(
            title="Document émojis 🎉 中文",
            content="Content with special chars: ñ, ü, ç"
        )
        assert "émojis" in doc.title
        assert "🎉" in doc.title
    
    # State change tests
    def test_update_content_changes_content_and_timestamp(self):
        """Test updating content updates both content and timestamp"""
        doc = Document(title="Title", content="Original")
        original_updated = doc.updated_at
        
        doc.update_content("Updated")
        
        assert doc.content == "Updated"
        assert doc.updated_at > original_updated
    
    def test_add_metadata_preserves_existing_metadata(self):
        """Test adding metadata doesn't remove existing data"""
        doc = Document(
            title="Title",
            content="Content",
            metadata={"key1": "value1"}
        )
        
        doc.add_metadata("key2", "value2")
        
        assert doc.metadata["key1"] == "value1"
        assert doc.metadata["key2"] == "value2"
    
    # Business logic tests
    def test_document_age_calculation(self):
        """Test document age is calculated correctly"""
        doc = Document(title="Title", content="Content")
        age = doc.get_age_in_days()
        assert age >= 0
    
    def test_document_is_stale_after_threshold(self):
        """Test document is marked stale after threshold"""
        # Mock created_at to be old
        doc = Document(title="Title", content="Content")
        doc.created_at = datetime(2020, 1, 1)
        
        assert doc.is_stale(days_threshold=30) is True
```

---

## ✅ Checklist

### Per-Service Testing Checklist

**Setup**:
- [ ] pytest.ini configured
- [ ] Test directory structure created
- [ ] conftest.py with fixtures
- [ ] Coverage measurement enabled
- [ ] CI/CD pipeline configured

**Unit Tests**:
- [ ] All domain entities tested
- [ ] All value objects tested
- [ ] All domain services tested
- [ ] All application commands tested
- [ ] All application queries tested
- [ ] All repository interfaces tested
- [ ] All controllers tested
- [ ] Coverage > 90% for domain layer

**Integration Tests**:
- [ ] Repository implementations tested
- [ ] Database integration tested
- [ ] External service clients tested
- [ ] API endpoints tested
- [ ] Service-to-service tested
- [ ] Coverage > 70% for infrastructure

**Functional Tests**:
- [ ] Each core feature has tests
- [ ] Happy paths tested
- [ ] Error paths tested
- [ ] Edge cases tested
- [ ] Coverage > 80% of core features

**E2E Tests**:
- [ ] Critical user journeys tested
- [ ] Cross-service workflows tested
- [ ] At least 3 E2E scenarios

**Quality**:
- [ ] All tests pass
- [ ] Overall coverage > 80%
- [ ] No flaky tests
- [ ] Tests run in < 5 minutes
- [ ] Coverage report generated

---

**Document Control**  
**Version**: 1.0.0  
**Last Updated**: October 8, 2025  
**Next Review**: 2025-11-08  
**Owner**: Hackathon Team

