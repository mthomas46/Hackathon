"""Documentation Consistency Test Configuration.

Focused configuration for testing the documentation consistency ecosystem.
Provides core fixtures and test setup for GitHub, Jira, Confluence, and OpenAPI testing.
"""

import os
import sys
import pytest
from pathlib import Path

# Core paths and environment
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
TEST_ROOT = Path(__file__).parent.absolute()

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Test environment setup
os.environ.setdefault('TESTING', 'true')
os.environ.setdefault('LOG_LEVEL', 'WARNING')

# Import focused fixtures
from .fixtures.documentation_consistency_fixtures import *

# Parallel-friendly: ensure any DB-like or external resources are function-scoped
# and isolated per test process. Provide a simple marker registry for CI filtering.
def pytest_addoption(parser):
    parser.addoption(
        "--test-mode",
        action="store",
        default=os.environ.get("TEST_MODE", "mocked"),
        help="Test mode: mocked | integration | live",
    )


def pytest_configure(config):
    """Documentation consistency test configuration."""
    markers = [
        ("unit", "Unit tests for individual components"),
        ("integration", "Integration tests across services"),
        ("consistency", "Documentation consistency analysis tests"),
        ("e2e", "End-to-end workflow tests"),
        ("orchestrator", "Orchestrator service tests"),
        ("doc_store", "Document store tests"),
        ("consistency_engine", "Consistency engine tests"),
        ("agents", "Source agent tests"),
        ("slow", "Long-running tests to be excluded from fast CI lanes"),
        ("live", "Tests that hit live/containerized services"),
        ("security", "Tests that validate security controls and vulnerability prevention"),
        ("mocks", "Tests that use mock objects for external dependencies")
    ]
    for marker, desc in markers:
        config.addinivalue_line("markers", f"{marker}: {desc}")

# Pytest configuration
@pytest.fixture
def test_mode(request):
    return request.config.getoption("--test-mode")

# Core test session
@pytest.fixture(scope="session")
def test_session():
    """Global test session for documentation consistency tests."""
    return {
        "start_time": None,
        "services_started": [],
        "test_documents": [],
        "consistency_findings": []
    }

@pytest.fixture
def test_context():
    """Test context for individual test cases."""
    return {
        "documents_ingested": [],
        "findings_generated": [],
        "cleanup_required": False
    }
