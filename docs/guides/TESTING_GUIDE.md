# Testing Guide

## Structure

### Standard Services
- Tests live in `tests/unit/<service>`
- Common config and fixtures: `tests/conftest.py`

### Orchestrator Service (DDD Architecture)
The orchestrator service follows a specialized DDD testing structure:

```
tests/unit/orchestrator/
├── bounded_contexts/           # Tests organized by bounded context
│   ├── workflow_management/
│   │   ├── domain/            # Domain layer tests
│   │   ├── application/       # Application layer tests
│   │   └── infrastructure/    # Infrastructure layer tests
│   ├── service_registry/
│   ├── health_monitoring/
│   ├── infrastructure/
│   ├── ingestion/
│   ├── query_processing/
│   └── reporting/
├── integration/               # Cross-context integration tests
│   └── bounded_contexts/
├── conftest.py               # Orchestrator-specific fixtures
├── pytest.ini               # Test configuration
└── run_tests.py             # Test runner utilities
```

## Running tests

### All Services
```bash
# All tests
pytest -q

# Verbose with short tracebacks
pytest -v --tb=short

# Parallel execution (if pytest-xdist installed)
pytest -n auto
```

### Orchestrator Service (DDD)
```bash
# All orchestrator tests
pytest tests/unit/orchestrator/ -v

# Specific bounded context
pytest tests/unit/orchestrator/bounded_contexts/workflow_management/ -v

# Domain layer only
pytest tests/unit/orchestrator/bounded_contexts/workflow_management/domain/ -v

# Application layer only
pytest tests/unit/orchestrator/bounded_contexts/workflow_management/application/ -v

# Integration tests
pytest tests/unit/orchestrator/integration/ -v

# Quick validation (using run_tests.py)
cd tests/unit/orchestrator && python run_tests.py
```

### Specific Services
```bash
# Standard service tests
pytest tests/unit/interpreter -q
pytest tests/unit/log_collector -q

# Orchestrator bounded context
pytest tests/unit/orchestrator/bounded_contexts/health_monitoring/ -q
```

## Useful markers and plugins
- Markers registered in `pytest.ini` and via `conftest.py` (unit, integration, slow, live, security, etc.)
- Plugins in use: `pytest-timeout`, `pytest-asyncio`, `pytest-xdist` (optional)

## Conventions

### General Testing
- Health checks: always assert `200` and expected JSON keys
- Envelope-aware tests: many endpoints return success envelopes; some return direct data
- Mocks: prefer lightweight async mocks and URL-based branching for service clients

### DDD Testing Patterns
- **Domain Layer**: Test business logic in isolation using value objects and entities
- **Application Layer**: Test use cases with mocked dependencies, verify DomainResult patterns
- **Infrastructure Layer**: Test repositories and external services with in-memory implementations
- **Integration Tests**: Test cross-bounded context workflows and data flow
- **Fixture Usage**: Use DDDTestHelper and TestDataFactory for consistent test data

## Examples

### Standard Service Tests
```bash
# Interpreter tests
pytest tests/unit/interpreter/test_interpreter_intents.py -q

# Log collector tests
pytest tests/unit/log_collector -q
```

### DDD Orchestrator Tests
```bash
# Complete bounded context test suite
pytest tests/unit/orchestrator/bounded_contexts/workflow_management/ -v

# Domain layer testing (entities, value objects)
pytest tests/unit/orchestrator/bounded_contexts/workflow_management/domain/ -v

# Application layer testing (use cases, commands)
pytest tests/unit/orchestrator/bounded_contexts/workflow_management/application/ -v

# Infrastructure layer testing (repositories, services)
pytest tests/unit/orchestrator/bounded_contexts/workflow_management/infrastructure/ -v

# Cross-context integration testing
pytest tests/unit/orchestrator/integration/bounded_contexts/ -v

# Run all orchestrator tests with coverage
pytest tests/unit/orchestrator/ --cov=services.orchestrator --cov-report=html
```

## CI tips
- Ensure Python 3.11+ and install from `services/requirements.base.txt`
- Use `-q` in CI for concise output; add `-v` when diagnosing
- For orchestrator DDD tests, use parallel execution: `pytest tests/unit/orchestrator/ -n auto`
- Run integration tests separately in CI: `pytest tests/unit/orchestrator/integration/`
- Generate coverage reports: `pytest tests/unit/orchestrator/ --cov=services.orchestrator`
