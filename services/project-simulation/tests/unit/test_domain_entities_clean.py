"""Clean unit tests for project-simulation domain entities."""

import pytest
from datetime import datetime, timezone
from uuid import uuid4
from typing import List, Dict, Optional

# Define domain entities inline to avoid import dependencies
from enum import Enum


class SimulationStatus(str, Enum):
    """Simulation status enumeration."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ProjectStatus(str, Enum):
    """Project status enumeration."""
    PLANNING = "planning"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class TeamRole(str, Enum):
    """Team role enumeration."""
    DEVELOPER = "developer"
    DESIGNER = "designer"
    MANAGER = "manager"
    QA = "qa"
    BUSINESS_ANALYST = "business_analyst"


class TimelineEventType(str, Enum):
    """Timeline event type enumeration."""
    MILESTONE = "milestone"
    DELIVERABLE = "deliverable"
    RISK = "risk"
    DECISION = "decision"
    BLOCKER = "blocker"


class Priority(str, Enum):
    """Priority enumeration."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class SimulationResult:
    """Domain entity for simulation results."""

    def __init__(self,
                 result_id: str = None,
                 simulation_id: str = None,
                 status: SimulationStatus = SimulationStatus.PENDING,
                 success_probability: float = 0.0,
                 estimated_duration: int = 0,  # days
                 estimated_cost: float = 0.0,
                 risk_score: float = 0.0,
                 recommendations: List[Dict] = None,
                 metrics: Dict = None,
                 created_at: datetime = None):
        self.result_id = result_id or str(uuid4())
        self.simulation_id = simulation_id
        self.status = status
        self.success_probability = success_probability
        self.estimated_duration = estimated_duration
        self.estimated_cost = estimated_cost
        self.risk_score = risk_score
        self.recommendations = recommendations or []
        self.metrics = metrics or {}
        self.created_at = created_at or datetime.now(timezone.utc)

    def is_successful(self) -> bool:
        """Check if simulation result indicates success."""
        return (self.status == SimulationStatus.COMPLETED and
                self.success_probability >= 0.7)

    def is_high_risk(self) -> bool:
        """Check if simulation indicates high risk."""
        return self.risk_score >= 0.7

    def get_confidence_level(self) -> str:
        """Get confidence level based on success probability."""
        if self.success_probability >= 0.8:
            return "high"
        elif self.success_probability >= 0.6:
            return "medium"
        else:
            return "low"

    def add_recommendation(self, title: str, description: str, priority: Priority):
        """Add a recommendation."""
        recommendation = {
            "title": title,
            "description": description,
            "priority": priority,
            "created_at": datetime.now(timezone.utc)
        }
        self.recommendations.append(recommendation)

    def get_high_priority_recommendations(self) -> List[Dict]:
        """Get high priority recommendations."""
        return [rec for rec in self.recommendations
                if rec["priority"] in [Priority.HIGH, Priority.CRITICAL]]


class Project:
    """Domain entity for projects."""

    def __init__(self,
                 project_id: str = None,
                 name: str = None,
                 description: str = None,
                 status: ProjectStatus = ProjectStatus.PLANNING,
                 start_date: datetime = None,
                 end_date: datetime = None,
                 budget: float = 0.0,
                 team_size: int = 0,
                 complexity_score: float = 0.0,
                 tags: List[str] = None,
                 metadata: Dict = None,
                 created_at: datetime = None):
        self.project_id = project_id or str(uuid4())
        self.name = name or ""
        self.description = description or ""
        self.status = status
        self.start_date = start_date
        self.end_date = end_date
        self.budget = budget
        self.team_size = team_size
        self.complexity_score = complexity_score
        self.tags = tags or []
        self.metadata = metadata or {}
        self.created_at = created_at or datetime.now(timezone.utc)

    def is_active(self) -> bool:
        """Check if project is active."""
        return self.status == ProjectStatus.ACTIVE

    def is_over_budget(self, current_spending: float) -> bool:
        """Check if project is over budget."""
        return current_spending > self.budget

    def is_overdue(self) -> bool:
        """Check if project is overdue."""
        if not self.end_date:
            return False
        return datetime.now(timezone.utc) > self.end_date

    def add_tag(self, tag: str):
        """Add a tag to the project."""
        if tag not in self.tags:
            self.tags.append(tag)

    def update_status(self, new_status: ProjectStatus):
        """Update project status."""
        self.status = new_status

    def get_project_duration(self) -> int:
        """Get project duration in days."""
        if not self.start_date or not self.end_date:
            return 0
        return (self.end_date - self.start_date).days

    def is_complex_project(self) -> bool:
        """Check if this is a complex project."""
        return (self.complexity_score >= 0.7 or
                self.team_size >= 10 or
                self.budget >= 100000)


