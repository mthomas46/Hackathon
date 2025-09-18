"""Integration Tests - Domain Event Cross-Boundary Communication.

This module contains integration tests for domain event communication
across bounded contexts, testing event-driven interactions.
"""

import pytest
from datetime import datetime
from uuid import uuid4
import asyncio

from simulation.domain.entities.project import Project
from simulation.domain.entities.timeline import Timeline
from simulation.domain.entities.team import Team
from simulation.domain.entities.simulation import Simulation
from simulation.domain.value_objects import (
    ProjectStatus, ProjectType, ComplexityLevel, TeamMember, Role,
    Phase, PhaseStatus, SimulationStatus, SimulationConfig
)
from simulation.domain.events import (
    ProjectCreated, ProjectStatusChanged, ProjectUpdated,
    PhaseStarted, PhaseCompleted, SimulationStarted, SimulationCompleted,
    DocumentGenerated, WorkflowExecuted
)
from simulation.infrastructure.events.domain_event_publisher import (
    DomainEventBus, get_domain_event_bus, publish_domain_event
)
from simulation.infrastructure.repositories.in_memory_repositories import (
    InMemoryProjectRepository, InMemoryTimelineRepository,
    InMemoryTeamRepository, InMemorySimulationRepository
)


class TestDomainEventIntegration:
    """Integration tests for domain event communication across boundaries."""

    @pytest.fixture
    def event_bus(self):
        """Create a fresh event bus for each test."""
        bus = DomainEventBus()
        yield bus
        # Clean up
        bus._event_bus = None

    @pytest.fixture
    def repositories(self):
        """Create fresh repositories for each test."""
        repos = {
            "projects": InMemoryProjectRepository(),
            "timelines": InMemoryTimelineRepository(),
            "teams": InMemoryTeamRepository(),
            "simulations": InMemorySimulationRepository()
        }
        yield repos

        # Reset repositories
        for repo in repos.values():
            if hasattr(repo, '_projects'):
                repo._projects.clear()
            if hasattr(repo, '_timelines'):
                repo._timelines.clear()
            if hasattr(repo, '_teams'):
                repo._teams.clear()
            if hasattr(repo, '_simulations'):
                repo._simulations.clear()

    @pytest.mark.asyncio
    async def test_project_creation_triggers_events(self, event_bus, repositories):
        """Test that project creation triggers appropriate domain events."""
        # Given
        await event_bus.initialize()
        project_repo = repositories["projects"]
        received_events = []

        # Subscribe to project events
        async def handle_project_created(event: ProjectCreated):
            received_events.append(event)

        event_bus.publisher.subscribe("ProjectCreated", handle_project_created)

        # When
        project = Project(
            project_id=str(uuid4()),
            name="Event Integration Test Project",
            description="Testing domain event integration",
            project_type=ProjectType.WEB_APPLICATION,
            complexity=ComplexityLevel.MEDIUM,
            duration_weeks=6
        )
        project_repo.save(project)

        # Publish project creation event
        await event_bus.publish(project.events[0])

        # Then
        await asyncio.sleep(0.1)  # Allow event processing
        assert len(received_events) == 1
        assert received_events[0].event_type == "ProjectCreated"
        assert received_events[0].project_id == project.project_id
        assert received_events[0].project_name == project.name

    @pytest.mark.asyncio
    async def test_project_status_change_cascades(self, event_bus, repositories):
        """Test that project status changes trigger cascading domain events."""
        # Given
        await event_bus.initialize()
        project_repo = repositories["projects"]
        timeline_repo = repositories["timelines"]
        received_events = []

        # Create project and timeline
        project = Project(
            project_id=str(uuid4()),
            name="Cascade Test Project",
            project_type=ProjectType.API_SERVICE
        )
        project_repo.save(project)

        timeline = Timeline(
            timeline_id=str(uuid4()),
            project_id=project.project_id,
            phases=[
                Phase(
                    phase_id=str(uuid4()),
                    name="Planning",
                    start_date=datetime.now(),
                    end_date=datetime.now().replace(hour=23, minute=59),
                    duration_days=1
                )
            ]
        )
        timeline_repo.save(timeline)

        # Subscribe to events
        async def handle_event(event):
            received_events.append(event)

        event_bus.publisher.subscribe("ProjectStatusChanged", handle_event)
        event_bus.publisher.subscribe("PhaseStarted", handle_event)

        # When - Change project status to in progress
        project.change_status(ProjectStatus.IN_PROGRESS)
        project_repo.save(project)

        # Publish the status change event
        await event_bus.publish(project.events[-1])  # Last event is the status change

        # Simulate timeline service reacting to project status change
        if project.status == ProjectStatus.IN_PROGRESS:
            # Start first phase
            first_phase = timeline.phases[0]
            timeline.start_phase(first_phase.phase_id)
            timeline_repo.save(timeline)
            await event_bus.publish(timeline.events[-1])

        # Then
        await asyncio.sleep(0.1)  # Allow event processing
        event_types = [e.event_type for e in received_events]

        assert "ProjectStatusChanged" in event_types
        assert "PhaseStarted" in event_types

        # Verify event data
        status_change_events = [e for e in received_events if e.event_type == "ProjectStatusChanged"]
        assert len(status_change_events) == 1
        assert status_change_events[0].project_id == project.project_id
        assert status_change_events[0].new_status == ProjectStatus.IN_PROGRESS

    @pytest.mark.asyncio
    async def test_simulation_lifecycle_events(self, event_bus, repositories):
        """Test simulation lifecycle triggers appropriate domain events."""
        # Given
        await event_bus.initialize()
        simulation_repo = repositories["simulations"]
        received_events = []

        # Subscribe to simulation events
        async def handle_simulation_event(event):
            received_events.append(event)

        event_bus.publisher.subscribe("SimulationStarted", handle_simulation_event)
        event_bus.publisher.subscribe("SimulationCompleted", handle_simulation_event)
        event_bus.publisher.subscribe("WorkflowExecuted", handle_simulation_event)

        # Create simulation configuration
        config = SimulationConfig(
            project_name="Simulation Event Test",
            project_type=ProjectType.WEB_APPLICATION,
            team_size=3,
            complexity=ComplexityLevel.SIMPLE,
            duration_weeks=4,
            team_member_details=[],
            timeline_phases_config=[],
            document_generation_config={},
            analysis_config={},
            reporting_config={}
        )

        # When - Create and run simulation
        simulation = Simulation(
            simulation_id=str(uuid4()),
            project_id=str(uuid4()),
            config=config
        )
        simulation_repo.save(simulation)

        # Start simulation
        simulation.start()
        simulation_repo.save(simulation)
        await event_bus.publish(simulation.events[-1])

        # Simulate workflow execution
        workflow_event = WorkflowExecuted(
            simulation_id=simulation.simulation_id,
            workflow_type="document_generation",
            success=True,
            execution_time_seconds=2.5,
            documents_generated=5
        )
        await event_bus.publish(workflow_event)

        # Complete simulation
        simulation.complete()
        simulation_repo.save(simulation)
        await event_bus.publish(simulation.events[-1])

        # Then
        await asyncio.sleep(0.1)  # Allow event processing
        event_types = [e.event_type for e in received_events]

        assert "SimulationStarted" in event_types
        assert "WorkflowExecuted" in event_types
        assert "SimulationCompleted" in event_types

        # Verify workflow event details
        workflow_events = [e for e in received_events if e.event_type == "WorkflowExecuted"]
        assert len(workflow_events) == 1
        assert workflow_events[0].simulation_id == simulation.simulation_id
        assert workflow_events[0].workflow_type == "document_generation"
        assert workflow_events[0].success is True
        assert workflow_events[0].execution_time_seconds == 2.5

    @pytest.mark.asyncio
    async def test_cross_context_document_generation(self, event_bus, repositories):
        """Test document generation events across simulation and document contexts."""
        # Given
        await event_bus.initialize()
        project_repo = repositories["projects"]
        received_events = []

        # Subscribe to document events
        async def handle_document_event(event):
            received_events.append(event)

        event_bus.publisher.subscribe("DocumentGenerated", handle_document_event)

        # Create project
        project = Project(
            project_id=str(uuid4()),
            name="Document Generation Test",
            project_type=ProjectType.WEB_APPLICATION
        )
        project_repo.save(project)

        # When - Simulate document generation triggered by project creation
        # This would typically be handled by application services
        document_events = [
            DocumentGenerated(
                simulation_id=str(uuid4()),
                document_type="requirements",
                document_title=f"{project.name} - Requirements",
                word_count=1200,
                generation_time_seconds=1.2
            ),
            DocumentGenerated(
                simulation_id=str(uuid4()),
                document_type="architecture",
                document_title=f"{project.name} - Architecture",
                word_count=800,
                generation_time_seconds=0.8
            )
        ]

        for event in document_events:
            await event_bus.publish(event)

        # Then
        await asyncio.sleep(0.1)  # Allow event processing
        assert len(received_events) == 2

        for event in received_events:
            assert event.event_type == "DocumentGenerated"
            assert event.simulation_id is not None
            assert event.document_type in ["requirements", "architecture"]
            assert event.word_count > 0
            assert event.generation_time_seconds > 0

    @pytest.mark.asyncio
    async def test_event_replay_functionality(self, event_bus):
        """Test event replay functionality for debugging and analytics."""
        # Given
        await event_bus.initialize()

        # Create some events
        events_to_publish = [
            ProjectCreated(
                project_id=str(uuid4()),
                project_name="Replay Test Project",
                project_type=ProjectType.API_SERVICE
            ),
            ProjectStatusChanged(
                project_id=str(uuid4()),
                new_status=ProjectStatus.IN_PROGRESS
            ),
            SimulationStarted(
                simulation_id=str(uuid4()),
                project_id=str(uuid4())
            )
        ]

        # Publish events
        for event in events_to_publish:
            await event_bus.publish(event)

        # When - Replay all events
        replayed_events = await event_bus.publisher.replay_events()

        # Then
        assert len(replayed_events) == 3
        assert all(e in events_to_publish for e in replayed_events)

        # When - Replay specific event type
        project_events = await event_bus.publisher.replay_events("ProjectCreated")
        status_events = await event_bus.publisher.replay_events("ProjectStatusChanged")

        # Then
        assert len(project_events) == 1
        assert project_events[0].event_type == "ProjectCreated"
        assert len(status_events) == 1
        assert status_events[0].event_type == "ProjectStatusChanged"

    @pytest.mark.asyncio
    async def test_event_bus_error_handling(self, event_bus):
        """Test event bus error handling and resilience."""
        # Given
        await event_bus.initialize()

        # Subscribe with a handler that raises an exception
        async def failing_handler(event):
            raise ValueError("Handler failed intentionally")

        async def successful_handler(event):
            successful_handler.call_count += 1

        successful_handler.call_count = 0

        event_bus.publisher.subscribe("TestEvent", failing_handler)
        event_bus.publisher.subscribe("TestEvent", successful_handler)

        # When - Publish event that causes handler to fail
        test_event = ProjectCreated(
            project_id=str(uuid4()),
            project_name="Error Handling Test",
            project_type=ProjectType.WEB_APPLICATION
        )
        test_event.event_type = "TestEvent"  # Override for testing

        await event_bus.publish(test_event)

        # Then - Successful handler should still execute despite failing handler
        await asyncio.sleep(0.1)  # Allow event processing
        assert successful_handler.call_count == 1

    @pytest.mark.asyncio
    async def test_event_bus_cleanup(self, event_bus):
        """Test event bus cleanup and resource management."""
        # Given
        await event_bus.initialize()

        event_count = 0
        async def counting_handler(event):
            nonlocal event_count
            event_count += 1

        event_bus.publisher.subscribe("CleanupTest", counting_handler)

        # When - Publish events
        for i in range(3):
            event = ProjectCreated(
                project_id=str(uuid4()),
                project_name=f"Cleanup Test {i}",
                project_type=ProjectType.WEB_APPLICATION
            )
            event.event_type = "CleanupTest"
            await event_bus.publish(event)

        # Then - Events should be processed
        await asyncio.sleep(0.1)
        assert event_count == 3

        # When - Clear events
        event_bus.publisher.clear_published_events()

        # Then - Event history should be cleared
        assert len(event_bus.publisher.get_published_events()) == 0

        # When - Publish new event
        new_event = ProjectCreated(
            project_id=str(uuid4()),
            project_name="After Cleanup",
            project_type=ProjectType.API_SERVICE
        )
        new_event.event_type = "CleanupTest"
        await event_bus.publish(new_event)

        # Then - Only new event should be in history
        await asyncio.sleep(0.1)
        assert len(event_bus.publisher.get_published_events()) == 1
        assert event_count == 4  # Should have incremented for new event

    @pytest.mark.asyncio
    async def test_concurrent_event_processing(self, event_bus):
        """Test concurrent event processing and thread safety."""
        # Given
        await event_bus.initialize()

        processed_events = []
        async def thread_safe_handler(event):
            # Simulate some processing time
            await asyncio.sleep(0.01)
            processed_events.append(event.event_id)

        event_bus.publisher.subscribe("ConcurrentTest", thread_safe_handler)

        # When - Publish multiple events concurrently
        events = []
        for i in range(10):
            event = ProjectCreated(
                project_id=str(uuid4()),
                project_name=f"Concurrent Test {i}",
                project_type=ProjectType.WEB_APPLICATION
            )
            event.event_type = "ConcurrentTest"
            events.append(event)

        # Publish all events concurrently
        tasks = [event_bus.publish(event) for event in events]
        await asyncio.gather(*tasks)

        # Then - All events should be processed
        await asyncio.sleep(0.2)  # Allow processing time
        assert len(processed_events) == 10

        # Verify all event IDs are unique and accounted for
        event_ids = [e.event_id for e in events]
        assert len(set(processed_events)) == 10
        assert all(eid in processed_events for eid in event_ids)
