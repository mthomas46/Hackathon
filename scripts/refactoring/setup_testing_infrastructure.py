#!/usr/bin/env python3
"""
Testing Infrastructure Setup Script

Automatically sets up comprehensive testing infrastructure for a service
following the Comprehensive Testing Strategy.

Usage:
    python setup_testing_infrastructure.py <service-name>

Example:
    python setup_testing_infrastructure.py doc-store
"""

import os
import sys
import json
from pathlib import Path
from typing import Dict, List


def create_pytest_ini(service_path: Path) -> None:
    """Create pytest.ini with standard configuration"""
    pytest_content = """[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
asyncio_mode = auto
addopts = 
    -v
    --tb=short
    --strict-markers
    --cov=.
    --cov-report=html
    --cov-report=term
    --cov-fail-under=80
    -n auto
markers =
    unit: Unit tests
    integration: Integration tests
    functional: Functional tests
    e2e: End-to-end tests
    slow: Slow tests (> 1s)
    performance: Performance tests
"""
    
    pytest_path = service_path / "pytest.ini"
    pytest_path.write_text(pytest_content)
    print(f"✓ Created {pytest_path}")


def create_test_directories(service_path: Path) -> None:
    """Create standard test directory structure"""
    test_dirs = [
        "tests",
        "tests/unit",
        "tests/unit/domain",
        "tests/unit/domain/entities",
        "tests/unit/domain/value_objects",
        "tests/unit/domain/services",
        "tests/unit/application",
        "tests/unit/application/commands",
        "tests/unit/application/queries",
        "tests/unit/infrastructure",
        "tests/unit/infrastructure/repositories",
        "tests/unit/presentation",
        "tests/unit/presentation/api",
        "tests/integration",
        "tests/integration/api",
        "tests/integration/database",
        "tests/integration/services",
        "tests/functional",
        "tests/functional/features",
        "tests/e2e",
        "tests/e2e/workflows",
        "tests/performance",
        "tests/fixtures",
    ]
    
    for dir_name in test_dirs:
        dir_path = service_path / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            init_file.write_text('"""Test package"""\n')
        
        print(f"✓ Created {dir_path}")


def create_conftest(service_path: Path, service_name: str) -> None:
    """Create main conftest.py with common fixtures"""
    conftest_content = f'''"""
Pytest configuration and shared fixtures

This module provides common fixtures used across all tests.
"""

import pytest
import asyncio
from typing import AsyncGenerator, Generator
from httpx import AsyncClient

# Test database fixtures

@pytest.fixture
async def test_db():
    """Provide test database"""
    from infrastructure.database import Database
    
    # Use in-memory database for tests
    db = Database(":memory:")
    await db.initialize()
    
    yield db
    
    await db.cleanup()


# Service fixtures

@pytest.fixture
def service_config():
    """Provide test service configuration"""
    return {{
        "service_name": "{service_name}",
        "environment": "test",
        "log_level": "DEBUG",
        "database_url": ":memory:",
    }}


# API client fixtures

@pytest.fixture
async def api_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide HTTP client for API testing"""
    from presentation.api.main import app
    
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


# Mock fixtures

@pytest.fixture
def mock_logger():
    """Provide mock logger"""
    from unittest.mock import Mock
    
    logger = Mock()
    logger.info = Mock()
    logger.error = Mock()
    logger.debug = Mock()
    logger.warning = Mock()
    
    return logger


# Sample data fixtures

@pytest.fixture
def sample_entity():
    """Provide sample entity for testing"""
    # TODO: Customize based on your domain entities
    return None


# Event loop configuration for async tests

@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
'''
    
    conftest_path = service_path / "tests" / "conftest.py"
    conftest_path.write_text(conftest_content)
    print(f"✓ Created {conftest_path}")


