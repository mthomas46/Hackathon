"""Test configuration and fixtures for the Simulation Dashboard."""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock
from typing import Dict, Any, Generator
import sys
import os

# Add the service directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from infrastructure.config.config import DashboardSettings, SimulationServiceConfig


@pytest.fixture
def mock_config():
    """Create a mock dashboard configuration for testing."""
    config = DashboardSettings()
    config.environment = "test"
    config.debug = True
    config.service_name = "simulation-dashboard-test"
    config.simulation_service = SimulationServiceConfig(
        host="localhost",
        port=5075,
        base_url="http://localhost:5075",
        timeout=5.0,
        retry_attempts=1
    )
    return config


@pytest.fixture
def mock_simulation_client():
    """Create a mock simulation service client."""
    client = MagicMock()
    client.get_health = AsyncMock(return_value={
        "status": "healthy",
        "version": "1.0.0",
        "uptime": "1h 30m"
    })
    client.list_simulations = AsyncMock(return_value=[
        {
            "id": "sim_001",
            "name": "Test Simulation",
            "status": "completed",
            "created_at": "2024-01-15T10:00:00Z"
        }
    ])
    client.create_simulation = AsyncMock(return_value={
        "id": "sim_002",
        "name": "New Test Simulation",
        "status": "created",
        "created_at": "2024-01-16T10:00:00Z"
    })
    return client


@pytest.fixture
def mock_websocket_client():
    """Create a mock WebSocket client."""
    client = MagicMock()
    client.connect = AsyncMock()
    client.disconnect = AsyncMock()
    client.send_message = AsyncMock()
    client.is_connected = True
    client.connection_status = "connected"
    return client


@pytest.fixture
def sample_simulation_data():
    """Sample simulation data for testing."""
    return {
        "id": "sim_001",
        "name": "E-commerce Platform Development",
        "type": "software_development",
        "complexity": "medium",
        "team_size": 8,
        "duration_weeks": 12,
        "status": "running",
        "progress": 65.5,
        "created_at": "2024-01-15T10:00:00Z",
        "updated_at": "2024-01-16T08:30:00Z",
        "config": {
            "methodology": "agile",
            "budget": 150000,
            "risk_level": "medium"
        }
    }


@pytest.fixture
def sample_event_data():
    """Sample event data for testing."""
    return [
        {
            "event_id": "evt_001",
            "event_type": "SimulationStarted",
            "timestamp": "2024-01-16T10:00:00Z",
            "simulation_id": "sim_001",
            "correlation_id": "corr_001",
            "data": {
                "description": "Simulation execution began",
                "sequence_number": 1
            }
        },
        {
            "event_id": "evt_002",
            "event_type": "DocumentGenerated",
            "timestamp": "2024-01-16T10:15:00Z",
            "simulation_id": "sim_001",
            "correlation_id": "corr_002",
            "data": {
                "description": "Requirements document generated",
                "document_type": "requirements",
                "word_count": 2450
            }
        }
    ]


@pytest.fixture
def sample_report_data():
    """Sample report data for testing."""
    return {
        "simulation_id": "sim_001",
        "report_type": "executive_summary",
        "generated_at": "2024-01-16T12:00:00Z",
        "status": "completed",
        "quality_score": 0.85,
        "execution_time_seconds": 120.5,
        "documents_generated": 12,
        "workflows_executed": 8,
        "consistency_score": 0.78,
        "success_rate": 0.95
    }


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_streamlit_session_state():
    """Mock Streamlit session state for testing."""
    class MockSessionState:
        def __init__(self):
            self.data = {}

        def __getitem__(self, key):
            return self.data[key]

        def __setitem__(self, key, value):
            self.data[key] = value

        def get(self, key, default=None):
            return self.data.get(key, default)

        def __contains__(self, key):
            return key in self.data

    return MockSessionState()


@pytest.fixture
def mock_streamlit_context():
    """Mock Streamlit context for testing."""
    class MockStreamlitContext:
        def __init__(self):
            self.session_state = {}

        def sidebar(self):
            return MockContainer()

        def container(self):
            return MockContainer()

        def columns(self, num):
            return [MockContainer() for _ in range(num)]

        def expander(self, label, expanded=False):
            return MockContainer()

        def success(self, text):
            pass

        def error(self, text):
            pass

        def warning(self, text):
            pass

        def info(self, text):
            pass

        def metric(self, label, value, delta=None):
            pass

        def button(self, label, key=None, help=None, **kwargs):
            return False

        def text_input(self, label, value="", key=None, **kwargs):
            return value

        def selectbox(self, label, options, index=0, key=None, **kwargs):
            return options[index] if options else None

        def multiselect(self, label, options, default=None, key=None, **kwargs):
            return default or []

        def checkbox(self, label, value=False, key=None, **kwargs):
            return value

        def slider(self, label, min_value=None, max_value=None, value=None, key=None, **kwargs):
            return value

        def date_input(self, label, value=None, key=None, **kwargs):
            from datetime import date
            return value or date.today()

        def plotly_chart(self, figure, use_container_width=False, **kwargs):
            pass

        def dataframe(self, data, use_container_width=False, **kwargs):
            pass

        def table(self, data):
            pass

        def json(self, body):
            pass

        def download_button(self, label, data, file_name, mime, key=None, **kwargs):
            pass

        def spinner(self, text):
            class SpinnerContext:
                def __enter__(self):
                    return self
                def __exit__(self, exc_type, exc_val, exc_tb):
                    pass
            return SpinnerContext()

        def balloons(self):
            pass

    class MockContainer:
        def __init__(self):
            pass

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

        def write(self, text):
            pass

        def markdown(self, text):
            pass

        def header(self, text):
            pass

        def subheader(self, text):
            pass

        def title(self, text):
            pass

        def success(self, text):
            pass

        def error(self, text):
            pass

        def warning(self, text):
            pass

        def info(self, text):
            pass

        def metric(self, label, value, delta=None):
            pass

        def button(self, label, key=None, help=None, **kwargs):
            return False

        def text_input(self, label, value="", key=None, **kwargs):
            return value

        def selectbox(self, label, options, index=0, key=None, **kwargs):
            return options[index] if options else None

        def multiselect(self, label, options, default=None, key=None, **kwargs):
            return default or []

        def checkbox(self, label, value=False, key=None, **kwargs):
            return value

        def slider(self, label, min_value=None, max_value=None, value=None, key=None, **kwargs):
            return value

        def date_input(self, label, value=None, key=None, **kwargs):
            from datetime import date
            return value or date.today()

        def plotly_chart(self, figure, use_container_width=False, **kwargs):
            pass

        def dataframe(self, data, use_container_width=False, **kwargs):
            pass

        def table(self, data):
            pass

        def json(self, body):
            pass

        def download_button(self, label, data, file_name, mime, key=None, **kwargs):
            pass

        def spinner(self, text):
            class SpinnerContext:
                def __enter__(self):
                    return self
                def __exit__(self, exc_type, exc_val, exc_tb):
                    pass
            return SpinnerContext()

        def balloons(self):
            pass

    return MockStreamlitContext()


# Custom pytest markers
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "unit: mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "functional: mark test as a functional test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    config.addinivalue_line(
        "markers", "websocket: mark test as websocket related"
    )
    config.addinivalue_line(
        "markers", "ui: mark test as UI related"
    )
