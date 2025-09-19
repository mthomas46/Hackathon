"""Functional tests for dashboard UI components."""

import pytest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from pages.overview import render_overview_page
from pages.create import render_create_page
from pages.monitor import render_monitor_page
from pages.reports import render_reports_page
from pages.config import render_config_page


@pytest.mark.functional
@pytest.mark.ui
class TestOverviewPage:
    """Functional tests for overview page."""

    @patch('pages.overview.st')
    @patch('pages.overview.get_available_simulations')
    @patch('pages.overview.get_simulation_client')
    def test_overview_page_renders_without_errors(self, mock_get_client, mock_get_sims, mock_st):
        """Test that overview page renders without critical errors."""
        # Mock dependencies
        mock_get_sims.return_value = [
            {"id": "sim_001", "name": "Test Sim", "status": "completed"}
        ]

        mock_client = MagicMock()
        mock_client.get_health.return_value = {"status": "healthy"}
        mock_get_client.return_value = mock_client

        # Mock Streamlit components
        mock_st.markdown = Mock()
        mock_st.header = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock(), Mock(), Mock()])
        mock_st.metric = Mock()
        mock_st.info = Mock()
        mock_st.button = Mock(return_value=False)
        mock_st.selectbox = Mock(return_value="All Simulations")
        mock_st.container = Mock(return_value=Mock())

        # Should not raise exceptions
        render_overview_page()

        # Verify key components were called
        mock_st.markdown.assert_called()
        mock_st.header.assert_called()
        mock_st.columns.assert_called()

    @patch('pages.overview.st')
    @patch('pages.overview.get_available_simulations')
    def test_overview_page_handles_empty_simulations(self, mock_get_sims, mock_st):
        """Test overview page with no simulations available."""
        mock_get_sims.return_value = []

        mock_st.markdown = Mock()
        mock_st.header = Mock()
        mock_st.info = Mock()
        mock_st.button = Mock(return_value=False)
        mock_st.columns = Mock(return_value=[Mock(), Mock(), Mock(), Mock()])
        mock_st.metric = Mock()

        render_overview_page()

        # Should show appropriate empty state
        mock_st.info.assert_called()


