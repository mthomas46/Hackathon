# 🧪 Simulation Dashboard - Testing Suite

A comprehensive testing suite for the **Project Simulation Dashboard Service** that ensures reliability, performance, and user experience quality.

## 📋 Test Overview

### Test Categories

#### 🧩 **Unit Tests** (`tests/unit/`)
- **Configuration Testing**: Environment variables, Pydantic models, validation
- **Client Testing**: HTTP client, WebSocket client, error handling
- **Component Testing**: Individual functions and classes
- **Mock Integration**: Isolated testing with comprehensive mocking

#### 🔗 **Integration Tests** (`tests/integration/`)
- **Service Connectivity**: Real API calls to simulation service
- **WebSocket Communication**: Live WebSocket connection testing
- **Cross-Component Testing**: Multi-component interaction validation
- **Environment Testing**: Docker and deployment integration

#### 🎯 **Functional Tests** (`tests/functional/`)
- **UI Component Testing**: Streamlit component rendering and interaction
- **User Workflow Testing**: End-to-end user journey validation
- **Error Handling**: Graceful failure and recovery testing
- **Performance Testing**: UI responsiveness and load handling

## 🚀 Quick Start

### Prerequisites
```bash
pip install -r requirements.txt
```

### Run All Tests
```bash
# Using the test runner
python test_runner.py

# Or directly with pytest
pytest
```

### Run Specific Test Categories
```bash
# Unit tests only
python test_runner.py --unit
pytest tests/unit/

# Integration tests only
python test_runner.py --integration
pytest tests/integration/

# Functional tests only
python test_runner.py --functional
pytest tests/functional/
```

## 📊 Test Configuration

### Environment Setup
```bash
# Test environment variables
export DASHBOARD_ENVIRONMENT=test
export DASHBOARD_DEBUG=true

# Simulation service (for integration tests)
export DASHBOARD_SIMULATION_SERVICE_HOST=localhost
export DASHBOARD_SIMULATION_SERVICE_PORT=5075
```

### Test Markers
```bash
# Run only WebSocket-related tests
pytest -m websocket

# Run only UI-related tests
pytest -m ui

# Run only slow tests
pytest -m slow

# Skip integration tests
pytest -m "not integration"
```

## 📈 Test Coverage

### Coverage Report
```bash
# Terminal coverage report
python test_runner.py --coverage

# HTML coverage report
python test_runner.py --web
open htmlcov/index.html
```

### Coverage Goals
- **Unit Tests**: >90% coverage
- **Integration Tests**: >80% coverage
- **Functional Tests**: >70% coverage
- **Overall Coverage**: >85% coverage

## 🏗️ Test Structure

### Unit Tests
```
tests/unit/
├── test_config.py          # Configuration validation
├── test_simulation_client.py # HTTP client functionality
├── test_websocket_client.py  # WebSocket client functionality
└── test_*.py              # Additional unit tests
```

### Integration Tests
```
tests/integration/
├── test_simulation_integration.py # Service integration
└── test_*.py                 # Additional integration tests
```

### Functional Tests
```
tests/functional/
├── test_dashboard_ui.py     # UI component testing
└── test_*.py               # Additional functional tests
```

### Test Fixtures
```
tests/conftest.py            # Shared test fixtures and configuration
```

## 🧪 Test Fixtures

### Mock Clients
```python
@pytest.fixture
def mock_simulation_client():
    """Mock simulation service client for testing."""
    client = MagicMock()
    client.get_health = AsyncMock(return_value={"status": "healthy"})
    return client
```

### Mock Configuration
```python
@pytest.fixture
def mock_config():
    """Mock dashboard configuration."""
    config = MagicMock()
    config.simulation_service.host = "localhost"
    config.simulation_service.port = 5075
    return config
```

### Mock Streamlit Context
```python
@pytest.fixture
def mock_streamlit_context():
    """Mock Streamlit context for UI testing."""
    # Comprehensive Streamlit mocking
```

## 🔧 Test Utilities

### Custom Assertions
```python
def assert_simulation_response(response):
    """Assert valid simulation API response."""
    assert "id" in response
    assert "status" in response
    assert response["status"] in ["created", "running", "completed", "failed"]
```

### Test Data Generators
```python
def generate_test_simulation():
    """Generate test simulation data."""
    return {
        "id": f"sim_{random.randint(100, 999)}",
        "name": "Test Simulation",
        "status": "running",
        "progress": random.uniform(0, 100)
    }
```

## 🎯 Test Scenarios

### Unit Test Examples

#### Configuration Testing
```python
def test_environment_variable_loading():
    """Test loading configuration from environment variables."""
    with patch.dict(os.environ, {'DASHBOARD_PORT': '9000'}):
        config = DashboardSettings()
        assert config.port == 9000
```

#### Client Testing
```python
@pytest.mark.asyncio
async def test_simulation_client_health_check():
    """Test simulation client health check."""
    client = SimulationClient(mock_config.simulation_service)

    with patch('aiohttp.ClientSession.get') as mock_get:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.json = AsyncMock(return_value={"status": "healthy"})
        mock_get.return_value = mock_response

        result = await client.get_health()
        assert result["status"] == "healthy"
```

### Integration Test Examples

