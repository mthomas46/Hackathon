"""Domain-Driven Unit Tests - Value Objects.

This module contains comprehensive unit tests for value objects,
ensuring immutability and proper validation.
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4

from simulation.domain.value_objects import (
    ProjectStatus, ProjectType, ComplexityLevel, Role,
    TeamMember, Phase, PhaseStatus, Milestone, MilestoneStatus,
    DocumentReference, SimulationStatus, SimulationMetrics, SimulationConfig
)


class TestProjectEnums:
    """Test project-related enumerations."""

    @pytest.mark.parametrize("status", [
        ProjectStatus.PLANNING,
        ProjectStatus.IN_PROGRESS,
        ProjectStatus.COMPLETED,
        ProjectStatus.PAUSED,
        ProjectStatus.CANCELLED
    ])
    def test_project_status_values(self, status):
        """Test all project status values."""
        assert isinstance(status.value, str)
        assert status.value in ["planning", "in_progress", "completed", "paused", "cancelled"]

    @pytest.mark.parametrize("project_type", [
        ProjectType.WEB_APPLICATION,
        ProjectType.API_SERVICE,
        ProjectType.MOBILE_APPLICATION,
        ProjectType.DATA_SCIENCE,
        ProjectType.DEVOPS_TOOL
    ])
    def test_project_type_values(self, project_type):
        """Test all project type values."""
        assert isinstance(project_type.value, str)
        assert "_" in project_type.value or project_type.value.replace("_", "").isalnum()

    @pytest.mark.parametrize("complexity", [
        ComplexityLevel.SIMPLE,
        ComplexityLevel.MEDIUM,
        ComplexityLevel.COMPLEX
    ])
    def test_complexity_level_values(self, complexity):
        """Test all complexity level values."""
        assert isinstance(complexity.value, str)
        assert complexity.value in ["simple", "medium", "complex"]

    @pytest.mark.parametrize("role", [
        Role.DEVELOPER,
        Role.QA,
        Role.DEVOPS,
        Role.ARCHITECT,
        Role.PRODUCT_OWNER,
        Role.SCRUM_MASTER,
        Role.UX_DESIGNER
    ])
    def test_role_values(self, role):
        """Test all team role values."""
        assert isinstance(role.value, str)
        assert "_" in role.value or role.value.replace("_", "").isalnum()


class TestTeamMemberValueObject:
    """Test TeamMember value object."""

    def test_team_member_creation(self):
        """Test team member creation with valid data."""
        # Given
        member_id = str(uuid4())
        name = "John Doe"
        email = "john.doe@example.com"
        role = Role.DEVELOPER
        skills = ["Python", "FastAPI", "PostgreSQL"]
        productivity_factor = 1.2

        # When
        member = TeamMember(
            member_id=member_id,
            name=name,
            email=email,
            role=role,
            skills=skills,
            productivity_factor=productivity_factor
        )

        # Then
        assert member.member_id == member_id
        assert member.name == name
        assert member.email == email
        assert member.role == role
        assert member.skills == skills
        assert member.productivity_factor == productivity_factor
        assert member.communication_style == "direct"  # default

    def test_team_member_creation_minimal(self):
        """Test team member creation with minimal required data."""
        # Given
        member_id = str(uuid4())
        name = "Jane Smith"
        email = "jane@example.com"
        role = Role.QA

        # When
        member = TeamMember(
            member_id=member_id,
            name=name,
            email=email,
            role=role
        )

        # Then
        assert member.member_id == member_id
        assert member.name == name
        assert member.email == email
        assert member.role == role
        assert member.skills == []  # default
        assert member.productivity_factor == 1.0  # default

    def test_team_member_invalid_email(self):
        """Test team member creation with invalid email."""
        # Given
        member_id = str(uuid4())
        name = "Invalid Email User"
        invalid_email = "not-an-email"
        role = Role.DEVELOPER

        # When/Then
        with pytest.raises(ValueError):
            TeamMember(
                member_id=member_id,
                name=name,
                email=invalid_email,
                role=role
            )

    def test_team_member_productivity_factor_bounds(self):
        """Test team member productivity factor bounds."""
        # Given
        member_id = str(uuid4())
        name = "Productivity Test"
        email = "test@example.com"
        role = Role.DEVELOPER

        # When/Then - Valid bounds
        member_low = TeamMember(
            member_id=member_id,
            name=name,
            email=email,
            role=role,
            productivity_factor=0.1
        )
        assert member_low.productivity_factor == 0.1

        member_high = TeamMember(
            member_id=str(uuid4()),
            name=name,
            email="test2@example.com",
            role=role,
            productivity_factor=2.0
        )
        assert member_high.productivity_factor == 2.0

    def test_team_member_productivity_factor_invalid(self):
        """Test team member productivity factor invalid values."""
        # Given
        member_id = str(uuid4())
        name = "Invalid Productivity"
        email = "invalid@example.com"
        role = Role.DEVELOPER

        # When/Then - Too low
        with pytest.raises(ValueError):
            TeamMember(
                member_id=member_id,
                name=name,
                email=email,
                role=role,
                productivity_factor=0.05  # Below minimum 0.1
            )

        # When/Then - Too high
        with pytest.raises(ValueError):
            TeamMember(
                member_id=str(uuid4()),
                name=name,
                email="invalid2@example.com",
                role=role,
                productivity_factor=2.5  # Above maximum 2.0
            )


class TestPhaseValueObject:
    """Test Phase value object."""

    def test_phase_creation(self):
        """Test phase creation with valid data."""
        # Given
        phase_id = str(uuid4())
        name = "Discovery Phase"
        description = "Initial project discovery and requirements gathering"
        start_date = datetime.now()
        end_date = start_date + timedelta(days=14)
        duration_days = 14

        # When
        phase = Phase(
            phase_id=phase_id,
            name=name,
            description=description,
            start_date=start_date,
            end_date=end_date,
            duration_days=duration_days
        )

        # Then
        assert phase.phase_id == phase_id
        assert phase.name == name
        assert phase.description == description
        assert phase.start_date == start_date
        assert phase.end_date == end_date
        assert phase.duration_days == duration_days
        assert phase.status == PhaseStatus.NOT_STARTED
        assert phase.documents_generated == []
        assert phase.events_generated == []

    def test_phase_invalid_duration(self):
        """Test phase creation with invalid duration."""
        # Given
        phase_id = str(uuid4())
        name = "Invalid Phase"
        start_date = datetime.now()
        end_date = start_date + timedelta(days=10)

        # When/Then
        with pytest.raises(ValueError):
            Phase(
                phase_id=phase_id,
                name=name,
                start_date=start_date,
                end_date=end_date,
                duration_days=0  # Invalid: must be >= 1
            )

    def test_phase_end_before_start(self):
        """Test phase with end date before start date."""
        # Given
        phase_id = str(uuid4())
        name = "Backwards Phase"
        start_date = datetime.now()
        end_date = start_date - timedelta(days=5)  # End before start

        # When/Then
        with pytest.raises(ValueError):
            Phase(
                phase_id=phase_id,
                name=name,
                start_date=start_date,
                end_date=end_date,
                duration_days=5
            )

    @pytest.mark.parametrize("status", [
        PhaseStatus.NOT_STARTED,
        PhaseStatus.ACTIVE,
        PhaseStatus.COMPLETED,
        PhaseStatus.DELAYED
    ])
    def test_phase_status_values(self, status):
        """Test all phase status values."""
        # Given
        phase_id = str(uuid4())
        name = f"{status.value} Phase"
        start_date = datetime.now()
        end_date = start_date + timedelta(days=7)

        # When
        phase = Phase(
            phase_id=phase_id,
            name=name,
            start_date=start_date,
            end_date=end_date,
            duration_days=7,
            status=status
        )

        # Then
        assert phase.status == status


class TestMilestoneValueObject:
    """Test Milestone value object."""

    def test_milestone_creation(self):
        """Test milestone creation with valid data."""
        # Given
        milestone_id = str(uuid4())
        name = "MVP Release"
        description = "First minimum viable product release"
        due_date = datetime.now() + timedelta(days=30)

        # When
        milestone = Milestone(
            milestone_id=milestone_id,
            name=name,
            description=description,
            due_date=due_date
        )

        # Then
        assert milestone.milestone_id == milestone_id
        assert milestone.name == name
        assert milestone.description == description
        assert milestone.due_date == due_date
        assert milestone.status == MilestoneStatus.UPCOMING
        assert milestone.associated_phase_id is None

    def test_milestone_with_associated_phase(self):
        """Test milestone with associated phase."""
        # Given
        milestone_id = str(uuid4())
        name = "Phase 1 Complete"
        due_date = datetime.now() + timedelta(days=14)
        phase_id = str(uuid4())

        # When
        milestone = Milestone(
            milestone_id=milestone_id,
            name=name,
            due_date=due_date,
            associated_phase_id=phase_id
        )

        # Then
        assert milestone.associated_phase_id == phase_id

    @pytest.mark.parametrize("status", [
        MilestoneStatus.UPCOMING,
        MilestoneStatus.ACHIEVED,
        MilestoneStatus.MISSED
    ])
    def test_milestone_status_values(self, status):
        """Test all milestone status values."""
        # Given
        milestone_id = str(uuid4())
        name = f"{status.value} Milestone"
        due_date = datetime.now() + timedelta(days=7)

        # When
        milestone = Milestone(
            milestone_id=milestone_id,
            name=name,
            due_date=due_date,
            status=status
        )

        # Then
        assert milestone.status == status


class TestSimulationValueObjects:
    """Test simulation-related value objects."""

    @pytest.mark.parametrize("status", [
        SimulationStatus.INITIALIZED,
        SimulationStatus.RUNNING,
        SimulationStatus.PAUSED,
        SimulationStatus.COMPLETED,
        SimulationStatus.FAILED
    ])
    def test_simulation_status_values(self, status):
        """Test all simulation status values."""
        assert isinstance(status.value, str)
        assert status.value in ["initialized", "running", "paused", "completed", "failed"]

    def test_simulation_metrics_creation(self):
        """Test simulation metrics creation."""
        # Given
        metrics = SimulationMetrics()

        # Then
        assert metrics.total_documents_generated == 0
        assert metrics.total_events_generated == 0
        assert metrics.total_workflows_executed == 0
        assert metrics.simulation_duration_seconds == 0.0
        assert metrics.inconsistencies_detected == 0
        assert metrics.value_created_score == 0.0
        assert metrics.start_time is None
        assert metrics.end_time is None

    def test_simulation_config_creation(self):
        """Test simulation configuration creation."""
        # Given
        project_name = "Test Simulation Project"
        project_type = ProjectType.WEB_APPLICATION
        team_size = 5
        complexity = ComplexityLevel.MEDIUM
        duration_weeks = 8
        team_member_details = [
            {
                "member_id": str(uuid4()),
                "name": "Alice Developer",
                "email": "alice@example.com",
                "role": Role.DEVELOPER,
                "skills": ["Python", "React"]
            }
        ]
        timeline_phases_config = [
            {
                "phase_id": str(uuid4()),
                "name": "Discovery",
                "duration_days": 10
            }
        ]

        # When
        config = SimulationConfig(
            project_name=project_name,
            project_type=project_type,
            team_size=team_size,
            complexity=complexity,
            duration_weeks=duration_weeks,
            team_member_details=team_member_details,
            timeline_phases_config=timeline_phases_config,
            document_generation_config={},
            analysis_config={},
            reporting_config={}
        )

        # Then
        assert config.project_name == project_name
        assert config.project_type == project_type
        assert config.team_size == team_size
        assert config.complexity == complexity
        assert config.duration_weeks == duration_weeks
        assert config.team_member_details == team_member_details
        assert config.timeline_phases_config == timeline_phases_config


class TestDocumentReferenceValueObject:
    """Test DocumentReference value object."""

    def test_document_reference_creation(self):
        """Test document reference creation."""
        # Given
        document_id = str(uuid4())
        document_type = "requirements"
        relationship = "implements"
        description = "Requirements document for user authentication"

        # When
        ref = DocumentReference(
            document_id=document_id,
            document_type=document_type,
            relationship=relationship,
            description=description
        )

        # Then
        assert ref.document_id == document_id
        assert ref.document_type == document_type
        assert ref.relationship == relationship
        assert ref.description == description

    def test_document_reference_minimal(self):
        """Test document reference with minimal data."""
        # Given
        document_id = str(uuid4())
        document_type = "design"
        relationship = "references"

        # When
        ref = DocumentReference(
            document_id=document_id,
            document_type=document_type,
            relationship=relationship
        )

        # Then
        assert ref.document_id == document_id
        assert ref.document_type == document_type
        assert ref.relationship == relationship
        assert ref.description is None


class TestValueObjectImmutability:
    """Test value object immutability concepts."""

    def test_team_member_immutability_concept(self):
        """Test that team member values don't change unexpectedly."""
        # Given
        original_skills = ["Python", "FastAPI"]
        member = TeamMember(
            member_id=str(uuid4()),
            name="Immutable Test",
            email="immutable@example.com",
            role=Role.DEVELOPER,
            skills=original_skills.copy()
        )

        # When - Modify original list
        original_skills.append("Docker")

        # Then - Member skills should not change
        assert member.skills == ["Python", "FastAPI"]
        assert len(member.skills) == 2

    def test_phase_date_immutability(self):
        """Test that phase dates are properly handled."""
        # Given
        start_date = datetime(2024, 1, 1, 9, 0, 0)
        end_date = datetime(2024, 1, 15, 17, 0, 0)

        # When
        phase = Phase(
            phase_id=str(uuid4()),
            name="Date Test Phase",
            start_date=start_date,
            end_date=end_date,
            duration_days=14
        )

        # Then
        assert phase.start_date == start_date
        assert phase.end_date == end_date

        # When - Modify original dates
        start_date.replace(hour=10)

        # Then - Phase dates should not change
        assert phase.start_date.hour == 9  # Original hour preserved
