# Code Analyzer - Test Suite

**Service**: code-analyzer  
**Test Infrastructure Version**: 1.0.0  
**Coverage Target**: 80%+  
**Testing Framework**: pytest

---

## 📊 Test Suite Overview

This test suite follows the **Testing Pyramid** approach with comprehensive coverage across all layers.

```
        /\
       /  \
      /E2E \      10% - End-to-End Tests
     /------\
    /  INT   \    30% - Integration Tests
   /----------\
  /   UNIT     \  60% - Unit Tests
 /--------------\
```

**Target**: 225 tests achieving 80%+ code coverage

---

## 📁 Directory Structure

```
tests/
├── README.md                      # This file
├── pytest.ini                     # Pytest configuration
├── conftest.py                    # Shared fixtures and configuration
├── requirements-test.txt          # Testing dependencies
│
├── unit/                          # Unit tests (60% of tests)
│   ├── domain/                    # Domain layer tests
│   │   ├── test_code_analysis.py  # CodeAnalysis entity tests
│   │   ├── test_code_structure.py # CodeStructure entity tests
│   │   ├── test_value_objects.py  # Value object tests
│   │   └── services/              # Domain service tests
│   │       ├── test_code_analyzer.py
│   │       ├── test_structure_extractor.py
│   │       ├── test_complexity_calculator.py
│   │       └── test_security_scanner.py
│   ├── application/               # Application layer tests
│   │   └── test_analysis_service.py
│   ├── infrastructure/            # Infrastructure tests
│   │   └── test_repositories.py
│   └── presentation/              # API/Presentation tests
│       └── test_api_endpoints.py
│
├── integration/                   # Integration tests (30% of tests)
│   ├── test_full_analysis.py      # End-to-end analysis flow
│   ├── test_api_integration.py    # API integration tests
│   └── test_shared_infrastructure.py
│
├── e2e/                           # End-to-end tests (10% of tests)
│   └── test_prompt_store_workflow.py
│
└── performance/                   # Performance tests
    └── test_load.py
```

---

## 🧪 Available Fixtures

### Code Samples

- `simple_python_function` - Basic Python function for testing
- `python_class_code` - Python class with methods
- `complex_python_code` - High complexity code for testing metrics
- `code_with_security_issues` - Code with security vulnerabilities
- `large_python_file` - Large file for performance testing

### Request/Response

- `basic_analysis_request` - Complete analysis request payload
- `minimal_analysis_request` - Minimal request for basic tests
- `mock_analysis_response` - Sample analysis response

### Domain Entities

- `sample_code_structure` - CodeStructure entity data
- `sample_complexity_metrics` - ComplexityMetrics data
- `sample_security_finding` - SecurityFinding data

### Factories

- `analysis_factory` - Factory for creating test CodeAnalysis instances

### API Testing

- `api_client` - HTTP client for API testing

---

## 🚀 Running Tests

### Run All Tests

```bash
# Run all tests with coverage
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov --cov-report=html
```

### Run Specific Test Categories

```bash
# Unit tests only (fast)
pytest tests/unit -m unit

# Integration tests
pytest tests/integration -m integration

# E2E tests
pytest tests/e2e -m e2e

# Performance tests
pytest tests/performance -m performance
```

### Run Specific Layers

```bash
# Domain layer tests
pytest tests/unit/domain -m domain

# API tests
pytest tests/unit/presentation -m presentation

# Application layer
pytest tests/unit/application -m application
```

### Parallel Execution

```bash
# Run tests in parallel (faster)
pytest -n auto
```

---

## 📊 Coverage Requirements

### Overall Target

- **Minimum**: 80% total coverage
- **Goal**: 85%+ coverage

### By Layer

| Layer | Target | Rationale |
|-------|--------|-----------|
| Domain | 85%+ | Core business logic must be well-tested |
| Application | 80%+ | Orchestration logic |
| Infrastructure | 80%+ | External integrations |
| Presentation | 85%+ | API surface must be reliable |

### Excluded from Coverage

- `__init__.py` files
- Test files themselves
- Configuration files
- Scaffolding/boilerplate

---

## 🏷️ Test Markers

Use markers to organize and run specific test groups:

```python
@pytest.mark.unit
def test_simple_function():
    """Fast, isolated unit test."""
    pass

@pytest.mark.integration
def test_full_workflow():
    """Integration test with dependencies."""
    pass

@pytest.mark.slow
def test_large_file_analysis():
    """Slow-running test."""
    pass

@pytest.mark.domain
def test_code_analysis_entity():
    """Domain layer test."""
    pass
```

**Available Markers**:
- `unit` - Unit tests (fast, isolated)
- `integration` - Integration tests (slower)
- `e2e` - End-to-end tests (slowest)
- `performance` - Performance tests
- `security` - Security tests
- `slow` - Slow-running tests
- `domain` - Domain layer
- `application` - Application layer
- `infrastructure` - Infrastructure layer
- `presentation` - Presentation layer

---

## 🔧 Configuration

### pytest.ini