#### Service Connectivity
```python
@pytest.mark.integration
@pytest.mark.asyncio
async def test_simulation_service_connectivity():
    """Test actual connection to simulation service."""
    client = SimulationClient(config.simulation_service)

    try:
        result = await client.get_health()
        assert "status" in result
    except Exception:
        pytest.skip("Simulation service not available")
```

#### WebSocket Communication
```python
@pytest.mark.integration
@pytest.mark.websocket
@pytest.mark.asyncio
async def test_websocket_message_exchange():
    """Test WebSocket message exchange."""
    client = WebSocketClient(config.websocket)

    try:
        await client.connect("ws://localhost:5075/ws")
        await client.send_message({"type": "ping"})
        response = await client.receive_message()
        assert response["type"] == "pong"
    except Exception:
        pytest.skip("WebSocket server not available")
```

### Functional Test Examples

#### UI Component Testing
```python
@pytest.mark.functional
@pytest.mark.ui
def test_overview_page_rendering():
    """Test overview page renders without errors."""
    with patch('pages.overview.st') as mock_st:
        mock_st.markdown = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock()])

        render_overview_page()

        mock_st.markdown.assert_called()
        mock_st.columns.assert_called()
```

## 🚦 CI/CD Integration

### GitHub Actions Example
```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.13'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run unit tests
        run: python test_runner.py --unit --coverage
      - name: Run integration tests
        run: python test_runner.py --integration
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

### Pre-commit Hooks
```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: run-tests
        name: Run test suite
        entry: python test_runner.py --unit
        language: system
        pass_filenames: false
```

## 📊 Performance Testing

### Load Testing
```bash
# Test concurrent users
pytest tests/functional/test_performance.py -k "load"

# Memory usage testing
pytest tests/functional/test_performance.py -k "memory"
```

### Benchmarking
```python
import time

def benchmark_simulation_creation():
    """Benchmark simulation creation performance."""
    start_time = time.time()

    # Create multiple simulations
    for i in range(100):
        create_simulation(f"bench_sim_{i}")

    end_time = time.time()
    avg_time = (end_time - start_time) / 100

    assert avg_time < 0.5  # Should be under 500ms per simulation
```

## 🐛 Debugging Tests

### Verbose Output
```bash
# Detailed test output
python test_runner.py --verbose

# Debug specific test
pytest tests/unit/test_config.py::TestDashboardSettings::test_environment_variable_loading -v -s
```

### Test Isolation
```bash
# Run single test file
pytest tests/unit/test_config.py

# Run single test function
pytest tests/unit/test_config.py::TestDashboardSettings::test_environment_variable_loading

# Run tests matching pattern
pytest -k "config"
```

### Mock Debugging
```python
# Debug mock calls
mock_client.get_health.assert_called_once_with()
mock_client.get_health.assert_called_with("http://localhost:5075/health")

# Inspect mock return values
print(mock_response.json.return_value)
```

## 📈 Test Metrics & KPIs

### Quality Metrics
- **Test Pass Rate**: >95%
- **Test Execution Time**: <5 minutes
- **Flaky Test Rate**: <2%
- **Test Maintenance Effort**: <10% of development time

### Coverage Metrics
- **Line Coverage**: >85%
- **Branch Coverage**: >80%
- **Function Coverage**: >90%
- **Class Coverage**: >95%

## 🤝 Contributing to Tests

### Test Writing Guidelines
1. **Use descriptive test names**: `test_simulation_creation_success`
2. **Follow AAA pattern**: Arrange, Act, Assert
3. **Use appropriate fixtures**: Minimize setup code
4. **Mock external dependencies**: Keep tests fast and isolated
5. **Test edge cases**: Error conditions and boundary values

### Adding New Tests
```bash
# Create new test file
touch tests/unit/test_new_feature.py

# Add test function
def test_new_feature_functionality():
    """Test new feature works correctly."""
    # Test implementation
    pass
```

### Test Data Management
```python
# Use factories for test data
@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "id": "user_001",
        "name": "Test User",
        "email": "test@example.com"
    }
```

## 🔍 Troubleshooting

### Common Issues

#### Import Errors
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Verify dependencies
pip check

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
```

#### Mock Errors
```bash
# Verify mock setup
pytest --setup-show tests/unit/test_config.py

# Debug mock calls
pytest -v -s tests/unit/test_config.py::TestDashboardSettings::test_environment_variable_loading
```

#### Coverage Issues
```bash
# Check coverage configuration
pytest --cov-config=.coveragerc --cov=. --cov-report=term-missing

# Generate coverage report
python test_runner.py --web
```

## 📚 Resources

### Testing Documentation
- [Pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [pytest-mock](https://pytest-mock.readthedocs.io/)
- [Streamlit Testing](https://docs.streamlit.io/library/advanced-features/testing)

### Best Practices
- [Testing Pyramid](https://martinfowler.com/bliki/TestPyramid.html)
- [Unit Testing Best Practices](https://docs.python.org/3/library/unittest.html)
- [Mock Best Practices](https://docs.python.org/3/library/unittest.mock.html)

---

**🎯 Test Suite Status**: ✅ **COMPLETE & PRODUCTION-READY**

- **Unit Tests**: Comprehensive coverage of all core components
- **Integration Tests**: Real service connectivity validation
- **Functional Tests**: UI component and user workflow testing
- **CI/CD Ready**: Automated testing pipeline integration
- **Performance Testing**: Load and benchmark testing capabilities

**🚀 Ready to ensure dashboard reliability and quality!**
