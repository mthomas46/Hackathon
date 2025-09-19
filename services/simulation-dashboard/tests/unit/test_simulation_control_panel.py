"""Unit tests for simulation control panel functionality."""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from datetime import datetime, timedelta

from pages.controls import (
    render_control_panel, execute_control_action, get_simulation_details,
    update_simulation_priority, update_simulation_resources
)


@pytest.mark.unit
class TestControlPanel:
    """Test cases for simulation control panel."""

    @patch('pages.controls.st')
    @patch('pages.controls.get_available_simulations')
    @patch('pages.controls.get_simulation_details')
    def test_control_panel_renders_with_simulations(self, mock_get_details, mock_get_sims, mock_st):
        """Test that control panel renders correctly with available simulations."""
        # Mock data
        mock_get_sims.return_value = [
            {"id": "sim_001", "name": "Test Sim", "status": "running"}
        ]
        mock_get_details.return_value = {
            "id": "sim_001",
            "status": "running",
            "progress": 65.5,
            "elapsed_time": "2h 15m",
            "estimated_time_remaining": "45m"
        }

        # Mock Streamlit components
        mock_st.markdown = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock(), Mock(), Mock()])
        mock_st.metric = Mock()
        mock_st.selectbox = Mock(return_value="sim_001 - Test Sim (running)")
        mock_st.button = Mock(return_value=False)
        mock_st.expander = Mock(return_value=Mock())
        mock_st.slider = Mock(return_value=50)
        mock_st.success = Mock()

        # Execute function
        render_control_panel()

        # Verify key components were called
        assert mock_st.markdown.call_count >= 3
        mock_st.columns.assert_called()
        mock_st.metric.assert_called()
        mock_st.selectbox.assert_called()

    @patch('pages.controls.st')
    @patch('pages.controls.get_available_simulations')
    def test_control_panel_handles_no_simulations(self, mock_get_sims, mock_st):
        """Test control panel behavior when no simulations are available."""
        mock_get_sims.return_value = []

        mock_st.markdown = Mock()
        mock_st.warning = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock()])
        mock_st.selectbox = Mock(return_value="Select a simulation...")

        render_control_panel()

        mock_st.warning.assert_called_once()

    @patch('pages.controls.st')
    @patch('pages.controls.get_simulation_details')
    def test_execute_control_action_success(self, mock_get_details, mock_st):
        """Test successful execution of control action."""
        mock_get_details.return_value = {"id": "sim_001", "status": "running"}

        mock_st.markdown = Mock()
        mock_st.success = Mock()
        mock_st.info = Mock()

        # Mock session state
        mock_st.session_state = {
            'control_operations': []
        }

        execute_control_action("sim_001", "start")

        mock_st.success.assert_called_once()
        mock_st.info.assert_called_once()

        # Verify operation was recorded
        assert len(mock_st.session_state['control_operations']) == 1
        operation = mock_st.session_state['control_operations'][0]
        assert operation['simulation_id'] == "sim_001"
        assert operation['action'] == "start"

    @patch('pages.controls.st')
    def test_execute_control_action_error(self, mock_st):
        """Test control action execution with error."""
        mock_st.error = Mock()
        mock_st.session_state = {}

        # Mock an exception during execution
        with patch('pages.controls.logger') as mock_logger:
            mock_logger.error = Mock()

            # This should handle errors gracefully
            execute_control_action("sim_001", "invalid_action")

            mock_st.error.assert_called_once()

    @patch('pages.controls.st')
    def test_update_simulation_priority(self, mock_st):
        """Test simulation priority update."""
        mock_st.success = Mock()

        update_simulation_priority("sim_001", "High")

        mock_st.success.assert_called_once_with("✅ Priority updated to High for simulation sim_001")

    @patch('pages.controls.st')
    def test_update_simulation_resources(self, mock_st):
        """Test simulation resource update."""
        mock_st.success = Mock()

        update_simulation_resources("sim_001", 80, 1024)

        mock_st.success.assert_called_once_with("✅ Resources updated - CPU: 80%, Memory: 1024MB for simulation sim_001")

    def test_get_simulation_details_structure(self):
        """Test that simulation details return expected structure."""
        details = get_simulation_details("sim_001")

        expected_keys = ['id', 'name', 'status', 'progress', 'elapsed_time', 'estimated_time_remaining']

        for key in expected_keys:
            assert key in details
            assert details[key] is not None

    @patch('pages.controls.st')
    @patch('pages.controls.get_simulation_details')
    def test_render_simulation_controls_complete_flow(self, mock_get_details, mock_st):
        """Test complete simulation controls rendering flow."""
        mock_get_details.return_value = {
            "id": "sim_001",
            "name": "Test Simulation",
            "status": "running",
            "progress": 75.0,
            "elapsed_time": "3h 20m",
            "estimated_time_remaining": "1h 10m",
            "current_phase": "Implementation",
            "cpu_usage": 65.2,
            "memory_usage": 512.8,
            "documents_generated": 25,
            "workflows_executed": 18
        }

        # Mock all necessary Streamlit components
        mock_st.markdown = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock(), Mock(), Mock()])
        mock_st.metric = Mock()
        mock_st.button = Mock(return_value=False)
        mock_st.expander = Mock(return_value=Mock())
        mock_st.slider = Mock(return_value=50)
        mock_st.selectbox = Mock(return_value="Normal")

        # Import and call the function
        from pages.controls import render_simulation_controls
        render_simulation_controls("sim_001")

        # Verify all major components were rendered
        assert mock_st.markdown.call_count >= 2
        assert mock_st.columns.call_count >= 3  # Primary controls, advanced controls, status
        mock_st.metric.assert_called()  # Status metrics
        mock_st.button.assert_called()  # Control buttons


