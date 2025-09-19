"""Unit Tests for Domain Events - Domain Driven Design Foundation.

This module contains comprehensive unit tests for domain events,
testing event creation, serialization, deserialization, and event handling.
"""

import pytest
from datetime import datetime
from uuid import uuid4

from simulation.domain.events import (
    DomainEvent, ProjectCreated, ProjectStatusChanged, ProjectPhaseCompleted,
    TeamMemberAdded, TeamMemberRemoved, SimulationStarted, SimulationCompleted,
    SimulationFailed, DocumentGenerated, WorkflowExecuted, PhaseStarted,
    PhaseDelayed, MilestoneAchieved, EcosystemServiceHealthChanged,
    DocumentAnalysisCompleted, WorkflowOrchestrationCompleted,
    NotificationSent, AnalyticsDataGenerated, ConfigurationChanged,
    event_from_dict, EVENT_TYPES
)
from simulation.domain.value_objects import ProjectType, ProjectStatus


class TestDomainEventBase:
    """Test cases for base DomainEvent class."""

    def test_domain_event_creation(self):
        """Test creating a domain event."""
        event = TestEvent(event_data="test")
        assert event.event_data == "test"
        assert event.event_version == 1
        assert isinstance(event.occurred_at, datetime)
        assert event.event_id is not None
        assert event.event_type == "TestEvent"

    def test_domain_event_id_uniqueness(self):
        """Test that domain events have unique IDs."""
        event1 = TestEvent(event_data="test1")
        event2 = TestEvent(event_data="test2")

        assert event1.event_id != event2.event_id

    def test_domain_event_serialization(self):
        """Test domain event serialization."""
        event = TestEvent(event_data="test")
        data = event.to_dict()

        assert data["event_id"] == event.event_id
        assert data["event_type"] == "TestEvent"
        assert "occurred_at" in data
        assert data["event_version"] == 1
        assert data["event_data"] == "test"

    def test_domain_event_immutability(self):
        """Test that domain events are immutable after creation."""
        event = TestEvent(event_data="test")

        # Should not be able to modify attributes
        with pytest.raises(AttributeError):
            event.event_data = "modified"

        with pytest.raises(AttributeError):
            event.occurred_at = datetime.now()

    def test_abstract_method_enforcement(self):
        """Test that abstract methods must be implemented."""
        class IncompleteEvent(DomainEvent):
            pass

        with pytest.raises(TypeError):
            IncompleteEvent()


class TestProjectEvents:
    """Test cases for project-related domain events."""

    def test_project_created_event(self):
        """Test ProjectCreated event."""
        event = ProjectCreated(
            project_id="proj-123",
            project_name="Test Project",
            project_type="web_application",
            complexity="medium"
        )

        assert event.get_aggregate_id() == "proj-123"
        assert event.project_id == "proj-123"
        assert event.project_name == "Test Project"
        assert event.project_type == "web_application"

    def test_project_status_changed_event(self):
        """Test ProjectStatusChanged event."""
        event = ProjectStatusChanged(
            project_id="proj-123",
            old_status="created",
            new_status="in_progress",
            changed_by="user@example.com"
        )

        assert event.get_aggregate_id() == "proj-123"
        assert event.old_status == "created"
        assert event.new_status == "in_progress"

    def test_project_phase_completed_event(self):
        """Test ProjectPhaseCompleted event."""
        event = ProjectPhaseCompleted(
            project_id="proj-123",
            phase_name="planning",
            phase_number=1,
            completion_percentage=100.0,
            duration_days=5
        )

        assert event.get_aggregate_id() == "proj-123"
        assert event.phase_name == "planning"
        assert event.phase_number == 1
        assert event.completion_percentage == 100.0
        assert event.duration_days == 5

    def test_team_member_added_event(self):
        """Test TeamMemberAdded event."""
        event = TeamMemberAdded(
            team_id="team-789",
            project_id="proj-123",
            member_id="user-456",
            member_name="John Doe",
            role="developer",
            skills=["python", "django", "react"],
            experience_years=5,
            productivity_factor=1.2
        )

        assert event.get_aggregate_id() == "proj-123"
        assert event.member_id == "user-456"
        assert event.member_name == "John Doe"
        assert event.role == "developer"

    def test_team_member_removed_event(self):
        """Test TeamMemberRemoved event."""
        removal_date = datetime(2024, 1, 15, 10, 0, 0)
        event = TeamMemberRemoved(
            team_id="team-789",
            project_id="proj-123",
            member_id="user-456",
            member_name="John Doe",
            removal_reason="End of contract",
            removal_date=removal_date,
            replacement_planned=True
        )

        assert event.get_aggregate_id() == "proj-123"
        assert event.member_id == "user-456"
        assert event.member_name == "John Doe"


