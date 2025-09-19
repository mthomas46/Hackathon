"""Unit Tests for Domain Events - Event-Driven Engine Testing.

This module contains unit tests for domain events, event handling, and
event-driven architecture components in the simulation system.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json

from simulation.domain.events import (
    DomainEvent, ProjectCreated, ProjectStatusChanged, ProjectPhaseCompleted,
    SimulationStarted, SimulationCompleted, DocumentGenerated, TimelineEventOccurred,
    TeamMemberAdded, TeamMemberRemoved, PhaseStarted, PhaseCompleted,
    WorkflowExecuted, AnalysisCompleted, EcosystemServiceCalled,
    domain_event_registry, get_event_type, create_event_from_dict
)
from simulation.domain.value_objects import (
    ProjectType, ComplexityLevel, ProjectStatus, SimulationStatus
)


class TestDomainEventBase:
    """Test cases for the base DomainEvent class."""

    def test_domain_event_creation(self):
        """Test basic domain event creation."""
        event = DomainEvent()
        event.event_version = 1

        assert event.event_version == 1
        assert isinstance(event.occurred_at, datetime)
        assert event.event_id is not None
        assert event.event_type is not None

    def test_domain_event_initialization(self):
        """Test domain event initialization with custom values."""
        custom_time = datetime.now() - timedelta(hours=1)

        event = DomainEvent()
        event.occurred_at = custom_time
        event.event_version = 2

        assert event.occurred_at == custom_time
        assert event.event_version == 2

    def test_domain_event_id_generation(self):
        """Test automatic event ID generation."""
        event = DomainEvent()

        # Trigger post-init
        event.__post_init__()

        assert event.event_id is not None
        assert isinstance(event.event_id, str)
        assert "DomainEvent" in event.event_id

    def test_domain_event_type_setting(self):
        """Test automatic event type setting."""
        event = DomainEvent()

        # Trigger post-init
        event.__post_init__()

        assert event.event_type == "DomainEvent"

    def test_domain_event_to_dict(self):
        """Test domain event serialization to dictionary."""
        event = DomainEvent()
        event.event_version = 1
        event.__post_init__()

        event_dict = event.to_dict()

        assert isinstance(event_dict, dict)
        assert "event_id" in event_dict
        assert "event_type" in event_dict
        assert "occurred_at" in event_dict
        assert "event_version" in event_dict
        assert event_dict["event_type"] == "DomainEvent"
        assert event_dict["event_version"] == 1

    def test_domain_event_immutability(self):
        """Test domain event immutability (frozen dataclass)."""
        event = DomainEvent()

        # Should be able to set attributes during creation
        assert event.event_version == 1

        # But should be immutable after creation
        with pytest.raises(AttributeError):
            event.new_attribute = "test"


class TestProjectEvents:
    """Test cases for project-related domain events."""

    def test_project_created_event(self):
        """Test ProjectCreated event creation and properties."""
        event = ProjectCreated(
            project_id="proj-123",
            project_name="Test Project",
            project_type="web_application",
            complexity="medium"
        )

        assert event.project_id == "proj-123"
        assert event.project_name == "Test Project"
        assert event.project_type == "web_application"
        assert event.complexity == "medium"
        assert event.event_type == "ProjectCreated"

    def test_project_created_event_serialization(self):
        """Test ProjectCreated event serialization."""
        event = ProjectCreated(
            project_id="proj-123",
            project_name="Test Project",
            project_type="web_application",
            complexity="medium"
        )

        event_dict = event.to_dict()

        assert event_dict["project_id"] == "proj-123"
        assert event_dict["project_name"] == "Test Project"
        assert event_dict["project_type"] == "web_application"
        assert event_dict["complexity"] == "medium"
        assert "event_id" in event_dict
        assert "occurred_at" in event_dict

    def test_project_status_changed_event(self):
        """Test ProjectStatusChanged event."""
        event = ProjectStatusChanged(
            project_id="proj-123",
            old_status="planning",
            new_status="in_progress",
            changed_by="user@example.com"
        )

        assert event.project_id == "proj-123"
        assert event.old_status == "planning"
        assert event.new_status == "in_progress"
        assert event.changed_by == "user@example.com"
        assert event.event_type == "ProjectStatusChanged"

    def test_project_phase_completed_event(self):
        """Test ProjectPhaseCompleted event."""
        event = ProjectPhaseCompleted(
            project_id="proj-123",
            phase_name="design",
            phase_number=2,
            completion_percentage=100.0,
            duration_days=15
        )

        assert event.project_id == "proj-123"
        assert event.phase_name == "design"
        assert event.phase_number == 2
        assert event.completion_percentage == 100.0
        assert event.duration_days == 15
        assert event.event_type == "ProjectPhaseCompleted"


class TestSimulationEvents:
    """Test cases for simulation-related domain events."""

    def test_simulation_started_event(self):
        """Test SimulationStarted event."""
        event = SimulationStarted(
            simulation_id="sim-456",
            project_id="proj-123",
            scenario_type="comprehensive",
            estimated_duration_hours=24
        )

        assert event.simulation_id == "sim-456"
        assert event.project_id == "proj-123"
        assert event.scenario_type == "comprehensive"
        assert event.estimated_duration_hours == 24
        assert event.event_type == "SimulationStarted"

    def test_simulation_completed_event(self):
        """Test SimulationCompleted event."""
        metrics = {
            "total_documents": 25,
            "processing_time_hours": 18.5,
            "quality_score": 0.87,
            "success_rate": 0.95
        }

        event = SimulationCompleted(
            simulation_id="sim-456",
            project_id="proj-123",
            status="completed",
            metrics=metrics,
            total_duration_hours=22.0
        )

        assert event.simulation_id == "sim-456"
        assert event.project_id == "proj-123"
        assert event.status == "completed"
        assert event.metrics == metrics
        assert event.total_duration_hours == 22.0
        assert event.event_type == "SimulationCompleted"


class TestDocumentEvents:
    """Test cases for document-related domain events."""

    def test_document_generated_event(self):
        """Test DocumentGenerated event."""
        metadata = {
            "word_count": 1200,
            "quality_score": 0.85,
            "author": "test@example.com",
            "generation_time_seconds": 2.5
        }

        event = DocumentGenerated(
            document_id="doc-789",
            project_id="proj-123",
            simulation_id="sim-456",
            document_type="requirements_doc",
            title="System Requirements",
            content_hash="abc123def456",
            metadata=metadata
        )

        assert event.document_id == "doc-789"
        assert event.project_id == "proj-123"
        assert event.simulation_id == "sim-456"
        assert event.document_type == "requirements_doc"
        assert event.title == "System Requirements"
        assert event.content_hash == "abc123def456"
        assert event.metadata == metadata
        assert event.event_type == "DocumentGenerated"

    def test_document_generated_event_with_minimal_data(self):
        """Test DocumentGenerated event with minimal required data."""
        event = DocumentGenerated(
            document_id="doc-789",
            project_id="proj-123",
            document_type="confluence_page",
            title="Test Page"
        )

        assert event.document_id == "doc-789"
        assert event.project_id == "proj-123"
        assert event.document_type == "confluence_page"
        assert event.title == "Test Page"
        assert event.simulation_id is None
        assert event.content_hash is None
        assert event.metadata == {}


class TestTimelineEvents:
    """Test cases for timeline-related domain events."""

    def test_timeline_event_occurred(self):
        """Test TimelineEventOccurred event."""
        event_data = {
            "event_type": "milestone",
            "title": "Sprint 1 Complete",
            "description": "Successfully completed first development sprint",
            "impact": "high",
            "category": "delivery"
        }

        event = TimelineEventOccurred(
            timeline_id="timeline-101",
            project_id="proj-123",
            simulation_id="sim-456",
            event_date=datetime.now(),
            event_data=event_data
        )

        assert event.timeline_id == "timeline-101"
        assert event.project_id == "proj-123"
        assert event.simulation_id == "sim-456"
        assert isinstance(event.event_date, datetime)
        assert event.event_data == event_data
        assert event.event_type == "TimelineEventOccurred"

    def test_phase_started_event(self):
        """Test PhaseStarted event."""
        event = PhaseStarted(
            phase_id="phase-design-001",
            project_id="proj-123",
            simulation_id="sim-456",
            phase_name="Design",
            phase_number=2,
            estimated_duration_days=14,
            dependencies=["phase-planning-001"]
        )

        assert event.phase_id == "phase-design-001"
        assert event.project_id == "proj-123"
        assert event.simulation_id == "sim-456"
        assert event.phase_name == "Design"
        assert event.phase_number == 2
        assert event.estimated_duration_days == 14
        assert event.dependencies == ["phase-planning-001"]
        assert event.event_type == "PhaseStarted"

    def test_phase_completed_event(self):
        """Test PhaseCompleted event."""
        metrics = {
            "actual_duration_days": 16,
            "documents_generated": 8,
            "quality_score": 0.88,
            "budget_utilization": 0.75
        }

        event = PhaseCompleted(
            phase_id="phase-design-001",
            project_id="proj-123",
            simulation_id="sim-456",
            phase_name="Design",
            phase_number=2,
            metrics=metrics,
            next_phase="Development"
        )

        assert event.phase_id == "phase-design-001"
        assert event.project_id == "proj-123"
        assert event.simulation_id == "sim-456"
        assert event.phase_name == "Design"
        assert event.phase_number == 2
        assert event.metrics == metrics
        assert event.next_phase == "Development"
        assert event.event_type == "PhaseCompleted"


class TestTeamEvents:
    """Test cases for team-related domain events."""

    def test_team_member_added_event(self):
        """Test TeamMemberAdded event."""
        skills = ["Python", "FastAPI", "PostgreSQL"]
        event = TeamMemberAdded(
            team_id="team-alpha",
            project_id="proj-123",
            member_id="member-001",
            member_name="Alice Johnson",
            role="developer",
            skills=skills,
            experience_years=5,
            productivity_factor=1.2
        )

        assert event.team_id == "team-alpha"
        assert event.project_id == "proj-123"
        assert event.member_id == "member-001"
        assert event.member_name == "Alice Johnson"
        assert event.role == "developer"
        assert event.skills == skills
        assert event.experience_years == 5
        assert event.productivity_factor == 1.2
        assert event.event_type == "TeamMemberAdded"

    def test_team_member_removed_event(self):
        """Test TeamMemberRemoved event."""
        event = TeamMemberRemoved(
            team_id="team-alpha",
            project_id="proj-123",
            member_id="member-001",
            member_name="Bob Smith",
            removal_reason="end_of_contract",
            removal_date=datetime.now(),
            replacement_planned=True
        )

        assert event.team_id == "team-alpha"
        assert event.project_id == "proj-123"
        assert event.member_id == "member-001"
        assert event.member_name == "Bob Smith"
        assert event.removal_reason == "end_of_contract"
        assert isinstance(event.removal_date, datetime)
        assert event.replacement_planned == True
        assert event.event_type == "TeamMemberRemoved"


class TestWorkflowEvents:
    """Test cases for workflow-related domain events."""

    def test_workflow_executed_event(self):
        """Test WorkflowExecuted event."""
        parameters = {
            "service": "mock_data_generator",
            "operation": "generate_project_docs",
            "complexity": "high",
            "document_types": ["requirements", "design"]
        }

        results = {
            "status": "success",
            "documents_generated": 5,
            "processing_time_seconds": 45.2,
            "quality_score": 0.89
        }

        event = WorkflowExecuted(
            workflow_id="workflow-789",
            simulation_id="sim-456",
            workflow_type="document_generation",
            parameters=parameters,
            results=results,
            execution_time_seconds=45.2
        )

        assert event.workflow_id == "workflow-789"
        assert event.simulation_id == "sim-456"
        assert event.workflow_type == "document_generation"
        assert event.parameters == parameters
        assert event.results == results
        assert event.execution_time_seconds == 45.2
        assert event.event_type == "WorkflowExecuted"

    def test_analysis_completed_event(self):
        """Test AnalysisCompleted event."""
        analysis_results = {
            "overall_quality_score": 0.85,
            "completeness_score": 0.90,
            "consistency_score": 0.82,
            "issues_found": 3,
            "recommendations": ["Improve documentation", "Add code examples"]
        }

        event = AnalysisCompleted(
            analysis_id="analysis-101",
            simulation_id="sim-456",
            project_id="proj-123",
            analysis_type="document_quality",
            target_documents=["doc1", "doc2", "doc3"],
            results=analysis_results,
            processing_time_seconds=12.5
        )

        assert event.analysis_id == "analysis-101"
        assert event.simulation_id == "sim-456"
        assert event.project_id == "proj-123"
        assert event.analysis_type == "document_quality"
        assert event.target_documents == ["doc1", "doc2", "doc3"]
        assert event.results == analysis_results
        assert event.processing_time_seconds == 12.5
        assert event.event_type == "AnalysisCompleted"


class TestEcosystemEvents:
    """Test cases for ecosystem service-related domain events."""

    def test_ecosystem_service_called_event(self):
        """Test EcosystemServiceCalled event."""
        request_data = {
            "endpoint": "/simulation/project-docs",
            "method": "POST",
            "parameters": {
                "project_type": "web_app",
                "complexity": "medium"
            }
        }

        response_data = {
            "status_code": 200,
            "response_time_seconds": 2.1,
            "documents_generated": 3,
            "success": True
        }

        event = EcosystemServiceCalled(
            service_name="mock_data_generator",
            simulation_id="sim-456",
            request_data=request_data,
            response_data=response_data,
            call_duration_seconds=2.1,
            success=True
        )

        assert event.service_name == "mock_data_generator"
        assert event.simulation_id == "sim-456"
        assert event.request_data == request_data
        assert event.response_data == response_data
        assert event.call_duration_seconds == 2.1
        assert event.success == True
        assert event.event_type == "EcosystemServiceCalled"

    def test_ecosystem_service_called_with_failure(self):
        """Test EcosystemServiceCalled event with failure."""
        request_data = {"endpoint": "/unavailable", "method": "GET"}
        response_data = {
            "status_code": 503,
            "error": "Service unavailable",
            "retry_count": 2
        }

        event = EcosystemServiceCalled(
            service_name="failing_service",
            simulation_id="sim-456",
            request_data=request_data,
            response_data=response_data,
            call_duration_seconds=5.5,
            success=False
        )

        assert event.service_name == "failing_service"
        assert event.success == False
        assert event.call_duration_seconds == 5.5
        assert event.response_data["status_code"] == 503


class TestEventRegistry:
    """Test cases for domain event registry."""

    def test_domain_event_registry_registration(self):
        """Test that events are properly registered in the registry."""
        # Check that key events are registered
        assert "ProjectCreated" in domain_event_registry
        assert "SimulationStarted" in domain_event_registry
        assert "DocumentGenerated" in domain_event_registry
        assert "WorkflowExecuted" in domain_event_registry

        # Verify registry contains event classes
        assert domain_event_registry["ProjectCreated"] == ProjectCreated
        assert domain_event_registry["SimulationStarted"] == SimulationStarted

    def test_get_event_type_function(self):
        """Test get_event_type function."""
        # Test with registered event
        event_class = get_event_type("ProjectCreated")
        assert event_class == ProjectCreated

        # Test with non-existent event
        event_class = get_event_type("NonExistentEvent")
        assert event_class is None

    def test_create_event_from_dict(self):
        """Test create_event_from_dict function."""
        event_dict = {
            "event_type": "ProjectCreated",
            "event_version": 1,
            "project_id": "proj-123",
            "project_name": "Test Project",
            "project_type": "web_application",
            "complexity": "medium"
        }

        event = create_event_from_dict(event_dict)

        assert isinstance(event, ProjectCreated)
        assert event.project_id == "proj-123"
        assert event.project_name == "Test Project"
        assert event.project_type == "web_application"
        assert event.complexity == "medium"

    def test_create_event_from_dict_invalid_type(self):
        """Test create_event_from_dict with invalid event type."""
        event_dict = {
            "event_type": "InvalidEventType",
            "event_version": 1
        }

        event = create_event_from_dict(event_dict)
        assert event is None

    def test_event_registry_completeness(self):
        """Test that registry contains all expected event types."""
        expected_events = [
            "ProjectCreated", "ProjectStatusChanged", "ProjectPhaseCompleted",
            "SimulationStarted", "SimulationCompleted",
            "DocumentGenerated", "TimelineEventOccurred",
            "TeamMemberAdded", "TeamMemberRemoved",
            "PhaseStarted", "PhaseCompleted",
            "WorkflowExecuted", "AnalysisCompleted",
            "EcosystemServiceCalled"
        ]

        for event_type in expected_events:
            assert event_type in domain_event_registry, f"Missing event type: {event_type}"
            assert hasattr(domain_event_registry[event_type], '__dataclass_fields__'), f"Not a dataclass: {event_type}"


class TestEventSerialization:
    """Test cases for event serialization and deserialization."""

    def test_event_json_serialization(self):
        """Test JSON serialization of events."""
        event = ProjectCreated(
            project_id="proj-123",
            project_name="Test Project",
            project_type="web_application",
            complexity="medium"
        )

        event_dict = event.to_dict()

        # Convert to JSON and back
        json_str = json.dumps(event_dict)
        parsed_dict = json.loads(json_str)

        # Verify all data is preserved
        assert parsed_dict["event_type"] == "ProjectCreated"
        assert parsed_dict["project_id"] == "proj-123"
        assert parsed_dict["project_name"] == "Test Project"
        assert parsed_dict["project_type"] == "web_application"
        assert parsed_dict["complexity"] == "medium"

    def test_event_roundtrip_serialization(self):
        """Test complete roundtrip serialization."""
        original_event = DocumentGenerated(
            document_id="doc-789",
            project_id="proj-123",
            simulation_id="sim-456",
            document_type="requirements_doc",
            title="System Requirements",
            content_hash="abc123def456",
            metadata={"quality_score": 0.85}
        )

        # Serialize to dict
        event_dict = original_event.to_dict()

        # Create new event from dict
        recreated_event = create_event_from_dict(event_dict)

        # Verify all properties match
        assert isinstance(recreated_event, DocumentGenerated)
        assert recreated_event.document_id == original_event.document_id
        assert recreated_event.project_id == original_event.project_id
        assert recreated_event.simulation_id == original_event.simulation_id
        assert recreated_event.document_type == original_event.document_type
        assert recreated_event.title == original_event.title
        assert recreated_event.content_hash == original_event.content_hash
        assert recreated_event.metadata == original_event.metadata

    def test_event_serialization_with_datetime(self):
        """Test event serialization with datetime objects."""
        specific_time = datetime(2024, 1, 15, 10, 30, 45)
        event = TimelineEventOccurred(
            timeline_id="timeline-101",
            project_id="proj-123",
            event_date=specific_time,
            event_data={"type": "milestone"}
        )

        event_dict = event.to_dict()

        # Verify datetime is serialized as ISO string
        assert "event_date" in event_dict
        assert isinstance(event_dict["event_date"], str)

        # Verify it can be parsed back
        parsed_date = datetime.fromisoformat(event_dict["event_date"])
        assert parsed_date == specific_time


class TestEventValidation:
    """Test cases for event validation."""

    def test_event_required_fields_validation(self):
        """Test validation of required event fields."""
        # Test ProjectCreated with missing required fields
        with pytest.raises(TypeError):
            # This should fail because project_id is required
            ProjectCreated(
                project_name="Test Project",
                project_type="web_application",
                complexity="medium"
            )

    def test_event_field_type_validation(self):
        """Test validation of event field types."""
        # Test with correct types
        event = SimulationStarted(
            simulation_id="sim-456",
            project_id="proj-123",
            scenario_type="comprehensive",
            estimated_duration_hours=24
        )

        assert event.estimated_duration_hours == 24

        # Test with string instead of int (should still work due to Python's dynamic typing)
        # But let's verify the field is stored correctly
        event_dict = event.to_dict()
        assert event_dict["estimated_duration_hours"] == 24

    def test_event_relationship_validation(self):
        """Test validation of event relationships."""
        # Create a series of related events
        project_event = ProjectCreated(
            project_id="proj-123",
            project_name="Test Project",
            project_type="web_application",
            complexity="medium"
        )

        simulation_event = SimulationStarted(
            simulation_id="sim-456",
            project_id="proj-123",  # Same project ID
            scenario_type="comprehensive",
            estimated_duration_hours=24
        )

        # Verify relationship through project_id
        assert project_event.project_id == simulation_event.project_id

        # Verify event types are different
        assert project_event.event_type != simulation_event.event_type
        assert project_event.event_type == "ProjectCreated"
        assert simulation_event.event_type == "SimulationStarted"


class TestEventPerformance:
    """Test cases for event performance characteristics."""

    def test_event_creation_performance(self):
        """Test performance of event creation."""
        import time

        # Create multiple events quickly
        start_time = time.time()

        events = []
        for i in range(100):
            event = DocumentGenerated(
                document_id=f"doc-{i}",
                project_id="proj-123",
                document_type="confluence_page",
                title=f"Document {i}"
            )
            events.append(event)

        end_time = time.time()
        creation_time = end_time - start_time

        # Should create 100 events quickly
        assert len(events) == 100
        assert creation_time < 1.0  # Less than 1 second

        # Verify all events are valid
        for event in events:
            assert isinstance(event, DocumentGenerated)
            assert event.event_type == "DocumentGenerated"

    def test_event_serialization_performance(self):
        """Test performance of event serialization."""
        import time

        # Create a complex event
        event = WorkflowExecuted(
            workflow_id="workflow-789",
            simulation_id="sim-456",
            workflow_type="document_generation",
            parameters={"complex": "data"} * 100,  # Large parameters
            results={"large": "result"} * 50,     # Large results
            execution_time_seconds=45.2
        )

        # Test serialization performance
        start_time = time.time()

        for _ in range(100):
            event_dict = event.to_dict()

        end_time = time.time()
        serialization_time = end_time - start_time

        # Should serialize quickly even with large data
        assert serialization_time < 2.0  # Less than 2 seconds for 100 serializations
        assert isinstance(event_dict, dict)
        assert "parameters" in event_dict

    def test_event_registry_lookup_performance(self):
        """Test performance of event registry lookups."""
        import time

        # Test lookup performance
        start_time = time.time()

        for _ in range(1000):
            event_class = get_event_type("ProjectCreated")
            assert event_class == ProjectCreated

        end_time = time.time()
        lookup_time = end_time - start_time

        # Should be very fast lookups
        assert lookup_time < 0.1  # Less than 0.1 seconds for 1000 lookups