def create_sample_unit_test(service_path: Path) -> None:
    """Create sample unit test to demonstrate structure"""
    test_content = '''"""
Sample unit test demonstrating testing standards

This is a template - replace with actual tests for your domain entities.
"""

import pytest


@pytest.mark.unit
class TestSampleEntity:
    """Unit tests for SampleEntity"""
    
    def test_create_entity_with_valid_data_returns_entity(self):
        """Test creating entity with valid data"""
        # Arrange
        # TODO: Set up test data
        
        # Act
        # TODO: Execute code under test
        
        # Assert
        # TODO: Verify expected outcome
        pass
    
    def test_create_entity_with_invalid_data_raises_error(self):
        """Test validation: invalid data raises error"""
        # Arrange
        # TODO: Set up invalid test data
        
        # Act & Assert
        with pytest.raises(ValueError):
            # TODO: Execute code that should raise error
            pass
    
    @pytest.mark.parametrize("input,expected", [
        ("valid_input", "expected_output"),
        # Add more test cases
    ])
    def test_entity_handles_various_inputs(self, input, expected):
        """Test entity handles various input scenarios"""
        # TODO: Implement parametrized test
        pass
'''
    
    test_path = service_path / "tests" / "unit" / "test_sample.py"
    test_path.write_text(test_content)
    print(f"✓ Created {test_path}")


def create_sample_integration_test(service_path: Path) -> None:
    """Create sample integration test"""
    test_content = '''"""
Sample integration test demonstrating testing standards
"""

import pytest


@pytest.mark.integration
@pytest.mark.asyncio
class TestSampleIntegration:
    """Integration tests for sample functionality"""
    
    async def test_api_endpoint_returns_expected_response(self, api_client):
        """Test API endpoint integration"""
        # Arrange
        # TODO: Set up test data
        
        # Act
        response = await api_client.get("/api/v2/sample")
        
        # Assert
        assert response.status_code == 200
        # TODO: Verify response content
'''
    
    test_path = service_path / "tests" / "integration" / "test_sample_integration.py"
    test_path.write_text(test_content)
    print(f"✓ Created {test_path}")


def create_requirements_test(service_path: Path) -> None:
    """Create requirements-test.txt with testing dependencies"""
    requirements_content = """# Testing Dependencies
pytest==7.4.0
pytest-asyncio==0.21.0
pytest-cov==4.1.0
pytest-mock==3.11.1
pytest-xdist==3.3.1
pytest-timeout==2.1.0
faker==19.2.0
factory-boy==3.2.1
httpx==0.24.1
"""
    
    req_path = service_path / "requirements-test.txt"
    req_path.write_text(requirements_content)
    print(f"✓ Created {req_path}")


def create_github_workflow(service_path: Path, service_name: str) -> None:
    """Create GitHub Actions workflow for tests"""
    workflow_content = f"""name: Tests

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main, develop ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          cd services/{service_name}
          pip install -r requirements.txt
          pip install -r requirements-test.txt
      
      - name: Run tests
        run: |
          cd services/{service_name}
          pytest --cov --cov-fail-under=80
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          file: ./services/{service_name}/coverage.xml
"""
    
    workflow_dir = service_path / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    
    workflow_path = workflow_dir / "test.yml"
    workflow_path.write_text(workflow_content)
    print(f"✓ Created {workflow_path}")


def create_testing_readme(service_path: Path) -> None:
    """Create TESTING.md guide"""
    readme_content = """# Testing Guide

## Running Tests

### Run all tests
```bash
pytest
```

### Run with coverage
```bash
pytest --cov --cov-report=html
open htmlcov/index.html
```

### Run specific test types
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# Functional tests only
pytest -m functional

# E2E tests only
pytest -m e2e
```

### Run specific test file
```bash
pytest tests/unit/test_sample.py
```

### Run specific test
```bash
pytest tests/unit/test_sample.py::TestSampleEntity::test_create_entity_with_valid_data_returns_entity
```

### Run in parallel
```bash
pytest -n auto
```

## Test Coverage

Target: 80%+ overall coverage

- Domain: 90%+
- Application: 80%+
- Infrastructure: 70%+
- Presentation: 80%+

## Test Structure

Follow AAA pattern:
- **Arrange**: Set up test data
- **Act**: Execute code under test
- **Assert**: Verify expected outcome

## Naming Convention

```python
def test_<scenario>_<expected_behavior>():
    \"\"\"Test description\"\"\"
    pass
```

## References

- [Comprehensive Testing Strategy](../../docs/refactoring/COMPREHENSIVE_TESTING_STRATEGY.md)
- [TDD Checklist](../../docs/refactoring/TDD_CHECKLIST.md)
"""
    
    readme_path = service_path / "TESTING.md"
    readme_path.write_text(readme_content)
    print(f"✓ Created {readme_path}")


