# Test Datasets and Fixtures Guide

This guide documents the test datasets, fixtures, and testing patterns used throughout the LLM Documentation Ecosystem. It helps developers understand how to work with existing test data and extend the test suite.

## 📁 Test Structure Overview

```
tests/
├── conftest.py                 # Global test configuration and fixtures
├── fixtures/                   # Reusable test fixtures
│   ├── authentication.py       # Auth-related test data
│   ├── business_data.py        # Business logic test data
│   ├── documentation_fixtures.py  # Documentation-specific fixtures
│   ├── github_fixtures.py      # GitHub API test data
│   ├── jira_fixtures.py        # Jira API test data
│   ├── mocking.py              # Mock utilities and factories
│   ├── repository_fixtures.py  # Repository-related test data
│   ├── user_fixtures.py        # User and identity test data
│   └── workflow_fixtures.py    # Workflow and orchestration test data
├── helpers/                    # Test helper utilities
│   ├── assertions.py           # Custom assertion helpers
│   ├── clients.py              # Test client utilities
│   └── service_clients.py      # Service-specific test clients
├── integration/                # Integration test suites
├── unit/                       # Unit test suites (per service)
└── data/                       # Test data files (currently minimal)
```

## 🎯 Core Testing Concepts

### Test Categories and Markers

The test suite uses pytest markers to categorize tests:

```python
@pytest.mark.unit          # Unit tests for individual components
@pytest.mark.integration   # Integration tests across services
@pytest.mark.consistency   # Documentation consistency analysis tests
@pytest.mark.e2e           # End-to-end workflow tests
@pytest.mark.orchestrator  # Orchestrator service tests
@pytest.mark.doc_store     # Document store tests
@pytest.mark.consistency_engine  # Consistency engine tests
@pytest.mark.agents       # Source agent tests
@pytest.mark.slow         # Long-running tests to be excluded from fast CI lanes
@pytest.mark.live         # Tests that hit live/containerized services
@pytest.mark.security     # Tests that validate security controls
```

### Test Modes

Tests can run in different modes controlled by the `--test-mode` option:

- **mocked**: Default mode using mocks and stubs (fastest)
- **integration**: Tests with real service dependencies
- **live**: Tests against live/containerized services

## 📚 Key Fixture Categories

### Documentation Fixtures

Located in `tests/fixtures/documentation_fixtures.py`:

```python
@pytest.fixture
def sample_confluence_page():
    """Sample Confluence page with realistic structure."""
    return {
        "id": "page_123",
        "title": "API Documentation",
        "space": {"name": "Engineering", "key": "ENG"},
        "content": "<h1>API Documentation</h1><p>This is the API documentation.</p>",
        "author": {"displayName": "John Doe", "username": "john.doe"},
        "createdDate": "2024-01-01T10:00:00Z",
        "lastModified": "2024-01-15T10:00:00Z",
        "version": {"number": 5},
        "labels": ["api", "documentation"],
        "links": {"self": "https://company.atlassian.net/wiki/rest/api/content/123"}
    }

@pytest.fixture
def confluence_api_page():
    """Confluence page containing API documentation."""
    # Returns page with API endpoint documentation
    # Includes examples, parameters, and responses

@pytest.fixture
def github_wiki_with_api_docs():
    """GitHub wiki page containing API documentation."""
    # Returns wiki page with markdown-formatted API docs
    # Includes code examples and usage patterns
```

### Business Data Fixtures

Located in `tests/fixtures/business_data.py`:

```python
@pytest.fixture
def sample_analysis_request():
    """Sample analysis request with realistic data."""
    return {
        "target_type": "service",
        "target_id": "user-service",
        "analysis_type": "consistency",
        "scope": {"include_dependencies": True},
        "correlation_id": "test-request-123"
    }

@pytest.fixture
def mock_analysis_findings():
    """Mock analysis findings for testing."""
    return [
        {
            "id": "finding_001",
            "severity": "high",
            "category": "consistency",
            "title": "API mismatch detected",
            "description": "Endpoint /users differs between docs and code",
            "location": {"file": "user_service.py", "line": 45},
            "suggestions": ["Update documentation", "Align implementation"]
        }
    ]
```

