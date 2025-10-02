# Meta-Orchestrator Test Suite

Comprehensive test suite for the Meta-Orchestration Service, covering unit tests, integration tests, and end-to-end scenarios with high test coverage and automated CI/CD integration.

## 📋 Overview

The test suite ensures the reliability, correctness, and performance of the Meta-Orchestrator service through automated testing at multiple levels.

## 📁 Test Structure

```
tests/
├── __init__.py                      # Test package initialization
├── conftest.py                      # Shared test configuration and fixtures
├── fixtures/                        # Test data and mock fixtures
│   └── docker_compose_fixture.py    # Docker Compose test fixtures
│
├── integration/                     # Integration tests
│   ├── __init__.py
│   ├── test_api_integration.py      # API endpoint integration tests
│   ├── test_audit_features.py       # Audit feature integration tests
│   ├── test_config_modification_api.py # Configuration API tests
│   ├── test_config_modification_workflow.py # Config workflow tests
│   ├── test_dry_run_user_store.py   # Dry-run functionality tests
│   ├── test_monitoring_api.py       # Monitoring API integration tests
│   ├── test_monitoring_integration.py # Monitoring system integration
│   └── test_service_lifecycle.py    # Service lifecycle tests
│
└── unit/                           # Unit tests
    ├── __init__.py
    └── test_*.py                   # Individual component unit tests
        ├── test_config_manager.py  # Configuration manager tests
        ├── test_config_validator.py # Configuration validator tests
        ├── test_docker_manager.py  # Docker manager tests
        └── test_orchestrator.py    # Core orchestrator tests
```

## 🧪 Test Categories

### Unit Tests (`tests/unit/`)

Focused tests for individual components and functions:

```python
# test_config_manager.py
import pytest
from monitoring.config_manager import ServiceConfigManager

class TestServiceConfigManager:
    def test_store_service_config_success(self, config_manager, sample_config):
        """Test successful configuration storage"""
        result = config_manager.store_service_config("test-service", sample_config)
        assert result.success == True
        assert result.config_id is not None

    def test_store_service_config_validation_error(self, config_manager, invalid_config):
        """Test configuration validation error handling"""
        with pytest.raises(ValidationError):
            config_manager.store_service_config("test-service", invalid_config)

    def test_get_service_config_not_found(self, config_manager):
        """Test retrieving non-existent configuration"""
        result = config_manager.get_service_config("nonexistent-service")
        assert result is None
```

### Integration Tests (`tests/integration/`)

End-to-end tests covering component interactions:

```python
# test_service_lifecycle.py
class TestServiceLifecycle:
    @pytest.fixture
    async def orchestrator_with_services(self):
        """Fixture providing orchestrator with test services"""
        orchestrator = MetaOrchestrator()
        await orchestrator.initialize()

        # Start test services
        await orchestrator.start_services(["test-service-1", "test-service-2"])

        yield orchestrator

        # Cleanup
        await orchestrator.stop_all_services()

    async def test_service_start_stop_cycle(self, orchestrator_with_services):
        """Test complete service start/stop lifecycle"""
        orchestrator = orchestrator_with_services

        # Verify services are running
        status = await orchestrator.get_service_status()
        assert len(status) == 2
        assert all(s.status == "running" for s in status.values())

        # Stop one service
        await orchestrator.stop_service("test-service-1")
        status = await orchestrator.get_service_status()
        assert status["test-service-1"].status == "stopped"
        assert status["test-service-2"].status == "running"

        # Restart service
        await orchestrator.start_service("test-service-1")
        status = await orchestrator.get_service_status()
        assert status["test-service-1"].status == "running"
```

### API Integration Tests (`test_api_integration.py`)

Comprehensive API endpoint testing:

```python
# test_api_integration.py
class TestAPIIntegration:
    @pytest.fixture
    def client(self):
        """Test client fixture"""
        from main import app
        return TestClient(app)

    def test_list_services_endpoint(self, client, mock_orchestrator):
        """Test GET /api/v1/services endpoint"""
        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            response = client.get("/api/v1/services")

            assert response.status_code == 200
            data = response.json()
            assert "services" in data
            assert isinstance(data["services"], list)

    def test_service_detail_endpoint(self, client, mock_orchestrator):
        """Test GET /api/v1/services/{name} endpoint"""
        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            response = client.get("/api/v1/services/test-service")

            assert response.status_code == 200
            data = response.json()
            assert data["name"] == "test-service"
            assert "status" in data
            assert "image" in data

    def test_start_service_endpoint(self, client, mock_orchestrator):
        """Test POST /api/v1/services/{name}/start endpoint"""
        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            response = client.post("/api/v1/services/test-service/start")

            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert "operation_id" in data
```

