# LLM Documentation Ecosystem - Testing Framework

## Overview

This comprehensive testing framework provides unit, integration, and live functional testing with realistic business data and enterprise-grade features for the LLM Documentation Ecosystem.

## Quick Start

```bash
# Run all tests
pytest

# Run specific test types
pytest -m "unit"           # Fast unit tests
pytest -m "integration"    # Cross-service integration
pytest -m "functional"     # Live service testing

# Run with performance monitoring
pytest --performance

# Generate comprehensive report
pytest --html=report.html --self-contained-html
```

## Architecture

### Core Modules

1. **conftest.py** - Unified test configuration (351 lines)
2. **core_testing.py** - Assertions, mocking, utilities (751 lines)
3. **data_validation.py** - Data generation and validation (653 lines)
4. **performance_security.py** - Performance and security testing (732 lines)
5. **reporting_analytics.py** - Test reporting and analytics (863 lines)

**Total: 3,350 lines** - 70% reduction from previous 11,000+ lines

### Test Categories

- **Unit Tests** - Isolated component testing
- **Integration Tests** - Cross-service interaction testing
- **Functional Tests** - Live service testing with real data
- **Performance Tests** - Load and stress testing
- **Security Tests** - Vulnerability and authentication testing

## Realistic Business Data

### Users & Authentication

```python
# Developer user with realistic attributes
user = sample_user()
# {
#   "id": "user_123",
#   "email": "john.doe@company.com",
#   "name": "John Doe",
#   "role": "developer",
#   "department": "engineering"
# }

# Authentication tokens for testing
tokens = auth_tokens()
# {"valid": "eyJ...", "expired": "eyJ...", "invalid": "invalid"}
```

### Code Repositories

```python
# GitHub repository with realistic metrics
repo = sample_repository()
# {
#   "name": "api-service",
#   "full_name": "company/api-service",
#   "language": "Python",
#   "stars": 45,
#   "issues": 8,
#   "description": "REST API for e-commerce"
# }
```

### Issue Tracking

```python
# Jira issue with business workflow
ticket = sample_jira_ticket()
# {
#   "key": "PROJ-123",
#   "summary": "Implement user authentication API",
#   "status": "In Progress",
#   "assignee": "john.doe@company.com",
#   "priority": "High"
# }
```

### Documentation Content

```python
# Confluence page with realistic content
page = sample_confluence_page()
# {
#   "title": "API Authentication Guide",
#   "content": "<h1>Authentication</h1><p>JWT tokens...</p>",
#   "version": {"number": 3},
#   "space": {"name": "Developer Docs"}
# }
```

### Business Workflows

```python
# Complete workflow orchestration
workflow = sample_workflow()
# {
#   "name": "Content Analysis Pipeline",
#   "steps": [
#     {"type": "source_agent", "config": {"source": "github"}},
#     {"type": "analysis_service", "config": {"depth": "full"}},
#     {"type": "doc_store", "config": {"compression": True}}
#   ]
# }
```

## Test Patterns

### Unit Testing

```python
def test_user_validation():
    """Test user data validation."""
    user = sample_user()

    # Validate required fields
    assert user["email"]
    assert user["role"] in ["developer", "manager", "analyst"]

    # Validate business rules
    assert "@" in user["email"]
    assert len(user["name"]) > 0
```

### Integration Testing

```python
def test_workflow_execution(orchestrator_client, doc_store_client):
    """Test complete workflow execution."""
    workflow = sample_workflow()

    # Submit workflow
    response = orchestrator_client.post("/workflows", json=workflow)
    assert response.status_code == 201

    workflow_id = response.json()["id"]

    # Verify workflow stored
    stored = doc_store_client.get(f"/workflows/{workflow_id}")
    assert stored.status_code == 200
    assert stored.json()["status"] == "active"
```

### Functional Testing

```python
def test_live_document_analysis(orchestrator_client, sample_documentation):
    """Test live document analysis with real services."""
    # Submit document for analysis
    response = orchestrator_client.post("/analyze", json={
        "document": sample_documentation,
        "analysis_type": "comprehensive"
    })

    assert response.status_code == 200
    result = response.json()

    # Verify analysis quality
    assert "entities" in result
    assert "sentiment" in result
    assert result["confidence"] > 0.8
```