@pytest.mark.functional
@pytest.mark.ui
class TestCreatePage:
    """Functional tests for create page."""

    @patch('pages.create.st')
    @patch('pages.create.get_simulation_client')
    def test_create_page_renders_form(self, mock_get_client, mock_st):
        """Test that create page renders simulation creation form."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock Streamlit components
        mock_st.markdown = Mock()
        mock_st.header = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock()])
        mock_st.selectbox = Mock(return_value="software_development")
        mock_st.slider = Mock(return_value=5)
        mock_st.text_input = Mock(return_value="Test Simulation")
        mock_st.checkbox = Mock(return_value=True)
        mock_st.button = Mock(return_value=False)
        mock_st.expander = Mock(return_value=Mock())
        mock_st.success = Mock()

        render_create_page()

        # Verify form components were rendered
        mock_st.selectbox.assert_called()
        mock_st.slider.assert_called()
        mock_st.text_input.assert_called()

    @patch('pages.create.st')
    @patch('pages.create.get_simulation_client')
    def test_create_simulation_success_flow(self, mock_get_client, mock_st):
        """Test successful simulation creation flow."""
        mock_client = MagicMock()
        mock_client.create_simulation = Mock(return_value={
            "id": "sim_002",
            "name": "Test Simulation",
            "status": "created"
        })
        mock_get_client.return_value = mock_client

        # Mock Streamlit components
        mock_st.markdown = Mock()
        mock_st.header = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock()])
        mock_st.selectbox = Mock(return_value="software_development")
        mock_st.slider = Mock(return_value=5)
        mock_st.text_input = Mock(return_value="Test Simulation")
        mock_st.checkbox = Mock(return_value=True)
        mock_st.button = Mock(return_value=True)  # Click create button
        mock_st.success = Mock()
        mock_st.balloons = Mock()
        mock_st.expander = Mock(return_value=Mock())

        render_create_page()

        # Verify success flow
        mock_st.success.assert_called()
        mock_st.balloons.assert_called()
        mock_client.create_simulation.assert_called()


@pytest.mark.functional
@pytest.mark.ui
class TestMonitorPage:
    """Functional tests for monitor page."""

    @patch('pages.monitor.st')
    @patch('pages.monitor.get_simulation_client')
    @patch('pages.monitor.get_websocket_manager')
    def test_monitor_page_initialization(self, mock_get_ws, mock_get_client, mock_st):
        """Test monitor page initialization."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        mock_ws_manager = MagicMock()
        mock_get_ws.return_value = mock_ws_manager

        # Mock Streamlit components
        mock_st.markdown = Mock()
        mock_st.header = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock(), Mock()])
        mock_st.metric = Mock()
        mock_st.info = Mock()
        mock_st.button = Mock(return_value=False)
        mock_st.empty = Mock(return_value=Mock())
        mock_st.container = Mock(return_value=Mock())
        mock_st.session_state = {}

        from pages.monitor import render_monitor_page
        render_monitor_page()

        # Verify initialization
        mock_st.markdown.assert_called()
        mock_st.columns.assert_called()

    @patch('pages.monitor.st')
    @patch('pages.monitor.get_simulation_client')
    def test_monitor_page_handles_websocket_events(self, mock_get_client, mock_st):
        """Test monitor page handles WebSocket events."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock Streamlit components
        mock_st.markdown = Mock()
        mock_st.header = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock(), Mock()])
        mock_st.metric = Mock()
        mock_st.info = Mock()
        mock_st.button = Mock(return_value=False)
        mock_st.empty = Mock(return_value=Mock())
        mock_st.container = Mock(return_value=Mock())
        mock_st.session_state = {
            'websocket_connected': True,
            'realtime_events': []
        }

        from pages.monitor import render_monitor_page
        render_monitor_page()

        # Should handle WebSocket connection status
        assert 'websocket_connected' in mock_st.session_state


@pytest.mark.functional
@pytest.mark.ui
class TestReportsPage:
    """Functional tests for reports page."""

    @patch('pages.reports.st')
    @patch('pages.reports.get_simulation_client')
    def test_reports_page_renders_tabs(self, mock_get_client, mock_st):
        """Test reports page renders with tabbed interface."""
        mock_client = MagicMock()
        mock_get_client.return_value = mock_client

        # Mock Streamlit components
        mock_st.markdown = Mock()
        mock_st.tabs = Mock(return_value=[Mock(), Mock(), Mock(), Mock()])
        mock_st.header = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock()])
        mock_st.selectbox = Mock(return_value=None)
        mock_st.button = Mock(return_value=False)
        mock_st.info = Mock()
        mock_st.metric = Mock()

        from pages.reports import render_reports_page
        render_reports_page()

        # Verify tabs were created
        mock_st.tabs.assert_called()

    @patch('pages.reports.st')
    def test_reports_page_handles_empty_analytics(self, mock_st):
        """Test reports page with no analytics data."""
        # Mock Streamlit components
        mock_st.markdown = Mock()
        mock_st.tabs = Mock(return_value=[Mock(), Mock(), Mock(), Mock()])
        mock_st.info = Mock()

        from pages.reports import render_reports_page
        render_reports_page()

        # Should show empty state message
        mock_st.info.assert_called()


@pytest.mark.functional
@pytest.mark.ui
class TestConfigPage:
    """Functional tests for config page."""

    @patch('pages.config.st')
    @patch('pages.config.get_config')
    def test_config_page_renders_health_dashboard(self, mock_get_config, mock_st):
        """Test config page renders health dashboard."""
        mock_config = MagicMock()
        mock_config.simulation_service.host = "localhost"
        mock_config.simulation_service.port = 5075
        mock_get_config.return_value = mock_config

        # Mock Streamlit components
        mock_st.markdown = Mock()
        mock_st.tabs = Mock(return_value=[Mock(), Mock(), Mock(), Mock()])
        mock_st.columns = Mock(return_value=[Mock(), Mock(), Mock(), Mock()])
        mock_st.metric = Mock()
        mock_st.text_input = Mock(return_value="")
        mock_st.button = Mock(return_value=False)
        mock_st.info = Mock()

        from pages.config import render_config_page
        render_config_page()

        # Verify health dashboard components
        mock_st.tabs.assert_called()
        mock_st.columns.assert_called()


@pytest.mark.functional
@pytest.mark.ui
class TestPageNavigation:
    """Functional tests for page navigation."""

    @patch('app.st')
    @patch('app.render_page_content')
    def test_app_initialization(self, mock_render, mock_st):
        """Test main app initialization."""
        mock_st.set_page_config = Mock()
        mock_st.sidebar = Mock(return_value=Mock())
        mock_st.markdown = Mock()
        mock_st.selectbox = Mock(return_value="overview")
        mock_st.container = Mock(return_value=Mock())

        # Import should not fail
        try:
            from app import render_page_content, PAGES
            assert callable(render_page_content)
            assert isinstance(PAGES, dict)
            assert "overview" in PAGES
        except ImportError:
            pytest.skip("App module not available for testing")

    @patch('app.st')
    def test_page_routing(self, mock_st):
        """Test page routing functionality."""
        mock_st.set_page_config = Mock()
        mock_st.sidebar = Mock(return_value=Mock())
        mock_st.markdown = Mock()
        mock_st.selectbox = Mock(return_value="overview")
        mock_st.container = Mock(return_value=Mock())

        try:
            from app import render_page_content, PAGES

            # Test routing to overview page
            render_page_content("overview")
            # Should not raise exceptions

            # Test routing to invalid page
            render_page_content("invalid_page")
            # Should handle gracefully

        except ImportError:
            pytest.skip("App module not available for testing")


@pytest.mark.functional
@pytest.mark.ui
class TestErrorHandling:
    """Functional tests for error handling in UI."""

    @patch('pages.overview.st')
    @patch('pages.overview.get_simulation_client')
    def test_overview_handles_client_errors(self, mock_get_client, mock_st):
        """Test overview page handles client connection errors."""
        mock_client = MagicMock()
        mock_client.get_health.side_effect = Exception("Connection failed")
        mock_get_client.return_value = mock_client

        mock_st.markdown = Mock()
        mock_st.header = Mock()
        mock_st.error = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock(), Mock(), Mock()])
        mock_st.metric = Mock()

        from pages.overview import render_overview_page
        render_overview_page()

        # Should handle error gracefully
        mock_st.error.assert_called()

    @patch('pages.create.st')
    @patch('pages.create.get_simulation_client')
    def test_create_handles_creation_errors(self, mock_get_client, mock_st):
        """Test create page handles simulation creation errors."""
        mock_client = MagicMock()
        mock_client.create_simulation.side_effect = Exception("Creation failed")
        mock_get_client.return_value = mock_client

        mock_st.markdown = Mock()
        mock_st.header = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock()])
        mock_st.selectbox = Mock(return_value="software_development")
        mock_st.slider = Mock(return_value=5)
        mock_st.text_input = Mock(return_value="Test Simulation")
        mock_st.checkbox = Mock(return_value=True)
        mock_st.button = Mock(return_value=True)
        mock_st.error = Mock()

        from pages.create import render_create_page
        render_create_page()

        # Should handle error gracefully
        mock_st.error.assert_called()


if __name__ == "__main__":
    pytest.main([__file__])