## 🛠️ Test Configuration

### Shared Configuration (`conftest.py`)

Common test fixtures and configuration:

```python
# conftest.py
import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    """FastAPI test client"""
    return TestClient(app)

@pytest.fixture
def mock_orchestrator():
    """Mock orchestrator with common methods"""
    mock = MagicMock()
    mock.get_services = AsyncMock(return_value=[])
    mock.get_service_info = AsyncMock(return_value=None)
    mock.start_service = AsyncMock(return_value=True)
    mock.stop_service = AsyncMock(return_value=True)
    mock.restart_service = AsyncMock(return_value=True)
    return mock

@pytest.fixture
def sample_service_config():
    """Sample service configuration for testing"""
    return {
        "name": "test-service",
        "image": "nginx:alpine",
        "ports": ["80:80"],
        "environment": {"NODE_ENV": "test"},
        "volumes": ["/tmp:/app/data"],
        "restart_policy": "unless-stopped"
    }

@pytest.fixture
def sample_docker_compose():
    """Sample docker-compose configuration"""
    return {
        "version": "3.8",
        "services": {
            "web": {
                "image": "nginx:alpine",
                "ports": ["80:80"],
                "environment": ["NODE_ENV=production"]
            },
            "api": {
                "image": "python:3.11",
                "ports": ["8000:8000"],
                "environment": ["DEBUG=false"]
            }
        }
    }

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

### Test Fixtures (`fixtures/`)

Reusable test data and mock objects:

```python
# fixtures/docker_compose_fixture.py
import pytest
from pathlib import Path
import yaml

@pytest.fixture
def docker_compose_file(tmp_path):
    """Create temporary docker-compose file for testing"""
    compose_content = {
        "version": "3.8",
        "services": {
            "test-service": {
                "image": "nginx:alpine",
                "ports": ["8080:80"],
                "environment": ["TEST=true"]
            }
        }
    }

    compose_file = tmp_path / "docker-compose.yml"
    with open(compose_file, 'w') as f:
        yaml.dump(compose_content, f)

    return compose_file

@pytest.fixture
def mock_docker_client():
    """Mock Docker client for testing"""
    mock_client = MagicMock()
    mock_client.containers.list = MagicMock(return_value=[])
    mock_client.containers.run = MagicMock(return_value=MagicMock())
    mock_client.images.pull = MagicMock(return_value=MagicMock())
    return mock_client
```

## 🏃 Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/integration/test_api_integration.py

# Run specific test class/method
pytest tests/unit/test_config_manager.py::TestServiceConfigManager::test_store_service_config_success

# Run tests with coverage
pytest --cov=services/meta-orchestrator --cov-report=html --cov-report=term

# Run tests in parallel (requires pytest-xdist)
pytest -n auto

# Run tests with different markers
pytest -m "integration and not slow"
pytest -m "unit"
```

### Test Configuration Options

```ini
# pytest.ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --strict-markers
    --strict-config
    --cov=services/meta-orchestrator
    --cov-report=html
    --cov-report=term
    --cov-fail-under=85
markers =
    unit: Unit tests
    integration: Integration tests
    slow: Slow running tests
    docker: Tests requiring Docker
    api: API endpoint tests
asyncio_mode = auto
```

### CI/CD Integration

```yaml
# .github/workflows/test.yml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          cd services/meta-orchestrator
          pip install -r requirements.txt -r test-requirements.txt

      - name: Run unit tests
        run: |
          cd services/meta-orchestrator
          pytest tests/unit/ -v --cov --cov-report=xml

      - name: Run integration tests
        run: |
          cd services/meta-orchestrator
          pytest tests/integration/ -v --cov-append --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: services/meta-orchestrator/coverage.xml
```

## 📊 Test Coverage

### Coverage Requirements

- **Unit Tests**: 90%+ coverage for core business logic
- **Integration Tests**: 80%+ coverage for API endpoints and workflows
- **End-to-End Tests**: Critical user journeys covered

### Coverage Configuration

```ini
# .coveragerc
[run]
source = services/meta-orchestrator
omit =
    */tests/*
    */venv/*
    */__pycache__/*
    setup.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
    if __name__ == .__main__.:
    class .*\bProtocol\):
    @(abc\.)?abstractmethod

[html]
directory = htmlcov
```

### Coverage Report Analysis