class TestSimulationEvents:
    """Test cases for simulation-related domain events."""

    def test_simulation_started_event(self):
        """Test SimulationStarted event."""
        event = SimulationStarted(
            simulation_id="sim-123",
            project_id="proj-456",
            scenario_type="full_project",
            estimated_duration_hours=8
        )

        assert event.get_aggregate_id() == "sim-123"
        assert event.project_id == "proj-456"
        assert event.scenario_type == "full_project"
        assert event.estimated_duration_hours == 8

    def test_simulation_completed_event(self):
        """Test SimulationCompleted event."""
        end_time = datetime(2024, 1, 1, 12, 0, 0)
        metrics = {"documents": 10, "workflows": 5}

        event = SimulationCompleted(
            simulation_id="sim-123",
            project_id="proj-456",
            end_time=end_time,
            success=True,
            metrics=metrics
        )

        assert event.get_aggregate_id() == "sim-123"
        assert event.success == True
        assert event.metrics == metrics

    def test_simulation_failed_event(self):
        """Test SimulationFailed event."""
        failure_time = datetime(2024, 1, 1, 11, 30, 0)
        event = SimulationFailed(
            simulation_id="sim-123",
            project_id="proj-456",
            failure_reason="Service unavailable",
            failure_time=failure_time
        )

        assert event.get_aggregate_id() == "sim-123"
        assert event.failure_reason == "Service unavailable"
        assert event.failure_time == failure_time

    def test_document_generated_event(self):
        """Test DocumentGenerated event."""
        event = DocumentGenerated(
            simulation_id="sim-123",
            document_id="doc-456",
            document_type="technical_design",
            title="API Design Document",
            word_count=1500
        )

        assert event.get_aggregate_id() == "sim-123"
        assert event.document_id == "doc-456"
        assert event.document_type == "technical_design"
        assert event.word_count == 1500

    def test_workflow_executed_event(self):
        """Test WorkflowExecuted event."""
        event = WorkflowExecuted(
            simulation_id="sim-123",
            workflow_id="wf-456",
            workflow_type="document_generation",
            execution_time_seconds=45.5,
            success=True
        )

        assert event.get_aggregate_id() == "sim-123"
        assert event.workflow_type == "document_generation"
        assert event.execution_time_seconds == 45.5
        assert event.success == True


class TestTimelineEvents:
    """Test cases for timeline-related domain events."""

    def test_phase_started_event(self):
        """Test PhaseStarted event."""
        start_date = datetime(2024, 1, 1, 9, 0, 0)
        event = PhaseStarted(
            timeline_id="tl-123",
            project_id="proj-456",
            phase_name="development",
            start_date=start_date
        )

        assert event.get_aggregate_id() == "tl-123"
        assert event.phase_name == "development"
        assert event.start_date == start_date

    def test_phase_delayed_event(self):
        """Test PhaseDelayed event."""
        original_end = datetime(2024, 1, 10, 17, 0, 0)
        new_end = datetime(2024, 1, 15, 17, 0, 0)

        event = PhaseDelayed(
            timeline_id="tl-123",
            project_id="proj-456",
            phase_name="development",
            original_end_date=original_end,
            new_end_date=new_end,
            delay_reason="Resource constraints"
        )

        assert event.get_aggregate_id() == "tl-123"
        assert event.delay_reason == "Resource constraints"
        assert event.new_end_date > event.original_end_date

    def test_milestone_achieved_event(self):
        """Test MilestoneAchieved event."""
        achieved_date = datetime(2024, 1, 15, 14, 30, 0)
        event = MilestoneAchieved(
            timeline_id="tl-123",
            project_id="proj-456",
            milestone_name="MVP Release",
            achieved_date=achieved_date
        )

        assert event.get_aggregate_id() == "tl-123"
        assert event.milestone_name == "MVP Release"
        assert event.achieved_date == achieved_date