### Authentication Fixtures

Located in `tests/fixtures/authentication.py`:

```python
@pytest.fixture
def valid_jwt_token():
    """Valid JWT token for authenticated requests."""
    # Returns properly signed JWT token

@pytest.fixture
def expired_jwt_token():
    """Expired JWT token for testing auth failures."""
    # Returns JWT token that has expired

@pytest.fixture
def invalid_jwt_token():
    """Malformed JWT token for testing validation."""
    # Returns invalid JWT token
```

### Mocking Utilities

Located in `tests/fixtures/mocking.py`:

```python
@pytest.fixture
def mock_http_client():
    """Mock HTTP client for testing external API calls."""
    # Returns AsyncMock configured for HTTP requests

@pytest.fixture
def mock_redis_client():
    """Mock Redis client for testing caching."""
    # Returns mock Redis client with expected methods

@pytest.fixture
def mock_database_session():
    """Mock database session for testing data operations."""
    # Returns mock SQLAlchemy session
```

## 🛠️ Test Helper Utilities

### Assertions

Located in `tests/helpers/assertions.py`:

```python
def assert_success_response(response, expected_data=None):
    """Assert that response follows success envelope pattern."""
    assert response.status_code == 200
    data = response.json()
    assert "success" in data
    assert data["success"] is True
    assert "data" in data
    if expected_data:
        assert data["data"] == expected_data

def assert_error_response(response, expected_error_code=None):
    """Assert that response follows error envelope pattern."""
    assert response.status_code in [400, 422, 500]
    data = response.json()
    assert "success" in data
    assert data["success"] is False
    assert "details" in data
    if expected_error_code:
        assert data.get("error_code") == expected_error_code

def assert_envelope_structure(response):
    """Assert that response has proper envelope structure."""
    data = response.json()
    required_keys = ["success", "data"] if data.get("success") else ["success", "details"]
    for key in required_keys:
        assert key in data
```

### Service Clients

Located in `tests/helpers/service_clients.py`:

```python
class TestDocStoreClient:
    """Test client for Doc Store service interactions."""

    def __init__(self, base_url="http://localhost:5001"):
        self.base_url = base_url
        self.client = TestClient(app)  # FastAPI TestClient

    async def store_document(self, document_data):
        """Store document via test client."""
        return await self.client.post("/documents", json=document_data)

    async def search_documents(self, query):
        """Search documents via test client."""
        return await self.client.get(f"/documents/search?q={query}")

class TestOrchestratorClient:
    """Test client for Orchestrator service interactions."""
    # Similar pattern for orchestrator operations
```

## 📋 Extending Test Data

### Adding New Fixtures

1. **Choose appropriate location**:
   - `tests/fixtures/` for reusable fixtures
   - Service-specific test files for local fixtures

2. **Follow naming conventions**:
   ```python
   @pytest.fixture
   def sample_{entity}_{variant}():
       """Clear description of what the fixture provides."""
       return { ... }
   ```

3. **Make fixtures flexible**:
   ```python
   @pytest.fixture
   def configurable_analysis_request(analysis_type="consistency"):
       """Configurable analysis request fixture."""
       return {
           "target_type": "service",
           "analysis_type": analysis_type,
           "correlation_id": f"test-{analysis_type}-123"
       }
   ```

### Creating Mock Data Factories

```python
def create_mock_document(**overrides):
    """Factory for creating mock documents with defaults."""
    base_document = {
        "id": "doc_123",
        "title": "Sample Document",
        "content": "Sample content",
        "source": "test",
        "created_at": "2024-01-01T00:00:00Z"
    }
    return {**base_document, **overrides}

@pytest.fixture
def mock_document_factory():
    """Factory fixture for creating mock documents."""
    return create_mock_document
```

## 🧪 Testing Patterns

### Service Testing Pattern