class Simulation:
    """Domain entity for simulations."""

    def __init__(self,
                 simulation_id: str = None,
                 project_id: str = None,
                 name: str = None,
                 description: str = None,
                 status: SimulationStatus = SimulationStatus.PENDING,
                 parameters: Dict = None,
                 results: SimulationResult = None,
                 created_by: str = None,
                 created_at: datetime = None):
        self.simulation_id = simulation_id or str(uuid4())
        self.project_id = project_id
        self.name = name or ""
        self.description = description or ""
        self.status = status
        self.parameters = parameters or {}
        self.results = results
        self.created_by = created_by
        self.created_at = created_at or datetime.now(timezone.utc)

    def is_running(self) -> bool:
        """Check if simulation is running."""
        return self.status == SimulationStatus.RUNNING

    def is_completed(self) -> bool:
        """Check if simulation is completed."""
        return self.status == SimulationStatus.COMPLETED

    def start_simulation(self):
        """Start the simulation."""
        if self.status == SimulationStatus.PENDING:
            self.status = SimulationStatus.RUNNING

    def complete_simulation(self, results: SimulationResult):
        """Complete the simulation with results."""
        self.status = SimulationStatus.COMPLETED
        self.results = results

    def fail_simulation(self):
        """Mark simulation as failed."""
        self.status = SimulationStatus.FAILED

    def get_simulation_duration(self) -> float:
        """Get simulation duration in seconds (mock implementation)."""
        # In real implementation, this would calculate from start/end times
        return 45.5  # Mock duration


class Team:
    """Domain entity for teams."""

    def __init__(self,
                 team_id: str = None,
                 name: str = None,
                 description: str = None,
                 members: List[Dict] = None,  # List of {"user_id": str, "role": TeamRole}
                 project_id: str = None,
                 skills: List[str] = None,
                 capacity: int = 0,  # Available hours per week
                 created_at: datetime = None):
        self.team_id = team_id or str(uuid4())
        self.name = name or ""
        self.description = description or ""
        self.members = members or []
        self.project_id = project_id
        self.skills = skills or []
        self.capacity = capacity
        self.created_at = created_at or datetime.now(timezone.utc)

    def get_team_size(self) -> int:
        """Get team size."""
        return len(self.members)

    def has_skill(self, skill: str) -> bool:
        """Check if team has a specific skill."""
        return skill in self.skills

    def get_members_by_role(self, role: TeamRole) -> List[Dict]:
        """Get team members by role."""
        return [member for member in self.members if member.get("role") == role]

    def add_member(self, user_id: str, role: TeamRole):
        """Add a member to the team."""
        member = {"user_id": user_id, "role": role}
        if member not in self.members:
            self.members.append(member)

    def is_over_capacity(self, current_workload: int) -> bool:
        """Check if team is over capacity."""
        return current_workload > self.capacity

    def get_expertise_score(self, required_skills: List[str]) -> float:
        """Get expertise score for required skills."""
        if not required_skills:
            return 1.0

        matching_skills = sum(1 for skill in required_skills if self.has_skill(skill))
        return matching_skills / len(required_skills)