```bash
# Generate coverage report
pytest --cov=services/meta-orchestrator --cov-report=html

# View coverage gaps
coverage report --show-missing

# Check coverage for specific module
coverage report --include="services/meta-orchestrator/api/*"
```

## 🧩 Mocking & Fixtures

### Advanced Mocking

```python
# tests/integration/test_monitoring_integration.py
from unittest.mock import patch, MagicMock, AsyncMock
import pytest

class TestMonitoringIntegration:
    @pytest.fixture
    async def mock_monitoring_service(self):
        """Mock monitoring service with realistic behavior"""
        mock_service = MagicMock()

        # Mock health check results
        mock_service.check_all_services_health = AsyncMock(return_value={
            "web-frontend": HealthResult(
                service_name="web-frontend",
                healthy=True,
                response_time=0.15,
                status_code=200,
                error=None
            ),
            "api-backend": HealthResult(
                service_name="api-backend",
                healthy=False,
                response_time=2.5,
                status_code=500,
                error="Internal server error"
            )
        })

        # Mock drift detection
        mock_service.detect_configuration_drift = AsyncMock(return_value={
            "success": True,
            "total_issues": 2,
            "high_severity": 1,
            "issues": [
                {
                    "type": "port_mismatch",
                    "severity": "high",
                    "description": "Port mapping differs between compose and runtime"
                }
            ]
        })

        return mock_service

    async def test_monitoring_integration_workflow(self, mock_monitoring_service):
        """Test complete monitoring workflow"""
        # Simulate monitoring cycle
        health_results = await mock_monitoring_service.check_all_services_health()
        drift_results = await mock_monitoring_service.detect_configuration_drift()

        # Verify results
        assert len(health_results) == 2
        assert health_results["web-frontend"].healthy == True
        assert health_results["api-backend"].healthy == False

        assert drift_results["success"] == True
        assert drift_results["total_issues"] == 2
        assert len(drift_results["issues"]) == 1
```

### Docker Mocking

```python
# Mock Docker client for testing
@pytest.fixture
def mock_docker_client():
    """Mock Docker client with realistic container data"""
    mock_client = MagicMock()

    # Mock container list
    mock_container = MagicMock()
    mock_container.name = "test-service"
    mock_container.status = "running"
    mock_container.ports = {"80/tcp": [{"HostPort": "8080"}]}
    mock_container.attrs = {
        "Config": {
            "Image": "nginx:alpine",
            "Env": ["NODE_ENV=test", "PORT=80"]
        }
    }

    mock_client.containers.list = MagicMock(return_value=[mock_container])
    return mock_client
```

## 🔄 Test Data Management

### Test Database Setup

```python
# tests/conftest.py
@pytest.fixture
async def test_database():
    """Create test database with clean state"""
    # Create in-memory SQLite database for tests
    conn = sqlite3.connect(":memory:")
    db_manager = DatabaseManager(connection=conn)

    # Create tables
    db_manager.create_tables()

    # Insert test data
    await db_manager.insert_test_data()

    yield db_manager

    # Cleanup
    conn.close()
```

### Test Configuration Files

```python
@pytest.fixture
def temp_config_file(tmp_path):
    """Create temporary configuration file"""
    config_data = {
        "server": {
            "host": "0.0.0.0",
            "port": 8080,
            "debug": True
        },
        "database": {
            "url": "postgresql://test:test@localhost/test"
        }
    }

    config_file = tmp_path / "config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config_data, f)

    return config_file
```

## 🚨 Test Error Handling

### Expected Exceptions

```python
def test_invalid_service_name(client):
    """Test handling of invalid service names"""
    response = client.get("/api/v1/services/invalid@service")

    assert response.status_code == 422  # Validation error
    data = response.json()
    assert "detail" in data
```

### Async Error Handling

```python
async def test_service_timeout(mock_orchestrator):
    """Test handling of service operation timeouts"""
    mock_orchestrator.start_service = AsyncMock(side_effect=asyncio.TimeoutError())

    with pytest.raises(asyncio.TimeoutError):
        await mock_orchestrator.start_service("slow-service")
```

### Network Error Simulation

```python
def test_api_network_error(client, mock_orchestrator):
    """Test API behavior during network errors"""
    mock_orchestrator.get_services = AsyncMock(side_effect=httpx.ConnectError("Connection failed"))

    response = client.get("/api/v1/services")

    assert response.status_code == 503  # Service unavailable
    data = response.json()
    assert "detail" in data
    assert "Connection failed" in data["detail"]
```