class TestIntegrationEvents:
    """Test cases for integration domain events."""

    def test_ecosystem_service_health_changed_event(self):
        """Test EcosystemServiceHealthChanged event."""
        affected_sims = ["sim-1", "sim-2", "sim-3"]
        event = EcosystemServiceHealthChanged(
            service_name="mock_data_generator",
            old_status="healthy",
            new_status="degraded",
            response_time_ms=2500.0,
            affected_simulations=affected_sims
        )

        assert event.get_aggregate_id() == "mock_data_generator"
        assert event.old_status == "healthy"
        assert event.new_status == "degraded"
        assert event.response_time_ms == 2500.0
        assert event.affected_simulations == affected_sims

    def test_document_analysis_completed_event(self):
        """Test DocumentAnalysisCompleted event."""
        event = DocumentAnalysisCompleted(
            document_id="doc-123",
            analysis_type="quality_check",
            confidence_score=0.85,
            insights_found=5,
            processing_time_seconds=12.3
        )

        assert event.get_aggregate_id() == "doc-123"
        assert event.analysis_type == "quality_check"
        assert event.confidence_score == 0.85
        assert event.insights_found == 5

    def test_workflow_orchestration_completed_event(self):
        """Test WorkflowOrchestrationCompleted event."""
        services = ["mock_data_generator", "analysis_service", "doc_store"]
        event = WorkflowOrchestrationCompleted(
            workflow_id="wf-123",
            orchestration_type="document_pipeline",
            services_involved=services,
            total_execution_time_seconds=45.7,
            success=True
        )

        assert event.get_aggregate_id() == "wf-123"
        assert event.orchestration_type == "document_pipeline"
        assert event.services_involved == services
        assert event.success == True

    def test_notification_sent_event(self):
        """Test NotificationSent event."""
        sent_at = datetime(2024, 1, 1, 10, 15, 0)
        event = NotificationSent(
            notification_id="notif-123",
            recipient="user@example.com",
            notification_type="simulation_complete",
            priority="normal",
            sent_at=sent_at
        )

        assert event.get_aggregate_id() == "notif-123"
        assert event.recipient == "user@example.com"
        assert event.notification_type == "simulation_complete"
        assert event.sent_at == sent_at

    def test_analytics_data_generated_event(self):
        """Test AnalyticsDataGenerated event."""
        event = AnalyticsDataGenerated(
            analytics_id="analytics-123",
            data_type="performance_metrics",
            records_generated=1000,
            time_range_days=30,
            processing_time_seconds=25.5
        )

        assert event.get_aggregate_id() == "analytics-123"
        assert event.data_type == "performance_metrics"
        assert event.records_generated == 1000
        assert event.time_range_days == 30

    def test_configuration_changed_event(self):
        """Test ConfigurationChanged event."""
        affected_services = ["simulation_service", "orchestrator"]
        event = ConfigurationChanged(
            config_id="config-123",
            config_type="environment_settings",
            changed_by="admin@example.com",
            change_description="Updated service timeouts",
            affected_services=affected_services
        )

        assert event.get_aggregate_id() == "config-123"
        assert event.config_type == "environment_settings"
        assert event.changed_by == "admin@example.com"
        assert event.affected_services == affected_services