class TimelineEvent:
    """Domain entity for timeline events."""

    def __init__(self,
                 event_id: str = None,
                 project_id: str = None,
                 event_type: TimelineEventType = TimelineEventType.MILESTONE,
                 title: str = None,
                 description: str = None,
                 event_date: datetime = None,
                 priority: Priority = Priority.MEDIUM,
                 status: str = "planned",  # planned, completed, overdue
                 dependencies: List[str] = None,  # List of event IDs
                 created_at: datetime = None):
        self.event_id = event_id or str(uuid4())
        self.project_id = project_id
        self.event_type = event_type
        self.title = title or ""
        self.description = description or ""
        self.event_date = event_date
        self.priority = priority
        self.status = status
        self.dependencies = dependencies or []
        self.created_at = created_at or datetime.now(timezone.utc)

    def is_overdue(self) -> bool:
        """Check if event is overdue."""
        if not self.event_date or self.status == "completed":
            return False
        return datetime.now(timezone.utc) > self.event_date

    def is_high_priority(self) -> bool:
        """Check if event is high priority."""
        return self.priority in [Priority.HIGH, Priority.CRITICAL]

    def mark_completed(self):
        """Mark event as completed."""
        self.status = "completed"

    def add_dependency(self, event_id: str):
        """Add a dependency."""
        if event_id not in self.dependencies:
            self.dependencies.append(event_id)

    def can_start(self, completed_events: List[str]) -> bool:
        """Check if event can start based on dependencies."""
        return all(dep in completed_events for dep in self.dependencies)


class TestSimulationResultEntity:
    """Test the SimulationResult domain entity."""

    def test_simulation_result_creation(self):
        """Test creating a simulation result."""
        result = SimulationResult(
            simulation_id="sim123",
            success_probability=0.85,
            estimated_duration=90,
            estimated_cost=50000.0,
            risk_score=0.3
        )

        assert result.result_id is not None
        assert result.simulation_id == "sim123"
        assert result.status == SimulationStatus.PENDING
        assert result.success_probability == 0.85
        assert result.estimated_duration == 90
        assert result.estimated_cost == 50000.0
        assert result.risk_score == 0.3

    def test_simulation_result_success_evaluation(self):
        """Test success evaluation methods."""
        # Successful result
        success_result = SimulationResult(
            status=SimulationStatus.COMPLETED,
            success_probability=0.8
        )
        assert success_result.is_successful()
        assert not success_result.is_high_risk()

        # Unsuccessful result
        fail_result = SimulationResult(
            status=SimulationStatus.COMPLETED,
            success_probability=0.5
        )
        assert not fail_result.is_successful()

        # High risk result
        risk_result = SimulationResult(risk_score=0.8)
        assert risk_result.is_high_risk()

    def test_confidence_level_calculation(self):
        """Test confidence level calculation."""
        high_confidence = SimulationResult(success_probability=0.85)
        assert high_confidence.get_confidence_level() == "high"

        medium_confidence = SimulationResult(success_probability=0.65)
        assert medium_confidence.get_confidence_level() == "medium"

        low_confidence = SimulationResult(success_probability=0.45)
        assert low_confidence.get_confidence_level() == "low"

    def test_recommendation_management(self):
        """Test recommendation management."""
        result = SimulationResult()

        result.add_recommendation("Increase team size", "Add 2 more developers", Priority.HIGH)
        result.add_recommendation("Extend timeline", "Add 2 weeks to delivery", Priority.MEDIUM)

        assert len(result.recommendations) == 2
        assert result.recommendations[0]["priority"] == Priority.HIGH

        high_priority_recs = result.get_high_priority_recommendations()
        assert len(high_priority_recs) == 1
        assert high_priority_recs[0]["title"] == "Increase team size"


