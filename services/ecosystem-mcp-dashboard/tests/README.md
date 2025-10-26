# Dashboard Test Suite

Comprehensive tests for the Ecosystem MCP Dashboard state management and core functionality.

## Test Coverage

### State Manager Tests (`test_state_manager.py`)

**1. Initialization Tests**
- ✅ Creates all required session state keys
- ✅ Idempotent initialization (doesn't reset data)

**2. Process Tracking Tests**
- ✅ Register new processes
- ✅ Update process status and progress
- ✅ Complete processes successfully
- ✅ Stop running processes

**3. Content Management Tests**
- ✅ Save generated content
- ✅ Filter content by type
- ✅ Remove content

**4. Document Manager Tests**
- ✅ Add documents with metadata
- ✅ Update existing documents
- ✅ Search documents by content/tags

**5. Query Cache Tests**
- ✅ Cache query/answer pairs
- ✅ Find similar cached queries
- ✅ Clear query cache

**6. State Persistence Tests**
- ✅ State survives navigation
- ✅ Export/import state data

**7. Refresh Safety Tests**
- ✅ Active process warnings
- ✅ No warnings when no processes

## Running Tests

### Run all tests:
```bash
cd services/ecosystem-mcp-dashboard
pytest tests/ -v
```

### Run specific test file:
```bash
pytest tests/test_state_manager.py -v
```

### Run specific test class:
```bash
pytest tests/test_state_manager.py::TestProcessTracking -v
```

### Run specific test:
```bash
pytest tests/test_state_manager.py::TestProcessTracking::test_register_process -v
```

### Run with coverage:
```bash
pytest tests/ --cov=utils --cov-report=html
```

## Test Requirements

```bash
pip install pytest pytest-cov streamlit
```

## Test Structure

```
tests/
├── __init__.py
├── README.md
├── test_state_manager.py          # StateManager tests
└── conftest.py                     # Shared fixtures (future)
```

## Future Test Additions

- **UI Widget Tests**: Test Streamlit widget rendering
- **Integration Tests**: Test page navigation and workflows
- **Performance Tests**: Test with large datasets
- **API Integration Tests**: Test dashboard<->backend communication

## Notes

- Tests use pytest fixtures for setup/teardown
- Streamlit session_state is mocked/cleared between tests
- Tests are isolated and can run in any order
- Each test class focuses on a specific component

## Continuous Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# .github/workflows/test.yml
name: Dashboard Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v
```

