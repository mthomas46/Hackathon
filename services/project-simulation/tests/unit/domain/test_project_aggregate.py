"""Unit Tests for Project Aggregate - Domain Driven Design Foundation.

This module contains comprehensive unit tests for the Project aggregate,
testing business rules, invariants, state transitions, and domain behavior.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from simulation.domain.entities.project import (
    Project, ProjectId, TeamMember, ProjectPhase
)
from simulation.domain.value_objects import (
    ProjectType, ComplexityLevel, ProjectStatus
)
from simulation.domain.events import (
    ProjectCreated, ProjectStatusChanged, ProjectPhaseCompleted
)


class TestProjectId:
    """Test cases for ProjectId value object."""

    def test_project_id_creation(self):
        """Test ProjectId creation with valid UUID."""
        test_uuid = uuid4()
        project_id = ProjectId(value=test_uuid)

        assert project_id.value == test_uuid
        assert str(project_id) == str(test_uuid)

    def test_project_id_from_string(self):
        """Test ProjectId creation from string."""
        test_uuid_str = str(uuid4())
        project_id = ProjectId.from_string(test_uuid_str)

        assert str(project_id.value) == test_uuid_str

    def test_project_id_equality(self):
        """Test ProjectId equality comparison."""
        uuid1 = uuid4()
        uuid2 = uuid4()

        id1a = ProjectId(value=uuid1)
        id1b = ProjectId(value=uuid1)
        id2 = ProjectId(value=uuid2)

        assert id1a == id1b
        assert id1a != id2

    def test_project_id_hash(self):
        """Test ProjectId hash for use in sets/dicts."""
        test_uuid = uuid4()
        project_id = ProjectId(value=test_uuid)

        # Should be hashable for use in sets and dict keys
        project_set = {project_id}
        assert len(project_set) == 1
        assert project_id in project_set


class TestTeamMember:
    """Test cases for TeamMember entity."""

    def test_team_member_creation(self):
        """Test TeamMember creation with valid data."""
        member = TeamMember(
            id="dev-001",
            name="John Doe",
            role="developer",
            expertise_level="senior",
            communication_style="direct",
            work_style="focused",
            specialization=["backend", "api"],
            productivity_multiplier=1.2
        )

        assert member.id == "dev-001"
        assert member.name == "John Doe"
        assert member.role == "developer"
        assert member.expertise_level == "senior"
        assert member.productivity_multiplier == 1.2

    def test_team_member_can_handle_task(self):
        """Test task handling capability."""
        member = TeamMember(
            id="dev-001",
            name="John Doe",
            role="developer",
            expertise_level="senior",
            communication_style="direct",
            work_style="focused",
            specialization=["backend", "api"]
        )

        # Should handle tasks in specialization
        assert member.can_handle_task("backend") == True
        assert member.can_handle_task("api") == True

        # Should handle tasks based on expertise
        assert member.can_handle_task("frontend") == True  # senior level

        # Should not handle unknown tasks with basic expertise
        basic_member = TeamMember(
            id="dev-002",
            name="Jane Smith",
            role="developer",
            expertise_level="junior",
            communication_style="collaborative",
            work_style="agile"
        )
        assert basic_member.can_handle_task("unknown") == False

    def test_team_member_productivity(self):
        """Test productivity calculation for tasks."""
        member = TeamMember(
            id="dev-001",
            name="John Doe",
            role="developer",
            expertise_level="senior",
            communication_style="direct",
            work_style="focused",
            specialization=["backend"],
            productivity_multiplier=1.3
        )

        # Full productivity for specialized task
        assert member.get_productivity_for_task("backend") == 1.3

        # Reduced productivity for non-specialized task
        assert member.get_productivity_for_task("frontend") == 1.3 * 0.7


class TestProjectPhase:
    """Test cases for ProjectPhase entity."""

    def test_project_phase_creation(self):
        """Test ProjectPhase creation with valid data."""
        phase = ProjectPhase(
            name="development",
            duration_days=14,
            deliverables=["api", "database", "tests"],
            dependencies=["design"],
            team_allocation={"developer": 3, "qa": 1}
        )

        assert phase.name == "development"
        assert phase.duration_days == 14
        assert phase.status == "pending"
        assert phase.start_date is None
        assert phase.end_date is None

    def test_project_phase_start(self):
        """Test starting a project phase."""
        phase = ProjectPhase(name="development", duration_days=14)
        start_time = datetime.now()

        phase.start_phase(start_time)

        assert phase.status == "in_progress"
        assert phase.start_date == start_time

    def test_project_phase_complete(self):
        """Test completing a project phase."""
        phase = ProjectPhase(name="development", duration_days=14)
        start_time = datetime.now() - timedelta(days=14)

        phase.start_phase(start_time)
        phase.complete_phase()

        assert phase.status == "completed"
        assert phase.end_date is not None

    def test_project_phase_duration_calculation(self):
        """Test duration calculation for active phase."""
        phase = ProjectPhase(name="development", duration_days=14)
        start_time = datetime.now() - timedelta(hours=5)

        phase.start_phase(start_time)

        # Should return duration since start
        duration = phase.get_duration_so_far()
        assert duration is not None
        assert duration.total_seconds() >= 5 * 3600  # At least 5 hours

    def test_project_phase_is_completed(self):
        """Test completion status checking."""
        phase = ProjectPhase(name="development", duration_days=14)

        assert phase.is_completed() == False

        phase.complete_phase()
        assert phase.is_completed() == True


class TestProjectAggregate:
    """Test cases for Project aggregate root."""

    def test_project_creation_web_app(self):
        """Test Project creation for web application type."""
        project = Project(
            id=ProjectId(),
            name="E-commerce Platform",
            description="Modern e-commerce solution",
            type=ProjectType.WEB_APPLICATION,
            team_size=5,
            complexity=ComplexityLevel.COMPLEX,
            duration_weeks=12
        )

        assert project.name == "E-commerce Platform"
        assert project.type == ProjectType.WEB_APPLICATION
        assert project.status == ProjectStatus.CREATED
        assert len(project.phases) == 5  # Web app has 5 default phases
        assert len(project.team_members) == 0

        # Check domain events
        events = project.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], ProjectCreated)

    def test_project_creation_api_service(self):
        """Test Project creation for API service type."""
        project = Project(
            id=ProjectId(),
            name="User API Service",
            description="REST API for user management",
            type=ProjectType.API_SERVICE,
            team_size=3,
            complexity=ComplexityLevel.MEDIUM,
            duration_weeks=8
        )

        assert project.type == ProjectType.API_SERVICE
        assert len(project.phases) == 4  # API service has 4 default phases

    def test_add_team_member_success(self):
        """Test successfully adding a team member."""
        project = Project(
            id=ProjectId(),
            name="Test Project",
            description="Test",
            type=ProjectType.WEB_APPLICATION,
            team_size=3,
            complexity=ComplexityLevel.SIMPLE,
            duration_weeks=4
        )

        member = TeamMember(
            id="dev-001",
            name="John Doe",
            role="developer",
            expertise_level="senior",
            communication_style="direct",
            work_style="focused"
        )

        project.add_team_member(member)

        assert len(project.team_members) == 1
        assert project.team_members[0].id == "dev-001"
        assert project.updated_at > project.created_at

    def test_add_team_member_exceeds_capacity(self):
        """Test adding team member beyond capacity fails."""
        project = Project(
            id=ProjectId(),
            name="Small Project",
            description="Test",
            type=ProjectType.WEB_APPLICATION,
            team_size=1,  # Only 1 member allowed
            complexity=ComplexityLevel.SIMPLE,
            duration_weeks=4
        )

        # Add first member
        member1 = TeamMember(id="dev-001", name="John", role="developer",
                           expertise_level="senior", communication_style="direct",
                           work_style="focused")
        project.add_team_member(member1)

        # Try to add second member - should fail
        member2 = TeamMember(id="dev-002", name="Jane", role="developer",
                           expertise_level="senior", communication_style="direct",
                           work_style="focused")

        with pytest.raises(ValueError, match="already has maximum team size"):
            project.add_team_member(member2)

    def test_add_duplicate_team_member(self):
        """Test adding duplicate team member fails."""
        project = Project(
            id=ProjectId(),
            name="Test Project",
            description="Test",
            type=ProjectType.WEB_APPLICATION,
            team_size=3,
            complexity=ComplexityLevel.SIMPLE,
            duration_weeks=4
        )

        member = TeamMember(
            id="dev-001",
            name="John Doe",
            role="developer",
            expertise_level="senior",
            communication_style="direct",
            work_style="focused"
        )

        # Add member first time
        project.add_team_member(member)

        # Try to add same member again - should fail
        with pytest.raises(ValueError, match="already exists"):
            project.add_team_member(member)

    def test_remove_team_member(self):
        """Test removing a team member."""
        project = Project(
            id=ProjectId(),
            name="Test Project",
            description="Test",
            type=ProjectType.WEB_APPLICATION,
            team_size=3,
            complexity=ComplexityLevel.SIMPLE,
            duration_weeks=4
        )

        member = TeamMember(
            id="dev-001",
            name="John Doe",
            role="developer",
            expertise_level="senior",
            communication_style="direct",
            work_style="focused"
        )

        project.add_team_member(member)
        assert len(project.team_members) == 1

        project.remove_team_member("dev-001")
        assert len(project.team_members) == 0

    def test_start_phase_success(self):
        """Test successfully starting a project phase."""
        project = Project(
            id=ProjectId(),
            name="Test Project",
            description="Test",
            type=ProjectType.WEB_APPLICATION,
            team_size=3,
            complexity=ComplexityLevel.SIMPLE,
            duration_weeks=4
        )

        # Start the first phase (planning - no dependencies)
        project.start_phase("planning")

        phase = project._get_phase("planning")
        assert phase.status == "in_progress"
        assert phase.start_date is not None

    def test_start_phase_with_dependencies(self):
        """Test starting a phase with unmet dependencies fails."""
        project = Project(
            id=ProjectId(),
            name="Test Project",
            description="Test",
            type=ProjectType.WEB_APPLICATION,
            team_size=3,
            complexity=ComplexityLevel.SIMPLE,
            duration_weeks=4
        )

        # Try to start development phase without completing planning
        with pytest.raises(ValueError, match="dependency.*not completed"):
            project.start_phase("development")

    def test_complete_phase(self):
        """Test completing a project phase."""
        project = Project(
            id=ProjectId(),
            name="Test Project",
            description="Test",
            type=ProjectType.WEB_APPLICATION,
            team_size=3,
            complexity=ComplexityLevel.SIMPLE,
            duration_weeks=4
        )

        project.start_phase("planning")
        project.complete_phase("planning")

        phase = project._get_phase("planning")
        assert phase.status == "completed"
        assert phase.end_date is not None

        # Check domain event was raised
        events = project.get_domain_events()
        phase_events = [e for e in events if isinstance(e, ProjectPhaseCompleted)]
        assert len(phase_events) == 1
        assert phase_events[0].phase_name == "planning"

    def test_update_status(self):
        """Test updating project status."""
        project = Project(
            id=ProjectId(),
            name="Test Project",
            description="Test",
            type=ProjectType.WEB_APPLICATION,
            team_size=3,
            complexity=ComplexityLevel.SIMPLE,
            duration_weeks=4
        )

        original_status = project.status
        project.update_status(ProjectStatus.IN_PROGRESS)

        assert project.status == ProjectStatus.IN_PROGRESS
        assert project.status != original_status

        # Check domain event was raised
        events = project.get_domain_events()
        status_events = [e for e in events if isinstance(e, ProjectStatusChanged)]
        assert len(status_events) == 1
        assert status_events[0].old_status == original_status.value
        assert status_events[0].new_status == ProjectStatus.IN_PROGRESS.value

    def test_get_current_phase(self):
        """Test getting the currently active phase."""
        project = Project(
            id=ProjectId(),
            name="Test Project",
            description="Test",
            type=ProjectType.WEB_APPLICATION,
            team_size=3,
            complexity=ComplexityLevel.SIMPLE,
            duration_weeks=4
        )

        # Initially no current phase
        assert project.get_current_phase() is None

        # Start a phase
        project.start_phase("planning")
        current_phase = project.get_current_phase()
        assert current_phase is not None
        assert current_phase.name == "planning"
        assert current_phase.status == "in_progress"

    def test_get_completed_phases(self):
        """Test getting completed phases."""
        project = Project(
            id=ProjectId(),
            name="Test Project",
            description="Test",
            type=ProjectType.WEB_APPLICATION,
            team_size=3,
            complexity=ComplexityLevel.SIMPLE,
            duration_weeks=4
        )

        # Initially no completed phases
        assert len(project.get_completed_phases()) == 0

        # Complete a phase
        project.start_phase("planning")
        project.complete_phase("planning")

        completed_phases = project.get_completed_phases()
        assert len(completed_phases) == 1
        assert completed_phases[0].name == "planning"

    def test_get_team_members_by_role(self):
        """Test filtering team members by role."""
        project = Project(
            id=ProjectId(),
            name="Test Project",
            description="Test",
            type=ProjectType.WEB_APPLICATION,
            team_size=5,
            complexity=ComplexityLevel.SIMPLE,
            duration_weeks=4
        )

        # Add members with different roles
        dev_member = TeamMember(
            id="dev-001", name="John", role="developer",
            expertise_level="senior", communication_style="direct", work_style="focused"
        )
        qa_member = TeamMember(
            id="qa-001", name="Jane", role="qa",
            expertise_level="senior", communication_style="direct", work_style="focused"
        )

        project.add_team_member(dev_member)
        project.add_team_member(qa_member)

        developers = project.get_team_members_by_role("developer")
        assert len(developers) == 1
        assert developers[0].id == "dev-001"

        qa_members = project.get_team_members_by_role("qa")
        assert len(qa_members) == 1
        assert qa_members[0].id == "qa-001"

    def test_calculate_progress_percentage(self):
        """Test project progress calculation."""
        project = Project(
            id=ProjectId(),
            name="Test Project",
            description="Test",
            type=ProjectType.WEB_APPLICATION,
            team_size=3,
            complexity=ComplexityLevel.SIMPLE,
            duration_weeks=4
        )

        # Initially 0% progress
        assert project.calculate_progress_percentage() == 0.0

        # Complete one phase out of five (20%)
        project.start_phase("planning")
        project.complete_phase("planning")
        assert project.calculate_progress_percentage() == 20.0

        # Complete another phase (40%)
        project.start_phase("design")
        project.complete_phase("design")
        assert project.calculate_progress_percentage() == 40.0

    def test_get_estimated_completion_date(self):
        """Test estimated completion date calculation."""
        created_at = datetime(2024, 1, 1)
        project = Project(
            id=ProjectId(),
            name="Test Project",
            description="Test",
            type=ProjectType.WEB_APPLICATION,
            team_size=3,
            complexity=ComplexityLevel.SIMPLE,
            duration_weeks=8
        )
        # Manually set created_at for testing
        object.__setattr__(project, 'created_at', created_at)

        estimated_completion = project.get_estimated_completion_date()
        expected_completion = created_at + timedelta(weeks=8)

        assert estimated_completion == expected_completion

    def test_is_overdue(self):
        """Test project overdue detection."""
        # Create project that should be completed in 4 weeks
        created_at = datetime.now() - timedelta(weeks=5)  # Created 5 weeks ago
        project = Project(
            id=ProjectId(),
            name="Test Project",
            description="Test",
            type=ProjectType.WEB_APPLICATION,
            team_size=3,
            complexity=ComplexityLevel.SIMPLE,
            duration_weeks=4
        )
        # Manually set created_at for testing
        object.__setattr__(project, 'created_at', created_at)

        assert project.is_overdue() == True

        # Test project that's still on time
        on_time_project = Project(
            id=ProjectId(),
            name="On Time Project",
            description="Test",
            type=ProjectType.WEB_APPLICATION,
            team_size=3,
            complexity=ComplexityLevel.SIMPLE,
            duration_weeks=12  # Plenty of time
        )

        assert on_time_project.is_overdue() == False

    def test_domain_events_management(self):
        """Test domain event collection and clearing."""
        project = Project(
            id=ProjectId(),
            name="Test Project",
            description="Test",
            type=ProjectType.WEB_APPLICATION,
            team_size=3,
            complexity=ComplexityLevel.SIMPLE,
            duration_weeks=4
        )

        # Should have ProjectCreated event initially
        events = project.get_domain_events()
        assert len(events) == 1
        assert isinstance(events[0], ProjectCreated)

        # Events should still be available after getting
        events_again = project.get_domain_events()
        assert len(events_again) == 1

        # Clear events
        project.clear_domain_events()
        assert len(project.get_domain_events()) == 0

        # New events should be collected after clearing
        project.update_status(ProjectStatus.IN_PROGRESS)
        new_events = project.get_domain_events()
        assert len(new_events) == 1
        assert isinstance(new_events[0], ProjectStatusChanged)

    def test_project_string_representation(self):
        """Test project string representations."""
        project_id = ProjectId()
        project = Project(
            id=project_id,
            name="Test Project",
            description="Test Description",
            type=ProjectType.WEB_APPLICATION,
            team_size=3,
            complexity=ComplexityLevel.SIMPLE,
            duration_weeks=4,
            status=ProjectStatus.IN_PROGRESS
        )

        expected_str = f"Project(id={project_id}, name='Test Project', status=in_progress)"
        assert str(project) == expected_str
        assert repr(project) == expected_str

    def test_project_phase_dependencies_validation(self):
        """Test phase dependency validation logic."""
        project = Project(
            id=ProjectId(),
            name="Test Project",
            description="Test",
            type=ProjectType.WEB_APPLICATION,
            team_size=3,
            complexity=ComplexityLevel.SIMPLE,
            duration_weeks=4
        )

        # Create custom phases with dependencies
        planning_phase = ProjectPhase(
            name="custom_planning",
            duration_days=5,
            deliverables=["plan"]
        )

        dev_phase = ProjectPhase(
            name="custom_development",
            duration_days=10,
            deliverables=["code"],
            dependencies=["custom_planning"]
        )

        # Manually set phases for testing
        object.__setattr__(project, 'phases', [planning_phase, dev_phase])

        # Should be able to start planning (no dependencies)
        project.start_phase("custom_planning")
        assert planning_phase.status == "in_progress"

        # Should not be able to start development yet
        with pytest.raises(ValueError, match="dependency.*not completed"):
            project.start_phase("custom_development")

        # After completing planning, should be able to start development
        project.complete_phase("custom_planning")
        project.start_phase("custom_development")
        assert dev_phase.status == "in_progress"
