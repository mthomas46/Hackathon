# Data Services Dashboard - Testing Framework

This directory contains a comprehensive testing framework for the Data Services Dashboard, providing unit tests, integration tests, and end-to-end tests to ensure code quality and functionality.

## 🏗️ Test Structure

```
tests/
├── conftest.py              # Pytest configuration and global fixtures
├── pytest.ini              # Pytest settings and markers
├── README.md               # This file
├── fixtures/               # Test data fixtures
├── unit/                   # Unit tests
│   ├── test_prompt_tuning.py
│   └── test_document_analysis.py
├── integration/            # Integration tests
│   └── test_service_clients.py
├── e2e/                    # End-to-end tests
│   └── test_dashboard_workflow.py
└── utils/                  # Test utilities and runners
    └── test_runner.py
```

## 🧪 Test Types

### Unit Tests (`tests/unit/`)
- **Purpose**: Test individual functions and components in isolation
- **Mocking**: Heavy use of mocks for external dependencies
- **Coverage**: Helper functions, data processing, validation
- **Examples**:
  - Prompt variable extraction and validation
  - Document content analysis and keyword extraction
  - Token counting and formatting utilities

### Integration Tests (`tests/integration/`)
- **Purpose**: Test interactions between components and services
- **Mocking**: Mock service clients and HTTP responses
- **Coverage**: Service client functionality, API interactions
- **Examples**:
  - Memory Agent client operations
  - Prompt Store client CRUD operations
  - Document Store client interactions
  - Concurrent request handling

### End-to-End Tests (`tests/e2e/`)
- **Purpose**: Test complete workflows and user journeys
- **Mocking**: Minimal, focuses on component integration
- **Coverage**: Full dashboard workflows, cross-service interactions
- **Examples**:
  - Complete service workflows (create → read → update → delete)
  - Cross-service data flows
  - Error handling and recovery
  - Concurrent operations

## 🚀 Running Tests

### Prerequisites

Install test dependencies:
```bash
pip install -r requirements-test.txt
```

### Quick Start

Run all tests:
```bash
# From the dashboard root directory
python tests/utils/test_runner.py

# Or using pytest directly
pytest tests/
```

### Specific Test Types

```bash
# Unit tests only
python tests/utils/test_runner.py unit

# Integration tests only
python tests/utils/test_runner.py integration

# End-to-end tests only
python tests/utils/test_runner.py e2e
```

### Advanced Options

```bash
# Verbose output
python tests/utils/test_runner.py --verbose

# With coverage report
python tests/utils/test_runner.py --coverage

# Generate test report
python tests/utils/test_runner.py --report

# Setup test environment
python tests/utils/test_runner.py --setup
```

### Running Individual Tests

```bash
# Run specific test file
pytest tests/unit/test_prompt_tuning.py

# Run specific test function
pytest tests/unit/test_prompt_tuning.py::TestVariableExtraction::test_extract_variables_basic

# Run with coverage for specific module
pytest --cov=pages.prompt_browser tests/unit/test_prompt_tuning.py
```

## 🛠️ Test Configuration

### Pytest Configuration (`pytest.ini`)

The test suite is configured with:
- **Async support**: Automatic asyncio mode detection
- **Markers**: `unit`, `integration`, `e2e`, `slow`, `skip_ci`
- **Warning filters**: Ignores common deprecation warnings
- **Test discovery**: Standard pytest patterns

### Global Fixtures (`conftest.py`)

#### Mock Clients
- `mock_memory_client`: Mock Memory Agent client with realistic responses
- `mock_prompt_client`: Mock Prompt Store client for CRUD operations
- `mock_document_client`: Mock Document Store client for content operations

#### Sample Data
- `sample_memory_items`: Realistic memory data for testing
- `sample_prompts`: Sample prompts with variables and metadata
- `sample_documents`: Test documents with different content types

#### Environment Setup
- `mock_streamlit`: Mocks Streamlit UI functions to avoid display dependencies
- `test_config`: Test configuration with service endpoints

## 📊 Test Coverage

### Target Coverage Areas

1. **Prompt Management**
   - Variable extraction and validation
   - Content analysis and quality scoring
   - AI tuning and optimization
   - Version comparison and rollback

2. **Document Processing**
   - Content analysis and keyword extraction
   - Quality indicators and readability scores
   - Export functionality and formatting
   - Search within documents

3. **Memory Operations**
   - Item storage and retrieval
   - Search and filtering
   - Analytics and health monitoring
   - Concurrent operations

4. **Service Integration**
   - HTTP client functionality
   - Error handling and recovery
   - Session management
   - Concurrent request handling