Key configurations:
- Coverage reporting enabled
- Minimum 80% coverage required
- HTML coverage reports generated
- Strict marker enforcement
- Verbose output

### conftest.py

Provides:
- Shared fixtures
- Test data generators
- Mock objects
- Setup/teardown logic
- Custom pytest hooks

---

## 📝 Writing Tests

### Test Naming Convention

```python
# File: test_<module_name>.py
# Class: Test<ClassName>
# Function: test_<what_it_tests>

# Example:
# tests/unit/domain/test_code_analysis.py

class TestCodeAnalysis:
    def test_create_with_valid_inputs(self):
        """Test CodeAnalysis creation with valid inputs."""
        pass
    
    def test_reject_empty_code(self):
        """Test CodeAnalysis rejects empty code."""
        pass
```

### AAA Pattern (Arrange-Act-Assert)

```python
def test_complexity_calculation(simple_python_function):
    # Arrange
    code = simple_python_function
    calculator = ComplexityCalculator()
    
    # Act
    metrics = calculator.calculate(code)
    
    # Assert
    assert metrics.cyclomatic_complexity >= 1
    assert 0 <= metrics.comment_ratio <= 1
```

### Using Fixtures

```python
def test_analysis_request(basic_analysis_request, api_client):
    """Test analysis endpoint with fixture data."""
    response = api_client.post("/api/v2/analyze", json=basic_analysis_request)
    assert response.status_code == 200
```

---

## 🎯 Test Development Workflow (TDD)

### Red-Green-Refactor Cycle

1. **Red**: Write a failing test
   ```bash
   pytest tests/unit/domain/test_code_analysis.py::test_new_feature
   # FAIL - Feature not implemented
   ```

2. **Green**: Make the test pass (minimum code)
   ```bash
   # Implement feature
   pytest tests/unit/domain/test_code_analysis.py::test_new_feature
   # PASS
   ```

3. **Refactor**: Improve code while keeping tests green
   ```bash
   # Refactor implementation
   pytest tests/unit/domain/test_code_analysis.py::test_new_feature
   # PASS (still passing)
   ```

---

## 📈 Coverage Reports

### Viewing Coverage

```bash
# Generate HTML coverage report
pytest --cov --cov-report=html

# Open in browser
open htmlcov/index.html
```

### Terminal Coverage

```bash
# Show coverage in terminal
pytest --cov --cov-report=term-missing
```

---

## 🔍 Debugging Tests

### Run Specific Test

```bash
# By file
pytest tests/unit/domain/test_code_analysis.py

# By function
pytest tests/unit/domain/test_code_analysis.py::test_create_with_valid_inputs

# By class and function
pytest tests/unit/domain/test_code_analysis.py::TestCodeAnalysis::test_create_with_valid_inputs
```

### Debugging Options

```bash
# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l

# Drop into debugger on failure
pytest --pdb

# Show print statements
pytest -s
```

---

## 🎨 Code Quality

### Run Linting

```bash
# Type checking
mypy services/code-analyzer

# Linting
pylint services/code-analyzer

# Code formatting check
black --check services/code-analyzer

# Complexity analysis
radon cc services/code-analyzer -a
```

---

## 🚨 CI/CD Integration

### On Pull Request

```bash
# Fast feedback (unit tests only)
pytest tests/unit --cov --cov-fail-under=80
mypy .
pylint .
```

### On Merge

```bash
# Full test suite
pytest tests/ --cov --cov-report=html
```

### Nightly

```bash
# Include performance and security tests
pytest tests/ --cov -m "not slow"
pytest tests/performance -m performance
pytest tests/ -m security
```

---

## 📚 Dependencies

See `requirements-test.txt` for full list. Key dependencies:

- **pytest** - Test framework
- **pytest-cov** - Coverage plugin
- **pytest-asyncio** - Async test support
- **httpx** - HTTP client for API tests
- **faker** - Test data generation
- **factory-boy** - Object factories
- **mypy** - Type checking
- **pylint** - Code linting

Install test dependencies:

```bash
pip install -r requirements-test.txt
```

---

## ✅ Test Infrastructure Checklist

- [x] pytest.ini configured
- [x] conftest.py with comprehensive fixtures
- [x] requirements-test.txt with all dependencies
- [x] Test directory structure (unit/integration/e2e/performance)
- [x] Subdirectories for each layer (domain/application/infrastructure/presentation)
- [x] __init__.py files in all test directories
- [x] Sample fixtures for common test scenarios
- [x] Test markers defined
- [x] Coverage configuration
- [x] CI/CD integration guidelines
- [x] Documentation (this file)

---

## 🎯 Next Steps

1. **Red Phase**: Write failing tests based on test_plan.md
2. **Green Phase**: Implement features to make tests pass
3. **Refactor Phase**: Optimize while maintaining test coverage
4. **Validate**: Ensure 80%+ coverage achieved

---

**Testing Infrastructure Complete**  
**Ready for TDD Implementation** ✅

**Version**: 1.0.0  
**Last Updated**: October 9, 2025  
**Owner**: Hackathon Team

