# Timeline Analysis Test Suite

## Overview

Comprehensive test suite for Timeline Analysis features (Phases 1-3).

## Test Structure

```
tests/
├── unit/                          # Unit tests (fast, isolated)
│   ├── models/                    # Pydantic model tests
│   │   └── test_timeline_models.py
│   ├── services/
│   │   ├── timeline/              # Timeline service tests
│   │   │   ├── test_confidence_calculator.py
│   │   │   ├── test_timeline_manager.py
│   │   │   ├── test_gap_analyzer.py
│   │   │   └── test_drift_detector.py
│   │   ├── rag/                   # RAG service tests
│   │   │   └── test_temporal_rag.py
│   │   └── maintenance/           # Maintenance service tests
│   │       ├── test_staleness_detector.py
│   │       ├── test_coverage_analyzer.py
│   │       ├── test_quality_dashboard.py
│   │       └── test_export_service.py
│
├── integration/                   # Integration tests (require services)
│   ├── api/                       # API endpoint tests
│   │   ├── test_timeline_api.py
│   │   ├── test_temporal_rag_api.py
│   │   ├── test_maintenance_api.py
│   │   └── test_analysis_api.py
│   └── services/                  # Service integration tests
│       └── test_service_workflows.py
│
├── e2e/                          # End-to-end tests (full workflows)
│   └── test_complete_workflow.py
│
└── smoke/                        # Smoke tests (quick validation)
    └── test_timeline_phase1.py
```

## Running Tests

### All Tests
```bash
pytest
```

### By Test Type
```bash
# Unit tests only (fast)
pytest -m unit

# Integration tests
pytest -m integration

# E2E tests
pytest -m e2e

# Smoke tests
pytest -m smoke
```

### By Module
```bash
# Timeline tests
pytest tests/unit/services/timeline/

# API tests
pytest tests/integration/api/

# Specific file
pytest tests/unit/models/test_timeline_models.py
```

### With Coverage
```bash
# Run with coverage report
pytest --cov=src --cov-report=html

# View coverage in browser
open htmlcov/index.html
```

### Verbose Output
```bash
pytest -v
pytest -vv  # Extra verbose
```

## Test Markers

Tests are marked for easy filtering:

- `@pytest.mark.unit` - Fast, isolated unit tests
- `@pytest.mark.integration` - Requires running services
- `@pytest.mark.e2e` - Full workflow tests
- `@pytest.mark.smoke` - Quick smoke tests
- `@pytest.mark.slow` - Tests that take >1s

## Test Coverage Goals

| Component | Target | Current |
|-----------|--------|---------|
| Services | 90%+ | TBD |
| Models | 95%+ | TBD |
| API Routes | 85%+ | TBD |
| Overall | 90%+ | TBD |

## Writing Tests

### Unit Test Example
```python
import pytest
from src.services.timeline import TimelineManager

@pytest.mark.unit
async def test_timeline_creation():
    manager = TimelineManager()
    # Test logic here
    assert manager is not None
```

### Integration Test Example
```python
import pytest
from httpx import AsyncClient

@pytest.mark.integration
async def test_api_endpoint(client: AsyncClient):
    response = await client.get("/api/v1/timelines")
    assert response.status_code == 200
```

### E2E Test Example
```python
import pytest

@pytest.mark.e2e
async def test_complete_workflow(client):
    # 1. Create timeline
    # 2. Generate periods
    # 3. Query
    # 4. Validate
    pass
```

## Test Fixtures

Common fixtures available:

- `client` - Async HTTP client for API tests
- `db_session` - Database session for integration tests
- `mock_documents` - Sample document data
- `mock_timeline` - Sample timeline data

## Continuous Integration

Tests run automatically on:
- Pull requests
- Main branch commits
- Scheduled nightly runs

## Troubleshooting

### Import Errors
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=/path/to/services/ecosystem-mcp:$PYTHONPATH
```

### Database Errors
```bash
# Ensure database is running
docker-compose up postgres

# Run migrations
alembic upgrade head
```

### Async Errors
```bash
# Ensure pytest-asyncio is installed
pip install pytest-asyncio
```

## Contributing

When adding new features:
1. Write unit tests first (TDD)
2. Add integration tests for APIs
3. Update E2E tests for workflows
4. Ensure 90%+ coverage

## Resources

- [pytest documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-cov](https://pytest-cov.readthedocs.io/)