5. **Dashboard Workflows**
   - Page navigation and component loading
   - Cross-service data flows
   - Error recovery and fallback behavior
   - Performance under load

## 🔧 Test Utilities

### Test Runner (`tests/utils/test_runner.py`)

A comprehensive test runner with:
- **Flexible execution**: Run specific test types or all tests
- **Coverage reporting**: HTML and terminal coverage reports
- **Environment setup**: Automatic test environment configuration
- **Report generation**: JSON test reports with results summary

### Custom Fixtures

- **Service mocks**: Realistic mock implementations of all service clients
- **Data fixtures**: Pre-defined test data for consistent testing
- **Environment mocks**: Streamlit and external dependency mocking
- **Async utilities**: Async test helpers and event loop management

## 📈 Continuous Integration

### CI Pipeline Integration

The test suite is designed for CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run Tests
  run: |
    cd services/data-services-dashboard
    python tests/utils/test_runner.py --coverage --report

- name: Upload Coverage
  uses: codecov/codecov-action@v3
  with:
    file: ./services/data-services-dashboard/htmlcov/coverage.xml
```

### Coverage Requirements

- **Minimum coverage**: 80% overall
- **Critical paths**: 90%+ for core business logic
- **Exclusions**: Generated code, test utilities, UI components

## 🐛 Debugging Tests

### Common Issues

1. **Import Errors**: Ensure correct Python path in test environment
2. **Async Issues**: Check asyncio mode and event loop configuration
3. **Mock Conflicts**: Verify mock isolation between tests
4. **Streamlit Dependencies**: Ensure UI functions are properly mocked

### Debugging Commands

```bash
# Run with detailed output
pytest -v -s tests/unit/test_prompt_tuning.py

# Run specific test with debugging
pytest --pdb tests/integration/test_service_clients.py::TestMemoryAgentClient::test_memory_client_health_check

# Check test discovery
pytest --collect-only tests/

# Run with coverage details
pytest --cov-report=html --cov=pages tests/unit/
```

## 📚 Test Best Practices

### Writing New Tests

1. **Use descriptive names**: `test_extract_variables_from_complex_prompt`
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Mock external dependencies**: Don't rely on real services
4. **Use fixtures**: Leverage existing fixtures for consistency
5. **Test edge cases**: Include boundary conditions and error scenarios

### Example Test Structure

```python
class TestMyFeature:
    """Test suite for my feature."""

    def test_basic_functionality(self, mock_client):
        """Test basic functionality."""
        # Arrange
        test_data = {"key": "value"}

        # Act
        result = my_function(test_data)

        # Assert
        assert result["success"] is True
        assert result["data"] == test_data

    @pytest.mark.asyncio
    async def test_async_operation(self, mock_client):
        """Test async operations."""
        # Arrange
        test_input = "test input"

        # Act
        result = await async_function(test_input)

        # Assert
        assert result["status"] == "completed"
```

### Mock Best Practices

1. **Use spec**: `Mock(spec=RealClass)` to match real interfaces
2. **AsyncMock for async methods**: Use `AsyncMock()` for async functions
3. **Return realistic data**: Mock responses should match real API responses
4. **Side effects**: Use `side_effect` for exceptions and complex behavior

## 📋 Test Checklist

Before committing new code:

- [ ] Unit tests written for new functions
- [ ] Integration tests for new components
- [ ] E2E tests for new workflows
- [ ] Test coverage maintained (>80%)
- [ ] All tests pass locally
- [ ] No new linting errors
- [ ] Documentation updated

## 🔍 Troubleshooting

### Test Failures

1. **Check imports**: Ensure all modules can be imported
2. **Verify mocks**: Check that mocks match current API signatures
3. **Environment**: Ensure test environment variables are set
4. **Dependencies**: Verify all test dependencies are installed

### Performance Issues

1. **Mock efficiency**: Use appropriate mock types for performance
2. **Test isolation**: Ensure tests don't interfere with each other
3. **Resource cleanup**: Properly close connections and clean up resources

### Coverage Issues

1. **Missing lines**: Identify untested code paths
2. **Branch coverage**: Test both true and false conditions
3. **Exception handling**: Test error conditions and edge cases

## 📞 Support

For test-related issues:

1. Check the test output for detailed error messages
2. Run tests with `-v` flag for verbose output
3. Use `--pdb` for interactive debugging
4. Check the test fixtures and mocks are up to date
5. Verify service APIs haven't changed

The testing framework is designed to be maintainable, comprehensive, and fast, ensuring the Data Services Dashboard maintains high code quality and reliability.
