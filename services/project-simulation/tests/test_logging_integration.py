"""Tests for Project Simulation logging integration with LogCollectorClient."""

import asyncio
import os
import sys
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from main import app, logger_client

from services.shared.utilities.logging_client import LogCollectorClient


class TestProjectSimulationLoggingIntegration:
    """Test Project Simulation logging integration with LogCollectorClient."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)

    @pytest.fixture
    def mock_logger_client(self):
        """Mock LogCollectorClient."""
        mock_client = AsyncMock(spec=LogCollectorClient)
        return mock_client

    @pytest.fixture(autouse=True)
    async def setup_logger_client(self, mock_logger_client):
        """Setup mock logger client for all tests."""
        global logger_client
        logger_client = mock_logger_client
        yield
        logger_client = None

    @pytest.mark.asyncio
    async def test_simulation_creation_successful_logging(self, client, mock_logger_client):
        """Test successful simulation creation logging."""
        # Mock the application service
        mock_simulation_result = {
            "success": True,
            "simulation_id": "sim_12345",
            "message": "Simulation created successfully",
            "simulation": {
                "team": [{"role": "developer"}, {"role": "manager"}],
                "milestones": [{"name": "Planning"}, {"name": "Development"}],
                "requirements": [{"type": "functional"}, {"type": "non-functional"}],
            },
        }

        with patch("main.application_service") as mock_app_service, patch(
            "main.SimulationResource"
        ) as mock_sim_resource, patch("main.create_crud_response") as mock_crud_response:

            mock_app_service.create_simulation.return_value = mock_simulation_result
            mock_sim_resource.create_simulation_links.return_value = {"self": "/api/v1/simulations/sim_12345"}
            mock_crud_response.return_value = {"operation": "create", "resource_id": "sim_12345"}

            # Make request
            request_data = {
                "name": "Test Project",
                "description": "A test simulation project",
                "duration_weeks": 12,
                "complexity": "medium",
                "technologies": ["Python", "FastAPI", "React"],
                "requirements": ["User authentication", "Data persistence"],
                "team": [{"role": "developer", "count": 3}],
                "milestones": [{"name": "Planning", "week": 2}],
            }

            response = client.post("/api/v1/simulations", json=request_data)
            assert response.status_code == 201

            # Verify logging calls
            assert mock_logger_client.log_business_event.call_count >= 2  # start and completion
            assert mock_logger_client.log_info.call_count >= 1

            # Check business events
            business_calls = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] in ["simulation_creation_started", "simulation_creation_completed"]
            ]

            assert len(business_calls) == 2

            # Check start event
            start_call = next(call for call in business_calls if call[0][0] == "simulation_creation_started")
            start_data = start_call[0][1]
            assert start_data["project_name"] == "Test Project"
            assert start_data["duration_weeks"] == 12
            assert start_data["complexity"] == "medium"
            assert start_data["technologies"] == ["Python", "FastAPI", "React"]
            assert start_data["has_requirements"] is True
            assert start_data["has_team"] is True
            assert start_data["has_milestones"] is True
            assert "correlation_id" in start_data

            # Check completion event
            completion_call = next(call for call in business_calls if call[0][0] == "simulation_creation_completed")
            completion_data = completion_call[0][1]
            assert completion_data["simulation_id"] == "sim_12345"
            assert completion_data["project_name"] == "Test Project"
            assert completion_data["team_size"] == 2
            assert completion_data["milestones_count"] == 2
            assert completion_data["requirements_count"] == 2
            assert completion_data["success"] is True

    @pytest.mark.asyncio
    async def test_simulation_creation_failure_logging(self, client, mock_logger_client):
        """Test failed simulation creation logging."""
        # Mock the application service to return failure
        mock_failure_result = {"success": False, "message": "Invalid project configuration"}

        with patch("main.application_service") as mock_app_service:
            mock_app_service.create_simulation.return_value = mock_failure_result

            # Make request
            request_data = {
                "name": "Invalid Project",
                "description": "This will fail",
                "duration_weeks": -5,  # Invalid duration
                "complexity": "invalid",
            }

            response = client.post("/api/v1/simulations", json=request_data)
            assert response.status_code == 400

            # Verify error logging
            assert mock_logger_client.log_business_event.call_count >= 2  # start and failure

            # Check failure business event
            failure_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "simulation_creation_failed"
            ]
            assert len(failure_events) >= 1

            failure_data = failure_events[0][0][1]
            assert failure_data["project_name"] == "Invalid Project"
            assert failure_data["failure_reason"] == "Invalid project configuration"
            assert failure_data["error_type"] == "validation_error"

    @pytest.mark.asyncio
    async def test_simulation_creation_exception_logging(self, client, mock_logger_client):
        """Test simulation creation exception logging."""
        # Mock the application service to raise an exception
        with patch("main.application_service") as mock_app_service:
            mock_app_service.create_simulation.side_effect = Exception("Database connection failed")

            # Make request
            request_data = {
                "name": "Test Project",
                "description": "Will fail with exception",
                "duration_weeks": 8,
                "complexity": "low",
            }

            response = client.post("/api/v1/simulations", json=request_data)
            assert response.status_code == 500

            # Verify error logging
            assert mock_logger_client.log_error.call_count >= 1
            assert mock_logger_client.log_business_event.call_count >= 2  # start and failure

            # Check error call
            error_calls = mock_logger_client.log_error.call_args_list
            sim_error = next((call for call in error_calls if "Simulation creation failed" in call[0][0]), None)
            assert sim_error is not None
            assert sim_error[0][1]["project_name"] == "Test Project"
            assert sim_error[0][1]["error_type"] == "Exception"
            assert "Database connection failed" in sim_error[0][1]["error_type"]

            # Check failure business event
            failure_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "simulation_creation_failed"
            ]
            assert len(failure_events) >= 1

            failure_data = failure_events[0][0][1]
            assert failure_data["project_name"] == "Test Project"
            assert failure_data["error_type"] == "Exception"
            assert "Database connection failed" in failure_data["error_message"]
            assert failure_data["failure_stage"] == "execution"

    @pytest.mark.asyncio
    async def test_startup_logging(self, mock_logger_client):
        """Test service startup logging."""
        from main import startup_event

        await startup_event()

        # Verify startup logging
        assert mock_logger_client.log_business_event.call_count >= 1

        # Check startup business event
        business_call = mock_logger_client.log_business_event.call_args
        assert business_call[0][0] == "project_simulation_startup"
        startup_data = business_call[0][1]
        assert "capabilities" in startup_data
        assert "integrations" in startup_data
        assert "features" in startup_data
        assert "websocket_communication" in startup_data["features"]
        assert "correlation_tracking" in startup_data["features"]

    @pytest.mark.asyncio
    async def test_shutdown_logging(self, mock_logger_client):
        """Test service shutdown logging."""
        from main import shutdown_event

        # Set logger client
        global logger_client
        logger_client = mock_logger_client

        await shutdown_event()

        # Verify shutdown logging
        assert mock_logger_client.log_info.call_count >= 1

        info_call = mock_logger_client.log_info.call_args
        assert "Project Simulation service shutting down" in info_call[0][0]

    @pytest.mark.asyncio
    async def test_different_simulation_complexities_logging(self, client, mock_logger_client):
        """Test logging for different simulation complexities."""
        complexities = ["low", "medium", "high"]

        for complexity in complexities:
            # Mock successful creation
            mock_result = {
                "success": True,
                "simulation_id": f"sim_{complexity}_123",
                "simulation": {"team": [], "milestones": [], "requirements": []},
            }

            with patch("main.application_service") as mock_app_service, patch(
                "main.SimulationResource"
            ) as mock_sim_resource, patch("main.create_crud_response") as mock_crud_response:

                mock_app_service.create_simulation.return_value = mock_result
                mock_sim_resource.create_simulation_links.return_value = {
                    "self": f"/api/v1/simulations/sim_{complexity}_123"
                }
                mock_crud_response.return_value = {"operation": "create", "resource_id": f"sim_{complexity}_123"}

                # Make request
                request_data = {
                    "name": f"{complexity.title()} Complexity Project",
                    "description": f"A {complexity} complexity simulation",
                    "duration_weeks": 8,
                    "complexity": complexity,
                    "technologies": ["Python"],
                }

                response = client.post("/api/v1/simulations", json=request_data)
                assert response.status_code == 201

                # Check that complexity is correctly logged
                completion_events = [
                    call
                    for call in mock_logger_client.log_business_event.call_args_list
                    if call[0][0] == "simulation_creation_completed"
                ]

                # Get the most recent completion event
                completion_data = completion_events[-1][0][1]
                assert completion_data["complexity"] == complexity
                assert completion_data["simulation_id"] == f"sim_{complexity}_123"

    @pytest.mark.asyncio
    async def test_simulation_creation_with_teams_and_milestones_logging(self, client, mock_logger_client):
        """Test logging for simulations with complex team and milestone structures."""
        # Mock complex simulation result
        mock_result = {
            "success": True,
            "simulation_id": "sim_complex_456",
            "simulation": {
                "team": [
                    {"role": "developer", "count": 3},
                    {"role": "designer", "count": 2},
                    {"role": "manager", "count": 1},
                    {"role": "qa", "count": 2},
                    {"role": "devops", "count": 1},
                ],
                "milestones": [
                    {"name": "Planning", "week": 2},
                    {"name": "Design", "week": 4},
                    {"name": "Development", "week": 8},
                    {"name": "Testing", "week": 10},
                    {"name": "Deployment", "week": 12},
                    {"name": "Launch", "week": 13},
                ],
                "requirements": [
                    {"type": "functional", "description": "User login"},
                    {"type": "non-functional", "description": "Performance"},
                    {"type": "security", "description": "Data encryption"},
                ],
            },
        }

        with patch("main.application_service") as mock_app_service, patch(
            "main.SimulationResource"
        ) as mock_sim_resource, patch("main.create_crud_response") as mock_crud_response:

            mock_app_service.create_simulation.return_value = mock_result
            mock_sim_resource.create_simulation_links.return_value = {"self": "/api/v1/simulations/sim_complex_456"}
            mock_crud_response.return_value = {"operation": "create", "resource_id": "sim_complex_456"}

            # Make request with complex structure
            request_data = {
                "name": "Complex Enterprise Project",
                "description": "Large scale project simulation",
                "duration_weeks": 16,
                "complexity": "high",
                "technologies": ["Python", "React", "PostgreSQL", "Docker", "Kubernetes"],
                "requirements": ["Advanced user auth", "Real-time features", "Multi-tenant"],
                "team": [{"role": "developer", "count": 3}, {"role": "designer", "count": 2}],
                "milestones": [{"name": "Planning", "week": 2}, {"name": "Development", "week": 8}],
            }

            response = client.post("/api/v1/simulations", json=request_data)
            assert response.status_code == 201

            # Check completion event has correct metrics
            completion_events = [
                call
                for call in mock_logger_client.log_business_event.call_args_list
                if call[0][0] == "simulation_creation_completed"
            ]
            assert len(completion_events) >= 1

            completion_data = completion_events[0][0][1]
            assert completion_data["team_size"] == 5  # 5 team members in mock result
            assert completion_data["milestones_count"] == 6  # 6 milestones in mock result
            assert completion_data["requirements_count"] == 3  # 3 requirements in mock result
            assert completion_data["complexity"] == "high"
            assert len(completion_data["technologies_used"]) == 5

    @pytest.mark.asyncio
    async def test_logging_disabled_graceful_handling(self, client):
        """Test graceful handling when logging is disabled."""
        # Set logger client to None
        global logger_client
        logger_client = None

        # Mock application service
        mock_result = {
            "success": True,
            "simulation_id": "sim_no_log_789",
            "simulation": {"team": [], "milestones": [], "requirements": []},
        }

        with patch("main.application_service") as mock_app_service, patch(
            "main.SimulationResource"
        ) as mock_sim_resource, patch("main.create_crud_response") as mock_crud_response:

            mock_app_service.create_simulation.return_value = mock_result
            mock_sim_resource.create_simulation_links.return_value = {"self": "/api/v1/simulations/sim_no_log_789"}
            mock_crud_response.return_value = {"operation": "create", "resource_id": "sim_no_log_789"}

            # Make request - should still work without logging
            request_data = {
                "name": "No Logging Test",
                "description": "Testing without logger client",
                "duration_weeks": 4,
                "complexity": "low",
            }

            response = client.post("/api/v1/simulations", json=request_data)
            assert response.status_code == 201

    def test_request_id_generation(self, client, mock_logger_client):
        """Test that correlation IDs are properly generated and used."""
        # Mock successful creation
        mock_result = {
            "success": True,
            "simulation_id": "sim_corr_101",
            "simulation": {"team": [], "milestones": [], "requirements": []},
        }

        with patch("main.application_service") as mock_app_service, patch(
            "main.SimulationResource"
        ) as mock_sim_resource, patch("main.create_crud_response") as mock_crud_response:

            mock_app_service.create_simulation.return_value = mock_result
            mock_sim_resource.create_simulation_links.return_value = {"self": "/api/v1/simulations/sim_corr_101"}
            mock_crud_response.return_value = {"operation": "create", "resource_id": "sim_corr_101"}

            # Make request
            request_data = {"name": "Correlation Test", "duration_weeks": 6, "complexity": "medium"}
            client.post("/api/v1/simulations", json=request_data)

            # Check that correlation IDs are generated and used consistently
            business_calls = mock_logger_client.log_business_event.call_args_list

            # Extract correlation IDs from simulation creation events
            correlation_ids = set()
            for call in business_calls:
                if len(call[0]) > 1 and isinstance(call[0][1], dict):
                    correlation_id = call[0][1].get("correlation_id")
                    if correlation_id and "simulation_creation" in call[0][0]:
                        correlation_ids.add(correlation_id)

            # All simulation creation events should use the same correlation ID
            assert len(correlation_ids) == 1

    @pytest.mark.asyncio
    async def test_performance_metrics_not_tracked_for_creation(self, client, mock_logger_client):
        """Test that performance metrics are not tracked for simulation creation (unlike some other services)."""
        # Mock successful creation
        mock_result = {
            "success": True,
            "simulation_id": "sim_perf_202",
            "simulation": {"team": [], "milestones": [], "requirements": []},
        }

        with patch("main.application_service") as mock_app_service, patch(
            "main.SimulationResource"
        ) as mock_sim_resource, patch("main.create_crud_response") as mock_crud_response:

            mock_app_service.create_simulation.return_value = mock_result
            mock_sim_resource.create_simulation_links.return_value = {"self": "/api/v1/simulations/sim_perf_202"}
            mock_crud_response.return_value = {"operation": "create", "resource_id": "sim_perf_202"}

            # Make request
            request_data = {"name": "Performance Test", "duration_weeks": 10, "complexity": "high"}
            response = client.post("/api/v1/simulations", json=request_data)
            assert response.status_code == 201

            # Check that no performance metrics are logged for creation (unlike some other services)
            perf_calls = mock_logger_client.log_performance_metric.call_args_list
            # Should be 0 for simulation creation (unlike other services that track timing)
            assert len(perf_calls) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
