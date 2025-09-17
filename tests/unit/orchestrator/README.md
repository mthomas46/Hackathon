# Orchestrator Service Unit Tests

Comprehensive test suite for the orchestrator service following Domain-Driven Design principles.

## Test Structure

```
tests/unit/orchestrator/
├── bounded_contexts/                    # Tests organized by bounded context
│   ├── workflow_management/
│   │   ├── domain/                     # Domain layer tests (entities, value objects, services)
│   │   ├── application/                # Application layer tests (use cases)
│   │   └── infrastructure/             # Infrastructure layer tests (repositories)
│   ├── health_monitoring/
│   │   ├── domain/
│   │   └── application/
│   ├── infrastructure/
│   │   ├── domain/                     # Split into value_objects.py and services.py
│   │   ├── application/
│   │   └── infrastructure/
│   ├── ingestion/
│   │   ├── domain/
│   │   └── application/
│   ├── service_registry/
│   │   ├── domain/
│   │   └── application/
│   ├── query_processing/
│   │   ├── domain/
│   │   └── application/
│   └── reporting/
│       ├── domain/
│       └── application/
├── integration/                        # Cross-bounded-context integration tests
│   └── bounded_contexts/
├── shared/                             # Shared test utilities and base classes
│   └── presentation/                   # API endpoint tests
├── conftest.py                         # Shared test fixtures and configuration
├── pytest.ini                          # Pytest configuration with parallel execution
├── run_tests.py                        # Test runner script
└── README.md                           # This file
```

## Running Tests

### Using the Test Runner

The `run_tests.py` script provides convenient commands for running different test suites:

```bash
# Run all tests
python run_tests.py all

# Run only fast tests (exclude slow/integration)
python run_tests.py fast

# Run tests with coverage
python run_tests.py coverage

# Run tests by architectural layer
python run_tests.py domain
python run_tests.py application
python run_tests.py infrastructure

# Run tests by bounded context
python run_tests.py --context workflow_management
python run_tests.py --context health_monitoring --layer domain

# Run integration tests
python run_tests.py integration

# View test structure
python run_tests.py structure
```

### Using Pytest Directly

```bash
# Run all tests with parallel execution
pytest -n auto

# Run specific bounded context
pytest bounded_contexts/workflow_management/ -m "workflow_management"

# Run specific layer
pytest -m "domain"

# Run with coverage
pytest --cov=services.orchestrator --cov-report=html
```

## Test Organization Principles

### 1. **DDD-Aligned Structure**
- Tests are organized by bounded context (domain) and architectural layer
- Each bounded context has its own directory with domain, application, and infrastructure subdirectories
- This mirrors the main service structure for easy navigation

### 2. **DRY (Don't Repeat Yourself)**
- Shared base test classes in `test_base.py` eliminate repetitive test setup
- Common fixtures in `conftest.py` provide reusable test data and mocks
- Helper classes for each bounded context reduce duplication

### 3. **KISS (Keep It Simple, Stupid)**
- Simple, focused test files with clear responsibilities
- Consistent naming and structure across all tests
- Minimal test boilerplate through shared utilities

### 4. **Parallel Execution**
- Tests are designed to run in parallel using pytest-xdist
- Proper fixture scoping prevents resource conflicts
- Markers identify tests that must run sequentially

## Test Categories

### Unit Tests
- **Domain Layer**: Test entities, value objects, and domain services
- **Application Layer**: Test use cases, commands, and queries
- **Infrastructure Layer**: Test repositories and external services

### Integration Tests
- **Bounded Context Integration**: Test interactions between bounded contexts
- **Cross-Layer Integration**: Test data flow between architectural layers

### API Tests
- **Endpoint Tests**: Test FastAPI routes and DTO validation
- **Contract Tests**: Ensure API contracts are maintained

## Writing New Tests

### 1. Choose the Right Location
- Domain tests: `bounded_contexts/{context}/domain/`
- Application tests: `bounded_contexts/{context}/application/`
- Infrastructure tests: `bounded_contexts/{context}/infrastructure/`

### 2. Use Base Classes
```python
from tests.unit.orchestrator.test_base import BaseDomainTest, BaseApplicationTest

class TestMyEntity(BaseDomainTest):
    def get_test_subject(self):
        return MyEntity(...)
```

### 3. Use Shared Fixtures
```python
def test_my_use_case(mock_repository, test_data_factory, ddd_helper):
    # Use shared fixtures for consistent test data
    pass
```

### 4. Add Appropriate Markers
```python
@pytest.mark.workflow_management
@pytest.mark.application
@pytest.mark.parallel_safe
def test_my_use_case():
    pass
```

## Continuous Integration

### Parallel Execution
Tests are configured to run in parallel using pytest-xdist:
- Automatic worker count based on CPU cores
- Proper isolation between test workers
- Resource conflict prevention

### Coverage Requirements
- Minimum 80% code coverage
- HTML and XML coverage reports
- Coverage failure stops the build

### Test Markers
- `unit`: Individual component tests
- `integration`: Cross-component tests
- `slow`: Long-running tests (excluded from fast CI)
- `parallel_safe`: Can run in parallel
- `sequential_only`: Must run sequentially

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure PYTHONPATH includes the project root
2. **Fixture Conflicts**: Use appropriate fixture scoping (`function`, `class`, `module`)
3. **Parallel Execution**: Some tests may need `@pytest.mark.serial` if they conflict
4. **Mock Issues**: Use `AsyncMock` for async methods, regular `Mock` for sync

### Debugging
```bash
# Run single test with debug output
pytest tests/unit/orchestrator/bounded_contexts/workflow_management/domain/test_entities.py::TestWorkflowEntity::test_creation -v -s

# Run with coverage for specific module
pytest --cov=services.orchestrator.domain.workflow_management --cov-report=html
```

## Contributing

When adding new tests:

1. Follow the established directory structure
2. Use shared base classes and fixtures
3. Add appropriate pytest markers
4. Ensure tests can run in parallel
5. Maintain minimum coverage requirements
6. Update this README if adding new patterns or structures
