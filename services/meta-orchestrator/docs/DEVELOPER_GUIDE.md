# Meta-Orchestrator Developer Guide

Comprehensive guide for developers working with or extending the Meta-Orchestration Service.

## 📋 Table of Contents

- [Getting Started](#getting-started)
- [Development Environment](#development-environment)
- [Project Structure](#project-structure)
- [Adding New Endpoints](#adding-new-endpoints)
- [Extending Monitoring](#extending-monitoring)
- [Custom Validators](#custom-validators)
- [Database Schema](#database-schema)
- [Testing Strategy](#testing-strategy)
- [Code Quality](#code-quality)
- [Contributing Guidelines](#contributing-guidelines)
- [Troubleshooting](#troubleshooting)

## 🚀 Getting Started

### Prerequisites

```bash
# Required software
Python 3.11+
Docker 20.10+
Docker Compose 2.0+
Git

# Recommended tools
poetry          # Dependency management
pre-commit      # Git hooks
docker-compose  # Local development
pytest          # Testing
black           # Code formatting
isort           # Import sorting
mypy            # Type checking
```

### Quick Setup

```bash
# Clone the repository
git clone <repository-url>
cd hackathon

# Start development environment
make dev-up

# Install dependencies
cd services/meta-orchestrator
poetry install

# Run tests
poetry run pytest

# Start the service
poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

## 🛠️ Development Environment

### Local Development Setup

```bash
# Using Docker Compose (recommended)
docker-compose -f docker-compose.dev.yml up -d

# Or using Make
make meta-orchestrator-dev

# Access the service
curl http://localhost:8080/api/v1/services
```

### IDE Configuration

#### VS Code Settings

```json
{
  "python.defaultInterpreterPath": "./.venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": true,
  "python.linting.mypyEnabled": true,
  "python.formatting.provider": "black",
  "python.sortImports.args": ["--profile", "black"],
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  }
}
```

#### PyCharm Configuration

1. **Interpreter**: Set to project virtual environment
2. **Linters**: Enable Flake8, MyPy, Black
3. **Testing**: Configure pytest with `--cov` for coverage
4. **Run Configuration**:
   - Script: `services/meta-orchestrator/main.py`
   - Environment: `PYTHONPATH=services/meta-orchestrator`

## 📁 Project Structure

```
services/meta-orchestrator/
├── main.py                    # FastAPI application entry point
├── pyrightconfig.json         # Python type checking config
├── pytest.ini                # Test configuration
├── requirements.txt          # Python dependencies
├── test-requirements.txt     # Test dependencies
│
├── api/                      # REST API layer
│   ├── __init__.py
│   └── routes.py            # All API endpoints
│
├── core/                     # Core business logic
│   ├── __init__.py
│   └── orchestrator.py      # Main orchestration logic
│
├── models/                   # Pydantic models
│   ├── __init__.py
│   ├── service.py           # Service-related models
│   ├── container.py         # Docker container models
│   ├── result.py            # Operation result models
│   └── config_api.py        # Configuration API models
│
├── monitoring/               # Monitoring and audit system
│   ├── __init__.py
│   ├── service.py           # Main monitoring service
│   ├── config_manager.py    # Configuration management
│   ├── config_validator.py  # Configuration validation
│   │
│   ├── alerts/              # Alert management
│   │   └── manager.py
│   │
│   ├── analytics/           # Analytics and reporting
│   │   └── analyzer.py
│   │
│   ├── audit/               # Audit and validation modules
│   │   ├── config_drift_detector.py
│   │   ├── config_standardizer.py
│   │   ├── docker_compose_validator.py
│   │   └── docker_standardizer.py
│   │
│   ├── database/            # Database models and operations
│   │   ├── manager.py
│   │   └── models.py
│   │
│   ├── drift_detector.py    # Configuration drift detection
│   │
│   └── health/              # Health monitoring
│       └── checker.py
│
├── utils/                   # Utility functions
│   └── exceptions.py        # Custom exceptions
│
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── conftest.py         # Test configuration
│   ├── fixtures/           # Test fixtures
│   │   └── docker_compose_fixture.py
│   └── integration/        # Integration tests
│       ├── test_api_integration.py
│       ├── test_audit_features.py
│       ├── test_config_modification_api.py
│       ├── test_config_modification_workflow.py
│       ├── test_dry_run_user_store.py
│       ├── test_monitoring_api.py
│       └── test_service_lifecycle.py
│
└── docs/                    # Documentation
    ├── API_REFERENCE.md     # Complete API documentation
    ├── ARCHITECTURE.md      # Architecture deep-dive
    └── DEVELOPER_GUIDE.md   # This file
```

## ➕ Adding New Endpoints

### 1. Define Pydantic Models

```python
# models/config_api.py
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class NewOperationRequest(BaseModel):
    service_name: str = Field(..., description="Name of the service")
    operation_params: Dict[str, Any] = Field(default_factory=dict,
                                           description="Operation parameters")

class NewOperationResponse(BaseModel):
    success: bool
    operation_id: str
    status: str
    message: str
```

### 2. Add Route Handler

```python
# api/routes.py
from models.config_api import NewOperationRequest, NewOperationResponse

@router.post(
    "/services/{service_name}/new-operation",
    response_model=NewOperationResponse,
    tags=["Service Management"],
    summary="Perform New Operation",
    description="""
    Perform a new operation on the specified service.

    This endpoint allows you to execute custom operations
    with full validation and error handling.
    """,
    responses={
        200: {
            "description": "Operation completed successfully",
            "content": {
                "application/json": {
                    "example": {
                        "success": True,
                        "operation_id": "op_12345",
                        "status": "completed",
                        "message": "Operation completed successfully"
                    }
                }
            }
        },
        400: {"description": "Invalid request parameters"},
        404: {"description": "Service not found"},
        503: {"description": "Service unavailable"}
    }
)
async def perform_new_operation(
    service_name: str,
    request: NewOperationRequest
) -> NewOperationResponse:
    """Perform new operation on service"""
    try:
        if meta_orchestrator is None:
            raise HTTPException(status_code=503, detail="Meta-orchestrator not initialized")

        # Implement operation logic here
        result = await meta_orchestrator.perform_new_operation(
            service_name, request.operation_params
        )

        return NewOperationResponse(
            success=True,
            operation_id=result.operation_id,
            status="completed",
            message="Operation completed successfully"
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to perform operation on {service_name}: {e}")
        raise HTTPException(status_code=500, detail=f"Operation failed: {e}")
```

### 3. Implement Business Logic

```python
# core/orchestrator.py
class MetaOrchestrator:
    async def perform_new_operation(self, service_name: str, params: Dict[str, Any]) -> OperationResult:
        """Perform new operation logic"""
        # Validate service exists
        service = await self.get_service(service_name)
        if not service:
            raise ValueError(f"Service {service_name} not found")

        # Implement operation logic
        operation_id = f"op_{int(time.time())}_{service_name}"

        # Log operation
        logger.info(f"🔧 Performing new operation on {service_name}",
                   extra={"operation_id": operation_id})

        # Perform operation
        # ... operation implementation ...

        return OperationResult(
            operation_id=operation_id,
            status="completed"
        )
```

### 4. Add Tests

```python
# tests/integration/test_new_operation.py
import pytest
from fastapi.testclient import TestClient
from main import app

class TestNewOperation:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_new_operation_success(self, client, mock_orchestrator):
        """Test successful new operation"""
        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            response = client.post(
                "/api/v1/services/test-service/new-operation",
                json={"operation_params": {"key": "value"}}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert "operation_id" in data

    def test_new_operation_service_not_found(self, client, mock_orchestrator):
        """Test operation on non-existent service"""
        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            mock_orchestrator.perform_new_operation.side_effect = ValueError("Service not found")

            response = client.post(
                "/api/v1/services/nonexistent-service/new-operation",
                json={"operation_params": {}}
            )

            assert response.status_code == 500
```

## 📊 Extending Monitoring

### Adding New Health Checks

```python
# monitoring/health/checker.py
class HealthChecker:
    async def add_custom_health_check(self, service_name: str, check_config: Dict[str, Any]):
        """Add custom health check for service"""
        check = HealthCheckConfig(
            service_name=service_name,
            health_endpoint=check_config["endpoint"],
            check_type=check_config["type"],  # 'http', 'tcp', 'custom'
            timeout=check_config.get("timeout", 30.0),
            interval=check_config.get("interval", 60),
            custom_check_function=check_config.get("custom_function")
        )

        self.health_configs[service_name] = check
        await self.db_manager.save_health_config(check)

    async def perform_custom_health_check(self, config: HealthCheckConfig) -> HealthResult:
        """Perform custom health check"""
        if config.custom_check_function:
            # Execute custom health check function
            return await self._execute_custom_check(config)
        else:
            # Use standard health check
            return await self._perform_standard_check(config)
```

### Adding New Metrics

```python
# monitoring/analytics/analyzer.py
class DriftAnalytics:
    def add_custom_metric(self, metric_name: str, metric_config: Dict[str, Any]):
        """Add custom metric to analytics"""
        self.custom_metrics[metric_name] = metric_config

    async def calculate_custom_metric(self, metric_name: str, time_range: str) -> Dict[str, Any]:
        """Calculate custom metric"""
        config = self.custom_metrics.get(metric_name)
        if not config:
            raise ValueError(f"Unknown metric: {metric_name}")

        # Implement custom metric calculation
        query = config["query"]
        data = await self.db_manager.execute_analytics_query(query, time_range)

        return self._process_metric_data(data, config)
```

## ✅ Custom Validators

### Creating New Validators

```python
# monitoring/audit/custom_validator.py
from monitoring.audit.base_validator import BaseValidator, ValidationResult

class CustomServiceValidator(BaseValidator):
    """Custom validator for specific service types"""

    def __init__(self, workspace_path: Path):
        super().__init__(workspace_path)
        self.validator_name = "custom_service_validator"

    async def validate_service(self, service_name: str, service_config: Dict[str, Any]) -> ValidationResult:
        """Validate custom service requirements"""
        issues = []

        # Check custom requirements
        if service_name.startswith("special-"):
            # Special validation for special services
            if "special_config" not in service_config:
                issues.append(ValidationIssue(
                    service_name=service_name,
                    issue_type="missing_special_config",
                    severity="error",
                    description="Special services must have special_config defined"
                ))

        # Check environment variables
        required_env_vars = ["CUSTOM_VAR1", "CUSTOM_VAR2"]
        env_vars = service_config.get("environment", {})

        for var in required_env_vars:
            if var not in env_vars:
                issues.append(ValidationIssue(
                    service_name=service_name,
                    issue_type="missing_env_var",
                    severity="warning",
                    description=f"Missing required environment variable: {var}"
                ))

        return ValidationResult(
            service_name=service_name,
            success=len(issues) == 0,
            issues=issues,
            validator_name=self.validator_name
        )
```

### Registering Custom Validators

```python
# monitoring/service.py
class MonitoringService:
    def __init__(self, orchestrator: MetaOrchestrator, db_path: str = "/tmp/monitoring.db"):
        # ... existing initialization ...

        # Register custom validators
        from monitoring.audit.custom_validator import CustomServiceValidator
        self.custom_validator = CustomServiceValidator(orchestrator.settings.workspace_path)

    async def validate_service_custom(self, service_name: str) -> Dict[str, Any]:
        """Run custom validation"""
        result = await self.custom_validator.validate_service(service_name, {})

        return {
            "service_name": service_name,
            "validation_passed": result.success,
            "issues_found": len(result.issues),
            "issues": [
                {
                    "type": issue.issue_type,
                    "severity": issue.severity,
                    "description": issue.description
                } for issue in result.issues
            ]
        }
```

## 🗄️ Database Schema

### Current Schema Overview

```sql
-- Configuration drift tracking
CREATE TABLE configuration_drift (
    id INTEGER PRIMARY KEY,
    service_name TEXT NOT NULL,
    drift_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    description TEXT,
    field_path TEXT,
    old_value TEXT,
    new_value TEXT,
    timestamp REAL NOT NULL,
    resolved BOOLEAN DEFAULT FALSE,
    resolved_at REAL,
    resolved_by TEXT
);

-- Service health monitoring
CREATE TABLE service_health (
    id INTEGER PRIMARY KEY,
    service_name TEXT NOT NULL,
    health_status TEXT NOT NULL,
    response_time REAL,
    endpoint TEXT,
    error_message TEXT,
    timestamp REAL NOT NULL
);

-- Audit log for all operations
CREATE TABLE audit_log (
    id INTEGER PRIMARY KEY,
    operation TEXT NOT NULL,
    service_name TEXT,
    user TEXT,
    ip_address TEXT,
    user_agent TEXT,
    request_data TEXT,
    response_data TEXT,
    status_code INTEGER,
    duration REAL,
    timestamp REAL NOT NULL,
    correlation_id TEXT
);

-- Configuration backups
CREATE TABLE configuration_backups (
    id INTEGER PRIMARY KEY,
    service_name TEXT NOT NULL,
    config_hash TEXT NOT NULL,
    config_data TEXT NOT NULL,
    backup_reason TEXT,
    created_by TEXT,
    created_at REAL NOT NULL,
    restored BOOLEAN DEFAULT FALSE,
    restored_at REAL,
    restored_by TEXT
);
```

### Adding New Tables

```python
# monitoring/database/models.py
from dataclasses import dataclass
from typing import Optional
from datetime import datetime

@dataclass
class CustomOperation:
    id: Optional[int] = None
    operation_name: str = ""
    service_name: str = ""
    parameters: str = ""  # JSON string
    status: str = "pending"
    result: Optional[str] = None
    created_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

# monitoring/database/manager.py
class DatabaseManager:
    def create_custom_operation_table(self):
        """Create custom operations table"""
        self.conn.execute('''
            CREATE TABLE IF NOT EXISTS custom_operations (
                id INTEGER PRIMARY KEY,
                operation_name TEXT NOT NULL,
                service_name TEXT NOT NULL,
                parameters TEXT,
                status TEXT DEFAULT 'pending',
                result TEXT,
                created_at REAL NOT NULL,
                completed_at REAL
            )
        ''')

    async def save_custom_operation(self, operation: CustomOperation) -> int:
        """Save custom operation to database"""
        # Implementation here
        pass

    async def get_custom_operation(self, operation_id: int) -> Optional[CustomOperation]:
        """Retrieve custom operation from database"""
        # Implementation here
        pass
```

## 🧪 Testing Strategy

### Test Categories

#### Unit Tests
```python
# tests/unit/test_custom_validator.py
import pytest
from monitoring.audit.custom_validator import CustomServiceValidator

class TestCustomServiceValidator:
    def test_validates_special_service_config(self):
        validator = CustomServiceValidator(Path("/tmp"))
        config = {"special_config": {"enabled": True}}

        result = asyncio.run(validator.validate_service("special-service", config))

        assert result.success == True
        assert len(result.issues) == 0

    def test_fails_without_special_config(self):
        validator = CustomServiceValidator(Path("/tmp"))
        config = {}

        result = asyncio.run(validator.validate_service("special-service", config))

        assert result.success == False
        assert len(result.issues) == 1
        assert result.issues[0].issue_type == "missing_special_config"
```

#### Integration Tests
```python
# tests/integration/test_custom_endpoint.py
class TestCustomEndpoint:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_custom_endpoint_success(self, client, mock_orchestrator):
        with patch('api.routes.meta_orchestrator', mock_orchestrator):
            response = client.post(
                "/api/v1/services/test-service/custom-operation",
                json={"param1": "value1", "param2": 42}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["success"] == True
            assert "operation_id" in data

    def test_custom_endpoint_validation_error(self, client):
        response = client.post(
            "/api/v1/services/test-service/custom-operation",
            json={"invalid_param": "value"}
        )

        assert response.status_code == 422  # Validation error
```

#### End-to-End Tests
```python
# tests/e2e/test_service_lifecycle.py
class TestServiceLifecycleE2E:
    def test_full_service_lifecycle(self, docker_client):
        """Test complete service lifecycle from creation to destruction"""
        # 1. Create service configuration
        # 2. Deploy service
        # 3. Verify service is running
        # 4. Update configuration
        # 5. Verify configuration applied
        # 6. Stop service
        # 7. Verify service stopped
        # 8. Clean up resources
        pass
```

### Running Tests

```bash
# Run all tests
poetry run pytest

# Run specific test file
poetry run pytest tests/integration/test_custom_endpoint.py

# Run with coverage
poetry run pytest --cov=services/meta-orchestrator --cov-report=html

# Run specific test class/method
poetry run pytest tests/unit/test_custom_validator.py::TestCustomServiceValidator::test_validates_special_service_config

# Run tests in parallel
poetry run pytest -n auto

# Run tests with different markers
poetry run pytest -m "integration and not slow"
```

## 📏 Code Quality

### Code Formatting

```bash
# Format code with Black
black services/meta-orchestrator/

# Sort imports with isort
isort services/meta-orchestrator/

# Type checking with mypy
mypy services/meta-orchestrator/

# Lint with flake8
flake8 services/meta-orchestrator/
```

### Pre-commit Hooks

```yaml
# .pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/pycqa/isort
    rev: 5.12.0
    hooks:
      - id: isort
        args: ["--profile", "black"]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]
```

### CI/CD Pipeline

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
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

      - name: Run tests
        run: |
          cd services/meta-orchestrator
          pytest --cov --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: services/meta-orchestrator/coverage.xml
```

## 🤝 Contributing Guidelines

### Development Workflow

1. **Create Feature Branch**
   ```bash
   git checkout -b feature/new-endpoint
   ```

2. **Write Tests First**
   ```python
   # tests/integration/test_new_feature.py
   def test_new_feature():
       # Test implementation
       pass
   ```

3. **Implement Feature**
   ```python
   # services/meta-orchestrator/api/routes.py
   @router.post("/new-endpoint")
   async def new_endpoint():
       # Implementation
       pass
   ```

4. **Add Documentation**
   ```markdown
   <!-- docs/API_REFERENCE.md -->
   ### New Endpoint
   Description of the new endpoint...
   ```

5. **Run Tests**
   ```bash
   poetry run pytest
   poetry run black .
   poetry run isort .
   ```

6. **Create Pull Request**
   - Descriptive title and description
   - Reference any related issues
   - Include screenshots for UI changes
   - Update CHANGELOG.md

### Code Review Checklist

- [ ] **Tests pass** - All tests pass locally
- [ ] **Code coverage** - New code has adequate test coverage
- [ ] **Documentation** - API documentation updated
- [ ] **Type hints** - All functions have proper type hints
- [ ] **Linting** - Code passes all linting checks
- [ ] **Security** - No security vulnerabilities introduced
- [ ] **Performance** - No performance regressions
- [ ] **Breaking changes** - Documented if any

### Commit Message Format

```
type(scope): description

[optional body]

[optional footer]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Test additions
- `chore`: Maintenance

**Examples:**
```
feat(api): add service restart endpoint
fix(monitoring): resolve memory leak in health checker
docs(api): update endpoint documentation
```

## 🔧 Troubleshooting

### Common Development Issues

#### Import Errors
```bash
# Fix Python path issues
export PYTHONPATH="${PYTHONPATH}:$(pwd)/services/meta-orchestrator"

# Or use poetry
poetry run python -c "import services.meta_orchestrator.monitoring.service"
```

#### Docker Connection Issues
```bash
# Check Docker daemon
docker info

# Fix socket permissions
sudo chown $USER /var/run/docker.sock

# Use Docker context
docker context use default
```

#### Database Issues
```bash
# Reset database
rm /tmp/monitoring.db

# Check database file
sqlite3 /tmp/monitoring.db .tables

# View database schema
sqlite3 /tmp/monitoring.db .schema
```

#### Test Failures
```bash
# Run specific failing test with debug
pytest tests/integration/test_api_integration.py::TestAPIIntegration::test_service_list -v -s

# Check test logs
tail -f /tmp/test_logs.log

# Run tests with different Python path
PYTHONPATH=services/meta-orchestrator pytest
```

#### Performance Issues
```bash
# Profile code execution
python -m cProfile -s cumtime services/meta-orchestrator/main.py

# Check memory usage
python -c "import psutil; print(psutil.virtual_memory())"

# Monitor Docker resource usage
docker stats
```

### Debugging Techniques

#### Logging Debug Information
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Add debug logs
logger.debug(f"Processing request: {request}")
logger.debug(f"Service config: {service_config}")
```

#### Interactive Debugging
```python
# Add breakpoint
import pdb; pdb.set_trace()

# Or use ipdb for better experience
import ipdb; ipdb.set_trace()
```

#### API Debugging
```bash
# Test API endpoints
curl -v http://localhost:8080/api/v1/services

# Check API documentation
open http://localhost:8080/docs

# View API logs
docker-compose logs meta-orchestrator
```

### Getting Help

1. **Check Existing Documentation**
   - README.md - Service overview
   - API_REFERENCE.md - Complete API docs
   - ARCHITECTURE.md - System design
   - This developer guide

2. **Search Existing Issues**
   - GitHub issues
   - Internal documentation
   - Code comments

3. **Ask for Help**
   - Team chat/Slack
   - Code reviews
   - Architecture discussions

This guide provides a comprehensive foundation for developing with and extending the Meta-Orchestration Service. Follow these guidelines to ensure high-quality, maintainable, and well-tested code contributions.