@pytest.mark.unit
class TestBulkOperations:
    """Test cases for bulk operations functionality."""

    @patch('pages.controls.st')
    @patch('pages.controls.get_available_simulations')
    def test_bulk_operations_render_without_selection(self, mock_get_sims, mock_st):
        """Test bulk operations interface when no simulations are selected."""
        mock_get_sims.return_value = [
            {"id": "sim_001", "name": "Test Sim 1"},
            {"id": "sim_002", "name": "Test Sim 2"}
        ]

        mock_st.markdown = Mock()
        mock_st.multiselect = Mock(return_value=[])
        mock_st.info = Mock()

        from pages.controls import render_bulk_operations
        render_bulk_operations()

        mock_st.info.assert_called_with("Select one or more simulations to enable bulk operations.")

    @patch('pages.controls.st')
    @patch('pages.controls.get_available_simulations')
    def test_bulk_operations_with_selection(self, mock_get_sims, mock_st):
        """Test bulk operations with simulation selection."""
        mock_get_sims.return_value = [
            {"id": "sim_001", "name": "Test Sim 1"},
            {"id": "sim_002", "name": "Test Sim 2"}
        ]

        mock_st.markdown = Mock()
        mock_st.multiselect = Mock(return_value=["sim_001 - Test Sim 1"])
        mock_st.button = Mock(return_value=False)
        mock_st.columns = Mock(return_value=[Mock(), Mock(), Mock(), Mock()])

        from pages.controls import render_bulk_operations
        render_bulk_operations()

        # Verify bulk operation buttons are rendered
        assert mock_st.button.call_count >= 4  # Start, Pause, Stop, Cancel

    @patch('pages.controls.st')
    def test_execute_bulk_operation_success(self, mock_st):
        """Test successful bulk operation execution."""
        mock_st.success = Mock()
        mock_st.session_state = {}

        from pages.controls import execute_bulk_operation
        execute_bulk_operation(["sim_001", "sim_002"], "start")

        mock_st.success.assert_called_with("✅ Bulk start initiated for 2 simulations")

        # Verify bulk operation status is set
        assert 'bulk_operation_status' in mock_st.session_state
        status = mock_st.session_state['bulk_operation_status']
        assert status['action'] == 'start'
        assert status['total'] == 2


