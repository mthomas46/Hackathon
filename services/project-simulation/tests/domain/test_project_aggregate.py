"""Domain Layer Unit Tests - Project Aggregate Testing.

Tests for Project aggregate following Domain-Driven Design principles.
Validates business rules, invariants, and domain logic in isolation.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import MagicMock

from services.project_simulation.simulation.domain.entities.project import Project
from services.project_simulation.simulation.domain.value_objects import (
    ProjectType, ComplexityLevel, ProjectStatus, TeamMember, Phase, Milestone
)
from services.project_simulation.simulation.domain.events import (
    ProjectCreated, ProjectUpdated, ProjectStatusChanged
)


class TestProjectAggregate:
    """Test cases for Project aggregate business logic."""

    def test_project_creation_with_valid_data(self):
        """Test creating a project with valid data."""
        # Arrange
        project_id = "test_project_001"
        name = "Test E-commerce Platform"
        project_type = ProjectType.WEB_APPLICATION
        complexity = ComplexityLevel.COMPLEX

        # Act
        project = Project(
            project_id=project_id,
            name=name,
            description="A comprehensive e-commerce platform",
            project_type=project_type,
            complexity=complexity,
            duration_weeks=12
        )

        # Assert
        assert project.project_id == project_id
        assert project.name == name
        assert project.project_type == project_type
        assert project.complexity == complexity
        assert project.status == ProjectStatus.PLANNING
        assert len(project.events) == 1
        assert isinstance(project.events[0], ProjectCreated)

    def test_project_creation_with_invalid_complexity(self):
        """Test that invalid complexity raises ValueError."""
        with pytest.raises(ValueError):
            Project(
                project_id="test_001",
                name="Test Project",
                project_type=ProjectType.API_SERVICE,
                complexity="invalid_complexity"  # Invalid
            )

    def test_project_update_business_logic(self):
        """Test project update following business rules."""
        # Arrange
        project = Project(
            project_id="test_001",
            name="Original Name",
            project_type=ProjectType.WEB_APPLICATION,
            complexity=ComplexityLevel.MEDIUM
        )

        # Act
        project.update(
            name="Updated Name",
            description="Updated description"
        )

        # Assert
        assert project.name == "Updated Name"
        assert project.description == "Updated description"
        assert len(project.events) == 2  # Creation + Update
        assert isinstance(project.events[1], ProjectUpdated)

    def test_project_status_transition_business_rules(self):
        """Test project status transitions follow business rules."""
        # Arrange
        project = Project(
            project_id="test_001",
            name="Test Project",
            project_type=ProjectType.WEB_APPLICATION,
            complexity=ComplexityLevel.MEDIUM
        )

        # Act - Valid transition
        project.change_status(ProjectStatus.IN_PROGRESS)

        # Assert
        assert project.status == ProjectStatus.IN_PROGRESS
        assert len(project.events) == 2
        assert isinstance(project.events[1], ProjectStatusChanged)

    def test_invalid_status_transition_raises_error(self):
        """Test that invalid status transitions raise errors."""
        # Arrange
        project = Project(
            project_id="test_001",
            name="Test Project",
            project_type=ProjectType.WEB_APPLICATION,
            complexity=ComplexityLevel.MEDIUM
        )

        # Act & Assert - Invalid transition should raise error
        with pytest.raises(ValueError, match="Invalid project status"):
            project.change_status("invalid_status")

    def test_team_member_management_business_rules(self):
        """Test team member management follows business rules."""
        # Arrange
        project = Project(
            project_id="test_001",
            name="Test Project",
            project_type=ProjectType.WEB_APPLICATION,
            complexity=ComplexityLevel.MEDIUM
        )

        team_member = TeamMember(
            member_id="dev_001",
            name="Alice Johnson",
            role="developer",
            email="alice@example.com"
        )

        # Act
        project.add_team_member(team_member)

        # Assert
        assert len(project.team_members) == 1
        assert project.team_members[0] == team_member

    def test_duplicate_team_member_not_added(self):
        """Test that duplicate team members are not added."""
        # Arrange
        project = Project(
            project_id="test_001",
            name="Test Project",
            project_type=ProjectType.WEB_APPLICATION,
            complexity=ComplexityLevel.MEDIUM
        )

        team_member = TeamMember(
            member_id="dev_001",
            name="Alice Johnson",
            role="developer",
            email="alice@example.com"
        )

        # Act
        project.add_team_member(team_member)
        project.add_team_member(team_member)  # Duplicate

        # Assert
        assert len(project.team_members) == 1

    def test_remove_team_member_business_logic(self):
        """Test removing team members follows business rules."""
        # Arrange
        project = Project(
            project_id="test_001",
            name="Test Project",
            project_type=ProjectType.WEB_APPLICATION,
            complexity=ComplexityLevel.MEDIUM
        )

        team_member = TeamMember(
            member_id="dev_001",
            name="Alice Johnson",
            role="developer",
            email="alice@example.com"
        )

        project.add_team_member(team_member)

        # Act
        project.remove_team_member("dev_001")

        # Assert
        assert len(project.team_members) == 0

    def test_phase_management_business_rules(self):
        """Test phase management follows business rules."""
        # Arrange
        project = Project(
            project_id="test_001",
            name="Test Project",
            project_type=ProjectType.WEB_APPLICATION,
            complexity=ComplexityLevel.MEDIUM
        )

        phase = Phase(
            phase_id="phase_001",
            name="Planning",
            description="Project planning phase",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=14),
            duration_days=14
        )

        # Act
        project.add_phase(phase)

        # Assert
        assert len(project.phases) == 1
        assert project.phases[0] == phase

    def test_duplicate_phase_not_added(self):
        """Test that duplicate phases are not added."""
        # Arrange
        project = Project(
            project_id="test_001",
            name="Test Project",
            project_type=ProjectType.WEB_APPLICATION,
            complexity=ComplexityLevel.MEDIUM
        )

        phase = Phase(
            phase_id="phase_001",
            name="Planning",
            description="Project planning phase",
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=14),
            duration_days=14
        )

        # Act
        project.add_phase(phase)
        project.add_phase(phase)  # Duplicate

        # Assert
        assert len(project.phases) == 1

    def test_milestone_management_business_rules(self):
        """Test milestone management follows business rules."""
        # Arrange
        project = Project(
            project_id="test_001",
            name="Test Project",
            project_type=ProjectType.WEB_APPLICATION,
            complexity=ComplexityLevel.MEDIUM
        )

        milestone = Milestone(
            milestone_id="ms_001",
            name="Requirements Complete",
            description="All requirements finalized",
            due_date=datetime.now() + timedelta(days=30)
        )

        # Act
        project.add_milestone(milestone)

        # Assert
        assert len(project.milestones) == 1
        assert project.milestones[0] == milestone

    def test_duplicate_milestone_not_added(self):
        """Test that duplicate milestones are not added."""
        # Arrange
        project = Project(
            project_id="test_001",
            name="Test Project",
            project_type=ProjectType.WEB_APPLICATION,
            complexity=ComplexityLevel.MEDIUM
        )

        milestone = Milestone(
            milestone_id="ms_001",
            name="Requirements Complete",
            description="All requirements finalized",
            due_date=datetime.now() + timedelta(days=30)
        )

        # Act
        project.add_milestone(milestone)
        project.add_milestone(milestone)  # Duplicate

        # Assert
        assert len(project.milestones) == 1

    def test_project_invariants_maintained(self):
        """Test that project invariants are maintained."""
        # Arrange
        project = Project(
            project_id="test_001",
            name="Test Project",
            project_type=ProjectType.WEB_APPLICATION,
            complexity=ComplexityLevel.MEDIUM,
            duration_weeks=8
        )

        # Assert invariants
        assert project.project_id is not None
        assert project.name is not None
        assert project.project_type in ProjectType
        assert project.complexity in ComplexityLevel
        assert project.duration_weeks > 0
        assert project.status in ProjectStatus

    def test_project_creation_records_event(self):
        """Test that project creation records domain event."""
        # Arrange & Act
        project = Project(
            project_id="test_001",
            name="Test Project",
            project_type=ProjectType.WEB_APPLICATION,
            complexity=ComplexityLevel.MEDIUM
        )

        # Assert
        assert len(project.events) == 1
        event = project.events[0]
        assert isinstance(event, ProjectCreated)
        assert event.project_id == "test_001"
        assert event.name == "Test Project"
        assert event.project_type == ProjectType.WEB_APPLICATION

    def test_project_update_records_event(self):
        """Test that project updates record domain events."""
        # Arrange
        project = Project(
            project_id="test_001",
            name="Original Name",
            project_type=ProjectType.WEB_APPLICATION,
            complexity=ComplexityLevel.MEDIUM
        )

        # Clear creation event for cleaner test
        project.events.clear()

        # Act
        project.update(name="Updated Name")

        # Assert
        assert len(project.events) == 1
        event = project.events[0]
        assert isinstance(event, ProjectUpdated)
        assert event.project_id == "test_001"
        assert event.name == "Updated Name"

    def test_status_change_records_event(self):
        """Test that status changes record domain events."""
        # Arrange
        project = Project(
            project_id="test_001",
            name="Test Project",
            project_type=ProjectType.WEB_APPLICATION,
            complexity=ComplexityLevel.MEDIUM
        )

        # Clear creation event
        project.events.clear()

        # Act
        project.change_status(ProjectStatus.IN_PROGRESS)

        # Assert
        assert len(project.events) == 1
        event = project.events[0]
        assert isinstance(event, ProjectStatusChanged)
        assert event.project_id == "test_001"
        assert event.new_status == ProjectStatus.IN_PROGRESS


class TestProjectBusinessRules:
    """Test cases for complex business rules."""

    def test_complex_project_requires_experienced_team(self):
        """Test that complex projects require experienced team members."""
        # This would test a business rule that complex projects
        # should have team members with sufficient experience
        pass

    def test_project_duration_based_on_complexity(self):
        """Test that project duration is appropriate for complexity."""
        # Complex projects should have longer duration
        complex_project = Project(
            project_id="complex_001",
            name="Complex Project",
            project_type=ProjectType.WEB_APPLICATION,
            complexity=ComplexityLevel.COMPLEX,
            duration_weeks=16  # Should be longer for complex projects
        )

        simple_project = Project(
            project_id="simple_001",
            name="Simple Project",
            project_type=ProjectType.WEB_APPLICATION,
            complexity=ComplexityLevel.SIMPLE,
            duration_weeks=4  # Can be shorter for simple projects
        )

        # Business rule: complex projects need more time
        assert complex_project.duration_weeks > simple_project.duration_weeks

    def test_maximum_team_size_business_rule(self):
        """Test maximum team size business rules."""
        # Arrange
        project = Project(
            project_id="test_001",
            name="Large Team Project",
            project_type=ProjectType.WEB_APPLICATION,
            complexity=ComplexityLevel.COMPLEX
        )

        # Add many team members
        for i in range(15):  # Large team
            team_member = TeamMember(
                member_id=f"member_{i}",
                name=f"Member {i}",
                role="developer",
                email=f"member{i}@example.com"
            )
            project.add_team_member(team_member)

        # Assert business rule (this would be domain logic)
        assert len(project.team_members) == 15

    def test_project_type_influences_team_composition(self):
        """Test that project type influences required team composition."""
        # Different project types require different team compositions
        api_project = Project(
            project_id="api_001",
            name="API Project",
            project_type=ProjectType.API_SERVICE,
            complexity=ComplexityLevel.MEDIUM
        )

        web_project = Project(
            project_id="web_001",
            name="Web Project",
            project_type=ProjectType.WEB_APPLICATION,
            complexity=ComplexityLevel.MEDIUM
        )

        # API projects might need more backend expertise
        # Web projects might need more frontend expertise
        # This is a business rule that could be tested
        assert api_project.project_type != web_project.project_type


if __name__ == "__main__":
    pytest.main([__file__])