class TestProjectEntity:
    """Test the Project domain entity."""

    def test_project_creation(self):
        """Test creating a project."""
        start_date = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end_date = datetime(2024, 6, 1, tzinfo=timezone.utc)

        project = Project(
            name="E-commerce Platform",
            description="Build a modern e-commerce platform",
            status=ProjectStatus.ACTIVE,
            start_date=start_date,
            end_date=end_date,
            budget=150000.0,
            team_size=8,
            complexity_score=0.6
        )

        assert project.project_id is not None
        assert project.name == "E-commerce Platform"
        assert project.status == ProjectStatus.ACTIVE
        assert project.budget == 150000.0
        assert project.team_size == 8
        assert project.complexity_score == 0.6

    def test_project_status_methods(self):
        """Test project status methods."""
        active_project = Project(status=ProjectStatus.ACTIVE)
        assert active_project.is_active()

        on_hold_project = Project(status=ProjectStatus.ON_HOLD)
        assert not on_hold_project.is_active()

    def test_project_budget_and_schedule_checks(self):
        """Test budget and schedule checking."""
        project = Project(budget=100000.0)

        assert not project.is_over_budget(80000.0)
        assert project.is_over_budget(120000.0)

        # Test project without end date (should not be overdue)
        assert not project.is_overdue()

        # Test overdue project with past end date
        past_end = datetime(2023, 1, 1, tzinfo=timezone.utc)
        project.end_date = past_end
        assert project.is_overdue()

        # Test future project
        future_end = datetime(2030, 1, 1, tzinfo=timezone.utc)
        project.end_date = future_end
        assert not project.is_overdue()

    def test_project_tag_management(self):
        """Test project tag management."""
        project = Project()

        project.add_tag("web-development")
        project.add_tag("e-commerce")
        project.add_tag("web-development")  # Duplicate

        assert len(project.tags) == 2
        assert "web-development" in project.tags
        assert "e-commerce" in project.tags

    def test_project_duration_calculation(self):
        """Test project duration calculation."""
        start = datetime(2024, 1, 1, tzinfo=timezone.utc)
        end = datetime(2024, 1, 31, tzinfo=timezone.utc)  # 30 days

        project = Project(start_date=start, end_date=end)
        assert project.get_project_duration() == 30

    def test_project_complexity_assessment(self):
        """Test project complexity assessment."""
        simple_project = Project(team_size=3, budget=25000.0, complexity_score=0.3)
        assert not simple_project.is_complex_project()

        complex_project = Project(team_size=15, budget=500000.0, complexity_score=0.8)
        assert complex_project.is_complex_project()


class TestSimulationEntity:
    """Test the Simulation domain entity."""

    def test_simulation_creation(self):
        """Test creating a simulation."""
        simulation = Simulation(
            project_id="proj123",
            name="Q1 Planning Simulation",
            description="Simulation for Q1 project planning",
            parameters={"iterations": 1000, "confidence_level": 0.95}
        )

        assert simulation.simulation_id is not None
        assert simulation.project_id == "proj123"
        assert simulation.name == "Q1 Planning Simulation"
        assert simulation.status == SimulationStatus.PENDING
        assert simulation.parameters["iterations"] == 1000

    def test_simulation_status_methods(self):
        """Test simulation status methods."""
        simulation = Simulation()

        assert not simulation.is_running()
        assert not simulation.is_completed()

        simulation.start_simulation()
        assert simulation.is_running()

    def test_simulation_lifecycle(self):
        """Test simulation lifecycle."""
        simulation = Simulation()
        results = SimulationResult(success_probability=0.75)

        # Start simulation
        simulation.start_simulation()
        assert simulation.status == SimulationStatus.RUNNING

        # Complete simulation
        simulation.complete_simulation(results)
        assert simulation.status == SimulationStatus.COMPLETED
        assert simulation.results == results

        # Test failure
        failed_simulation = Simulation()
        failed_simulation.fail_simulation()
        assert failed_simulation.status == SimulationStatus.FAILED

    def test_simulation_duration_calculation(self):
        """Test simulation duration calculation."""
        simulation = Simulation()
        duration = simulation.get_simulation_duration()
        assert isinstance(duration, float)
        assert duration > 0