## Assertions & Validation

### HTTP Assertions

```python
from core_testing import HTTPAssertions

def test_api_endpoints(orchestrator_client):
    response = orchestrator_client.get("/health")

    HTTPAssertions.assert_status(response, 200)
    HTTPAssertions.assert_json_structure(response, ["status", "version", "uptime"])
    HTTPAssertions.assert_response_time(response, max_time=0.5)
```

### Data Validation

```python
from data_validation import DataValidationFramework

def test_workflow_schema_validation():
    validator = DataValidationFramework()

    workflow = sample_workflow()
    schema = {
        "type": "object",
        "required": ["name", "steps"],
        "properties": {
            "steps": {"type": "array", "minItems": 1}
        }
    }

    result = validator.validate_data(workflow, "workflow_schema")
    assert result["valid"], result["errors"]
```

## Mocking Strategies

### Service Mocking

```python
from core_testing import UnifiedMockingFramework

def test_with_mocked_services():
    mock_framework = UnifiedMockingFramework()

    with mock_framework.mock_http_client():
        # Test external API calls
        result = call_external_service()
        assert result["status"] == "success"
```

### Database Mocking

```python
def test_database_operations():
    with mock_framework.mock_database():
        # Test database interactions
        user = create_user(sample_user())
        assert user["id"] is not None
```

## Performance Testing

### Load Testing

```python
from performance_security import PerformanceTestingFramework

def test_api_under_load(orchestrator_client):
    framework = PerformanceTestingFramework()

    results = framework.load_test(
        operation=lambda: orchestrator_client.get("/health"),
        concurrent_users=50,
        duration_seconds=60
    )

    assert results.success_rate > 0.95
    assert results.avg_response_time < 0.5
```

### Stress Testing

```python
def test_system_limits(orchestrator_client):
    results = framework.stress_test(
        operation=lambda: orchestrator_client.post("/workflows", json=sample_workflow()),
        max_concurrent_users=100,
        duration_per_level=30
    )

    # System should degrade gracefully
    assert results[-1].success_rate > 0.7  # At least 70% success at peak load
```

## Security Testing

### Input Validation

```python
from performance_security import SecurityTestingFramework

def test_security_boundaries():
    security_framework = SecurityTestingFramework()

    malicious_inputs = [
        "' OR '1'='1",  # SQL injection
        "<script>alert('xss')</script>",  # XSS
        "../../../etc/passwd",  # Path traversal
        "A" * 10000  # Buffer overflow attempt
    ]

    for malicious_input in malicious_inputs:
        result = security_framework.test_input_validation(malicious_input)
        assert len(result["vulnerabilities"]) > 0, f"Missed vulnerability in: {malicious_input}"
```

### Authentication Testing

```python
def test_authentication_flow(orchestrator_client, auth_tokens):
    # Test valid authentication
    from tests.helpers.clients import request_with_defaults
    response = request_with_defaults(orchestrator_client, "get", "/protected", auth_token=auth_tokens['valid'])
    assert response.status_code == 200

    # Test expired token
    response = request_with_defaults(orchestrator_client, "get", "/protected", auth_token=auth_tokens['expired'])
    assert response.status_code == 401
```

## Error Scenarios

### Realistic Error Testing

```python
from performance_security import ErrorScenarioFramework

def test_error_recovery(orchestrator_client):
    error_framework = ErrorScenarioFramework()

    @error_framework.simulate_error_scenario("database_failure")
    def operation_with_failure():
        return orchestrator_client.post("/workflows", json=sample_workflow())

    # Test should handle database failure gracefully
    with pytest.raises(Exception) as exc_info:
        operation_with_failure()

    assert "database" in str(exc_info.value).lower()
```

## Test Execution Optimization

### Intelligent Test Selection

```python
from reporting_analytics import TestExecutionOptimizer

def test_execution_plan():
    optimizer = TestExecutionOptimizer()

    test_suite = [
        {"id": "user_validation", "type": "unit", "estimated_duration": 0.1},
        {"id": "workflow_integration", "type": "integration", "estimated_duration": 2.0},
        {"id": "live_analysis", "type": "functional", "estimated_duration": 5.0}
    ]

    plan = optimizer.optimize_execution_plan(test_suite)

    assert plan["estimated_duration"] < 12  # Should be optimized from 7.1s
    assert len(plan["batches"]) <= 3  # Should be batched efficiently
```

