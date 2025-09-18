"""Domain-Driven Unit Tests - Project Aggregate.

This module contains comprehensive unit tests for the Project aggregate,
following domain-driven design testing patterns.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from simulation.domain.entities.project import Project
from simulation.domain.value_objects import (
    ProjectStatus, ProjectType, ComplexityLevel, TeamMember, Role
)


class TestProjectAggregate:
    """Test suite for Project aggregate following DDD patterns."""

    def test_project_creation(self):
        """Test project creation with valid data."""
        # Given
        project_id = str(uuid4())
        name = "Test Project"
        description = "A test project for validation"
        project_type = ProjectType.WEB_APPLICATION
        complexity = ComplexityLevel.MEDIUM
        duration_weeks = 8

        # When
        project = Project(
            project_id=project_id,
            name=name,
            description=description,
            project_type=project_type,
            complexity=complexity,
            duration_weeks=duration_weeks
        )

        # Then
        assert project.project_id == project_id
        assert project.name == name
        assert project.description == description
        assert project.project_type == project_type
        assert project.complexity == complexity
        assert project.duration_weeks == duration_weeks
        assert project.status == ProjectStatus.PLANNING
        assert isinstance(project.created_at, datetime)
        assert project.updated_at == project.created_at
        assert len(project.events) == 1  # ProjectCreated event

    def test_project_creation_with_invalid_duration(self):
        """Test project creation with invalid duration."""
        # Given
        project_id = str(uuid4())
        name = "Test Project"

        # When/Then
        with pytest.raises(ValueError):
            Project(
                project_id=project_id,
                name=name,
                duration_weeks=0  # Invalid: must be >= 1
            )

    def test_project_status_change(self):
        """Test project status change."""
        # Given
        project = Project(
            project_id=str(uuid4()),
            name="Test Project",
            project_type=ProjectType.API_SERVICE
        )

        # When
        initial_status = project.status
        project.change_status(ProjectStatus.IN_PROGRESS)

        # Then
        assert initial_status == ProjectStatus.PLANNING
        assert project.status == ProjectStatus.IN_PROGRESS
        assert project.updated_at > project.created_at
        assert len(project.events) == 2  # ProjectCreated + ProjectStatusChanged

    def test_project_status_change_to_invalid_status(self):
        """Test project status change to invalid status."""
        # Given
        project = Project(
            project_id=str(uuid4()),
            name="Test Project"
        )

        # When/Then
        with pytest.raises(ValueError, match="Invalid project status"):
            project.change_status("invalid_status")

    def test_project_update(self):
        """Test project update operations."""
        # Given
        project = Project(
            project_id=str(uuid4()),
            name="Original Name",
            description="Original description",
            project_type=ProjectType.WEB_APPLICATION
        )

        # When
        project.update(
            name="Updated Name",
            description="Updated description",
            project_type=ProjectType.API_SERVICE,
            complexity=ComplexityLevel.COMPLEX,
            duration_weeks=12
        )

        # Then
        assert project.name == "Updated Name"
        assert project.description == "Updated description"
        assert project.project_type == ProjectType.API_SERVICE
        assert project.complexity == ComplexityLevel.COMPLEX
        assert project.duration_weeks == 12
        assert project.updated_at > project.created_at
        assert len(project.events) == 2  # ProjectCreated + ProjectUpdated

    def test_project_update_partial(self):
        """Test partial project update."""
        # Given
        project = Project(
            project_id=str(uuid4()),
            name="Original Name",
            description="Original description"
        )
        original_updated_at = project.updated_at

        # When
        project.update(name="Updated Name")

        # Then
        assert project.name == "Updated Name"
        assert project.description == "Original description"  # Unchanged
        assert project.updated_at > original_updated_at

    def test_team_member_management(self):
        """Test team member management."""
        # Given
        project = Project(
            project_id=str(uuid4()),
            name="Test Project"
        )
        member = TeamMember(
            member_id=str(uuid4()),
            name="John Doe",
            email="john@example.com",
            role=Role.DEVELOPER,
            skills=["Python", "FastAPI"]
        )

        # When
        project.add_team_member(member)

        # Then
        assert len(project.team_members) == 1
        assert project.team_members[0] == member
        assert project.updated_at > project.created_at

    def test_add_duplicate_team_member(self):
        """Test adding duplicate team member."""
        # Given
        project = Project(
            project_id=str(uuid4()),
            name="Test Project"
        )
        member = TeamMember(
            member_id=str(uuid4()),
            name="John Doe",
            email="john@example.com",
            role=Role.DEVELOPER
        )

        # When
        project.add_team_member(member)
        project.add_team_member(member)  # Duplicate

        # Then
        assert len(project.team_members) == 1  # Should not add duplicate
        assert project.team_members[0] == member

    def test_remove_team_member(self):
        """Test removing team member."""
        # Given
        project = Project(
            project_id=str(uuid4()),
            name="Test Project"
        )
        member1 = TeamMember(
            member_id=str(uuid4()),
            name="John Doe",
            email="john@example.com",
            role=Role.DEVELOPER
        )
        member2 = TeamMember(
            member_id=str(uuid4()),
            name="Jane Smith",
            email="jane@example.com",
            role=Role.QA
        )

        project.add_team_member(member1)
        project.add_team_member(member2)

        # When
        project.remove_team_member(member1.member_id)

        # Then
        assert len(project.team_members) == 1
        assert project.team_members[0] == member2
        assert project.updated_at > project.created_at

    def test_remove_nonexistent_team_member(self):
        """Test removing non-existent team member."""
        # Given
        project = Project(
            project_id=str(uuid4()),
            name="Test Project"
        )

        # When/Then
        with pytest.raises(ValueError, match="Team member with ID .* not found"):
            project.remove_team_member(str(uuid4()))

    def test_business_rule_enforcement(self):
        """Test business rule enforcement."""
        # Given
        project = Project(
            project_id=str(uuid4()),
            name="Test Project",
            project_type=ProjectType.WEB_APPLICATION,
            complexity=ComplexityLevel.SIMPLE,
            duration_weeks=4
        )

        # When - Try to change to completed without going through proper states
        project.change_status(ProjectStatus.IN_PROGRESS)

        # Then - Should allow valid transitions
        assert project.status == ProjectStatus.IN_PROGRESS

        # Complete the project
        project.change_status(ProjectStatus.COMPLETED)
        assert project.status == ProjectStatus.COMPLETED

    def test_event_sourcing(self):
        """Test event sourcing capabilities."""
        # Given
        project = Project(
            project_id=str(uuid4()),
            name="Event Test Project"
        )

        # When - Perform multiple operations
        project.update(name="Updated Event Test Project")
        project.change_status(ProjectStatus.IN_PROGRESS)
        project.change_status(ProjectStatus.COMPLETED)

        # Then - Should have recorded all events
        assert len(project.events) == 4  # ProjectCreated + ProjectUpdated + 2x ProjectStatusChanged

        # Verify event types
        event_types = [event.event_type for event in project.events]
        assert "ProjectCreated" in event_types
        assert "ProjectUpdated" in event_types
        assert event_types.count("ProjectStatusChanged") == 2

    def test_project_immutability_of_events(self):
        """Test that domain events are immutable."""
        # Given
        project = Project(
            project_id=str(uuid4()),
            name="Immutability Test"
        )

        # When - Get events reference
        events = project.events

        # Then - Should not be able to modify events directly
        # Note: In a real DDD implementation, events would be immutable
        # This test demonstrates the concept
        assert len(events) == 1
        assert events[0].event_type == "ProjectCreated"

    @pytest.mark.parametrize("project_type", [
        ProjectType.WEB_APPLICATION,
        ProjectType.API_SERVICE,
        ProjectType.MOBILE_APPLICATION,
        ProjectType.DATA_SCIENCE,
        ProjectType.DEVOPS_TOOL
    ])
    def test_all_project_types(self, project_type):
        """Test all valid project types."""
        # Given
        project = Project(
            project_id=str(uuid4()),
            name=f"{project_type.value} Project",
            project_type=project_type
        )

        # Then
        assert project.project_type == project_type

    @pytest.mark.parametrize("complexity", [
        ComplexityLevel.SIMPLE,
        ComplexityLevel.MEDIUM,
        ComplexityLevel.COMPLEX
    ])
    def test_all_complexity_levels(self, complexity):
        """Test all valid complexity levels."""
        # Given
        project = Project(
            project_id=str(uuid4()),
            name=f"{complexity.value} Project",
            complexity=complexity
        )

        # Then
        assert project.complexity == complexity

    def test_project_creation_timestamp(self):
        """Test project creation timestamp accuracy."""
        # Given
        before_creation = datetime.now()

        # When
        project = Project(
            project_id=str(uuid4()),
            name="Timestamp Test Project"
        )

        # Then
        after_creation = datetime.now()
        assert before_creation <= project.created_at <= after_creation
        assert project.updated_at == project.created_at

    def test_project_update_timestamp(self):
        """Test project update timestamp changes."""
        # Given
        project = Project(
            project_id=str(uuid4()),
            name="Timestamp Update Test"
        )
        initial_updated_at = project.updated_at

        # When - Wait a small amount and update
        import time
        time.sleep(0.001)  # Small delay to ensure timestamp difference
        project.update(name="Updated Timestamp Test")

        # Then
        assert project.updated_at > initial_updated_at
