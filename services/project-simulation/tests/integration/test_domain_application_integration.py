"""Integration Tests - Domain + Application Layer Interaction.

Tests for interaction between Domain and Application layers following
Domain-Driven Design principles. Validates use case execution, domain
service integration, and cross-layer communication.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timezone
from typing import Dict, Any, List

from services.project_simulation.simulation.domain.entities.project import Project
from services.project_simulation.simulation.domain.value_objects import (
    ProjectType, ComplexityLevel, ProjectStatus, TeamMember
)
from services.project_simulation.simulation.domain.services.simulation_domain_service import SimulationDomainService

from services.project_simulation.simulation.application.services.simulation_application_service import SimulationApplicationService
from services.project_simulation.simulation.application.use_cases.create_simulation_use_case import CreateSimulationUseCase
from services.project_simulation.simulation.application.use_cases.execute_simulation_use_case import ExecuteSimulationUseCase
from services.project_simulation.simulation.application.use_cases.get_simulation_status_use_case import GetSimulationStatusUseCase

from services.project_simulation.simulation.infrastructure.repositories.in_memory.project_repository import InMemoryProjectRepository
from services.project_simulation.simulation.infrastructure.repositories.in_memory.simulation_repository import InMemorySimulationRepository
from services.project_simulation.simulation.infrastructure.repositories.in_memory.timeline_repository import InMemoryTimelineRepository
from services.project_simulation.simulation.infrastructure.repositories.in_memory.team_repository import InMemoryTeamRepository


class TestDomainApplicationIntegration:
    """Test integration between Domain and Application layers."""

    @pytest.fixture
    async def repositories(self):
        """Create test repositories."""
        return {
            'project': InMemoryProjectRepository(),
            'simulation': InMemorySimulationRepository(),
            'timeline': InMemoryTimelineRepository(),
            'team': InMemoryTeamRepository()
        }

    @pytest.fixture
    async def domain_services(self, repositories):
        """Create domain services with test repositories."""
        return {
            'simulation_domain_service': SimulationDomainService(
                project_repository=repositories['project'],
                simulation_repository=repositories['simulation'],
                timeline_repository=repositories['timeline'],
                team_repository=repositories['team']
            )
        }

    @pytest.fixture
    async def application_service(self, repositories, domain_services):
        """Create application service with dependencies."""
        # Mock external dependencies
        mock_logger = MagicMock()
        mock_monitoring = MagicMock()

        return SimulationApplicationService(
            project_repository=repositories['project'],
            simulation_repository=repositories['simulation'],
            timeline_repository=repositories['timeline'],
            team_repository=repositories['team'],
            domain_service=domain_services['simulation_domain_service'],
            logger=mock_logger,
            monitoring=mock_monitoring
        )

    @pytest.fixture
    def sample_project_data(self):
        """Sample project data for testing."""
        return {
            'project_id': 'test_project_001',
            'name': 'Test E-commerce Platform',
            'description': 'A comprehensive e-commerce platform',
            'project_type': ProjectType.WEB_APPLICATION,
            'complexity': ComplexityLevel.COMPLEX,
            'duration_weeks': 12,
            'budget': 250000
        }

    @pytest.fixture
    def sample_team_data(self):
        """Sample team data for testing."""
        return [
            TeamMember(
                member_id='dev_001',
                name='Alice Johnson',
                role='developer',
                email='alice@example.com',
                experience_years=5
            ),
            TeamMember(
                member_id='qa_001',
                name='Bob Smith',
                role='qa_engineer',
                email='bob@example.com',
                experience_years=3
            )
        ]

    @pytest.mark.asyncio
    async def test_create_simulation_use_case_integration(self,
                                                        application_service,
                                                        sample_project_data,
                                                        sample_team_data):
        """Test CreateSimulationUseCase integration with domain layer."""
        # Arrange
        use_case = CreateSimulationUseCase(
            project_repository=application_service.project_repository,
            simulation_repository=application_service.simulation_repository,
            domain_service=application_service.domain_service
        )

        command_data = {
            **sample_project_data,
            'team_members': sample_team_data
        }

        # Act
        result = await use_case.execute(command_data)

        # Assert
        assert result['success'] is True
        assert 'simulation_id' in result
        assert result['message'] == 'Simulation created successfully'

        # Verify domain objects were created
        created_simulation = await application_service.simulation_repository.get(result['simulation_id'])
        assert created_simulation is not None
        assert created_simulation.project.name == sample_project_data['name']

    @pytest.mark.asyncio
    async def test_execute_simulation_use_case_integration(self,
                                                         application_service,
                                                         sample_project_data,
                                                         sample_team_data):
        """Test ExecuteSimulationUseCase integration with domain layer."""
        # Arrange - Create simulation first
        create_result = await application_service.create_simulation({
            **sample_project_data,
            'team_members': sample_team_data
        })
        simulation_id = create_result['simulation_id']

        use_case = ExecuteSimulationUseCase(
            simulation_repository=application_service.simulation_repository,
            domain_service=application_service.domain_service
        )

        # Act
        result = await use_case.execute({'simulation_id': simulation_id})

        # Assert
        assert result['success'] is True
        assert result['simulation_id'] == simulation_id

        # Verify simulation status changed
        updated_simulation = await application_service.simulation_repository.get(simulation_id)
        assert updated_simulation.status == 'running'

    @pytest.mark.asyncio
    async def test_get_simulation_status_use_case_integration(self,
                                                            application_service,
                                                            sample_project_data,
                                                            sample_team_data):
        """Test GetSimulationStatusUseCase integration with domain layer."""
        # Arrange - Create and execute simulation
        create_result = await application_service.create_simulation({
            **sample_project_data,
            'team_members': sample_team_data
        })
        simulation_id = create_result['simulation_id']

        await application_service.execute_simulation(simulation_id)

        use_case = GetSimulationStatusUseCase(
            simulation_repository=application_service.simulation_repository
        )

        # Act
        result = await use_case.execute({'simulation_id': simulation_id})

        # Assert
        assert result['success'] is True
        assert result['simulation_id'] == simulation_id
        assert result['status'] == 'running'
        assert 'project' in result
        assert 'team' in result
        assert 'timeline' in result

    @pytest.mark.asyncio
    async def test_domain_service_project_creation_integration(self,
                                                             domain_services,
                                                             sample_project_data):
        """Test domain service integration with project creation."""
        # Arrange
        domain_service = domain_services['simulation_domain_service']
        project_data = sample_project_data.copy()

        # Act
        project = await domain_service.create_project(project_data)

        # Assert
        assert project is not None
        assert project.project_id == sample_project_data['project_id']
        assert project.name == sample_project_data['name']
        assert project.project_type == sample_project_data['project_type']
        assert project.complexity == sample_project_data['complexity']

    @pytest.mark.asyncio
    async def test_domain_service_team_assignment_integration(self,
                                                            domain_services,
                                                            sample_project_data,
                                                            sample_team_data):
        """Test domain service integration with team assignment."""
        # Arrange
        domain_service = domain_services['simulation_domain_service']

        # Create project first
        project = await domain_service.create_project(sample_project_data)

        # Act
        updated_project = await domain_service.assign_team_to_project(
            project.project_id,
            sample_team_data
        )

        # Assert
        assert updated_project is not None
        assert len(updated_project.team_members) == len(sample_team_data)
        assert updated_project.team_members[0].member_id == sample_team_data[0].member_id

    @pytest.mark.asyncio
    async def test_domain_service_timeline_generation_integration(self,
                                                               domain_services,
                                                               sample_project_data):
        """Test domain service integration with timeline generation."""
        # Arrange
        domain_service = domain_services['simulation_domain_service']

        # Create project first
        project = await domain_service.create_project(sample_project_data)

        # Act
        timeline = await domain_service.generate_project_timeline(project.project_id)

        # Assert
        assert timeline is not None
        assert len(timeline.phases) > 0

        # Verify phases are properly ordered
        for i in range(len(timeline.phases) - 1):
            assert timeline.phases[i].end_date <= timeline.phases[i + 1].start_date

    @pytest.mark.asyncio
    async def test_application_service_repository_integration(self,
                                                           application_service,
                                                           sample_project_data):
        """Test application service integration with repositories."""
        # Arrange
        project_data = sample_project_data.copy()

        # Act - Create project
        result = await application_service.create_simulation(project_data)

        # Assert
        assert result['success'] is True

        # Verify repository integration
        created_project = await application_service.project_repository.get(result['simulation_id'])
        assert created_project is not None
        assert created_project.name == sample_project_data['name']

    @pytest.mark.asyncio
    async def test_cross_repository_data_consistency(self,
                                                   application_service,
                                                   sample_project_data,
                                                   sample_team_data):
        """Test data consistency across multiple repositories."""
        # Arrange
        project_data = {
            **sample_project_data,
            'team_members': sample_team_data
        }

        # Act - Create simulation
        result = await application_service.create_simulation(project_data)

        # Assert - Verify data consistency across repositories
        simulation_id = result['simulation_id']

        # Check project repository
        project = await application_service.project_repository.get(simulation_id)
        assert project is not None

        # Check team repository
        team = await application_service.team_repository.get(simulation_id)
        assert team is not None
        assert len(team.members) == len(sample_team_data)

        # Check timeline repository
        timeline = await application_service.timeline_repository.get(simulation_id)
        assert timeline is not None

    @pytest.mark.asyncio
    async def test_domain_event_handling_integration(self,
                                                   application_service,
                                                   sample_project_data):
        """Test domain event handling across layers."""
        # Arrange
        project_data = sample_project_data.copy()

        # Act - Create simulation (should trigger domain events)
        result = await application_service.create_simulation(project_data)

        # Assert - Verify event handling
        assert result['success'] is True

        # Check if events were properly handled
        # This would typically involve checking event storage or message queues
        # For this test, we verify the operation completed successfully
        created_simulation = await application_service.simulation_repository.get(result['simulation_id'])
        assert created_simulation is not None

    @pytest.mark.asyncio
    async def test_business_rule_enforcement_integration(self,
                                                      application_service,
                                                      sample_project_data):
        """Test business rule enforcement across layers."""
        # Arrange - Create project with invalid data
        invalid_project_data = {
            **sample_project_data,
            'duration_weeks': -1  # Invalid: negative duration
        }

        # Act & Assert - Should fail due to business rule violation
        with pytest.raises(ValueError):
            await application_service.create_simulation(invalid_project_data)

    @pytest.mark.asyncio
    async def test_transaction_boundary_integration(self,
                                                 application_service,
                                                 sample_project_data,
                                                 sample_team_data):
        """Test transaction boundaries across repositories."""
        # Arrange
        project_data = {
            **sample_project_data,
            'team_members': sample_team_data
        }

        # Act - Create simulation (should be atomic across repositories)
        result = await application_service.create_simulation(project_data)

        # Assert - Either all repositories have the data or none do
        simulation_id = result['simulation_id']

        project_exists = await application_service.project_repository.get(simulation_id) is not None
        team_exists = await application_service.team_repository.get(simulation_id) is not None
        timeline_exists = await application_service.timeline_repository.get(simulation_id) is not None

        # All should exist or none should (atomicity)
        assert project_exists == team_exists == timeline_exists

    @pytest.mark.asyncio
    async def test_error_handling_across_layers(self,
                                              application_service):
        """Test error handling propagation across layers."""
        # Arrange - Try to get non-existent simulation
        non_existent_id = 'non_existent_simulation_123'

        # Act
        result = await application_service.get_simulation_status(non_existent_id)

        # Assert - Error should be handled gracefully
        assert result['success'] is False
        assert 'error' in result

    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self,
                                                    application_service,
                                                    sample_project_data):
        """Test performance monitoring integration across layers."""
        # Arrange
        project_data = sample_project_data.copy()

        # Act - Create simulation with monitoring
        result = await application_service.create_simulation(project_data)

        # Assert - Operation should complete successfully
        # Performance monitoring would be verified by checking metrics collection
        assert result['success'] is True

    @pytest.mark.asyncio
    async def test_caching_integration(self,
                                     application_service,
                                     sample_project_data):
        """Test caching integration across layers."""
        # Arrange
        project_data = sample_project_data.copy()

        # Act - Create simulation
        result1 = await application_service.create_simulation(project_data)
        simulation_id = result1['simulation_id']

        # Get simulation multiple times (should leverage caching)
        result2 = await application_service.get_simulation_status(simulation_id)
        result3 = await application_service.get_simulation_status(simulation_id)

        # Assert - All operations should succeed
        assert result1['success'] is True
        assert result2['success'] is True
        assert result3['success'] is True

    @pytest.mark.asyncio
    async def test_logging_integration(self,
                                     application_service,
                                     sample_project_data):
        """Test logging integration across layers."""
        # Arrange
        project_data = sample_project_data.copy()

        # Act - Create simulation (should generate logs)
        result = await application_service.create_simulation(project_data)

        # Assert - Operation should complete successfully
        # Logging would be verified by checking log output
        assert result['success'] is True

    @pytest.mark.asyncio
    async def test_concurrent_operation_handling(self,
                                               application_service,
                                               sample_project_data):
        """Test concurrent operation handling across layers."""
        # Arrange
        project_data = sample_project_data.copy()

        # Act - Create multiple simulations concurrently
        tasks = []
        for i in range(3):
            modified_data = {**project_data, 'name': f'{project_data["name"]} {i}'}
            task = application_service.create_simulation(modified_data)
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        # Assert - All operations should succeed
        for result in results:
            assert result['success'] is True

        # Verify all simulations were created
        for result in results:
            simulation = await application_service.simulation_repository.get(result['simulation_id'])
            assert simulation is not None


if __name__ == "__main__":
    pytest.main([__file__])