@pytest.mark.unit
class TestStatusMonitor:
    """Test cases for status monitor functionality."""

    @patch('pages.controls.st')
    @patch('pages.controls.get_available_simulations')
    def test_status_monitor_renders_grid(self, mock_get_sims, mock_st):
        """Test status monitor renders simulation grid."""
        mock_get_sims.return_value = [
            {"id": "sim_001", "name": "Test Sim 1", "status": "running", "progress": 50.0},
            {"id": "sim_002", "name": "Test Sim 2", "status": "paused", "progress": 25.0}
        ]

        mock_st.markdown = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock(), Mock()])
        mock_st.container = Mock(return_value=Mock())

        from pages.controls import render_simulation_status_grid
        render_simulation_status_grid(mock_get_sims.return_value)

        # Verify grid layout is created
        assert mock_st.columns.call_count >= 2  # Should create columns for grid
        mock_st.container.assert_called()

    @patch('pages.controls.st')
    def test_status_monitor_resource_display(self, mock_st):
        """Test system resource status display."""
        mock_st.metric = Mock()

        from pages.controls import render_system_resources_status
        render_system_resources_status()

        # Verify resource metrics are displayed
        assert mock_st.metric.call_count >= 4  # CPU, Memory, Disk, Network


@pytest.mark.unit
class TestQueueManagement:
    """Test cases for queue management functionality."""

    @patch('pages.controls.st')
    def test_queue_management_renders_status(self, mock_st):
        """Test queue management renders status correctly."""
        mock_st.markdown = Mock()
        mock_st.columns = Mock(return_value=[Mock(), Mock(), Mock(), Mock()])
        mock_st.metric = Mock()

        from pages.controls import render_queue_management
        render_queue_management()

        # Verify queue status is displayed
        assert mock_st.metric.call_count >= 4  # Queued, Running, Completed, Failed

    @patch('pages.controls.st')
    def test_control_queue_processing(self, mock_st):
        """Test queue processing control."""
        mock_st.success = Mock()

        from pages.controls import control_queue_processing
        control_queue_processing("start")

        mock_st.success.assert_called_with("✅ Queue processing started successfully")

    @patch('pages.controls.st')
    def test_save_queue_configuration(self, mock_st):
        """Test queue configuration saving."""
        mock_st.success = Mock()

        from pages.controls import save_queue_configuration
        save_queue_configuration({
            'max_concurrent': 5,
            'priority_weight': 3,
            'timeout_minutes': 60,
            'retry_attempts': 2
        })

        mock_st.success.assert_called_with("✅ Queue configuration saved successfully")


@pytest.mark.unit
class TestUtilityFunctions:
    """Test cases for utility functions."""

    def test_get_status_color_mapping(self):
        """Test status color mapping function."""
        from pages.controls import get_status_color

        assert get_status_color("running") == "🟢"
        assert get_status_color("paused") == "🟡"
        assert get_status_color("completed") == "✅"
        assert get_status_color("failed") == "❌"
        assert get_status_color("cancelled") == "🚫"
        assert get_status_color("unknown") == "⚪"

    @patch('pages.controls.st')
    def test_get_available_simulations_returns_list(self, mock_st):
        """Test that get_available_simulations returns proper list structure."""
        from pages.controls import get_available_simulations

        simulations = get_available_simulations()

        assert isinstance(simulations, list)
        assert len(simulations) >= 0

        if simulations:  # If there are simulations
            sim = simulations[0]
            assert "id" in sim
            assert "name" in sim
            assert "status" in sim

    def test_simulation_details_structure(self):
        """Test simulation details data structure."""
        details = get_simulation_details("sim_001")

        required_keys = [
            "id", "name", "status", "progress",
            "elapsed_time", "estimated_time_remaining"
        ]

        for key in required_keys:
            assert key in details, f"Missing required key: {key}"

        # Verify data types
        assert isinstance(details["progress"], (int, float))
        assert isinstance(details["elapsed_time"], str)
        assert isinstance(details["estimated_time_remaining"], str)


if __name__ == "__main__":
    pytest.main([__file__])