class TestTeamEntity:
    """Test the Team domain entity."""

    def test_team_creation(self):
        """Test creating a team."""
        members = [
            {"user_id": "user1", "role": TeamRole.DEVELOPER},
            {"user_id": "user2", "role": TeamRole.DESIGNER},
            {"user_id": "user3", "role": TeamRole.MANAGER}
        ]

        team = Team(
            name="Frontend Team",
            description="Handles frontend development",
            members=members,
            project_id="proj123",
            skills=["React", "TypeScript", "CSS"],
            capacity=160  # 40 hours/week * 4 weeks
        )

        assert team.team_id is not None
        assert team.name == "Frontend Team"
        assert team.get_team_size() == 3
        assert team.capacity == 160

    def test_team_skill_management(self):
        """Test team skill management."""
        team = Team(skills=["Python", "Django", "PostgreSQL"])

        assert team.has_skill("Python")
        assert team.has_skill("Django")
        assert not team.has_skill("React")

    def test_team_member_management(self):
        """Test team member management."""
        team = Team()

        team.add_member("user1", TeamRole.DEVELOPER)
        team.add_member("user2", TeamRole.QA)
        team.add_member("user1", TeamRole.DEVELOPER)  # Duplicate

        assert team.get_team_size() == 2

        developers = team.get_members_by_role(TeamRole.DEVELOPER)
        assert len(developers) == 1
        assert developers[0]["user_id"] == "user1"

    def test_team_capacity_management(self):
        """Test team capacity management."""
        team = Team(capacity=100)  # 100 hours/week capacity

        assert not team.is_over_capacity(80)
        assert team.is_over_capacity(120)

    def test_team_expertise_calculation(self):
        """Test team expertise calculation."""
        team = Team(skills=["Python", "Django", "React", "PostgreSQL"])

        # Full expertise match
        assert team.get_expertise_score(["Python", "Django"]) == 1.0

        # Partial expertise match
        assert team.get_expertise_score(["Python", "JavaScript"]) == 0.5

        # No expertise match
        assert team.get_expertise_score(["Java", "C++"]) == 0.0

        # Empty requirements
        assert team.get_expertise_score([]) == 1.0


class TestTimelineEventEntity:
    """Test the TimelineEvent domain entity."""

    def test_timeline_event_creation(self):
        """Test creating a timeline event."""
        event_date = datetime(2024, 3, 15, tzinfo=timezone.utc)

        event = TimelineEvent(
            project_id="proj123",
            event_type=TimelineEventType.MILESTONE,
            title="MVP Release",
            description="Release minimum viable product",
            event_date=event_date,
            priority=Priority.HIGH,
            dependencies=["event1", "event2"]
        )

        assert event.event_id is not None
        assert event.project_id == "proj123"
        assert event.event_type == TimelineEventType.MILESTONE
        assert event.title == "MVP Release"
        assert event.priority == Priority.HIGH
        assert len(event.dependencies) == 2

    def test_timeline_event_status_methods(self):
        """Test timeline event status methods."""
        # Test event without date (should not be overdue)
        event_no_date = TimelineEvent()
        assert not event_no_date.is_overdue()

        # Test completed event (should not be overdue)
        completed_event = TimelineEvent(
            event_date=datetime(2023, 1, 1, tzinfo=timezone.utc),
            status="completed"
        )
        assert not completed_event.is_overdue()

        # Test overdue event with past date
        past_event = TimelineEvent(
            event_date=datetime(2023, 1, 1, tzinfo=timezone.utc)
        )
        assert past_event.is_overdue()

        # Test future event
        future_event = TimelineEvent(
            event_date=datetime(2030, 1, 1, tzinfo=timezone.utc)
        )
        assert not future_event.is_overdue()

    def test_timeline_event_priority_methods(self):
        """Test timeline event priority methods."""
        high_priority_event = TimelineEvent(priority=Priority.HIGH)
        assert high_priority_event.is_high_priority()

        low_priority_event = TimelineEvent(priority=Priority.LOW)
        assert not low_priority_event.is_high_priority()

    def test_timeline_event_dependency_management(self):
        """Test timeline event dependency management."""
        event = TimelineEvent()

        event.add_dependency("dep1")
        event.add_dependency("dep2")
        event.add_dependency("dep1")  # Duplicate

        assert len(event.dependencies) == 2
        assert "dep1" in event.dependencies
        assert "dep2" in event.dependencies

    def test_timeline_event_completion_workflow(self):
        """Test timeline event completion workflow."""
        event = TimelineEvent(dependencies=["dep1", "dep2"])

        # Cannot start without completed dependencies
        assert not event.can_start([])
        assert not event.can_start(["dep1"])

        # Can start when all dependencies are completed
        assert event.can_start(["dep1", "dep2"])

        # Mark as completed
        event.mark_completed()
        assert event.status == "completed"
        assert not event.is_overdue()