```python
class TestDocStoreService:
    """Test suite for Doc Store service."""

    @pytest.mark.asyncio
    async def test_store_document_success(self, mock_document):
        """Test successful document storage."""
        client = TestDocStoreClient()
        response = await client.store_document(mock_document)

        assert_success_response(response)
        stored_doc = response.json()["data"]
        assert stored_doc["id"] == mock_document["id"]

    @pytest.mark.asyncio
    async def test_store_document_validation_error(self, invalid_document):
        """Test document storage with validation error."""
        client = TestDocStoreClient()
        response = await client.store_document(invalid_document)

        assert_error_response(response, "VALIDATION_ERROR")
```

### Integration Testing Pattern

```python
@pytest.mark.integration
class TestDocStoreIntegration:
    """Integration tests for Doc Store with dependencies."""

    async def test_full_workflow(self, real_doc_store, mock_analysis_service):
        """Test complete document processing workflow."""
        # Arrange
        document = create_mock_document()

        # Act
        store_response = await real_doc_store.store(document)
        analysis_response = await mock_analysis_service.analyze(document["id"])

        # Assert
        assert_success_response(store_response)
        assert_success_response(analysis_response)
```

### Mock Testing Pattern

```python
@pytest.mark.unit
class TestAnalysisService:
    """Unit tests for Analysis Service with mocks."""

    async def test_analysis_with_mocked_dependencies(
        self, mock_doc_store, mock_source_agent, sample_analysis_request
    ):
        """Test analysis with mocked dependencies."""
        # Arrange
        service = AnalysisService(
            doc_store=mock_doc_store,
            source_agent=mock_source_agent
        )

        # Act
        result = await service.analyze(sample_analysis_request)

        # Assert
        assert result["status"] == "completed"
        mock_doc_store.search.assert_called_once()
        mock_source_agent.fetch.assert_called_once()
```

## 🔧 Test Configuration

### Environment Variables for Testing

```bash
# Test-specific environment variables
TESTING=true
LOG_LEVEL=WARNING
TEST_MODE=mocked

# Service URLs for integration tests
DOC_STORE_URL=http://localhost:5001
SOURCE_AGENT_URL=http://localhost:5002
ORCHESTRATOR_URL=http://localhost:5099

# External service mocks
GITHUB_TOKEN=mock_token
JIRA_API_TOKEN=mock_token
CONFLUENCE_API_TOKEN=mock_token
```

### Running Tests

```bash
# Run all unit tests
pytest tests/unit/ -v

# Run integration tests
pytest tests/integration/ -v --test-mode=integration

# Run with coverage
pytest --cov=services --cov-report=html

# Run specific test categories
pytest -m "unit and not slow"
pytest -m "integration"
pytest -m "security"

# Run tests for specific service
pytest tests/unit/doc_store/
```

## 📈 Best Practices

### Fixture Design
- **Scope appropriately**: Use `function` scope for most fixtures, `session` for expensive setup
- **Keep fixtures simple**: Complex fixtures should be factories
- **Document fixtures**: Clear docstrings explaining what each fixture provides
- **Avoid side effects**: Fixtures should not modify global state

### Test Organization
- **Group related tests**: Use classes to group related test methods
- **Use descriptive names**: Test names should clearly indicate what they're testing
- **Test one thing**: Each test should verify a single behavior
- **Use parametrize**: For testing multiple inputs/outputs

### Mock Strategy
- **Mock external dependencies**: Don't rely on external services in unit tests
- **Use AsyncMock**: For async function mocking
- **Verify interactions**: Use `assert_called_once()`, `assert_called_with()` for verification
- **Keep mocks realistic**: Mock responses should match real API behavior

## 🚀 Contributing to Test Suite

### Adding New Test Data

1. **Identify the need**: What scenario or data pattern is missing?
2. **Choose location**: Add to existing fixture file or create new one
3. **Follow patterns**: Use existing naming and structure conventions
4. **Add documentation**: Document new fixtures and their usage
5. **Update this guide**: Add new fixtures to this documentation

### Test Coverage Guidelines

- **Unit tests**: Aim for 80%+ coverage of business logic
- **Integration tests**: Cover critical service interactions
- **Edge cases**: Test error conditions and boundary values
- **Performance**: Include performance regression tests where appropriate

This guide should be updated as new fixtures and testing patterns are added to the codebase.