class TestEventSerialization:
    """Test cases for event serialization and deserialization."""

    def test_event_serialization_roundtrip(self):
        """Test that events can be serialized and deserialized correctly."""
        original_event = ProjectCreated(
            project_id="proj-123",
            project_name="Test Project",
            project_type="web_application"
        )

        # Serialize
        data = original_event.to_dict()

        # Deserialize
        restored_event = event_from_dict(data)

        # Compare
        assert isinstance(restored_event, ProjectCreated)
        assert restored_event.project_id == original_event.project_id
        assert restored_event.project_name == original_event.project_name
        assert restored_event.project_type == original_event.project_type
        assert restored_event.event_type == original_event.event_type

    def test_all_event_types_registered(self):
        """Test that all event types are properly registered."""
        expected_events = [
            "ProjectCreated", "ProjectStatusChanged", "ProjectPhaseCompleted",
            "TeamMemberAdded", "TeamMemberRemoved", "SimulationStarted",
            "SimulationCompleted", "SimulationFailed", "DocumentGenerated",
            "WorkflowExecuted", "PhaseStarted", "PhaseDelayed", "MilestoneAchieved",
            "EcosystemServiceHealthChanged", "DocumentAnalysisCompleted",
            "WorkflowOrchestrationCompleted", "NotificationSent",
            "AnalyticsDataGenerated", "ConfigurationChanged"
        ]

        for event_name in expected_events:
            assert event_name in EVENT_TYPES
            assert EVENT_TYPES[event_name] is not None

    def test_unknown_event_type_deserialization(self):
        """Test that unknown event types raise errors."""
        data = {
            "event_type": "UnknownEvent",
            "event_id": "test-id",
            "occurred_at": datetime.now().isoformat(),
            "event_version": 1,
            "test_data": "value"
        }

        with pytest.raises(ValueError, match="Unknown event type"):
            event_from_dict(data)

    def test_event_serialization_with_datetime(self):
        """Test event serialization with datetime objects."""
        event = SimulationStarted(
            simulation_id="sim-123",
            project_id="proj-456",
            scenario_type="full_project",
            start_time=datetime(2024, 1, 1, 10, 0, 0)
        )

        data = event.to_dict()

        # Should serialize datetime to ISO format
        assert "start_time" in data
        assert isinstance(data["start_time"], str)

        # Should be able to deserialize back
        restored = event_from_dict(data)
        assert isinstance(restored.start_time, datetime)
        assert restored.start_time == event.start_time

    def test_event_serialization_with_optional_fields(self):
        """Test event serialization with optional fields."""
        event = ProjectPhaseCompleted(
            project_id="proj-123",
            phase_name="planning",
            completed_at=None
        )

        data = event.to_dict()
        assert "completed_at" in data
        assert data["completed_at"] is None

        # Should deserialize correctly
        restored = event_from_dict(data)
        assert restored.completed_at is None


class TestEventRegistry:
    """Test cases for event registry functionality."""

    def test_event_registry_completeness(self):
        """Test that event registry contains all defined events."""
        # This test will help catch any missing registrations
        # when new events are added

        # Count actual event classes in the module
        import simulation.domain.events as events_module
        event_classes = []

        for attr_name in dir(events_module):
            attr = getattr(events_module, attr_name)
            if (isinstance(attr, type) and
                issubclass(attr, DomainEvent) and
                attr != DomainEvent):
                event_classes.append(attr_name)

        # Verify all event classes are registered
        for event_class_name in event_classes:
            if event_class_name != "DomainEvent":  # Skip base class
                assert event_class_name in EVENT_TYPES, f"{event_class_name} not registered"

    def test_event_registry_functionality(self):
        """Test that registered events can be instantiated."""
        for event_name, event_class in EVENT_TYPES.items():
            # Try to create a minimal instance for testing
            try:
                if event_name == "ProjectCreated":
                    event = event_class(
                        project_id="test-123",
                        project_name="Test",
                        project_type="test"
                    )
                elif event_name == "ProjectStatusChanged":
                    event = event_class(
                        project_id="test-123",
                        old_status="created",
                        new_status="in_progress"
                    )
                elif event_name == "ProjectPhaseCompleted":
                    event = event_class(
                        project_id="test-123",
                        phase_name="planning",
                        completed_at=None
                    )
                elif event_name == "SimulationStarted":
                    event = event_class(
                        simulation_id="test-123",
                        project_id="proj-456",
                        scenario_type="test",
                        start_time=datetime.now()
                    )
                elif event_name == "SimulationCompleted":
                    event = event_class(
                        simulation_id="test-123",
                        project_id="proj-456",
                        end_time=datetime.now(),
                        success=True,
                        metrics={}
                    )
                elif event_name == "DocumentGenerated":
                    event = event_class(
                        simulation_id="test-123",
                        document_id="doc-456",
                        document_type="test",
                        title="Test Doc",
                        word_count=100
                    )
                elif event_name == "WorkflowExecuted":
                    event = event_class(
                        simulation_id="test-123",
                        workflow_id="wf-456",
                        workflow_type="test",
                        execution_time_seconds=10.0,
                        success=True
                    )
                else:
                    # For other events, skip detailed instantiation test
                    continue

                assert event.event_type == event_name
                assert isinstance(event, DomainEvent)

            except Exception as e:
                pytest.fail(f"Failed to create {event_name}: {e}")


# Helper class for testing
from dataclasses import dataclass

@dataclass(frozen=True)
class TestEvent(DomainEvent):
    """Test event for domain event base class testing."""
    event_data: str

    def get_aggregate_id(self) -> str:
        return "test-aggregate"