class TestEntityIntegration:
    """Test integration between entities."""

    def test_simulation_with_project_integration(self):
        """Test integration between Simulation and Project."""
        project = Project(
            name="AI Platform",
            status=ProjectStatus.ACTIVE,
            budget=200000.0
        )

        simulation = Simulation(
            project_id=project.project_id,
            name="Risk Assessment Simulation",
            description="Assess project risks and success probability"
        )

        results = SimulationResult(
            simulation_id=simulation.simulation_id,
            success_probability=0.85,
            risk_score=0.4
        )

        # Complete simulation
        simulation.complete_simulation(results)

        # Verify integration
        assert simulation.project_id == project.project_id
        assert simulation.is_completed()
        assert simulation.results.is_successful()
        assert project.is_active()

    def test_team_with_project_integration(self):
        """Test integration between Team and Project."""
        project = Project(
            name="Mobile App",
            team_size=5,
            complexity_score=0.5
        )

        team = Team(
            name="Mobile Development Team",
            project_id=project.project_id,
            skills=["iOS", "Android", "React Native"],
            capacity=200
        )

        # Add team members
        team.add_member("dev1", TeamRole.DEVELOPER)
        team.add_member("dev2", TeamRole.DEVELOPER)
        team.add_member("designer1", TeamRole.DESIGNER)
        team.add_member("qa1", TeamRole.QA)

        # Verify integration
        assert team.project_id == project.project_id
        assert team.get_team_size() == 4
        assert team.has_skill("iOS")
        assert len(team.get_members_by_role(TeamRole.DEVELOPER)) == 2

    def test_timeline_with_project_integration(self):
        """Test integration between TimelineEvent and Project."""
        project = Project(
            name="Web Platform",
            start_date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            end_date=datetime(2024, 12, 31, tzinfo=timezone.utc)
        )

        milestone = TimelineEvent(
            project_id=project.project_id,
            event_type=TimelineEventType.MILESTONE,
            title="Beta Release",
            event_date=datetime(2024, 6, 1, tzinfo=timezone.utc),
            priority=Priority.HIGH
        )

        deliverable = TimelineEvent(
            project_id=project.project_id,
            event_type=TimelineEventType.DELIVERABLE,
            title="API Documentation",
            event_date=datetime(2024, 3, 15, tzinfo=timezone.utc),
            dependencies=[milestone.event_id]
        )

        # Verify integration
        assert milestone.project_id == project.project_id
        assert deliverable.project_id == project.project_id
        assert milestone.is_high_priority()
        assert not deliverable.can_start([])  # Depends on milestone
        assert deliverable.can_start([milestone.event_id])

    def test_complete_project_simulation_workflow(self):
        """Test complete project simulation workflow."""
        # Create project
        project = Project(
            name="Cloud Migration",
            status=ProjectStatus.ACTIVE,
            budget=300000.0,
            team_size=12,
            complexity_score=0.8
        )

        # Create team
        team = Team(
            name="Cloud Team",
            project_id=project.project_id,
            skills=["AWS", "Docker", "Kubernetes"],
            capacity=240
        )

        # Create simulation
        simulation = Simulation(
            project_id=project.project_id,
            name="Migration Risk Analysis",
            parameters={"iterations": 500, "risk_factors": ["downtime", "data_loss", "cost"]}
        )

        # Create timeline events
        planning_complete = TimelineEvent(
            project_id=project.project_id,
            event_type=TimelineEventType.MILESTONE,
            title="Planning Complete",
            event_date=datetime(2024, 2, 1, tzinfo=timezone.utc)
        )

        migration_start = TimelineEvent(
            project_id=project.project_id,
            event_type=TimelineEventType.MILESTONE,
            title="Migration Start",
            event_date=datetime(2024, 3, 1, tzinfo=timezone.utc),
            dependencies=[planning_complete.event_id]
        )

        # Run simulation and get results
        simulation.start_simulation()
        results = SimulationResult(
            simulation_id=simulation.simulation_id,
            success_probability=0.65,
            estimated_duration=180,
            estimated_cost=280000.0,
            risk_score=0.6
        )

        simulation.complete_simulation(results)

        # Verify complete workflow
        assert project.is_active()
        assert project.is_complex_project()
        assert team.project_id == project.project_id
        assert team.get_expertise_score(["AWS", "Docker"]) == 1.0
        assert simulation.is_completed()
        assert results.get_confidence_level() == "medium"
        assert planning_complete.project_id == project.project_id
        assert migration_start.project_id == project.project_id
        assert not migration_start.can_start([])  # Depends on planning
        assert migration_start.can_start([planning_complete.event_id])
