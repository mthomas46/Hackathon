"""Functional Tests - End-to-End Simulation Workflows.

This module contains comprehensive functional tests for complete
simulation workflows, testing the entire system from creation to completion.
"""

import pytest
from datetime import datetime
from uuid import uuid4
import httpx
import asyncio

from simulation.application.services.simulation_application_service import SimulationApplicationService
from simulation.infrastructure.di_container import get_simulation_container
from simulation.infrastructure.repositories.in_memory_repositories import get_repository_registry
from simulation.domain.value_objects import (
    ProjectType, ComplexityLevel, SimulationConfig
)
from simulation.infrastructure.clients.ecosystem_clients import (
    get_mock_data_generator_client, get_doc_store_client,
    get_orchestrator_client, get_analysis_service_client
)


class TestSimulationWorkflowFunctional:
    """Functional tests for complete simulation workflows."""

    @pytest.fixture
    def app_service(self):
        """Create application service for testing."""
        container = get_simulation_container()
        return container.simulation_application_service

    @pytest.fixture
    def repositories(self):
        """Get repository registry for testing."""
        return get_repository_registry()

    def test_create_simulation_workflow(self, app_service, repositories):
        """Test complete simulation creation workflow."""
        # Given
        simulation_data = {
            "name": "Functional Test Project",
            "description": "Testing complete simulation workflow",
            "type": "web_application",
            "team_size": 4,
            "complexity": "medium",
            "duration_weeks": 6
        }

        # When
        result = asyncio.run(app_service.create_simulation(simulation_data))

        # Then
        assert result["success"] is True
        assert "simulation_id" in result
        assert result["message"] == "Simulation created successfully"

        # Verify simulation was persisted
        simulation_id = result["simulation_id"]
        simulation_repo = repositories.simulations
        simulation = simulation_repo.find_by_id(simulation_id)
        assert simulation is not None
        assert simulation.config.project_name == "Functional Test Project"
        assert simulation.status.value == "initialized"

    def test_simulation_execution_workflow(self, app_service, repositories):
        """Test complete simulation execution workflow."""
        # Given - Create a simulation first
        simulation_data = {
            "name": "Execution Test Project",
            "description": "Testing simulation execution",
            "type": "api_service",
            "team_size": 3,
            "complexity": "simple",
            "duration_weeks": 4
        }

        create_result = asyncio.run(app_service.create_simulation(simulation_data))
        assert create_result["success"] is True
        simulation_id = create_result["simulation_id"]

        # When - Execute the simulation
        execution_result = asyncio.run(app_service.execute_simulation(simulation_id))

        # Then
        assert execution_result["success"] is True
        assert execution_result["simulation_id"] == simulation_id
        assert "execution_time_seconds" in execution_result

        # Verify simulation status changed
        simulation_repo = repositories.simulations
        simulation = simulation_repo.find_by_id(simulation_id)
        assert simulation is not None
        assert simulation.status.value in ["running", "completed"]

    def test_simulation_status_tracking_workflow(self, app_service, repositories):
        """Test simulation status tracking throughout workflow."""
        # Given - Create simulation
        simulation_data = {
            "name": "Status Tracking Test",
            "type": "mobile_application",
            "team_size": 5,
            "complexity": "complex",
            "duration_weeks": 8
        }

        create_result = asyncio.run(app_service.create_simulation(simulation_data))
        simulation_id = create_result["simulation_id"]

        # When - Check status at different points
        initial_status = asyncio.run(app_service.get_simulation_status(simulation_id))

        # Execute simulation
        asyncio.run(app_service.execute_simulation(simulation_id))

        # Check status after execution
        post_execution_status = asyncio.run(app_service.get_simulation_status(simulation_id))

        # Then - Verify status progression
        assert initial_status["success"] is True
        assert initial_status["status"] == "initialized"
        assert initial_status["simulation_id"] == simulation_id

        assert post_execution_status["success"] is True
        assert post_execution_status["simulation_id"] == simulation_id
        # Status should be running or completed
        assert post_execution_status["status"] in ["running", "completed", "failed"]

    def test_simulation_cancellation_workflow(self, app_service, repositories):
        """Test simulation cancellation workflow."""
        # Given - Create and start simulation
        simulation_data = {
            "name": "Cancellation Test Project",
            "type": "web_application",
            "team_size": 3,
            "complexity": "medium",
            "duration_weeks": 5
        }

        create_result = asyncio.run(app_service.create_simulation(simulation_data))
        simulation_id = create_result["simulation_id"]

        # Start execution
        asyncio.run(app_service.execute_simulation(simulation_id))

        # When - Cancel the simulation
        cancel_result = asyncio.run(app_service.cancel_simulation(simulation_id))

        # Then
        assert cancel_result["success"] is True
        assert cancel_result["simulation_id"] == simulation_id
        assert "cancelled_at" in cancel_result

        # Verify simulation was cancelled
        simulation_repo = repositories.simulations
        simulation = simulation_repo.find_by_id(simulation_id)
        assert simulation is not None
        assert simulation.status.value == "cancelled"

    def test_multiple_simulations_workflow(self, app_service, repositories):
        """Test managing multiple simultaneous simulations."""
        # Given - Create multiple simulations
        simulation_configs = [
            {
                "name": f"Multi-Simulation Test {i}",
                "type": "web_application",
                "team_size": 3 + i,
                "complexity": "medium",
                "duration_weeks": 4 + i
            }
            for i in range(3)
        ]

        simulation_ids = []
        for config in simulation_configs:
            result = asyncio.run(app_service.create_simulation(config))
            assert result["success"] is True
            simulation_ids.append(result["simulation_id"])

        # When - List all simulations
        list_result = asyncio.run(app_service.list_simulations())

        # Then
        assert list_result["success"] is True
        assert list_result["total"] >= 3

        # Verify all our simulations are in the list
        simulation_ids_in_list = [s["id"] for s in list_result["simulations"]]
        for sim_id in simulation_ids:
            assert sim_id in simulation_ids_in_list

    def test_simulation_results_workflow(self, app_service, repositories):
        """Test accessing simulation results after completion."""
        # Given - Create and complete simulation
        simulation_data = {
            "name": "Results Test Project",
            "type": "api_service",
            "team_size": 4,
            "complexity": "medium",
            "duration_weeks": 6
        }

        create_result = asyncio.run(app_service.create_simulation(simulation_data))
        simulation_id = create_result["simulation_id"]

        # Execute simulation
        asyncio.run(app_service.execute_simulation(simulation_id))

        # When - Try to get results
        results_result = asyncio.run(app_service.get_simulation_results(simulation_id))

        # Then - Results should be accessible (even if simulation is still running)
        assert "success" in results_result
        assert results_result["simulation_id"] == simulation_id

        # If simulation completed, should have actual results
        if results_result["success"]:
            # Should have some result structure
            assert "results" in results_result or "message" in results_result

    def test_simulation_health_integration(self, app_service):
        """Test simulation service health integration."""
        # When - Check health
        health_result = asyncio.run(app_service.get_health_status())

        # Then
        assert health_result["success"] is True
        assert "health" in health_result
        assert "service_health" in health_result["health"]
        assert "system_health" in health_result["health"]
        assert "simulation_specific" in health_result["health"]

    @pytest.mark.parametrize("project_type", ["web_application", "api_service", "mobile_application"])
    def test_different_project_types_workflow(self, app_service, project_type):
        """Test simulation workflow with different project types."""
        # Given
        simulation_data = {
            "name": f"{project_type.replace('_', ' ').title()} Test",
            "type": project_type,
            "team_size": 4,
            "complexity": "medium",
            "duration_weeks": 6
        }

        # When
        create_result = asyncio.run(app_service.create_simulation(simulation_data))
        execution_result = asyncio.run(app_service.execute_simulation(create_result["simulation_id"]))

        # Then
        assert create_result["success"] is True
        assert execution_result["success"] is True
        assert execution_result["simulation_id"] == create_result["simulation_id"]

    @pytest.mark.parametrize("complexity", ["simple", "medium", "complex"])
    def test_different_complexity_levels_workflow(self, app_service, complexity):
        """Test simulation workflow with different complexity levels."""
        # Given
        simulation_data = {
            "name": f"{complexity.title()} Complexity Test",
            "type": "web_application",
            "team_size": 3 if complexity == "simple" else 5 if complexity == "medium" else 7,
            "complexity": complexity,
            "duration_weeks": 4 if complexity == "simple" else 8 if complexity == "medium" else 12
        }

        # When
        create_result = asyncio.run(app_service.create_simulation(simulation_data))
        execution_result = asyncio.run(app_service.execute_simulation(create_result["simulation_id"]))

        # Then
        assert create_result["success"] is True
        assert execution_result["success"] is True

    def test_simulation_error_handling_workflow(self, app_service):
        """Test simulation error handling and recovery."""
        # Given - Try to execute non-existent simulation
        invalid_simulation_id = str(uuid4())

        # When
        execution_result = asyncio.run(app_service.execute_simulation(invalid_simulation_id))
        status_result = asyncio.run(app_service.get_simulation_status(invalid_simulation_id))
        results_result = asyncio.run(app_service.get_simulation_results(invalid_simulation_id))

        # Then - Should handle errors gracefully
        assert execution_result["success"] is False
        assert "error" in execution_result or "message" in execution_result

        assert status_result["success"] is False
        assert "error" in status_result

        assert results_result["success"] is False
        assert "error" in results_result

    def test_simulation_concurrent_operations(self, app_service, repositories):
        """Test concurrent simulation operations."""
        # Given - Create multiple simulations
        simulation_ids = []
        for i in range(3):
            simulation_data = {
                "name": f"Concurrent Test {i}",
                "type": "web_application",
                "team_size": 3,
                "complexity": "simple",
                "duration_weeks": 4
            }
            result = asyncio.run(app_service.create_simulation(simulation_data))
            simulation_ids.append(result["simulation_id"])

        # When - Execute all simulations concurrently
        async def execute_and_check(simulation_id):
            exec_result = await app_service.execute_simulation(simulation_id)
            status_result = await app_service.get_simulation_status(simulation_id)
            return exec_result, status_result

        # Run concurrent operations
        tasks = [execute_and_check(sid) for sid in simulation_ids]
        results = asyncio.run(asyncio.gather(*tasks))

        # Then - All operations should succeed
        for exec_result, status_result in results:
            assert exec_result["success"] is True
            assert status_result["success"] is True

    def test_simulation_data_consistency(self, app_service, repositories):
        """Test data consistency across simulation operations."""
        # Given - Create simulation
        simulation_data = {
            "name": "Consistency Test Project",
            "type": "api_service",
            "team_size": 4,
            "complexity": "medium",
            "duration_weeks": 6
        }

        create_result = asyncio.run(app_service.create_simulation(simulation_data))
        simulation_id = create_result["simulation_id"]

        # When - Perform multiple operations
        status1 = asyncio.run(app_service.get_simulation_status(simulation_id))
        asyncio.run(app_service.execute_simulation(simulation_id))
        status2 = asyncio.run(app_service.get_simulation_status(simulation_id))

        # Then - Data should remain consistent
        assert status1["simulation_id"] == simulation_id
        assert status2["simulation_id"] == simulation_id
        assert status1["created_at"] == status2["created_at"]  # Creation time shouldn't change

        # Status should progress logically
        initial_status = status1["status"]
        final_status = status2["status"]

        # Should not go backwards in status progression
        status_order = ["initialized", "running", "completed", "failed", "cancelled"]
        initial_index = status_order.index(initial_status)
        final_index = status_order.index(final_status)
        assert final_index >= initial_index

    def test_simulation_workflow_with_ecosystem_integration(self, app_service):
        """Test simulation workflow with ecosystem service integration."""
        # This test would integrate with actual ecosystem services
        # For now, we'll test the integration points

        # Given - Create simulation
        simulation_data = {
            "name": "Ecosystem Integration Test",
            "type": "web_application",
            "team_size": 5,
            "complexity": "medium",
            "duration_weeks": 8
        }

        create_result = asyncio.run(app_service.create_simulation(simulation_data))
        simulation_id = create_result["simulation_id"]

        # When - Execute simulation (which should integrate with ecosystem)
        execution_result = asyncio.run(app_service.execute_simulation(simulation_id))

        # Then - Should handle ecosystem integration gracefully
        # (Actual integration testing would require running ecosystem services)
        assert "success" in execution_result
        assert execution_result["simulation_id"] == simulation_id

        # If ecosystem services are available, execution should succeed
        # If not available, should handle gracefully with appropriate error
        if not execution_result["success"]:
            assert "error" in execution_result or "message" in execution_result