## 📈 Performance Testing

### Load Testing

```python
# tests/integration/test_performance.py
import asyncio
import time
from concurrent.futures import ThreadPoolExecutor

class TestPerformance:
    def test_api_concurrent_requests(self, client):
        """Test API performance under concurrent load"""
        def make_request():
            return client.get("/api/v1/services")

        # Test with 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            start_time = time.time()
            futures = [executor.submit(make_request) for _ in range(10)]
            responses = [f.result() for f in futures]
            end_time = time.time()

        # Verify all requests succeeded
        assert all(r.status_code == 200 for r in responses)

        # Check response time
        total_time = end_time - start_time
        avg_response_time = total_time / 10
        assert avg_response_time < 1.0  # Should respond within 1 second
```

### Memory Leak Testing

```python
def test_memory_usage_growth(client):
    """Test for memory leaks during repeated operations"""
    import psutil
    import os

    process = psutil.Process(os.getpid())
    initial_memory = process.memory_info().rss

    # Perform 100 operations
    for _ in range(100):
        response = client.get("/api/v1/services")
        assert response.status_code == 200

    final_memory = process.memory_info().rss
    memory_growth = final_memory - initial_memory

    # Memory growth should be minimal (< 10MB)
    assert memory_growth < 10 * 1024 * 1024
```

## 🔧 Test Utilities

### Custom Test Assertions

```python
# tests/test_utils.py
def assert_service_config_equal(actual, expected):
    """Assert that two service configurations are equivalent"""
    # Normalize configurations for comparison
    normalized_actual = normalize_config(actual)
    normalized_expected = normalize_config(expected)

    assert normalized_actual == normalized_expected

def assert_api_response_format(response, expected_fields):
    """Assert API response has expected structure"""
    data = response.json()
    for field in expected_fields:
        assert field in data, f"Missing field: {field}"

def assert_health_status(health_result, expected_status):
    """Assert health check result status"""
    assert health_result.healthy == (expected_status == "healthy")
    if expected_status == "healthy":
        assert health_result.response_time < 1.0
        assert health_result.status_code == 200
    else:
        assert health_result.error is not None
```

### Test Data Builders

```python
# tests/builders.py
class ServiceConfigBuilder:
    """Builder for creating test service configurations"""

    def __init__(self):
        self.config = {
            "name": "test-service",
            "image": "nginx:alpine",
            "ports": [],
            "environment": {},
            "volumes": []
        }

    def with_name(self, name):
        self.config["name"] = name
        return self

    def with_ports(self, *ports):
        self.config["ports"] = list(ports)
        return self

    def with_env(self, **env_vars):
        self.config["environment"].update(env_vars)
        return self

    def build(self):
        return self.config.copy()

# Usage
config = ServiceConfigBuilder() \
    .with_name("web-service") \
    .with_ports("80:80", "443:443") \
    .with_env(NODE_ENV="production", DEBUG="false") \
    .build()
```

## 📋 Test Documentation

### Test Case Naming Convention

```
test_[component]_[action]_[expected_result]
```

Examples:
- `test_api_list_services_returns_200`
- `test_monitoring_health_check_detects_failures`
- `test_config_drift_detector_finds_port_mismatches`

### Test Documentation Standards

```python
def test_service_start_with_dependencies():
    """
    Test that starting a service also starts its dependencies.

    This test verifies the dependency resolution logic in the orchestrator
    by ensuring that when a service with dependencies is started, all
    required dependencies are also started in the correct order.

    Dependencies tested:
    - Database services start before API services
    - Message queue services start before workers
    - Load balancers start after backend services
    """
    # Test implementation
    pass
```

## 🎯 Test Quality Metrics

### Test Quality Checklist

- [ ] **Coverage**: >85% code coverage
- [ ] **Performance**: Tests run within reasonable time limits
- [ ] **Isolation**: Tests don't depend on external state
- [ ] **Documentation**: All tests have clear docstrings
- [ ] **Maintainability**: Tests are easy to understand and modify
- [ ] **Reliability**: Tests are deterministic and don't flake

### Continuous Integration

```yaml
# CI pipeline with quality gates
test:
  stage: test
  script:
    - pytest --cov --cov-fail-under=85
    - black --check .
    - isort --check-only .
    - mypy .
  coverage: '/TOTAL.*\s+(\d+%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml
    expire_in: 1 week
```

This comprehensive test suite ensures the Meta-Orchestrator service maintains high quality, reliability, and performance through automated testing at all levels.