### Parallel Execution

```python
from reporting_analytics import ParallelTestExecutor

def test_parallel_execution():
    executor = ParallelTestExecutor(max_workers=4)

    test_functions = [
        lambda: test_user_creation(),
        lambda: test_workflow_validation(),
        lambda: test_document_analysis()
    ]

    results = executor.execute_parallel(test_functions)

    successful = sum(1 for r in results if r["status"] == "passed")
    assert successful == len(results)  # All should pass
```

## Reporting & Analytics

### Comprehensive Reports

```python
from reporting_analytics import EnhancedReportingFramework

def test_reporting_system():
    reporting = EnhancedReportingFramework()

    # Generate different report formats
    json_report = reporting.generate_report("json")
    html_report = reporting.generate_report("html")

    report_data = json.loads(json_report)
    assert "summary" in report_data
    assert report_data["summary"]["total"] > 0
```

## Best Practices

### Test Organization

1. **Unit Tests**: `< 0.1s`, no external dependencies
2. **Integration Tests**: `0.1-2s`, test component interactions
3. **Functional Tests**: `2-10s`, test complete workflows
4. **Performance Tests**: `10-60s`, validate system limits

### Naming Conventions

```python
# ✅ Good
def test_user_creation_with_valid_data():
def test_workflow_execution_timeout_handling():
def test_api_rate_limiting_under_high_load():

# ❌ Avoid
def test_user():
def test_workflow():
def test_api():
```

### Fixture Usage

```python
@pytest.fixture
def authenticated_client(orchestrator_client, valid_jwt):
    """Authenticated client for protected endpoints."""
    from tests.helpers.clients import build_request_kwargs
    kwargs = build_request_kwargs(auth_token=valid_jwt)
    # Example usage in tests: orchestrator_client.get("/admin/users", **kwargs)
    return orchestrator_client

def test_protected_operations(authenticated_client):
    response = authenticated_client.get("/admin/users")
    assert response.status_code == 200
```

## CI/CD Integration

```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: [3.8, 3.9, "3.10"]

    steps:
    - uses: actions/checkout@v3
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt

    - name: Run unit tests
      run: pytest -m "unit" --cov=services --cov-report=xml

    - name: Run integration tests
      run: pytest -m "integration"

    - name: Run functional tests
      run: pytest -m "functional"

    - name: Run performance tests
      run: pytest -m "performance"

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Performance Optimization

### Session-Scoped Fixtures

```python
@pytest.fixture(scope="session")
def database_connection():
    """Expensive database connection - created once per session."""
    conn = create_db_connection()
    yield conn
    conn.close()
```

### Parametrization

```python
@pytest.mark.parametrize("user_role,expected_status", [
    ("admin", 200),
    ("user", 403),
    ("guest", 401)
])
def test_role_based_access(orchestrator_client, user_role, expected_status):
    # Test access control for different roles
    pass
```

This framework provides comprehensive testing capabilities with realistic business data, ensuring the LLM Documentation Ecosystem maintains high quality and reliability across all components and workflows.

## Per-Service Run Guide

### Orchestrator
```bash
# Mocked (fast)
pytest tests/services/orchestrator -m "not slow and not live" -n auto
# Integration (no containers)
pytest tests/services/orchestrator -m integration -n auto
# Live (containers)
python tests/test_runner.py live orchestrator
```

### Doc Store
```bash
pytest tests/services/doc_store -m "not slow and not live" -n auto
pytest tests/services/doc_store -m integration -n auto
python tests/test_runner.py live doc-store
```

### Source Agent
```bash
pytest tests/services/source_agent -m "not slow and not live" -n auto
pytest tests/services/source_agent -m integration -n auto
python tests/test_runner.py live source-agent
```

### Analysis Service
```bash
pytest tests/services/analysis_service -m "not slow and not live" -n auto
pytest tests/services/analysis_service -m integration -n auto
python tests/test_runner.py live analysis-service
```

### Frontend
```bash
pytest tests/services/frontend -m "not slow and not live" -n auto
pytest tests/services/frontend -m integration -n auto
python tests/test_runner.py live frontend
```