def update_service_readme(service_path: Path) -> None:
    """Add testing section to service README if not exists"""
    readme_path = service_path / "README.md"
    
    if not readme_path.exists():
        print(f"⚠ README.md not found at {readme_path}")
        return
    
    content = readme_path.read_text()
    
    testing_section = """
## Testing

This service has comprehensive test coverage (80%+) following the [Comprehensive Testing Strategy](../../docs/refactoring/COMPREHENSIVE_TESTING_STRATEGY.md).

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov --cov-report=html

# Specific test types
pytest -m unit
pytest -m integration
pytest -m functional
```

See [TESTING.md](./TESTING.md) for detailed testing guide.
"""
    
    if "## Testing" not in content:
        # Add before "## License" or at the end
        if "## License" in content:
            content = content.replace("## License", testing_section + "\n## License")
        else:
            content += "\n" + testing_section
        
        readme_path.write_text(content)
        print(f"✓ Updated {readme_path} with testing section")
    else:
        print(f"ℹ Testing section already exists in {readme_path}")


def generate_report(service_name: str, service_path: Path) -> Dict:
    """Generate setup report"""
    return {
        "service": service_name,
        "status": "complete",
        "files_created": [
            "pytest.ini",
            "tests/ (directory structure)",
            "tests/conftest.py",
            "tests/unit/test_sample.py",
            "tests/integration/test_sample_integration.py",
            "requirements-test.txt",
            ".github/workflows/test.yml",
            "TESTING.md",
        ],
        "next_steps": [
            "Replace sample tests with actual tests",
            "Implement domain entity tests",
            "Add integration tests for repositories",
            "Create functional tests for API endpoints",
            "Run: pytest --cov",
            "Achieve 80%+ coverage",
        ]
    }


def main():
    """Main entry point"""
    if len(sys.argv) != 2:
        print("Usage: python setup_testing_infrastructure.py <service-name>")
        print("Example: python setup_testing_infrastructure.py doc-store")
        sys.exit(1)
    
    service_name = sys.argv[1]
    
    # Determine service path
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent
    service_path = repo_root / "services" / service_name
    
    if not service_path.exists():
        print(f"✗ Service not found: {service_path}")
        sys.exit(1)
    
    print(f"\n🚀 Setting up testing infrastructure for '{service_name}'")
    print(f"   Path: {service_path}\n")
    
    # Create all testing infrastructure
    create_pytest_ini(service_path)
    create_test_directories(service_path)
    create_conftest(service_path, service_name)
    create_sample_unit_test(service_path)
    create_sample_integration_test(service_path)
    create_requirements_test(service_path)
    create_github_workflow(service_path, service_name)
    create_testing_readme(service_path)
    update_service_readme(service_path)
    
    # Generate report
    report = generate_report(service_name, service_path)
    
    report_path = service_path / "testing_setup_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    print(f"\n✓ Testing infrastructure setup complete!")
    print(f"  Report: {report_path}\n")
    
    print("📝 Next Steps:")
    for step in report["next_steps"]:
        print(f"  - {step}")
    
    print("\n📚 Reference:")
    print("  - Comprehensive Testing Strategy: docs/refactoring/COMPREHENSIVE_TESTING_STRATEGY.md")
    print("  - TDD Checklist: docs/refactoring/TDD_CHECKLIST.md")
    print(f"  - Service Testing Guide: services/{service_name}/TESTING.md")


if __name__ == "__main__":
    main()

