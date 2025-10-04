# Integration Tests for Expert Finder Service

This directory contains integration tests for the Expert Finder Service API endpoints and their integration with other services in the ecosystem.

## Overview

These tests verify:
- ✅ All 6 REST API endpoints of expert-finder-service
- ✅ Integration with user-store, doc-store, external-service-store
- ✅ Relevance scoring algorithm
- ✅ Team filtering functionality
- ✅ Error handling (400, 404, 500)
- ✅ Performance characteristics
- ✅ Concurrent request handling

## Test Coverage

### Test Files
- `test_expert_finder_api.py` - 24 integration tests

### Test Classes

1. **TestHealthEndpoint** (2 tests)
   - Health check returns 200
   - Health check includes dependency URLs

2. **TestNaturalLanguageExpertSearch** (7 tests)
   - Basic query functionality
   - max_results parameter
   - min_score filtering
   - Team filtering (include/exclude)
   - Relevance scoring validation
   - Results sorted by score

3. **TestTopicBasedSearch** (2 tests)
   - Find experts by topic
   - max_results parameter

4. **TestServiceBasedSearch** (1 test)
   - Find experts by service

5. **TestSMESearch** (2 tests)
   - Find SMEs in area
   - Minimum document threshold

6. **TestTeammateDiscovery** (1 test)
   - Find potential teammates

7. **TestTeamExpertise** (1 test)
   - Get team expertise summary

8. **TestErrorHandling** (4 tests)
   - Empty query
   - Invalid parameters
   - Non-existent endpoints

9. **TestPerformance** (2 tests)
   - Response time validation
   - Concurrent requests

10. **TestUserStoreIntegration** (2 tests)
    - Expert-finder queries user-store
    - Expert metadata from user-store

## Prerequisites

### Required Services

The following services must be running:

- **expert-finder-service** (port 5160) - PRIMARY
- **user-store** (port 5150) - REQUIRED
- **doc-store** (port 5087) - optional
- **external-service-store** (port 5140) - optional

### Check Service Status

```bash
# Check if services are running
python3 tests/integration/check_services.py
```

### Start Services

```bash
# Start all services
docker-compose -f docker-compose.dev.yml up -d

# Or start specific services only
docker-compose -f docker-compose.dev.yml up -d expert-finder-service user-store

# Verify services are healthy
python3 tests/integration/check_services.py
```

## Running Integration Tests

### Run All Integration Tests

```bash
pytest tests/integration/ -v -m integration
```

### Run Specific Test Class

```bash
pytest tests/integration/test_expert_finder_api.py::TestNaturalLanguageExpertSearch -v
```

### Run Specific Test

```bash
pytest tests/integration/test_expert_finder_api.py::TestHealthEndpoint::test_health_check_returns_200 -v
```

### Run with Performance Tests

```bash
# Include slow/performance tests
pytest tests/integration/ -v -m "integration or slow"
```

### Skip Integration Tests

```bash
# Skip integration tests (run only unit tests)
pytest tests/ -v -m "not integration"
```

## Test Markers

Integration tests use pytest markers for organization:

- `@pytest.mark.integration` - Integration test (requires services)
- `@pytest.mark.slow` - Slow test (performance/load tests)
- `@pytest.mark.asyncio` - Async test (uses httpx.AsyncClient)

## Test Data

### Fixtures

- `sample_expert_query` - Basic expert search query
- `sample_expert_query_with_team` - Query with team filter
- `sample_users_for_testing` - Test user data
- `create_test_users` - Creates/cleans up test users
- `performance_thresholds` - Performance benchmarks

### Test Users

Integration tests may create temporary test users in user-store:
- `test.user.001` - Python backend developer
- `test.user.002` - React frontend developer  
- `test.user.003` - Database developer

These are automatically cleaned up after tests complete.

## Expected Behavior

### When Services Are Running

Tests will execute and validate:
- ✅ API endpoints respond correctly
- ✅ Relevance scoring works
- ✅ Team filtering applies correctly
- ✅ Error handling is robust
- ✅ Performance meets thresholds

### When Services Are Not Running

Tests will be **automatically skipped**:
```
tests/integration/test_expert_finder_api.py::TestHealthEndpoint::test_health_check_returns_200 SKIPPED
```

This allows integration tests to coexist with unit tests without requiring services.

## Performance Benchmarks

Expected performance characteristics:

| Operation              | Target    | Acceptable |
|------------------------|-----------|------------|
| Health check           | < 50ms    | < 100ms    |
| Expert search          | < 500ms   | < 1000ms   |
| Topic search           | < 300ms   | < 500ms    |
| SME search             | < 500ms   | < 1000ms   |
| Concurrent requests    | All succeed | N/A      |

## Troubleshooting

### Services Not Running

```bash
# Check service status
python3 tests/integration/check_services.py

# Start services
docker-compose -f docker-compose.dev.yml up -d

# Check logs if service fails to start
docker-compose -f docker-compose.dev.yml logs expert-finder-service
```

### Connection Errors

If you see `httpx.ConnectError`:
1. Verify services are running: `docker-compose ps`
2. Check port availability: `lsof -i :5160`
3. Verify Docker network: `docker network ls | grep hackathon`

### Test Failures

If tests fail unexpectedly:
1. Check service logs for errors
2. Verify test data in user-store
3. Check network connectivity
4. Restart services and retry

### No Test Data

If expert searches return no results:
1. Populate user-store with test data
2. Run demo script: `python3 demo_hyper_realistic_parameterized.py`
3. Or create test users manually via user-store API

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      user-store:
        image: user-store:latest
        ports:
          - 5150:5150
      
      expert-finder:
        image: expert-finder-service:latest
        ports:
          - 5160:5160
    
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Check services
        run: python3 tests/integration/check_services.py
      
      - name: Run integration tests
        run: pytest tests/integration/ -v -m integration
```

## Contributing

When adding new integration tests:

1. Use `@pytest.mark.integration` marker
2. Handle `httpx.ConnectError` with `pytest.skip()`
3. Clean up test data in fixtures
4. Document expected behavior
5. Add to appropriate test class
6. Update this README if adding new test class

## Next Steps

- **Phase 2.2**: Add functional performance tests
- **Phase 3**: Integrate Workflow F into demo script
- **Phase 4**: Integrate expert-finder into planning service
- **Phase 5**: Enhance reports with SME sections

## References

- [Expert Finder Service README](../../services/expert-finder-service/README.md)
- [Workflow F Development Tracker](../../WORKFLOW_F_DEVELOPMENT_TRACKER.md)
- [Testing Guide](../../TESTING_GUIDE.md)

